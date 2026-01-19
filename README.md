<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-00FF41?style=for-the-badge&logo=github&logoColor=white" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Powered%20By-TorBox-blue?style=for-the-badge" alt="TorBox">

  <h1>🛰️ TGTB Station</h1>
  <p><i>The ultimate bridge between Telegram, TorBox, and your Local Storage.</i></p>
</div>

<hr>

<h2>📖 Overview</h2>
<p>
  <b>TGTB Station</b> is a high-performance automation station designed to turn your Telegram bot into a remote control for your media server. It intercepts Magnet links, handles cloud caching via TorBox, and "uplinks" files directly to your local machine with an interactive folder browser and a real-time hacker-style console.
</p>

<h2>🚀 Key Features</h2>
<ul>
  <li><b>🧲 Magnet Automation:</b> Send a magnet link; the bot adds it to TorBox and notifies you when the cloud cache is 100% ready.</li>
  <li><b>📂 Smart Local Indexing:</b> Navigate your PC/Server folders directly through Telegram buttons to choose download destinations.</li>
  <li><b>📦 Multi-File Intelligence:</b> Automatically groups multiple files from a single torrent into a clean parent folder.</li>
  <li><b>⚡ Dual-Engine Uplink:</b> Utilizes <b>Telethon (MTProto)</b> for Telegram files and <b>HTTPX</b> for high-speed TorBox streams.</li>
  <li><b>🖥️ Hacker UI:</b> A sleek, dark-themed Windows GUI with a real-time log console and "Radar" status updates.</li>
</ul>

<h2>🛠️ Installation</h2>
<pre><code>
# 1. Clone the repository
git clone https://github.com/VibeCoderEXE/TGTB-Station.git

# 2. Enter the directory
cd TGTB-Station

# 3. Install dependencies
pip install python-telegram-bot telethon httpx sv-ttk
</code></pre>

<h2>🚦 How to Use</h2>
<ol>
  <li><b>Calibration:</b> On first launch, the <b>Station Config</b> window will appear.</li>
  <li><b>Authentication:</b> Enter your Bot Token, API ID/Hash, and Phone Number. Click <b>SEND CODE</b> and enter the code from your Telegram app.</li>
  <li><b>Set Root Path:</b> Select the folder on your computer where you want files to be saved.</li>
  <li><b>Save & Restart:</b> The station will log <code>RELOADING CONFIG...</code> and reboot automatically.</li>
  <li><b>Operate:</b> Start forwarding files or pasting Magnet links to your bot!</li>
</ol>

<h2>🎮 Commands</h2>
<table>
  <tr>
    <th>Command</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><code>/TB [query]</code></td>
    <td>Search your TorBox cloud library for specific files.</td>
  </tr>
  <tr>
    <td><code>magnet:?xt...</code></td>
    <td>Paste any magnet link to start the cloud-to-local automation.</td>
  </tr>
</table>

<br>

<div align="center">
  <h3>🤝 Support the Project</h3>
  <p>Don't have a TorBox account? Support development by signing up here:</p>
  <a href="https://torbox.app/subscription?referral=4ce0906d-2f90-490a-a431-f908cff33277">
    <img src="https://img.shields.io/badge/Get%20TorBox%20Premium-00FF41?style=for-the-badge&logo=target&logoColor=black" alt="TorBox Referral">
  </a>
</div>

<hr>

<div align="center">
  <p>Developed by <b>VibeCoderEXE</b> | 🛰️ <i>TGTB Station - Signal Locked.</i></p>
</div>
