# 🤝 Contributing to ARIA

Thank you for your interest in contributing to **ARIA (Autonomous Resident Intelligence Agent)**!  
We welcome bug fixes, documentation improvements, new tool integrations, provider backends, and performance optimizations.

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Operating System:** Linux (Ubuntu 22.04+, Debian 12+, Fedora, Arch)
- **Display Server:** Wayland (recommended) or X11
- **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14
- **System Packages:**
  ```bash
  sudo apt-get install -y python3-venv python3-pip python3-pyqt6 grim ydotool wtype wl-clipboard ffmpeg
  ```

### 2. Clone & Virtual Environment
```bash
git clone https://github.com/your-username/Linux-Agent.git
cd Linux-Agent

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 3. Environment Configuration
```bash
cp .env.example .env
# Edit .env and supply your preferred AI provider API key (e.g. GEMINI_API_KEY)
```

---

## 📂 Project Structure Overview

```
Linux-Agent/
├── aria/
│   ├── main.py              # Application daemon entrypoint
│   ├── config.py            # Typed configuration and environment loader
│   ├── hotkey.py            # Global key listener and IPC socket listener
│   ├── toggle.py            # CLI toggle command
│   ├── agent/               # ReAct planning loop, tool execution, and SQLite/ChromaDB memory
│   ├── providers/           # AI provider backends (Gemini, OpenAI, Claude, Ollama)
│   ├── tools/               # Computer automation tools (screen, input, shell, browser, voice)
│   ├── overlay/             # Floating translucent HUD overlay and system tray
│   ├── gui/                 # Control Center dashboard, settings matrix, onboarding walkthrough, icons
│   └── utils/               # Logger, GNOME shortcuts, destructive action confirmation
├── tests/                   # Test suite and standalone simulation
├── assets/                  # Brand icons and vector assets
├── install.sh               # One-shot installation script
└── requirements.txt         # Python package dependencies
```

---

## 🧪 Testing Guidelines

Before submitting a Pull Request, verify that all test suites pass without regressions:

### 1. Subsystem & Workflow Simulation (8 Subsystems)
```bash
.venv/bin/python tests/simulate_full_workflow.py
```
*Validates screen capture, input controller, destructive command safety interception, shell tool, voice configuration, Playwright browser automation, SQLite/ChromaDB memory, and the autonomous ReAct execution loop.*

### 2. GUI Component & Offscreen Layout Verification
```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python tests/test_gui_instantiation.py
```
*Validates custom widgets, SettingsDialog, 25 vector SVG icons, OnboardingWizard 5-stage navigation, and DashboardWindow data tables without requiring an active physical display.*

### 3. Core Unit Tests
```bash
.venv/bin/python -m pytest tests/
```

---

## 🎨 Design & Style Guidelines

### 1. Swiss Modernism 2.0 Aesthetic
When contributing to the UI (`aria/gui/`, `aria/overlay/`):
- Adhere strictly to **Swiss Modernism 2.0** design principles: architectural dark canvas (`#090A0D`, `#111318`), hairline geometric borders (`1px solid #20242D`), sharp micro-radii (3px–5px), and high-contrast typography.
- Avoid blurry amorphous glassmorphism or bubbly rounded corners.
- Use vector SVG icons from [aria/gui/icons.py](file:///home/itsmeabirmohanta/College%20Coding/Linux-Agent/aria/gui/icons.py) instead of emoji characters.

### 2. Python Code Standards
- **Typing:** Provide explicit type hints on all function signatures (`typing.List`, `typing.Dict`, `typing.Optional`, etc.).
- **Formatting:** Keep line lengths reasonable, follow PEP 8, and use clean descriptive docstrings.
- **Safety First:** Any tool performing file deletions, disk changes, or root modifications must be wired through `confirmation_manager.request_confirmation()`.

---

## 🚀 Submitting a Pull Request

1. **Fork the Repository:** Create a feature branch (`git checkout -b feature/my-new-tool`).
2. **Commit Changes:** Write clear, concise commit messages (`git commit -m "feat(tools): add clipboard regex extraction tool"`).
3. **Verify Tests:** Ensure all tests pass.
4. **Push & Open PR:** Push to your fork and submit a PR to `main` with a clear explanation of changes, test results, and any relevant screenshots.

---

## 📜 Code of Conduct

We are dedicated to providing a welcoming, respectful, and inclusive environment for all contributors regardless of background, identity, or experience level. Be kind, constructive, and respectful in all issues and discussions.
