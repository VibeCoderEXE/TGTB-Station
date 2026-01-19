import os, time, asyncio, httpx, re, threading, json, logging, sys
from urllib.parse import urlparse, parse_qs, unquote
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import webbrowser

# --- Telegram Libraries ---
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# --- BRANDING & ART ---
APP_NAME = "TGTB Station"
VERSION = "1.0.0"

ASCII_BLOCKS = [
r"""
 /$$$$$$$$ /$$$$$$  /$$$$$$$$ /$$$$$$$                             
|__  $$__//$$__  $$|__  $$__/| $$__  $$                            
   | $$  | $$  \__/   | $$   | $$  \ $$                            
   | $$  | $$ /$$$$   | $$   | $$$$$$$                             
   | $$  | $$|_  $$   | $$   | $$__  $$                            
   | $$  | $$  \ $$   | $$   | $$  \ $$                            
   | $$  |  $$$$$$/   | $$   | $$$$$$$/                            
   |__/   \______/    |__/   |_______/                             
""",
r"""
  $$$$$$\  $$$$$$$$\  $$$$$$\  $$$$$$$$\ $$$$$$\  $$$$$$\  $$\   $$\ 
 $$  __$$\ \__$$  __|$$  __$$\ \__$$  __|\_$$  _|$$  __$$\ $$$\  $$ |
 $$ /  \__|   $$ |   $$ /  $$ |   $$ |     $$ |  $$ /  $$ |$$$$\ $$ |
 \$$$$$$\     $$ |   $$$$$$$$ |   $$ |     $$ |  $$ |  $$ |$$ $$\$$ |
  \____$$\    $$ |   $$  __$$ |   $$ |     $$ |  $$ |  $$ |$$ \$$$$ |
 $$\   $$ |   $$ |   $$ |  $$ |   $$ |     $$ |  $$ |  $$ |$$ |\$$$ |
 \$$$$$$  |   $$ |   $$ |  $$ |   $$ |   $$$$$$\  $$$$$$  |$$ | \$$ |
  \______|    \__|   \__|  \__|   \__|   \______| \______/ \__|  \__|
"""
]

# --- UTILS ---
def format_size(size_bytes):
    if not size_bytes: return "0B"
    size_bytes = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0: return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', str(name)).strip()

class TorBoxClient:
    def __init__(self, api_key):
        self.key = api_key
        self.base = "https://api.torbox.app/v1/api"
        self.headers = {"Authorization": f"Bearer {self.key}"}

    async def add_magnet(self, magnet):
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(f"{self.base}/torrents/createtorrent", 
                                     headers=self.headers, data={"magnet": magnet})
                return r.json()
            except: return None

    async def get_torrent_details(self, t_id):
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.base}/torrents/mylist", headers=self.headers)
                return next((t for t in r.json().get('data', []) if str(t['id']) == str(t_id)), None)
            except: return None

    async def get_link(self, t_id, file_id):
        params = {"token": self.key, "torrent_id": t_id, "file_id": file_id, "redirect": "false"}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.base}/torrents/requestdl", params=params)
                return r.json().get('data')
            except: return None

