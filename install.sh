#!/bin/bash
# ================================================================
# ARIA — Autonomous Resident Intelligence Agent
# One-shot installer for Ubuntu/Debian (Wayland)
# Run with: bash install.sh
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
ARIA_HOME="$HOME/.aria"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ARIA — Autonomous Resident AI Agent    ║"
echo "║              Installer v1.0              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ---- Step 1: System dependencies via apt ----------------------------
echo "📦 [1/6] Installing system dependencies..."
# Prompt for sudo once at the beginning
echo "🔑 Requesting sudo permission for package installation..."
sudo -v

# Keep sudo timestamp updated while script runs
while true; do sudo -n true; sleep 50; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_PID=$!
trap 'kill $SUDO_PID 2>/dev/null' EXIT

PY_MINOR=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3.14")
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3.14-venv \
    python3-dev \
    python3-pyqt6 \
    libportaudio2 \
    portaudio19-dev \
    ydotool \
    grim \
    slurp \
    gnome-screenshot \
    scrot \
    wtype \
    wl-clipboard \
    libgirepository1.0-dev \
    gcc \
    pkg-config \
    ffmpeg

echo "✅ System packages installed."

# ---- Step 2: Python virtual environment -----------------------------
echo ""
echo "🐍 [2/6] Creating Python virtual environment..."
if [ -f "$VENV_DIR/bin/pip" ]; then
    echo "   Existing virtual environment detected at $VENV_DIR"
    source "$VENV_DIR/bin/activate"
else
    rm -rf "$VENV_DIR"
    if ! python3 -m venv "$VENV_DIR" --system-site-packages 2>/dev/null; then
        echo "   Standard venv creation failed; attempting with --without-pip fallback..."
        python3 -m venv --without-pip "$VENV_DIR" --system-site-packages
        source "$VENV_DIR/bin/activate"
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3
    else
        source "$VENV_DIR/bin/activate"
    fi
fi

# Upgrade pip
pip install --upgrade pip setuptools wheel -q

echo "✅ Virtual environment ready at $VENV_DIR"

# ---- Step 3: Python packages ----------------------------------------
echo ""
echo "📚 [3/6] Installing Python packages..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Install Playwright and Chromium browser
echo "🌐 Installing Playwright browser (this may take a few minutes)..."
playwright install chromium 2>&1 | tail -5

echo "✅ Python packages installed."

# ---- Step 4: Create ARIA home directory + copy config ---------------
echo ""
echo "🏠 [4/6] Setting up ARIA home directory..."
mkdir -p "$ARIA_HOME"
mkdir -p "$ARIA_HOME/chroma"
mkdir -p "$ARIA_HOME/logs"
mkdir -p "$ARIA_HOME/voice_temp"

# Symlinks without spaces for robust systemd and launcher execution
ln -sfn "$SCRIPT_DIR" "$ARIA_HOME/app"
ln -sfn "$SCRIPT_DIR/run_daemon.sh" "$ARIA_HOME/run_daemon.sh"
ln -sfn "$SCRIPT_DIR/run_gui.sh" "$ARIA_HOME/run_gui.sh"
ln -sfn "$SCRIPT_DIR/assets/aria_icon.png" "$ARIA_HOME/aria_icon.png"
chmod +x "$SCRIPT_DIR/run_daemon.sh" "$SCRIPT_DIR/run_gui.sh"

# Copy .env template if .env doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "⚠️  Created .env from template — please edit .env and add your API key!"
else
    echo "   .env already exists, skipping."
fi

echo "✅ ARIA home at $ARIA_HOME"

# ---- Step 5: ydotool daemon setup (Wayland input control) -----------
echo ""
echo "⌨️  [5/6] Setting up ydotool for Wayland input control..."

# Add user to input group for ydotool
if ! groups | grep -q "input"; then
    sudo usermod -aG input "$USER"
    echo "   Added $USER to 'input' group (requires logout to take effect)."
fi

# Create ydotool daemon service
YDOTOOL_SERVICE="$HOME/.config/systemd/user/ydotoold.service"
mkdir -p "$HOME/.config/systemd/user/"
cat > "$YDOTOOL_SERVICE" << 'EOF'
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
EOF

systemctl --user daemon-reload
systemctl --user enable ydotoold.service 2>/dev/null || true
if [ -w /dev/uinput ]; then
    systemctl --user restart ydotoold.service 2>/dev/null || true
    echo "✅ ydotool daemon configured and active."
else
    echo "✅ ydotool service enabled (will start automatically after next login when input group is active)."
fi

# ---- Step 6: ARIA systemd user service ------------------------------
echo ""
echo "🚀 [6/6] Installing ARIA as a systemd user service..."

ARIA_SERVICE="$HOME/.config/systemd/user/aria.service"
cat > "$ARIA_SERVICE" << 'EOF'
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
EOF

systemctl --user daemon-reload
systemctl --user enable aria.service
systemctl --user restart aria.service || true

echo "✅ ARIA service installed and started."

# Install application desktop launcher
mkdir -p "$HOME/.local/share/applications/"
cp "$SCRIPT_DIR/aria.desktop" "$HOME/.local/share/applications/"
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true

# Register GNOME desktop global hotkey (Wayland native)
"$VENV_DIR/bin/python" -c "
from aria.utils.shortcuts import register_gnome_shortcut
from aria.config import config
register_gnome_shortcut(config.hotkey)
" 2>/dev/null || true

# ---- Step 7: Auto Walkthrough & Guided Tour -------------------------
echo ""
echo "🚀 [7/7] Launching ARIA Auto Walkthrough..."
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "   Desktop session detected. Launching ARIA Interactive Walkthrough..."
    nohup "$ARIA_HOME/run_gui.sh" --walkthrough > /dev/null 2>&1 &
    echo "✅ Interactive Walkthrough launched on your screen!"
else
    echo "ℹ️  No graphical display detected (SSH or headless install)."
    echo "   Run '~/.aria/run_gui.sh --walkthrough' once inside your desktop session."
fi

# ---- Done -----------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          ✅  ARIA is installed!          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  🔑  Edit .env or configure providers in the Walkthrough"
echo "  ⌨️   Press Ctrl+Space to summon the floating HUD"
echo "  📋  Check status: systemctl --user status aria"
echo "  📜  View logs:   journalctl --user -u aria -f"
echo ""

if ! groups | grep -q "input"; then
    echo "  ⚠️  Please log out and back in for input group to take effect"
    echo "     (required for ydotool keyboard/mouse control)"
fi
