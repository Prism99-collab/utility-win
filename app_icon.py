"""Shared application icon."""
from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap


def make_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_paint_icon(size))
    return icon


def _paint_icon(size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pad = max(1, round(size * 0.08))
    rect = QRect(pad, pad, size - pad * 2, size - pad * 2)
    radius = max(4, round(size * 0.22))

    path = QPainterPath()
    path.addRoundedRect(rect.toRectF(), radius, radius)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#15151c"))
    painter.drawPath(path)

    accent = QColor("#4f8cff")
    painter.setBrush(accent)
    bar_w = max(2, round(size * 0.10))
    painter.drawRoundedRect(
        QRect(rect.left() + round(size * 0.12), rect.top() + round(size * 0.18), bar_w, round(size * 0.64)),
        bar_w / 2,
        bar_w / 2,
    )

    painter.setPen(QColor("#f7f7f8"))
    painter.setFont(QFont("Segoe UI Variable", round(size * 0.42), QFont.Weight.Bold))
    painter.drawText(rect.adjusted(round(size * 0.13), 0, 0, 0), Qt.AlignmentFlag.AlignCenter, "U")

    painter.end()
    return pix
