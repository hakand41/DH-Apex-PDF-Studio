"""
Nexora PDF Studio - Vektörel İkon Fabrikası
Her DPI'da ultra keskin görüntü veren QPainter tabanlı profesyonel ikonlar.
"""

from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont,
    QPolygonF, QLinearGradient
)
from PyQt6.QtCore import Qt, QPointF, QRectF

class IconFactory:
    _cache = {}

    @classmethod
    def get(cls, name: str, size: int = 24, color: str = "#E0E0E0", accent: str = "#E5252A") -> QIcon:
        key = f"{name}_{size}_{color}_{accent}"
        if key in cls._cache:
            return cls._cache[key]
        
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        c = QColor(color)
        acc = QColor(accent)
        pen = QPen(c, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        s = size
        
        try:
            if name == "app_icon":
                # Adobe tarzı degrade zemin (#E5252A -> #B71C1C)
                grad = QLinearGradient(0, 0, s, s)
                grad.setColorAt(0.0, QColor("#E5252A"))
                grad.setColorAt(1.0, QColor("#B71C1C"))
                
                pad = max(1.0, s * 0.03)
                radius = s * 0.22
                rect = QRectF(pad, pad, s - pad * 2, s - pad * 2)
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(grad)
                painter.drawRoundedRect(rect, radius, radius)
                
                # İnce iç parlaklık çizgisi
                if s >= 24:
                    border_pen = QPen(QColor(255, 255, 255, 60), max(1.0, s * 0.02))
                    painter.setPen(border_pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
                
                # DH Monogramı
                stroke_w = max(1.5, s * 0.11)
                pen_dh = QPen(Qt.GlobalColor.white, stroke_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen_dh)
                
                # 'D' harfi
                d_path = QPainterPath()
                d_path.moveTo(s * 0.20, s * 0.26)
                d_path.lineTo(s * 0.20, s * 0.74)
                d_path.moveTo(s * 0.20, s * 0.26)
                d_path.cubicTo(s * 0.52, s * 0.26, s * 0.52, s * 0.74, s * 0.20, s * 0.74)
                painter.strokePath(d_path, pen_dh)
                
                # 'H' harfi
                h_path = QPainterPath()
                h_path.moveTo(s * 0.57, s * 0.26)
                h_path.lineTo(s * 0.57, s * 0.74)
                h_path.moveTo(s * 0.57, s * 0.50)
                h_path.lineTo(s * 0.83, s * 0.50)
                h_path.moveTo(s * 0.83, s * 0.26)
                h_path.lineTo(s * 0.83, s * 0.74)
                painter.strokePath(h_path, pen_dh)
                
            elif name == "new_file":
                painter.drawRoundedRect(QRectF(s*0.2, s*0.15, s*0.5, s*0.7), 2, 2)
                painter.drawLine(QPointF(s*0.35, s*0.35), QPointF(s*0.55, s*0.35))
                painter.drawLine(QPointF(s*0.35, s*0.5), QPointF(s*0.55, s*0.5))
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.75, s*0.55), QPointF(s*0.75, s*0.85))
                painter.drawLine(QPointF(s*0.6, s*0.7), QPointF(s*0.9, s*0.7))

            elif name == "open_file":
                path = QPainterPath()
                path.moveTo(s*0.15, s*0.3)
                path.lineTo(s*0.4, s*0.3)
                path.lineTo(s*0.5, s*0.4)
                path.lineTo(s*0.85, s*0.4)
                path.lineTo(s*0.85, s*0.75)
                path.lineTo(s*0.15, s*0.75)
                path.closeSubpath()
                painter.drawPath(path)
                
            elif name == "save_file":
                painter.drawRoundedRect(QRectF(s*0.18, s*0.18, s*0.64, s*0.64), 2, 2)
                painter.drawRect(QRectF(s*0.3, s*0.18, s*0.4, s*0.25))
                painter.drawRect(QRectF(s*0.28, s*0.52, s*0.44, s*0.3))

            elif name == "save_as":
                painter.drawRoundedRect(QRectF(s*0.15, s*0.15, s*0.55, s*0.55), 2, 2)
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.6, s*0.8), QPointF(s*0.85, s*0.55))

            elif name == "export":
                painter.drawRect(QRectF(s*0.2, s*0.4, s*0.6, s*0.45))
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.5, s*0.6), QPointF(s*0.5, s*0.18))
                painter.drawLine(QPointF(s*0.35, s*0.32), QPointF(s*0.5, s*0.18))
                painter.drawLine(QPointF(s*0.65, s*0.32), QPointF(s*0.5, s*0.18))

            elif name == "print":
                painter.drawRect(QRectF(s*0.3, s*0.15, s*0.4, s*0.2))
                painter.drawRoundedRect(QRectF(s*0.15, s*0.35, s*0.7, s*0.35), 2, 2)
                painter.drawRect(QRectF(s*0.28, s*0.55, s*0.44, s*0.3))

            elif name == "undo":
                path = QPainterPath()
                path.arcMoveTo(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), 0)
                path.arcTo(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), 0, 180)
                painter.strokePath(path, pen)
                painter.drawLine(QPointF(s*0.2, s*0.55), QPointF(s*0.08, s*0.35))
                painter.drawLine(QPointF(s*0.2, s*0.55), QPointF(s*0.35, s*0.4))

            elif name == "redo":
                path = QPainterPath()
                path.arcMoveTo(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), 180)
                path.arcTo(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), 180, -180)
                painter.strokePath(path, pen)
                painter.drawLine(QPointF(s*0.8, s*0.55), QPointF(s*0.92, s*0.35))
                painter.drawLine(QPointF(s*0.8, s*0.55), QPointF(s*0.65, s*0.4))

            elif name == "prev_page":
                painter.drawLine(QPointF(s*0.62, s*0.25), QPointF(s*0.35, s*0.5))
                painter.drawLine(QPointF(s*0.35, s*0.5), QPointF(s*0.62, s*0.75))

            elif name == "next_page":
                painter.drawLine(QPointF(s*0.38, s*0.25), QPointF(s*0.65, s*0.5))
                painter.drawLine(QPointF(s*0.65, s*0.5), QPointF(s*0.38, s*0.75))

            elif name == "first_page":
                painter.drawLine(QPointF(s*0.28, s*0.25), QPointF(s*0.28, s*0.75))
                painter.drawLine(QPointF(s*0.68, s*0.25), QPointF(s*0.42, s*0.5))
                painter.drawLine(QPointF(s*0.42, s*0.5), QPointF(s*0.68, s*0.75))

            elif name == "last_page":
                painter.drawLine(QPointF(s*0.72, s*0.25), QPointF(s*0.72, s*0.75))
                painter.drawLine(QPointF(s*0.32, s*0.25), QPointF(s*0.58, s*0.5))
                painter.drawLine(QPointF(s*0.58, s*0.5), QPointF(s*0.32, s*0.75))

            elif name == "zoom_in":
                painter.drawEllipse(QRectF(s*0.18, s*0.18, s*0.48, s*0.48))
                painter.drawLine(QPointF(s*0.55, s*0.55), QPointF(s*0.82, s*0.82))
                painter.drawLine(QPointF(s*0.42, s*0.28), QPointF(s*0.42, s*0.56))
                painter.drawLine(QPointF(s*0.28, s*0.42), QPointF(s*0.56, s*0.42))

            elif name == "zoom_out":
                painter.drawEllipse(QRectF(s*0.18, s*0.18, s*0.48, s*0.48))
                painter.drawLine(QPointF(s*0.55, s*0.55), QPointF(s*0.82, s*0.82))
                painter.drawLine(QPointF(s*0.28, s*0.42), QPointF(s*0.56, s*0.42))

            elif name == "zoom_fit":
                painter.drawRect(QRectF(s*0.22, s*0.22, s*0.56, s*0.56))
                painter.drawLine(QPointF(s*0.12, s*0.12), QPointF(s*0.3, s*0.12))
                painter.drawLine(QPointF(s*0.12, s*0.12), QPointF(s*0.12, s*0.3))
                painter.drawLine(QPointF(s*0.88, s*0.88), QPointF(s*0.7, s*0.88))
                painter.drawLine(QPointF(s*0.88, s*0.88), QPointF(s*0.88, s*0.7))

            elif name == "zoom_width":
                painter.drawRect(QRectF(s*0.28, s*0.2, s*0.44, s*0.6))
                painter.setPen(QPen(acc, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.1, s*0.5), QPointF(s*0.25, s*0.5))
                painter.drawLine(QPointF(s*0.75, s*0.5), QPointF(s*0.9, s*0.5))

            elif name == "rotate_cw":
                path = QPainterPath()
                path.arcMoveTo(QRectF(s*0.2, s*0.2, s*0.6, s*0.6), 240)
                path.arcTo(QRectF(s*0.2, s*0.2, s*0.6, s*0.6), 240, 260)
                painter.strokePath(path, pen)
                painter.drawLine(QPointF(s*0.75, s*0.45), QPointF(s*0.88, s*0.35))
                painter.drawLine(QPointF(s*0.75, s*0.45), QPointF(s*0.68, s*0.3))

            elif name == "rotate_ccw":
                path = QPainterPath()
                path.arcMoveTo(QRectF(s*0.2, s*0.2, s*0.6, s*0.6), -60)
                path.arcTo(QRectF(s*0.2, s*0.2, s*0.6, s*0.6), -60, -260)
                painter.strokePath(path, pen)
                painter.drawLine(QPointF(s*0.25, s*0.45), QPointF(s*0.12, s*0.35))
                painter.drawLine(QPointF(s*0.25, s*0.45), QPointF(s*0.32, s*0.3))

            elif name == "tool_select":
                path = QPainterPath()
                path.moveTo(s*0.2, s*0.15)
                path.lineTo(s*0.2, s*0.75)
                path.lineTo(s*0.38, s*0.58)
                path.lineTo(s*0.58, s*0.85)
                path.lineTo(s*0.7, s*0.75)
                path.lineTo(s*0.5, s*0.48)
                path.lineTo(s*0.72, s*0.48)
                path.closeSubpath()
                painter.setBrush(QBrush(c))
                painter.drawPath(path)

            elif name == "tool_pan":
                path = QPainterPath()
                path.moveTo(s*0.3, s*0.7)
                path.lineTo(s*0.3, s*0.35)
                path.quadTo(s*0.35, s*0.25, s*0.4, s*0.35)
                path.lineTo(s*0.4, s*0.7)
                path.moveTo(s*0.4, s*0.32)
                path.lineTo(s*0.5, s*0.22)
                path.quadTo(s*0.55, s*0.18, s*0.6, s*0.25)
                path.lineTo(s*0.6, s*0.7)
                painter.drawPath(path)
                painter.drawRoundedRect(QRectF(s*0.25, s*0.45, s*0.5, s*0.4), 3, 3)

            elif name == "tool_text":
                font = QFont("Arial", int(s*0.65), QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "T")

            elif name == "tool_image":
                painter.drawRoundedRect(QRectF(s*0.15, s*0.2, s*0.7, s*0.6), 3, 3)
                painter.drawEllipse(QRectF(s*0.28, s*0.32, s*0.14, s*0.14))
                path = QPainterPath()
                path.moveTo(s*0.2, s*0.72)
                path.lineTo(s*0.42, s*0.48)
                path.lineTo(s*0.6, s*0.65)
                path.lineTo(s*0.7, s*0.55)
                path.lineTo(s*0.82, s*0.72)
                painter.drawPath(path)

            elif name == "tool_pen":
                path = QPainterPath()
                path.moveTo(s*0.68, s*0.18)
                path.lineTo(s*0.82, s*0.32)
                path.lineTo(s*0.38, s*0.78)
                path.lineTo(s*0.2, s*0.82)
                path.lineTo(s*0.24, s*0.64)
                path.closeSubpath()
                painter.drawPath(path)
                painter.drawLine(QPointF(s*0.55, s*0.3), QPointF(s*0.7, s*0.45))

            elif name == "tool_highlighter":
                painter.setPen(QPen(QColor("#FFE600"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.2, s*0.8), QPointF(s*0.8, s*0.8))
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(s*0.65, s*0.2)
                path.lineTo(s*0.8, s*0.35)
                path.lineTo(s*0.45, s*0.7)
                path.lineTo(s*0.3, s*0.7)
                path.lineTo(s*0.3, s*0.55)
                path.closeSubpath()
                painter.drawPath(path)

            elif name == "tool_rect":
                painter.drawRoundedRect(QRectF(s*0.18, s*0.22, s*0.64, s*0.56), 2, 2)

            elif name == "tool_ellipse":
                painter.drawEllipse(QRectF(s*0.18, s*0.22, s*0.64, s*0.56))

            elif name == "tool_line":
                painter.drawLine(QPointF(s*0.2, s*0.8), QPointF(s*0.8, s*0.2))

            elif name == "tool_arrow":
                painter.drawLine(QPointF(s*0.2, s*0.8), QPointF(s*0.75, s*0.25))
                painter.drawLine(QPointF(s*0.55, s*0.25), QPointF(s*0.75, s*0.25))
                painter.drawLine(QPointF(s*0.75, s*0.45), QPointF(s*0.75, s*0.25))

            elif name == "tool_redact":
                painter.setBrush(QBrush(QColor("#000000")))
                painter.drawRoundedRect(QRectF(s*0.15, s*0.3, s*0.7, s*0.4), 2, 2)
                painter.setPen(QPen(acc, 2))
                painter.drawLine(QPointF(s*0.1, s*0.5), QPointF(s*0.9, s*0.5))

            elif name == "tool_watermark":
                painter.drawRoundedRect(QRectF(s*0.18, s*0.18, s*0.64, s*0.64), 3, 3)
                font = QFont("Arial", int(s*0.45), QFont.Weight.Bold)
                painter.setFont(font)
                painter.setPen(QPen(acc, 1.5))
                painter.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "W")

            elif name == "search":
                painter.drawEllipse(QRectF(s*0.2, s*0.2, s*0.44, s*0.44))
                painter.drawLine(QPointF(s*0.55, s*0.55), QPointF(s*0.82, s*0.82))

            elif name == "page_add":
                painter.drawRect(QRectF(s*0.2, s*0.15, s*0.5, s*0.7))
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.65, s*0.55), QPointF(s*0.85, s*0.55))
                painter.drawLine(QPointF(s*0.75, s*0.45), QPointF(s*0.75, s*0.65))

            elif name == "page_delete":
                painter.drawRect(QRectF(s*0.2, s*0.15, s*0.5, s*0.7))
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.65, s*0.45), QPointF(s*0.85, s*0.65))
                painter.drawLine(QPointF(s*0.85, s*0.45), QPointF(s*0.65, s*0.65))

            elif name == "page_extract":
                painter.drawRect(QRectF(s*0.15, s*0.2, s*0.45, s*0.6))
                painter.setPen(QPen(acc, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(s*0.45, s*0.5), QPointF(s*0.85, s*0.5))
                painter.drawLine(QPointF(s*0.7, s*0.35), QPointF(s*0.85, s*0.5))
                painter.drawLine(QPointF(s*0.7, s*0.65), QPointF(s*0.85, s*0.5))

            elif name == "merge":
                painter.drawRect(QRectF(s*0.15, s*0.2, s*0.4, s*0.55))
                painter.drawRect(QRectF(s*0.35, s*0.35, s*0.4, s*0.55))
                painter.setPen(QPen(acc, 1.8))
                painter.drawLine(QPointF(s*0.55, s*0.55), QPointF(s*0.75, s*0.55))

            elif name == "delete_item":
                painter.drawLine(QPointF(s*0.25, s*0.3), QPointF(s*0.75, s*0.3))
                painter.drawLine(QPointF(s*0.4, s*0.22), QPointF(s*0.6, s*0.22))
                painter.drawRect(QRectF(s*0.3, s*0.3, s*0.4, s*0.5))
                painter.drawLine(QPointF(s*0.42, s*0.4), QPointF(s*0.42, s*0.7))
                painter.drawLine(QPointF(s*0.58, s*0.4), QPointF(s*0.58, s*0.7))

            elif name == "metadata":
                painter.drawEllipse(QRectF(s*0.15, s*0.15, s*0.7, s*0.7))
                painter.drawPoint(QPointF(s*0.5, s*0.35))
                painter.drawLine(QPointF(s*0.5, s*0.48), QPointF(s*0.5, s*0.7))

            else:
                painter.drawEllipse(QRectF(s*0.3, s*0.3, s*0.4, s*0.4))
                
        finally:
            painter.end()

        icon = QIcon(pix)
        cls._cache[key] = icon
        return icon
