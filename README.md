<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-00FF41?style=for-the-badge&logo=github&logoColor=white" alt="Version">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
  
  <br><br>

  <p><b>POWERED BY:</b></p>
  <img src="https://img.shields.io/badge/Telegram-26A5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/TorBox-0061FE?style=for-the-badge&logo=dropbox&logoColor=white" alt="TorBox">
  <img src="https://img.shields.io/badge/VibeCoderEXE-00FF41?style=for-the-badge&logo=target&logoColor=black" alt="VibeCoderEXE">

  <h1>🛰️ TGTB Station</h1>
  <p><i>The ultimate bridge between Telegram, TorBox, and your Local Storage.</i></p>

  <br>

  <a href="https://github.com/VibeCoderEXE/TGTB-Station/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD-STATION_EXE-00FF41?style=for-the-badge&logo=windows&logoColor=black" height="45" alt="Download EXE">
  </a>
  <p><sub>Latest Stable Release: v1.0.0</sub></p>
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
  <li><b>📦 Multi-File Intelligence:</b> Automatically groups multiple files from a single torrent into a clean parent folder named after the torrent.</li>
  <li><b>⚡ Dual-Engine Uplink:</b> Utilizes <b>Telethon (MTProto)</b> for Telegram files and <b>HTTPX</b> for high-speed TorBox streams.</li>
  <li><b>🖥️ Hacker UI:</b> A sleek, dark-themed Windows GUI with a real-time log console and "Radar" status updates.</li>
</ul>

<h2>🚦 Getting Started</h2>
<h3>Option A: Using the Executable (Recommended)</h3>
<ol>
  <li>Download <code>TGTB_Station.exe</code> from the <b>Releases</b> section.</li>
  <li>Run the file. On first launch, the <b>Station Calibration</b> window will appear automatically.</li>
  <li>Enter your credentials and click <b>SEND CODE</b>. Enter the authentication code sent to your Telegram app.</li>
  <li>Set your local root download path and click <b>SAVE</b>. The app will reload and go online.</li>
</ol>

<h3>Option B: Running from Source</h3>
<pre><code>
# Clone and Install
git clone https://github.com/VibeCoderEXE/TGTB-Station.git
cd TGTB-Station
pip install -r requirements.txt

# Run
python main.py
</code></pre>

<h2>🎮 Commands</h2>
<table>
  <tr>
    <th align="left">Command</th>
    <th align="left">Description</th>
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
