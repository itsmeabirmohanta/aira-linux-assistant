"""
Configuration management for ARIA.
Loads settings from .env file and environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    # Load .env from project root or user home
    project_env = Path(__file__).resolve().parent.parent / ".env"
    if project_env.exists():
        load_dotenv(project_env)
    else:
        load_dotenv()
except ImportError:
    pass


def _clean_env(key: str, default: str = "") -> str:
    val = os.getenv(key)
    if val is None:
        return default
    if "#" in val:
        val = val.split("#", 1)[0]
    return val.strip()


def _int_env(key: str, default: int) -> int:
    raw = _clean_env(key, str(default))
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def _float_env(key: str, default: float) -> float:
    raw = _clean_env(key, str(default))
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default


def _bool_env(key: str, default: bool) -> bool:
    raw = _clean_env(key, "true" if default else "false").lower()
    return raw in ("true", "1", "yes", "on")


def _detect_display_server() -> str:
    explicit = _clean_env("ARIA_DISPLAY_SERVER")
    if explicit:
        return explicit.lower()
    xdg_type = os.getenv("XDG_SESSION_TYPE", "").lower()
    if "wayland" in xdg_type or os.getenv("WAYLAND_DISPLAY"):
        return "wayland"
    return "x11"


@dataclass
class Config:
    # AI Provider: gemini | openai | claude | ollama
    provider: str = field(default_factory=lambda: _clean_env("ARIA_PROVIDER", "gemini").lower())

    # API Keys
    gemini_api_key: str = field(default_factory=lambda: _clean_env("GEMINI_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: _clean_env("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: _clean_env("ANTHROPIC_API_KEY", ""))

    # Ollama settings
    ollama_base_url: str = field(default_factory=lambda: _clean_env("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _clean_env("OLLAMA_MODEL", "llava"))

    # Behavior
    hotkey: str = field(default_factory=lambda: _clean_env("ARIA_HOTKEY", "ctrl+space"))
    confirm_destructive: bool = field(default_factory=lambda: _bool_env("ARIA_CONFIRM_DESTRUCTIVE", True))
    max_steps: int = field(default_factory=lambda: _int_env("ARIA_MAX_STEPS", 20))
    stream_responses: bool = field(default_factory=lambda: _bool_env("ARIA_STREAM_RESPONSES", True))

    # Voice
    voice_model: str = field(default_factory=lambda: _clean_env("ARIA_VOICE_MODEL", "base.en"))
    voice_language: str = field(default_factory=lambda: _clean_env("ARIA_VOICE_LANGUAGE", "en"))

    # Memory
    memory_dir: Path = field(
        default_factory=lambda: Path(os.path.expanduser(_clean_env("ARIA_MEMORY_DIR", "~/.aria")))
    )
    memory_max_sessions: int = field(default_factory=lambda: _int_env("ARIA_MEMORY_MAX_SESSIONS", 100))
    context_window: int = field(default_factory=lambda: _int_env("ARIA_CONTEXT_WINDOW", 10))

    # Display & Input
    display_server: str = field(default_factory=_detect_display_server)

    # UI Settings
    overlay_width: int = field(default_factory=lambda: _int_env("ARIA_OVERLAY_WIDTH", 680))
    overlay_opacity: float = field(default_factory=lambda: _float_env("ARIA_OVERLAY_OPACITY", 0.95))
    theme: str = field(default_factory=lambda: _clean_env("ARIA_THEME", "dark"))

    # Logging
    log_level: str = field(default_factory=lambda: _clean_env("ARIA_LOG_LEVEL", "INFO").upper())

    def validate(self) -> list[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []
        if self.provider == "gemini" and not self.gemini_api_key:
            warnings.append("GEMINI_API_KEY is not set. Gemini provider will fail until configured.")
        elif self.provider == "openai" and not self.openai_api_key:
            warnings.append("OPENAI_API_KEY is not set. OpenAI provider will fail until configured.")
        elif self.provider == "claude" and not self.anthropic_api_key:
            warnings.append("ANTHROPIC_API_KEY is not set. Claude provider will fail until configured.")
        return warnings


config = Config()


def ensure_secure_permissions():
    """
    Enforce POSIX permission hardening for DPDP and system security compliance:
    - ~/.aria directory set to 0700 (owner rwx only)
    - Project .env file set to 0600 (owner rw only)
    """
    try:
        if config.memory_dir.exists():
            config.memory_dir.chmod(0o700)
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            env_file.chmod(0o600)
    except Exception:
        pass


ensure_secure_permissions()
