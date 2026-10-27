"""
ARIA Professional Vector Icon Engine.
Provides crisp, theme-aware SVG vector icons for PyQt6 widgets.
Zero external icon font dependencies; renders dynamically via QtSvg at native DPI.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import QByteArray, Qt, QSize
from PyQt6.QtSvg import QSvgRenderer

# Professional 24x24 stroke-based SVG path definitions (Lucide/Feather standard)
SVG_PATHS = {
    "screen": """
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
    """,
    "terminal": """
        <polyline points="4 17 10 11 4 5"/>
        <line x1="12" y1="19" x2="20" y2="19"/>
    """,
    "globe": """
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    """,
    "mic": """
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="22"/>
    """,
    "settings": """
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
        <circle cx="12" cy="12" r="3"/>
    """,
    "shield": """
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    """,
    "shield_check": """
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <polyline points="9 12 11 14 15 10"/>
    """,
    "cpu": """
        <rect x="4" y="4" width="16" height="16" rx="2"/>
        <rect x="9" y="9" width="6" height="6"/>
        <line x1="9" y1="1" x2="9" y2="4"/>
        <line x1="15" y1="1" x2="15" y2="4"/>
        <line x1="9" y1="20" x2="9" y2="23"/>
        <line x1="15" y1="20" x2="15" y2="23"/>
        <line x1="20" y1="9" x2="23" y2="9"/>
        <line x1="20" y1="14" x2="23" y2="14"/>
        <line x1="1" y1="9" x2="4" y2="9"/>
        <line x1="1" y1="14" x2="4" y2="14"/>
    """,
    "keyboard": """
        <rect x="2" y="4" width="20" height="16" rx="2"/>
        <line x1="6" y1="8" x2="6" y2="8"/>
        <line x1="10" y1="8" x2="10" y2="8"/>
        <line x1="14" y1="8" x2="14" y2="8"/>
        <line x1="18" y1="8" x2="18" y2="8"/>
        <line x1="6" y1="12" x2="6" y2="12"/>
        <line x1="10" y1="12" x2="10" y2="12"/>
        <line x1="14" y1="12" x2="14" y2="12"/>
        <line x1="18" y1="12" x2="18" y2="12"/>
        <line x1="7" y1="16" x2="17" y2="16"/>
    """,
    "database": """
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
    """,
    "server": """
        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
        <line x1="6" y1="6" x2="6.01" y2="6"/>
        <line x1="6" y1="18" x2="6.01" y2="18"/>
    """,
    "play": """
        <polygon points="5 3 19 12 5 21 5 3"/>
    """,
    "arrow_right": """
        <line x1="5" y1="12" x2="19" y2="12"/>
        <polyline points="12 5 19 12 12 19"/>
    """,
    "arrow_left": """
        <line x1="19" y1="12" x2="5" y2="12"/>
        <polyline points="12 19 5 12 12 5"/>
    """,
    "check": """
        <polyline points="20 6 9 17 4 12"/>
    """,
    "alert": """
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
    """,
    "refresh": """
        <path d="M3 12a9 9 0 0 1 15-6.7L22 9"/>
        <path d="M21 3v6h-6"/>
        <path d="M21 12a9 9 0 0 1-15 6.7L2 15"/>
        <path d="M3 21v-6h6"/>
    """,
    "trash": """
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        <line x1="10" y1="11" x2="10" y2="17"/>
        <line x1="14" y1="11" x2="14" y2="17"/>
    """,
    "search": """
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    """,
    "compass": """
        <circle cx="12" cy="12" r="10"/>
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
    """,
    "cross": """
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
    """,
    "power": """
        <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
        <line x1="12" y1="2" x2="12" y2="12"/>
    """,
    "sparkles": """
        <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>
    """,
    "command": """
        <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/>
    """,
    "external_link": """
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
    """
}

_PIXMAP_CACHE = {}


def build_svg_xml(name: str, color: str = "#E2E6EF", stroke_width: float = 2.0) -> str:
    inner = SVG_PATHS.get(name, SVG_PATHS["sparkles"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}'
        f'</svg>'
    )


def get_pixmap(name: str, color: str = "#E2E6EF", size: int = 20, stroke_width: float = 2.0) -> QPixmap:
    cache_key = (name, color, size, stroke_width)
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    svg_str = build_svg_xml(name, color=color, stroke_width=stroke_width)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    _PIXMAP_CACHE[cache_key] = pix
    return pix


def get_icon(name: str, color: str = "#E2E6EF", size: int = 20, stroke_width: float = 2.0) -> QIcon:
    pix = get_pixmap(name, color=color, size=size, stroke_width=stroke_width)
    return QIcon(pix)
