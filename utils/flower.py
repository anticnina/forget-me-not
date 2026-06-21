"""
Colored forget-me-not flower icon for PyQt6 labels.

Renders the 🌸 emoji and applies the same CSS filter used on the map markers:
  hue-rotate(234deg) saturate(0.74) brightness(0.93)
so every flower in the app looks identical.
"""
from __future__ import annotations

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QRect, Qt
from PyQt6.QtGui import QFont, QImage, QPainter, QPixmap


_HUE_ROTATE = 234.0
_SATURATE   = 0.74
_BRIGHTNESS = 0.93


# ── Colour-space helpers ──────────────────────────────────────

def _rgb_to_hsl(r: float, g: float, b: float):
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2.0
    if delta == 0:
        return 0.0, 0.0, l
    s = delta / (1.0 - abs(2.0 * l - 1.0))
    if cmax == r:
        h = 60.0 * (((g - b) / delta) % 6)
    elif cmax == g:
        h = 60.0 * ((b - r) / delta + 2.0)
    else:
        h = 60.0 * ((r - g) / delta + 4.0)
    return h, s, l


def _hsl_to_rgb(h: float, s: float, l: float):
    if s == 0:
        return l, l, l
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = l - c / 2.0
    r1, g1, b1 = ((c,x,0),(x,c,0),(0,c,x),(0,x,c),(x,0,c),(c,0,x))[int(h / 60.0) % 6]
    return r1 + m, g1 + m, b1 + m


def _apply_filter(pix: QPixmap) -> QPixmap:
    """Apply the map-marker CSS filter pixel-by-pixel."""
    img = pix.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(img.height()):
        for x in range(img.width()):
            rgba = img.pixel(x, y)
            a = (rgba >> 24) & 0xFF
            if a == 0:
                continue
            r = ((rgba >> 16) & 0xFF) / 255.0
            g = ((rgba >>  8) & 0xFF) / 255.0
            b = ( rgba        & 0xFF) / 255.0
            h, s, l = _rgb_to_hsl(r, g, b)
            h = (h + _HUE_ROTATE) % 360.0
            s = min(1.0, s * _SATURATE)
            r2, g2, b2 = _hsl_to_rgb(h, s, l)
            r2 = min(1.0, r2 * _BRIGHTNESS)
            g2 = min(1.0, g2 * _BRIGHTNESS)
            b2 = min(1.0, b2 * _BRIGHTNESS)
            img.setPixel(x, y,
                ((a & 0xFF) << 24) | (int(r2 * 255) << 16) |
                (int(g2 * 255) << 8) | int(b2 * 255))
    return QPixmap.fromImage(img)


# ── Public API ────────────────────────────────────────────────

def make_flower_pixmap(size: int = 24) -> QPixmap:
    """Render 🌸 at *size* px and apply the map-marker filter."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = QFont("Segoe UI Emoji")
    font.setPixelSize(size - 2)
    p.setFont(font)
    p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "🌸")
    p.end()
    return _apply_filter(pix)


def flower_img_tag(size: int = 24) -> str:
    """HTML <img> tag with the filtered 🌸 as an inline base64 PNG."""
    pix = make_flower_pixmap(size)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pix.save(buf, "PNG")
    b64 = bytes(ba.toBase64()).decode()
    return (
        f'<img src="data:image/png;base64,{b64}"'
        f' width="{size}" height="{size}" align="absmiddle"/>'
    )
