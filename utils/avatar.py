"""Circular profile picture helper."""
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap


def circular_pixmap(source: QPixmap, size: int,
                    border_color: str = "#85C1E9", border_px: int = 2) -> QPixmap:
    """Scale and centre-crop *source*, clip to a circle, and draw a border ring."""
    scaled = source.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    p = QPainter(result)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Clip and draw image
    clip = QPainterPath()
    clip.addEllipse(0.0, 0.0, float(size), float(size))
    p.setClipPath(clip)
    x = (scaled.width()  - size) // 2
    y = (scaled.height() - size) // 2
    p.drawPixmap(0, 0, scaled, x, y, size, size)

    # Draw border on top (unclipped so the stroke sits on the edge)
    p.setClipping(False)
    pen = QPen(QColor(border_color))
    pen.setWidth(border_px)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    half = border_px / 2.0
    p.drawEllipse(QRectF(half, half, size - border_px, size - border_px))

    p.end()
    return result