class UplinkEngine:
    def __init__(self, app_ref):
        self.app = app_ref
        self.queue = asyncio.Queue()
        self.active = {"name": "IDLE", "speed": "0 MB/s", "percent": 0}

    async def worker(self, bot, client):
        while True:
            dtype, source, dest, msg = await self.queue.get()
            filename = os.path.basename(dest)
            self.active["name"] = filename
            self.app.log(f"📡 SIGNAL LOCKED: {filename}", "info")
            try:
                if dtype == "tg_file":
                    await self.download_tg(source, dest, msg, client)
                else:
                    await self.download_http(source, dest, msg)
                await msg.edit_text(f"✅ *SUCCESS:* `{filename}`", parse_mode='Markdown')
                self.app.log(f"✅ PACKET WRITTEN: {filename}", "success")
            except Exception as e:
                self.app.log(f"❌ SIGNAL DROPPED: {str(e)}", "error")
                try: await msg.edit_text(f"❌ *FAILED:* `{str(e)}`", parse_mode='Markdown')
                except: pass
            finally:
                self.active = {"name": "IDLE", "speed": "0 MB/s", "percent": 0}
                self.queue.task_done()

    async def download_http(self, url, dest, msg):
        start, last_edit = time.time(), 0
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            async with client.stream("GET", url) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                curr = 0
                with open(dest, "wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=131072):
                        f.write(chunk); curr += len(chunk)
                        elapsed = max(time.time() - start, 0.1)
                        speed = curr / elapsed / 1024 / 1024
                        percent = (curr / total * 100) if total > 0 else 0
                        self.active.update({"speed": f"{speed:.2f} MB/s", "percent": percent})
                        if time.time() - last_edit > 4.0 or curr == total:
                            last_edit = time.time()
                            try: await msg.edit_text(f"🚀 *UPLINKING:* `{percent:.1f}%` @ `{speed:.1f}MB/s`", parse_mode='Markdown')
                            except: pass

    async def download_tg(self, message_obj, dest, msg, client):
        start_time, last_edit = time.time(), 0
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        async def progress(current, total):
            nonlocal last_edit
            now = time.time()
            percent = (current / total) * 100
            speed = (current / 1024 / 1024) / (now - start_time) if (now - start_time) > 0 else 0
            self.active.update({"percent": percent, "speed": f"{speed:.1f} MB/s"})
            if now - last_edit > 4.0 or current == total:
                last_edit = now
                try: await msg.edit_text(f"📥 *TG DOWNLOAD:* `{percent:.1f}%` @ `{speed:.1f}MB/s`", parse_mode='Markdown')
                except: pass
        await client.download_media(message_obj, file=dest, progress_callback=progress)

class TGTBStationBot:
    def __init__(self, root):
        self.root = root
        self.settings_path = "settings.json"
        self.session_path = "tgtb_session.session"
        self.config = self.load_config()
        self.engine = UplinkEngine(self)
        self.session_data = {}
        self.is_online = False
        self.client = None
        self.setup_ui()
        sv_ttk.set_theme("dark")
        
        if not os.path.exists(self.settings_path) or not os.path.exists(self.session_path):
            self.root.after(500, self.show_config)
            
        threading.Thread(target=self.run_engine_thread, daemon=True).start()
        threading.Thread(target=self.ui_update_loop, daemon=True).start()
        self.splash_screen()

    def load_config(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f: return json.load(f)
        return {"token": "", "api_id": "", "api_hash": "", "torbox_key": "", "phone": "", "path": os.getcwd()}

    def setup_ui(self):
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("950x750")
        self.root.configure(bg="#050505")
        hdr = ttk.Frame(self.root, padding=10); hdr.pack(fill="x")
        self.status_tag = tk.Label(hdr, text="[ OFFLINE ]", bg="#050505", fg="#FF3131", font=("Consolas", 10, "bold"))
        self.status_tag.pack(side="left")
        ttk.Label(hdr, text=f"  {APP_NAME}", font=("Consolas", 12, "bold"), foreground="#00FF41").pack(side="left")
        ttk.Button(hdr, text="STATION CONFIG", command=self.show_config).pack(side="right")
        self.prog = ttk.Progressbar(self.root, mode="determinate"); self.prog.pack(fill="x", padx=20, pady=10)
        self.radar_lbl = ttk.Label(self.root, text="INITIALIZING...", font=("Consolas", 10), foreground="#00FF41"); self.radar_lbl.pack()
        self.console = tk.Text(self.root, bg="#000000", fg="#00FF41", font=("Consolas", 9), state="disabled", borderwidth=0, highlightthickness=1, highlightbackground="#00FF41")
        self.console.pack(expand=True, fill="both", padx=20, pady=20)

    def log(self, txt, type="info"):
        prefix = {"info": ">>", "success": "OK", "error": "!!", "system": "##"}.get(type, ">>")
        self.console.config(state="normal")
        self.console.insert("end", f"[{time.strftime('%H:%M:%S')}] {prefix} {txt}\n")
        self.console.see("end"); self.console.config(state="disabled")

    def splash_screen(self):
        self.console.config(state="normal")
        for block in ASCII_BLOCKS:
            for line in block.split("\n"):
                self.console.insert("end", line + "\n")
                self.root.update(); time.sleep(0.005)
            self.console.insert("end", "-"*80 + "\n")
        self.console.config(state="disabled")
        self.log(f"STATION READY. VERSION {VERSION}", "system")

    def ui_update_loop(self):
        i = 0
        radar = ["📡 SCANNING [ - - - - ]", "📡 SCANNING [ > - - - ]", "📡 SCANNING [ - > - - ]", "📡 SCANNING [ - - > - ]", "📡 SCANNING [ - - - > ]"]
        while True:
            if self.engine.active["name"] == "IDLE":
                self.radar_lbl.config(text=radar[i % 5]); i += 1
                self.prog['value'] = 0
            else:
                self.prog['value'] = self.engine.active['percent']
                self.radar_lbl.config(text=f"🛰️ {self.engine.active['name']} | {self.engine.active['speed']}")
            self.status_tag.config(text="[ ONLINE ]" if self.is_online else "[ OFFLINE ]", fg="#00FF41" if self.is_online else "#FF3131")
            time.sleep(0.5)

    def show_config(self):
        win = tk.Toplevel(self.root); win.title("Station Calibration")
        win.grab_set()
        cont = ttk.Frame(win, padding=20); cont.pack()
        
        fields = [
            ("token", "Bot Token from @BotFather", "Ex: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"),
            ("api_id", "Telegram API ID", "Ex: 1234567"),
            ("api_hash", "Telegram API Hash", "Ex: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"),
            ("torbox_key", "TorBox API Key", "Ex: tb_a1b2c3d4e5f6..."),
            ("phone", "Phone with Country Code", "Ex: +919876543210")
        ]
        
        entries = {}
        for f, label, placeholder in fields:
            ttk.Label(cont, text=label.upper(), font=("Consolas", 9, "bold")).pack(anchor="w")
            e = ttk.Entry(cont, width=55)
            e.insert(0, self.config.get(f, ""))
            if not e.get(): 
                e.insert(0, placeholder)
                e.config(foreground="grey")
            
            # Placeholder handling
            def on_focus_in(event, entry=e, ph=placeholder):
                if entry.get() == ph:
                    entry.delete(0, tk.END)
                    entry.config(foreground="white")
            def on_focus_out(event, entry=e, ph=placeholder):
                if not entry.get():
                    entry.insert(0, ph)
                    entry.config(foreground="grey")
            e.bind("<FocusIn>", on_focus_in)
            e.bind("<FocusOut>", on_focus_out)
            
            e.pack(pady=2)
            entries[f] = e
            
            if f == "torbox_key":
                link = tk.Label(cont, text="Don't have a key? Buy TorBox Subscription", fg="#00FF41", bg="#1c1c1c", cursor="hand2", font=("Consolas", 8, "underline"))
                link.pack(anchor="w", pady=(0, 5))
                link.bind("<Button-1>", lambda e: webbrowser.open("https://torbox.app/subscription?referral=4ce0906d-2f90-490a-a431-f908cff33277"))

        # Auth Section
        auth_row = ttk.Frame(cont)
        auth_row.pack(fill="x", pady=10)
        
        code_entry = ttk.Entry(auth_row, width=20)
        code_entry.insert(0, "Enter Code Here")
        code_entry.pack(side="left")
        
        def send_code():
            self.config['api_id'] = entries['api_id'].get()
            self.config['api_hash'] = entries['api_hash'].get()
            self.config['phone'] = entries['phone'].get()
            threading.Thread(target=self.req_tg_code, args=(code_entry,), daemon=True).start()

        ttk.Button(auth_row, text="SEND CODE", command=send_code).pack(side="left", padx=5)

        # Path Selection (Hidden/Disabled until login)
        path_row = ttk.Frame(cont)
        path_row.pack(fill="x", pady=5)
        path_entry = ttk.Entry(path_row, width=45)
        path_entry.insert(0, self.config.get("path", ""))
        path_entry.pack(side="left")
        
        def browse():
            p = filedialog.askdirectory()
            if p: path_entry.delete(0, tk.END); path_entry.insert(0, p)
        
        browse_btn = ttk.Button(path_row, text="📁", width=3, command=browse)
        browse_btn.pack(side="left", padx=2)
        
        # Save Section
        def final_save():
            for f in ["token", "api_id", "api_hash", "torbox_key", "phone"]:
                self.config[f] = entries[f].get()
            self.config["path"] = path_entry.get()
            with open(self.settings_path, 'w') as f: json.dump(self.config, f)
            self.log("[SYSTEM] RELOADING CONFIG...", "system")
            win.destroy()
            os.execv(sys.executable, ['python'] + sys.argv)

        save_btn = ttk.Button(cont, text="💾 SAVE CALIBRATION", command=final_save)
        save_btn.pack(pady=10)

    def req_tg_code(self, code_field):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.client = TelegramClient('tgtb_session', self.config['api_id'], self.config['api_hash'])
            loop.run_until_complete(self.client.connect())
            
            if not loop.run_until_complete(self.client.is_user_authorized()):
                res = loop.run_until_complete(self.client.send_code_request(self.config['phone']))
                self.log("📡 CODE SENT TO TELEGRAM.")
                
                # Wait for user to type code
                while code_field.get() == "Enter Code Here": time.sleep(1)
                
                loop.run_until_complete(self.client.sign_in(self.config['phone'], code_field.get()))
                self.log("✅ AUTHENTICATION SUCCESSFUL.", "success")
                messagebox.showinfo("Success", "Telegram Auth Success! You can now select path and save.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_engine_thread(self):
        if os.path.exists(self.settings_path):
            asyncio.run(self.main_async())

    async def main_async(self):
        if not self.config['token'] or not self.config['api_id']: return
        
        self.client = TelegramClient('tgtb_session', self.config['api_id'], self.config['api_hash'])
        await self.client.start()
        
        app = Application.builder().token(self.config['token']).build()
        tb = TorBoxClient(self.config['torbox_key'])
        await app.initialize()
        bot_info = await app.bot.get_me()

        async def monitor_torbox(t_id, cid):
            while True:
                t = await tb.get_torrent_details(t_id)
                if not t: break
                if t['progress'] >= 1 or t['download_finished']:
                    kb = [[InlineKeyboardButton("🚀 START LOCAL UPLINK", callback_data=f"EXP|{t_id}")]]
                    await app.bot.send_message(cid, f"🏁 *TORBOX CACHE COMPLETE:*\n`{t['name']}`\n\nClick below to begin local transfer:", 
                                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
                    break
                await asyncio.sleep(30)

        async def prompt_rename(u_or_q, cid, name):
            kb = [[InlineKeyboardButton("✅ Use Default", callback_data="CONFIRM_NAME")], [InlineKeyboardButton("✏️ Rename Manually", callback_data="MAN_RENAME")]]
            text = f"❓ *VERIFY FILENAME:*\n`{name}`"
            if hasattr(u_or_q, 'edit_message_text'): await u_or_q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            else: await app.bot.send_message(cid, text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

        async def show_folders(u_or_q, cid, path):
            sess = self.session_data[cid]
            sess["browsing_path"] = path
            try: folders = sorted([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])
            except: folders = []
            kb = [[InlineKeyboardButton("🎯 [DOWNLOAD HERE]", callback_data="FINAL")]]
            sess["folder_map"] = {}
            for f in folders:
                short = f[:25]; kb.append([InlineKeyboardButton(f"📁 {f}", callback_data=f"CD|{short}")])
                sess["folder_map"][short] = f
            if path != self.config['path']: kb.append([InlineKeyboardButton("⬅️ BACK", callback_data="BACK")])
            text = f"📂 *LOCATION:* `{path}`"
            if hasattr(u_or_q, 'edit_message_text'): await u_or_q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            else: await app.bot.send_message(cid, text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

        async def refresh_files(q, cid):
            sess = self.session_data[cid]; t = await tb.get_torrent_details(sess["t_id"])
            kb = []
            for f in t['files']:
                st = "✅" if f['id'] in sess["selected"] else "⬜"
                kb.append([InlineKeyboardButton(f"{st} [{format_size(f['size'])}] {f['name'][:30]}", callback_data=f"TOG|{f['id']}")])
            kb.append([InlineKeyboardButton("✅ ALL", callback_data="ALL"), InlineKeyboardButton("➡️ NEXT", callback_data="NEXT")])
            await q.edit_message_text(f"📄 *FILES:* `{t['name'][:40]}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

        @self.client.on(events.NewMessage)
        async def handle_tg_files(event):
            if event.document and event.message.to_id.user_id == bot_info.id:
                cid = event.sender_id
                fname = event.file.name or f"file_{int(time.time())}.dat"
                self.session_data[cid] = {"type": "tg_file", "source": event.message, "name": fname}
                self.log(f"📩 BOT SIGNAL: {fname}")
                await prompt_rename(event, cid, fname)

        async def msg_handler(update, context):
            txt = update.message.text.strip(); cid = update.message.chat_id
            if cid in self.session_data and self.session_data[cid].get("awaiting_name"):
                self.session_data[cid]["name"] = txt; self.session_data[cid]["awaiting_name"] = False
                return await show_folders(update, cid, self.config['path'])
            
            if txt.startswith("magnet:"):
                res = await tb.add_magnet(txt)
                if res and res.get('success'):
                    t_id = res['data']['torrent_id']
                    self.log(f"🧲 MAGNET ADDED: {t_id}")
                    await update.message.reply_text(f"🧲 *MAGNET ADDED TO TORBOX:*\nID: `{t_id}`\n_Monitoring cloud progress..._", parse_mode='Markdown')
                    asyncio.create_task(monitor_torbox(t_id, cid))
                return

            if txt.startswith("http"):
                fname = unquote(os.path.basename(urlparse(txt).path)) or "file.bin"
                self.session_data[cid] = {"type": "direct", "source": txt, "name": fname}
                await prompt_rename(update, cid, fname)

        async def cb_handler(update, context):
            q = update.callback_query; await q.answer(); d = q.data.split('|'); cid = q.message.chat_id
            sess = self.session_data.get(cid)
            if d[0] == "EXP":
                t = await tb.get_torrent_details(d[1])
                self.session_data[cid] = {"type": "torbox", "t_id": d[1], "selected": [], "t_name": t['name']}
                await refresh_files(q, cid)
            elif d[0] == "TOG":
                fid = int(d[1]); sess["selected"] = sess["selected"] + [fid] if fid not in sess["selected"] else [x for x in sess["selected"] if x != fid]
                await refresh_files(q, cid)
            elif d[0] == "ALL":
                t = await tb.get_torrent_details(sess["t_id"])
                sess["selected"] = [f['id'] for f in t['files']]
                await refresh_files(q, cid)
            elif d[0] == "NEXT":
                t = await tb.get_torrent_details(sess["t_id"])
                if len(sess["selected"]) == 1:
                    sess["name"] = os.path.basename(next(f['name'] for f in t['files'] if f['id'] == sess["selected"][0]))
                    await prompt_rename(q, cid, sess["name"])
                else:
                    sess["name"] = t['name'] # Using Torrent Name for multiple files
                    await show_folders(q, cid, self.config['path'])
            elif d[0] == "MAN_RENAME":
                sess["awaiting_name"] = True
                await q.edit_message_text("⌨️ *Enter new filename with extension:*", parse_mode='Markdown')
            elif d[0] == "CONFIRM_NAME": await show_folders(q, cid, self.config['path'])
            elif d[0] == "CD": await show_folders(q, cid, os.path.join(sess["browsing_path"], sess["folder_map"][d[1]]))
            elif d[0] == "BACK": await show_folders(q, cid, os.path.dirname(sess["browsing_path"]))
            elif d[0] == "FINAL":
                await q.edit_message_text("🚀 *UPLINK QUEUED*")
                if sess["type"] == "torbox":
                    t_details = await tb.get_torrent_details(sess["t_id"])
                    # Create parent folder if multiple files selected
                    base_path = sess["browsing_path"]
                    if len(sess["selected"]) > 1:
                        base_path = os.path.join(base_path, sanitize_filename(t_details['name']))
                    
                    for fid in sess["selected"]:
                        url = await tb.get_link(sess["t_id"], fid)
                        f_name = next(f['name'] for f in t_details['files'] if f['id'] == fid)
                        final_fn = sess["name"] if len(sess["selected"]) == 1 else os.path.basename(f_name)
                        dest = os.path.join(base_path, sanitize_filename(final_fn))
                        await self.engine.queue.put(("direct", url, dest, await q.message.reply_text(f"⏳ `{final_fn}`")))
                else:
                    dest = os.path.join(sess["browsing_path"], sanitize_filename(sess["name"]))
                    await self.engine.queue.put((sess["type"], sess["source"], dest, q.message))

        async def tb_cmd(u, c):
            q_str = " ".join(c.args)
            async with httpx.AsyncClient() as client_h:
                r = await client_h.get(f"{tb.base}/torrents/mylist", headers=tb.headers)
                hits = [t for t in r.json().get('data', []) if q_str.lower() in t['name'].lower()]
            kb = [[InlineKeyboardButton(f"[{format_size(t['size'])}] {t['name'][:35]}", callback_data=f"EXP|{t['id']}")] for t in hits]
            await u.message.reply_text("📦 *TORBOX SOURCE:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

        app.add_handler(CommandHandler("TB", lambda u, c: asyncio.create_task(tb_cmd(u, c))))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
        app.add_handler(CallbackQueryHandler(cb_handler))
        
        asyncio.create_task(self.engine.worker(app.bot, self.client))
        self.is_online = True
        await app.start(); await app.updater.start_polling()
        await self.client.run_until_disconnected()

if __name__ == "__main__":
    root = tk.Tk(); TGTBStationBot(root); root.mainloop()