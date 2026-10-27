# 📦 Complete Installation & Architecture Reference ("What is What")

**ARIA — Autonomous Resident Intelligence Agent**  
*Open-Source Linux Assistant • Wayland Native • DPDP Compliant*

---

## 📋 Table of Contents
1. [System Requirements & Compatibility](#1-system-requirements--compatibility)
2. [Automated One-Shot Installation](#2-automated-one-shot-installation-recommended)
3. [Manual Step-by-Step Installation](#3-manual-step-by-step-installation)
4. ["What is What" — Codebase & Subsystem Reference](#4-what-is-what--codebase--subsystem-reference)
5. [AI Provider Configuration](#5-ai-provider-configuration)
6. [Air-Gapped / Offline Local Execution](#6-air-gapped--offline-local-execution)
7. [Troubleshooting & Diagnostics](#7-troubleshooting--diagnostics)

---

## 1. System Requirements & Compatibility

| Component | Minimum Specification | Recommended |
|---|---|---|
| **Operating System** | Linux (Ubuntu 22.04+, Debian 12+, Fedora 38+, Arch) | Ubuntu 24.04 LTS |
| **Display Server** | Wayland or X11 | Wayland native session |
| **Desktop Environment** | GNOME 42+, KDE Plasma 5/6, Sway, Hyprland | GNOME 44+ |
| **Python** | Python 3.10+ | Python 3.12+ |
| **RAM** | 4 GB | 8 GB+ (especially for local Whisper / Ollama) |
| **Audio** | Microphone input via PulseAudio / PipeWire / ALSA | PipeWire |

---

## 2. Automated One-Shot Installation (Recommended)

Clone the repository and run the automated installer:
```bash
git clone https://github.com/<your-username>/Linux-Agent.git
cd Linux-Agent
bash install.sh
```

### What `install.sh` does automatically:
1. Installs native system packages (`ydotool`, `grim`, `slurp`, `wl-clipboard`, `libportaudio2`, `ffmpeg`, `python3-pyqt6`).
2. Creates the Python virtual environment (`.venv`) with system site-packages for PyQt6.
3. Installs pinned dependencies from `requirements.txt`.
4. Installs the Playwright Chromium browser bundle.
5. Adds your user account to the `input` group for kernel `/dev/uinput` automation.
6. Configures and enables systemd user services (`ydotoold.service` and `aria.service`).
7. Registers GNOME's native global shortcut for `Ctrl+Space`.
8. Automatically launches the **Interactive Walkthrough** upon desktop completion!

---

## 3. Manual Step-by-Step Installation

If you prefer installing components manually without running the script:

### Step 1: Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip python3-venv python3-dev python3-pyqt6 \
    libportaudio2 portaudio19-dev ydotool grim slurp wtype \
    wl-clipboard gcc pkg-config ffmpeg
```

### Step 2: Set Up Python Virtual Environment
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Configure User Groups for Wayland Input Control
To allow `ydotool` to inject keystrokes and mouse clicks on Wayland without root:
```bash
sudo usermod -aG input $USER
echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/80-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
*(Note: You may need to log out and log back in once for group membership to activate).*

### Step 4: Configure systemd User Services
Create `~/.config/systemd/user/ydotoold.service`:
```ini
[Unit]
Description=ydotool daemon for Wayland input automation
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/ydotoold --socket-path /run/user/%U/ydotoold.socket --socket-own %U:input
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
```

Create `~/.config/systemd/user/aria.service`:
```ini
[Unit]
Description=ARIA — Autonomous Resident Intelligence Agent
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory=%h/.aria/app
ExecStart=%h/.aria/run_daemon.sh
Restart=on-failure
RestartSec=3
TimeoutStopSec=3
EnvironmentFile=-%h/.aria/app/.env

[Install]
WantedBy=default.target
```

Enable and start services:
```bash
systemctl --user daemon-reload
systemctl --user enable --now ydotoold.service
systemctl --user enable --now aria.service
```

### Step 5: Register GNOME Global Hotkey
```bash
.venv/bin/python -c "
from aria.utils.shortcuts import register_gnome_shortcut
from aria.config import config
register_gnome_shortcut(config.hotkey)
"
```

---

## 4. "What is What" — Codebase & Subsystem Reference

Here is a comprehensive directory and architectural breakdown explaining what each module does:

```
Linux-Agent/
├── aria/                             # Core Python Package
│   ├── main.py                       # Main application entry point: starts system tray, HUD, and IPC server
│   ├── config.py                     # Typed configuration loader, .env parsing, POSIX permission hardening
│   ├── hotkey.py                     # Global hotkey registration and Unix domain socket listener (~/.aria/aria.sock)
│   ├── toggle.py                     # Fast CLI toggle command invoked by desktop shortcut keybindings
│   │
│   ├── agent/                        # Autonomous Brain (ReAct Loop)
│   │   ├── core.py                   # ReAct (Reason + Act) loop driver with streaming event bus
│   │   ├── planner.py                # System prompt, capabilities manifest, and tool schemas
│   │   ├── executor.py               # Tool dispatcher with security checks and exception handlers
│   │   └── memory.py                 # SQLite relational history + ChromaDB semantic vector database
│   │
│   ├── gui/                          # Swiss Modernism 2.0 Desktop Application
│   │   ├── app.py                    # GUI dispatcher and first-time walkthrough launcher
│   │   ├── dashboard.py              # Control Center window: status hero banner, quick actions, history logs
│   │   ├── onboarding.py             # 5-stage interactive onboarding & guided walkthrough wizard
│   │   ├── settings_dialog.py        # 6-tab system configuration matrix (Engine, Hotkey, Safety, Voice, Memory, System)
│   │   ├── icons.py                  # Professional 24x24 stroke-based SVG vector icon engine (25 vector icons)
│   │   ├── widgets.py                # Custom widgets: ToggleSwitch, ActionCard, StatusBadge, HotkeyPicker
│   │   └── styles.qss                # Swiss Modernism 2.0 QSS stylesheet (carbon palette, hairline borders)
│   │
│   ├── overlay/                      # Floating User Interface
│   │   ├── hud.py                    # Translucent frameless Spotlight/Raycast-like overlay HUD window
│   │   ├── tray.py                   # System tray icon with modern context menu
│   │   └── styles.qss                # Overlay HUD styling, command inputs, and monospace transcripts
│   │
│   ├── providers/                    # Swappable Multimodal LLM Backends
│   │   ├── base.py                   # Base abstract provider interface
│   │   ├── gemini.py                 # Google Gemini 2.0 Flash / Pro multimodal adapter
│   │   ├── openai_p.py               # OpenAI GPT-4o / o1 visual reasoning adapter
│   │   ├── claude.py                 # Anthropic Claude 3.5 Sonnet computer-use adapter
│   │   └── ollama_p.py               # Local offline Ollama endpoint adapter
│   │
│   ├── tools/                        # Workstation Computer-Use Tools
│   │   ├── screen.py                 # Lossless Wayland (grim) and X11 screenshot capture and resizing
│   │   ├── input_control.py          # Mouse movement, click, drag, typing, and clipboard control
│   │   ├── browser.py                # Playwright Chromium web browser automation
│   │   ├── filesystem.py             # File reading, writing, searching, and directory listing
│   │   ├── shell.py                  # Local Bash command execution with stdout/stderr capture
│   │   └── voice.py                  # Local offline speech-to-text via faster-whisper neural networks
│   │
│   └── utils/                        # System & Safety Utilities
│       ├── confirmation.py           # Destructive command interceptor (safety confirmation barrier)
│       ├── shortcuts.py              # Native GNOME media-keys custom shortcut registrar
│       └── logger.py                 # Structured loguru logger with formatting and file rotation
│
├── tests/                            # Comprehensive Test Suite
│   ├── test_agent.py                 # Configuration, filesystem, shell, and DPDP compliance unit tests
│   ├── test_gui_instantiation.py     # Offscreen GUI, custom widget, vector icon, and walkthrough tests
│   └── simulate_full_workflow.py     # 8-subsystem end-to-end standalone ReAct agent simulation
│
├── assets/                           # Branding & Visual Assets
│   └── aria_icon.png                 # ARIA application icon
│
├── .github/                          # GitHub Automation & Community Standards
│   ├── workflows/ci.yml              # GitHub Actions CI matrix (Python 3.10, 3.11, 3.12)
│   ├── ISSUE_TEMPLATE/               # Bug report & feature request templates
│   └── pull_request_template.md      # Pull request checklist
│
├── LICENSE                           # Apache License 2.0
├── PRIVACY_DPDP.md                   # Digital Personal Data Protection Act (2023) Compliance Policy
├── PERMISSIONS.md                    # Linux Kernel Privileges, uinput, and Zero-Root Policy
├── SECURITY.md                       # Security Policy and Vulnerability Disclosure
├── CONTRIBUTING.md                   # Contributor Onboarding Guide
├── pyproject.toml                    # PEP 517/621 packaging metadata and tool configs
├── requirements.txt                  # Pinned Python package dependencies
├── aria.desktop                      # Linux desktop application launcher
├── install.sh                        # Automated one-shot setup script
├── run_gui.sh                        # Space-safe desktop GUI launch wrapper
└── run_daemon.sh                     # Space-safe daemon background launch wrapper
```

---

## 5. AI Provider Configuration

ARIA supports 4 swappable AI backends configured via `.env` or interactively in the Settings dialog:

### 1. Google Gemini 2.0 (Recommended Default)
- **Fast, high-rate limits, free tier available.**
- Obtain a key from [Google AI Studio](https://aistudio.google.com/).
- In `.env`:
  ```env
  ARIA_PROVIDER=gemini
  GEMINI_API_KEY=AIzaSy...
  ```

### 2. OpenAI GPT-4o
- In `.env`:
  ```env
  ARIA_PROVIDER=openai
  OPENAI_API_KEY=sk-proj-...
  ```

### 3. Anthropic Claude 3.5 Sonnet
- Excellent for code reasoning and precise computer-use actions.
- In `.env`:
  ```env
  ARIA_PROVIDER=claude
  ANTHROPIC_API_KEY=sk-ant-...
  ```

### 4. Ollama (100% Offline Local Model)
- Run models completely locally without transmitting data over the internet:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ollama run llava
  ```
- In `.env`:
  ```env
  ARIA_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llava
  ```

---

## 6. Air-Gapped / Offline Local Execution

For zero-cloud environments where data privacy is paramount:
1. Configure `ARIA_PROVIDER=ollama` with `OLLAMA_MODEL=llava`.
2. Voice transcription runs on-device using `faster-whisper` (`base.en` weights).
3. Result: **Zero outbound internet connections** during task execution.

---

## 7. Troubleshooting & Diagnostics

### Q: Pressing Ctrl+Space does nothing
1. Verify background service is active:
   ```bash
   systemctl --user status aria.service
   ```
2. Test manual trigger:
   ```bash
   ~/.aria/run_gui.sh --toggle
   ```
3. If using GNOME Wayland, check shortcut registration:
   ```bash
   gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
   ```

### Q: Mouse/Keyboard automation fails on Wayland
`ydotool` requires access to `/dev/uinput`:
1. Check if user is in `input` group:
   ```bash
   groups | grep input
   ```
   If missing, run `sudo usermod -aG input $USER` and log out/log in.
2. Check `ydotoold.service` status:
   ```bash
   systemctl --user status ydotoold.service
   ```

### Q: Screen capture returns black/empty image
Wayland requires `grim` or compositor portal access:
```bash
which grim && grim /tmp/test.png && ls -l /tmp/test.png
```

### Q: How do I view live logs?
```bash
journalctl --user -u aria.service -f
```
