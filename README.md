# 🤖 Jarvis — My Personal AI Assistant

Jarvis is a local-first AI assistant built for Fedora Linux. It runs a fast, private local model when you're offline and switches to Gemini Flash when you're connected, with a voice interface, smart home control, and OS-level tool access — launched straight from your desktop, no terminal required.

> 🔒 Runs primarily on your machine. Cloud (Gemini) is used only when online and only for reasoning — voice stays local either way.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎤 **Voice Control** | Push-to-talk by default, or launch straight into listening with `--listen` |
| 🧠 **Hybrid Brain** | Gemini Flash when online, local Ollama model when offline — switches automatically |
| 🛠️ **OS Control** | Shell command execution and window management, gated behind confirmation prompts for anything destructive |
| 💬 **AI Chat** | Streaming responses in a clean PySide6 GUI |
| 🏠 **Smart Home** | Control TP-Link Kasa smart lights and plugs |
| 📅 **Planner** | Calendar events, alarms, and timers |
| 📰 **Daily Briefing** | AI-curated news |
| 🌤️ **Weather** | Current conditions and forecast on the dashboard |
| 🖥️ **System Monitor** | Real-time CPU/memory usage |
| 🖱️ **Desktop Launchers** | Click-to-open app icon, plus a separate voice-trigger icon — no terminal needed |

---

## 📋 Prerequisites

### Fedora system packages

```
sudo dnf install portaudio-devel python3-devel libsndfile-devel
```

### Required software

| Software | Purpose |
|---|---|
| Python 3.11 | Runtime |
| [Ollama](https://ollama.com/download) | Local model server (offline fallback) |
| Gemini API key | Cloud reasoning when online — free tier at [aistudio.google.com](https://aistudio.google.com) |

### Hardware

- **Minimum**: 8GB RAM
- **Recommended**: 16GB RAM, NVIDIA GPU with 6GB+ VRAM (speeds up the offline Ollama path)
- **Storage**: ~5GB for local models

> **Wayland note**: window focus/list/close controls are intentionally reported as unsupported on Wayland. Use an X11 session with `wmctrl` for those tools.

---

## 🚀 Setup

```bash
# Clone your repo
git clone https://github.com/ayaan523/Jarvis_v1.git
cd Jarvis_v1

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Pull a local model for the offline fallback:

```bash
ollama pull qwen3:1.7b
```

Create a `.env` file with your Gemini key:

```
GEMINI_API_KEY=your_key_here
```

Run it:

```bash
python main.py
```

Or jump straight into a listening session:

```bash
python main.py --listen
```

---

## 🖱️ Desktop Launchers (no terminal needed)

1. Copy the launcher files:
   ```bash
   cp desktop/*.desktop ~/.local/share/applications/
   ```
2. Edit the `Exec=` and `Icon=` paths inside those files to match your actual home directory.
3. Register them:
   ```bash
   update-desktop-database ~/.local/share/applications/
   ```
4. Press `Super`, search "Jarvis" — you'll see both **Jarvis** (normal launch) and **Jarvis (Voice)** (starts listening immediately). Right-click either to pin to Favorites.

---

## 🧠 How the Hybrid Backend Works

```
Online + Gemini reachable  →  Gemini Flash handles reasoning
Offline or Gemini fails    →  Falls back to local Ollama model
```

Connectivity is checked with a short-timeout reachability check (not just "is wifi on"), cached briefly so it's not re-checked on every message. If a request starts on Gemini and the connection drops mid-session, it retries on Ollama automatically rather than failing outright.

---

## ⚡ Lightweight by Default

- Push-to-talk instead of always-on wake word — no idle background listening
- `tiny` Whisper model for speech-to-text — small and fast
- Local intent router is skipped when Gemini is active online (Gemini handles routing itself); only used for the offline Ollama path
- Ollama only starts on-demand for the offline fallback, not as a permanent background service
- An optional `ULTRA_LIGHT_MODE` flag in `config.py` trims further (cloud audio, tray-only UI) at the cost of some response latency — off by default

---

## 🛠️ OS Control & Safety

Shell command execution is available as a tool but is:
- Off by default (`SHELL_TOOL_ENABLED = False` in `config.py`)
- Checked against a denylist of destructive patterns before running anything
- Never run with auto-elevated privileges — sudo always prompts interactively
- Logged to `logs/shell_commands.log` with timestamp and stated reason

---

## 🏗️ Project Structure

```
Jarvis_v1/
├── main.py                    # Entry point (supports --listen)
├── config.py                  # All configuration, including backend + safety flags
├── desktop/                   # .desktop launcher files
├── core/
│   ├── backends.py            # Gemini/Ollama backend abstraction
│   ├── hybrid_client.py       # Online/offline selection + failover
│   ├── gemini_client.py       # Gemini Flash integration
│   ├── gemini_live_audio.py   # Optional cloud audio (ultra-light mode)
│   ├── function_executor.py   # Tool execution, including shell/window control
│   ├── router.py              # Local intent classifier (offline path)
│   ├── stt.py / tts.py        # Local voice I/O
│   ├── kasa_control.py        # Smart home
│   ├── weather.py / news.py / tasks.py / calendar_manager.py
│   └── history.py             # Persistent chat history
├── gui/                       # PySide6 interface
└── tests/
    └── test_shell_tool.py     # Verifies the safety denylist
```

---

## 🔧 Troubleshooting

**Ollama connection refused** — run `ollama serve`, confirm the model's pulled with `ollama list`, check `OLLAMA_URL` in `config.py`.

**Gemini errors / rate limits** — free tier has request limits; the app should fail over to Ollama automatically, but if you're offline entirely and Ollama isn't running, start it manually.

**Voice not working** — check mic permissions, confirm `realtimestt` is installed, try `python main.py --listen`.

**Wayland window controls not working** — expected; switch to X11 for those specific tools.

---

Made for local, private, genuinely useful AI on my own machine.