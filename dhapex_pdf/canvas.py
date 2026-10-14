"""
Nexora PDF Studio - Adobe Acrobat Seviyesi İnteraktif Çizim ve Görüntüleme Tuvali
Yüksek DPI, akıcı yakınlaştırma, 8 noktalı boyutlandırma tutamaçları, çift tıklama metin düzenleme,
klavye ile konum kaydırma (nudge), kopyala-yapıştır ve vektörel araçlar.
"""

import os
import math
from typing import Dict, List, Optional, Tuple
import pymupdf as fitz

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem,
    QGraphicsTextItem, QGraphicsPathItem, QInputDialog, QFileDialog, QMessageBox,
    QTextEdit
)
from PyQt6.QtGui import (
    QPainter, QPixmap, QImage, QColor, QPen, QBrush, QPainterPath,
    QFont, QCursor, QTransform, QPolygonF
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal

from dhapex_pdf.models import (
    BaseElement, TextElement, ImageElement, ShapeElement, DrawingElement, RedactionElement, WatermarkElement
)
from dhapex_pdf.commands import (
    AddElementCommand, DeleteElementCommand, TransformElementCommand
)

# 8 Noktalı Tutamaç Tanımları
HANDLE_SIZE = 8.0
HANDLE_TOP_LEFT = 0
HANDLE_TOP = 1
HANDLE_TOP_RIGHT = 2
HANDLE_RIGHT = 3
HANDLE_BOTTOM_RIGHT = 4
HANDLE_BOTTOM = 5
HANDLE_BOTTOM_LEFT = 6
HANDLE_LEFT = 7

class SelectionGizmo(QGraphicsItem):
    """Adobe Acrobat tarzı 8 noktalı interaktif seçim ve boyutlandırma çerçevesi."""
    def __init__(self):
        super().__init__()
        self.target_element = None
        self.rect = QRectF(0, 0, 100, 100)
        self.active_handle = -1
        self.setZValue(9999)
        self.setVisible(False)

    def set_target(self, element: Optional[BaseElement]):
        self.target_element = element
        if element:
            self.rect = element.get_rect()
            self.setVisible(True)
        else:
            self.setVisible(False)
        self.prepareGeometryChange()
        self.update()

    def update_geometry(self):
        if self.target_element:
            self.rect = self.target_element.get_rect()
            self.prepareGeometryChange()
            self.update()

    def boundingRect(self) -> QRectF:
        pad = HANDLE_SIZE + 4
        return self.rect.adjusted(-pad, -pad, pad, pad)

    def get_handle_rects(self) -> List[QRectF]:
        r = self.rect
        hs = HANDLE_SIZE
        half = hs / 2.0
        
        return [
            QRectF(r.left() - half, r.top() - half, hs, hs),
            QRectF(r.center().x() - half, r.top() - half, hs, hs),
            QRectF(r.right() - half, r.top() - half, hs, hs),
            QRectF(r.right() - half, r.center().y() - half, hs, hs),
            QRectF(r.right() - half, r.bottom() - half, hs, hs),
            QRectF(r.center().x() - half, r.bottom() - half, hs, hs),
            QRectF(r.left() - half, r.bottom() - half, hs, hs),
            QRectF(r.left() - half, r.center().y() - half, hs, hs),
        ]

    def hit_test_handle(self, pt: QPointF) -> int:
        for idx, h_rect in enumerate(self.get_handle_rects()):
            if h_rect.contains(pt):
                return idx
        return -1

    def paint(self, painter: QPainter, option, widget=None):
        if not self.target_element:
            return
            
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Seçim çerçevesi (Adobe mavi kesikli çizgi)
        pen = QPen(QColor("#0099FF"), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect)
        
        # 8 Tutamaç (Beyaz dolgu, mavi kenarlık)
        h_pen = QPen(QColor("#0099FF"), 1.5)
        h_brush = QBrush(QColor("#FFFFFF"))
        painter.setPen(h_pen)
        painter.setBrush(h_brush)
        
        for h_rect in self.get_handle_rects():
            painter.drawRect(h_rect)
            
        painter.restore()


class PDFCanvasView(QGraphicsView):
    zoom_changed = pyqtSignal(float)
    mouse_moved = pyqtSignal(float, float)
    element_selected = pyqtSignal(object)
    page_modified = pyqtSignal(int)

    def __init__(self, undo_stack, parent=None):
        super().__init__(parent)
        self.undo_stack = undo_stack
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor("#18181A")))
        
        self.doc: Optional[fitz.Document] = None
        self.current_page_idx = 0
        self.page_elements: Dict[int, List[BaseElement]] = {}
        self.selected_element: Optional[BaseElement] = None
        self.clipboard_element: Optional[BaseElement] = None
        
        self.page_bg_item: Optional[QGraphicsPixmapItem] = None
        self.page_shadow_item: Optional[QGraphicsRectItem] = None
        self.element_items: Dict[str, QGraphicsItem] = {}
        self.gizmo = SelectionGizmo()
        self.scene.addItem(self.gizmo)
        
        self.search_highlight_items: List[QGraphicsRectItem] = []
        
        self.tool_mode = "select"
        self.default_text_color = "#000000"
        self.default_font_size = 12.0
        self.default_font_family = "Arial"
        self.default_bold = False
        self.default_italic = False
        
        self.current_stroke_width = 2.0
        self.current_stroke_color = "#1E88E5"
        self.current_highlighter_width = 16.0
        self.current_highlighter_color = "#FFEB3B"
        
        self.inline_editor: Optional[QTextEdit] = None
        self.editing_element: Optional[TextElement] = None
        self.editing_is_new: bool = False
        
        self.is_space_pressed = False
        self.is_dragging_item = False
        self.is_resizing_handle = False
        self.active_handle_idx = -1
        self.drag_start_pos = QPointF()
        self.element_initial_rect = QRectF()
        
        self.current_drawing_element: Optional[DrawingElement] = None
        self.shape_start_pt = QPointF()

    def set_tool_mode(self, mode: str):
        self.tool_mode = mode
        if mode == "pan":
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.gizmo.setVisible(False)
        elif mode == "select":
            self.setCursor(Qt.CursorShape.ArrowCursor)
            if self.selected_element:
                self.gizmo.setVisible(True)
        elif mode in ["pen", "highlighter"]:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode in ["rect", "ellipse", "line", "arrow", "redact", "text", "image"]:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def load_document(self, doc: fitz.Document):
        self.doc = doc
        self.current_page_idx = 0
        self.page_elements.clear()
        self.render_current_page()
        self.fit_page()

    def render_current_page(self):
        if not self.doc or self.current_page_idx >= len(self.doc):
            self.scene.clear()
            return
            
        page = self.doc.load_page(self.current_page_idx)
        
        # Dinamik yüksek DPI render ölçeği (yakınlaştırma seviyesine göre keskinleştirir)
        current_zoom = self.transform().m11()
        render_scale = max(2.0, min(4.0, current_zoom * 2.0))
        mat = fitz.Matrix(render_scale, render_scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
        qpix = QPixmap.fromImage(qimg)
        
        self.scene.clear()
        self.element_items.clear()
        self.search_highlight_items.clear()
        
        page_rect = page.rect
        w, h = page_rect.width, page_rect.height
        
        # Sayfa gölgesi
        shadow_rect = QRectF(4, 4, w, h)
        self.page_shadow_item = self.scene.addRect(shadow_rect, QPen(Qt.PenStyle.NoPen), QBrush(QColor(10, 10, 12, 160)))
        
        # Sayfa piksel görüntüsü
        self.page_bg_item = self.scene.addPixmap(qpix)
        self.page_bg_item.setScale(1.0 / render_scale)
        self.page_bg_item.setZValue(0)
        
        # Gizmo'yu sahneye yeniden ekle
        self.gizmo = SelectionGizmo()
        self.scene.addItem(self.gizmo)
        
        elements = self.page_elements.get(self.current_page_idx, [])
        for el in elements:
            self.draw_element_on_scene(el)
            
        if self.selected_element in elements:
            self.gizmo.set_target(self.selected_element)
        else:
            self.selected_element = None
            self.gizmo.set_target(None)
            self.element_selected.emit(None)
            
        self.scene.setSceneRect(-50, -50, w + 100, h + 100)

    def draw_element_on_scene(self, el: BaseElement):
        if el.id in self.element_items:
            old_item = self.element_items[el.id]
            self.scene.removeItem(old_item)
            del self.element_items[el.id]
            
        item = None
        rect = el.get_rect()
        
        if isinstance(el, TextElement):
            item = self.scene.addText(el.text)
            f = QFont(el.font_family, max(6, int(el.font_size)))
            f.setBold(el.bold)
            f.setItalic(el.italic)
            item.setFont(f)
            item.setDefaultTextColor(QColor(el.color))
            item.setPos(QPointF(el.x, el.y))
            item.setTextWidth(max(20.0, el.width))
            
            # Dinamik metin kutusu boyutu
            tb = item.boundingRect()
            if el.width < tb.width() + 8:
                el.width = max(el.width, min(350.0, tb.width() + 10))
                item.setTextWidth(el.width)
            if el.height < tb.height() + 6:
                el.height = max(el.height, tb.height() + 6)
            
        elif isinstance(el, ImageElement):
            if el.image_path and os.path.isfile(el.image_path):
                try:
                    pix = QPixmap(el.image_path)
                    if not pix.isNull():
                        item = self.scene.addPixmap(pix)
                        item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                        scale_x = el.width / max(1.0, float(pix.width()))
                        scale_y = el.height / max(1.0, float(pix.height()))
                        if el.keep_aspect_ratio:
                            scale_val = min(scale_x, scale_y)
                            item.setTransform(QTransform().scale(scale_val, scale_val))
                        else:
                            item.setTransform(QTransform().scale(scale_x, scale_y))
                        item.setPos(QPointF(el.x, el.y))
                except Exception as img_err:
                    print(f"Resim yüklenirken hata: {img_err}")
            if not item:
                item = self.scene.addRect(rect, QPen(QColor("#888888"), 1, Qt.PenStyle.DashLine), QBrush(Qt.BrushStyle.NoBrush))
                    
        elif isinstance(el, ShapeElement):
            pen = QPen(QColor(el.stroke_color), el.stroke_width)
            brush = QBrush(QColor(el.fill_color)) if el.fill_color else QBrush(Qt.BrushStyle.NoBrush)
            
            if el.shape_type == "rectangle":
                item = self.scene.addRect(rect, pen, brush)
            elif el.shape_type == "ellipse":
                item = self.scene.addEllipse(rect, pen, brush)
            elif el.shape_type == "line":
                p1 = QPointF(el.x, el.y)
                p2 = QPointF(el.x + el.width, el.y + el.height)
                item = self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), pen)
            elif el.shape_type == "arrow":
                path = QPainterPath()
                p1 = QPointF(el.x, el.y)
                p2 = QPointF(el.x + el.width, el.y + el.height)
                path.moveTo(p1)
                path.lineTo(p2)
                
                dx = p2.x() - p1.x()
                dy = p2.y() - p1.y()
                l = math.hypot(dx, dy)
                if l > 4:
                    ux, uy = dx/l, dy/l
                    alen = min(14.0, l * 0.4)
                    aw = alen * 0.5
                    path.moveTo(p2)
                    path.lineTo(QPointF(p2.x() - alen*ux + aw*uy, p2.y() - alen*uy - aw*ux))
                    path.moveTo(p2)
                    path.lineTo(QPointF(p2.x() - alen*ux - aw*uy, p2.y() - alen*uy + aw*ux))
                item = self.scene.addPath(path, pen)
                    
        elif isinstance(el, DrawingElement):
            sw = getattr(el, "stroke_width", 2.0)
            if len(el.points) == 1:
                pt = el.points[0]
                r = max(1.0, sw / 2.0)
                c = QColor(el.color)
                if el.is_highlighter:
                    c.setAlphaF(el.opacity)
                item = self.scene.addEllipse(pt[0] - r, pt[1] - r, r * 2.0, r * 2.0, QPen(Qt.PenStyle.NoPen), QBrush(c))
            elif len(el.points) >= 2:
                path = QPainterPath()
                path.moveTo(el.points[0][0], el.points[0][1])
                for i in range(1, len(el.points)):
                    p0 = el.points[i - 1]
                    p1 = el.points[i]
                    mid_x = (p0[0] + p1[0]) / 2.0
                    mid_y = (p0[1] + p1[1]) / 2.0
                    path.quadTo(p0[0], p0[1], mid_x, mid_y)
                path.lineTo(el.points[-1][0], el.points[-1][1])
                    
                pen = QPen(QColor(el.color), sw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                if el.is_highlighter:
                    c = QColor(el.color)
                    c.setAlphaF(el.opacity)
                    pen.setColor(c)
                item = self.scene.addPath(path, pen)
                
        elif isinstance(el, RedactionElement):
            item = self.scene.addRect(rect, QPen(QColor("#E5252A"), 1.5, Qt.PenStyle.DashLine), QBrush(QColor(0, 0, 0, 240)))
            text_item = QGraphicsTextItem("SANSÜR / REDACTED", item)
            text_item.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            text_item.setDefaultTextColor(QColor("#FFFFFF"))
            text_item.setPos(rect.topLeft() + QPointF(4, 2))
            
        elif isinstance(el, WatermarkElement):
            item = self.scene.addText(el.text)
            f = QFont("Arial", int(el.font_size), QFont.Weight.Bold)
            item.setFont(f)
            c = QColor(el.color)
            c.setAlphaF(el.opacity)
            item.setDefaultTextColor(c)
            item.setRotation(el.angle)
            item.setPos(rect.topLeft())
            
        if item:
            item.setZValue(10)
            self.element_items[el.id] = item
            self.scene.update()
            self.viewport().update()

    def update_element_visual(self, el: BaseElement):
        self.draw_element_on_scene(el)
        if self.selected_element == el:
            self.gizmo.update_geometry()
        self.page_modified.emit(self.current_page_idx)

    def add_element_internal(self, page_num: int, element: BaseElement):
        self.page_elements.setdefault(page_num, []).append(element)
        if self.current_page_idx == page_num:
            self.draw_element_on_scene(element)
            self.selected_element = element
            self.gizmo.set_target(element)
            self.element_selected.emit(element)
        self.page_modified.emit(page_num)

    def remove_element_internal(self, page_num: int, element: BaseElement):
        page_elems = self.page_elements.get(page_num, [])
        if element in page_elems:
            page_elems.remove(element)
        if self.current_page_idx == page_num:
            if element.id in self.element_items:
                self.scene.removeItem(self.element_items[element.id])
                del self.element_items[element.id]
            if self.selected_element == element:
                self.selected_element = None
                self.gizmo.set_target(None)
                self.element_selected.emit(None)
        self.page_modified.emit(page_num)

    def zoom_in(self):
        self.finish_inline_text_editing(commit=True)
        self.scale(1.25, 1.25)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_out(self):
        self.finish_inline_text_editing(commit=True)
        self.scale(0.8, 0.8)
        self.zoom_changed.emit(self.transform().m11())

    def set_zoom(self, zoom_factor: float):
        self.finish_inline_text_editing(commit=True)
        current = self.transform().m11()
        if current > 0:
            scale_ratio = zoom_factor / current
            self.scale(scale_ratio, scale_ratio)
            self.zoom_changed.emit(zoom_factor)

    def fit_page(self):
        if not self.doc or not self.page_bg_item:
            return
        rect = self.page_bg_item.boundingRect()
        scale_val = self.page_bg_item.scale()
        target_rect = QRectF(0, 0, rect.width() * scale_val, rect.height() * scale_val)
        self.fitInView(target_rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit(self.transform().m11())

    def fit_width(self):
        if not self.doc or not self.page_bg_item:
            return
        rect = self.page_bg_item.boundingRect()
        scale_val = self.page_bg_item.scale()
        w = rect.width() * scale_val
        view_w = self.viewport().width() - 30
        if w > 0:
            target_scale = view_w / w
            self.set_zoom(target_scale)

    def highlight_search_rects(self, rects: List[fitz.Rect]):
        for itm in self.search_highlight_items:
            self.scene.removeItem(itm)
        self.search_highlight_items.clear()
        
        for r in rects:
            qrect = QRectF(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0)
            highlight_item = self.scene.addRect(
                qrect, 
                QPen(QColor("#FF9800"), 1.5), 
                QBrush(QColor(255, 235, 59, 130))
            )
            highlight_item.setZValue(20)
            self.search_highlight_items.append(highlight_item)

    # Kopyalama / Yapıştırma / Çoğaltma
    def copy_selected(self):
        if self.selected_element:
            self.clipboard_element = self.selected_element.clone()

    def paste_copied(self):
        if self.clipboard_element:
            new_el = self.clipboard_element.clone()
            new_el.x += 15.0
            new_el.y += 15.0
            cmd = AddElementCommand(self, self.current_page_idx, new_el, "Öğe Yapıştır")
            self.undo_stack.push(cmd)
            self.clipboard_element = new_el

    def duplicate_selected(self):
        if self.selected_element:
            new_el = self.selected_element.clone()
            new_el.x += 15.0
            new_el.y += 15.0
            cmd = AddElementCommand(self, self.current_page_idx, new_el, "Öğe Çoğalt")
            self.undo_stack.push(cmd)

    # Doğrudan Tuval Üzerinde Satır İçi Metin Düzenleme (Adobe Acrobat Seviyesi)
    def start_inline_text_editing(self, el: TextElement, is_new: bool = False):
        self.finish_inline_text_editing(commit=True)
        
        self.editing_element = el
        self.editing_is_new = is_new
        
        editor = QTextEdit(self.viewport())
        editor.setAcceptRichText(False)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        zoom = self.transform().m11()
        screen_pt = self.mapFromScene(QPointF(el.x, el.y))
        
        font = QFont(el.font_family, max(9, int(el.font_size * zoom)))
        font.setBold(el.bold)
        font.setItalic(el.italic)
        editor.setFont(font)
        
        # Adobe Acrobat tarzı profesyonel odak çerçevesi
        editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.96);
                color: {el.color};
                border: 2px solid #0099FF;
                border-radius: 3px;
                padding: 4px;
                selection-background-color: #0099FF;
                selection-color: #FFFFFF;
            }}
        """)
        
        w = max(180, int(el.width * zoom))
        h = max(45, int(el.height * zoom))
        editor.setGeometry(screen_pt.x(), screen_pt.y(), w, h)
        
        if not is_new and el.text:
            editor.setPlainText(el.text)
            editor.selectAll()
        else:
            editor.setPlaceholderText("Metin yazın... (Tamamlamak için dışarı tıklayın veya Ctrl+Enter)")
            
        editor.installEventFilter(self)
        editor.textChanged.connect(self._on_inline_text_changed)
        
        self.inline_editor = editor
        self.gizmo.setVisible(False)
        editor.show()
        editor.setFocus()

    def _on_inline_text_changed(self):
        if not self.inline_editor:
            return
        doc_h = self.inline_editor.document().size().height()
        current_h = self.inline_editor.height()
        if doc_h + 16 > current_h:
            self.inline_editor.resize(self.inline_editor.width(), int(doc_h + 20))

    def update_inline_editor_geometry(self):
        if self.inline_editor and self.editing_element:
            zoom = self.transform().m11()
            screen_pt = self.mapFromScene(QPointF(self.editing_element.x, self.editing_element.y))
            w = max(180, int(self.editing_element.width * zoom))
            h = max(45, int(self.editing_element.height * zoom))
            self.inline_editor.setGeometry(screen_pt.x(), screen_pt.y(), w, h)

    def finish_inline_text_editing(self, commit: bool = True):
        if not self.inline_editor or not self.editing_element:
            return
            
        el = self.editing_element
        is_new = self.editing_is_new
        text = self.inline_editor.toPlainText().strip()
        
        editor = self.inline_editor
        self.inline_editor = None
        self.editing_element = None
        self.editing_is_new = False
        editor.deleteLater()
        
        if commit and text:
            old_text = el.text
            el.text = text
            
            # Dinamik boyut hesaplama
            lines = text.split("\n")
            max_line_len = max(len(l) for l in lines)
            approx_w = max(60.0, max_line_len * (el.font_size * 0.65) + 20.0)
            approx_h = max(25.0, len(lines) * (el.font_size * 1.35) + 12.0)
            el.width = max(el.width, approx_w)
            el.height = max(el.height, approx_h)
            
            if is_new:
                cmd = AddElementCommand(self, self.current_page_idx, el)
                self.undo_stack.push(cmd)
            else:
                if old_text != text:
                    self.update_element_visual(el)
                    self.element_selected.emit(el)
            self.selected_element = el
            self.gizmo.set_target(el)
            self.element_selected.emit(el)
        else:
            if not is_new:
                self.gizmo.set_target(el)
        self.set_tool_mode("select")

    def eventFilter(self, obj, event):
        if obj == self.inline_editor:
            if event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key.Key_Escape:
                    self.finish_inline_text_editing(commit=False)
                    return True
                elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                    if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                        self.finish_inline_text_editing(commit=True)
                        return True
            elif event.type() == event.Type.FocusOut:
                self.finish_inline_text_editing(commit=True)
                return True
        return super().eventFilter(obj, event)

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.update_inline_editor_geometry()

    # Çift Tıklama ile Metin Düzenleme (Doğrudan tuvalde)
    def mouseDoubleClickEvent(self, event):
        sp = self.mapToScene(event.pos())
        if self.selected_element and isinstance(self.selected_element, TextElement):
            if self.selected_element.get_rect().contains(sp):
                self.start_inline_text_editing(self.selected_element, is_new=False)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        # Space ile el aracı geçici modu
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.is_space_pressed = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
            
        # Silme (Delete)
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_element:
                cmd = DeleteElementCommand(self, self.current_page_idx, self.selected_element)
                self.undo_stack.push(cmd)
                event.accept()
                return
                
        # Kopyala (Ctrl+C), Yapıştır (Ctrl+V), Çoğalt (Ctrl+D)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy_selected()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V:
                self.paste_copied()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_D:
                self.duplicate_selected()
                event.accept()
                return

        # Ok tuşlarıyla hassas konumlandırma (Nudge)
        step = 10.0 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1.0
        if self.selected_element and event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down]:
            old_r = self.selected_element.get_rect()
            dx, dy = 0.0, 0.0
            if event.key() == Qt.Key.Key_Left:
                dx = -step
            elif event.key() == Qt.Key.Key_Right:
                dx = step
            elif event.key() == Qt.Key.Key_Up:
                dy = -step
            elif event.key() == Qt.Key.Key_Down:
                dy = step
                
            new_r = old_r.translated(dx, dy)
            cmd = TransformElementCommand(self, self.selected_element, old_r, new_r, "Konum Kaydır")
            self.undo_stack.push(cmd)
            event.accept()
            return
            
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.is_space_pressed = False
            self.set_tool_mode(self.tool_mode)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if self.inline_editor:
            self.finish_inline_text_editing(commit=True)
            
        sp = self.mapToScene(event.pos())
        self.drag_start_pos = sp
        
        if self.is_space_pressed or self.tool_mode == "pan" or event.button() == Qt.MouseButton.MiddleButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._pan_start = event.pos()
            event.accept()
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tool_mode == "select":
                if self.selected_element:
                    handle_idx = self.gizmo.hit_test_handle(sp)
                    if handle_idx != -1:
                        self.is_resizing_handle = True
                        self.active_handle_idx = handle_idx
                        self.element_initial_rect = self.selected_element.get_rect()
                        event.accept()
                        return
                        
                clicked_el = None
                page_elems = self.page_elements.get(self.current_page_idx, [])
                for el in reversed(page_elems):
                    if el.get_rect().contains(sp):
                        clicked_el = el
                        break
                        
                if clicked_el:
                    self.selected_element = clicked_el
                    self.gizmo.set_target(clicked_el)
                    self.element_selected.emit(clicked_el)
                    self.is_dragging_item = True
                    self.element_initial_rect = clicked_el.get_rect()
                else:
                    self.selected_element = None
                    self.gizmo.set_target(None)
                    self.element_selected.emit(None)
                    
            elif self.tool_mode == "text":
                el = TextElement(x=sp.x(), y=sp.y(), width=180.0, height=35.0, text="")
                el.color = self.default_text_color
                el.font_size = self.default_font_size
                el.font_family = self.default_font_family
                el.bold = self.default_bold
                el.italic = self.default_italic
                self.start_inline_text_editing(el, is_new=True)
                return
                
            elif self.tool_mode == "image":
                path, _ = QFileDialog.getOpenFileName(self, "Resim / İmza Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tiff)")
                if path:
                    pix = QPixmap(path)
                    w, h = 200.0, 150.0
                    if not pix.isNull() and pix.width() > 0:
                        ratio = pix.height() / pix.width()
                        w = min(300.0, max(80.0, float(pix.width())))
                        h = w * ratio
                    el = ImageElement(x=sp.x(), y=sp.y(), width=w, height=h, image_path=path)
                    cmd = AddElementCommand(self, self.current_page_idx, el, "Resim Ekle")
                    self.undo_stack.push(cmd)
                self.set_tool_mode("select")
                event.accept()
                return
                
            elif self.tool_mode in ["pen", "highlighter"]:
                is_hi = (self.tool_mode == "highlighter")
                sw = self.current_highlighter_width if is_hi else self.current_stroke_width
                col = self.current_highlighter_color if is_hi else self.current_stroke_color
                self.current_drawing_element = DrawingElement(
                    points=[(sp.x(), sp.y())], 
                    is_highlighter=is_hi,
                    stroke_width=sw,
                    color=col
                )
                self.draw_element_on_scene(self.current_drawing_element)
                
            elif self.tool_mode in ["rect", "ellipse", "line", "arrow", "redact"]:
                self.shape_start_pt = sp
                if self.tool_mode == "redact":
                    el = RedactionElement(x=sp.x(), y=sp.y(), width=10, height=10)
                else:
                    el = ShapeElement(shape_type=self.tool_mode, x=sp.x(), y=sp.y(), width=10, height=10)
                    el.stroke_width = self.current_stroke_width
                    el.stroke_color = self.current_stroke_color
                self.current_drawing_element = el
                self.draw_element_on_scene(el)
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        sp = self.mapToScene(event.pos())
        self.mouse_moved.emit(sp.x(), sp.y())
        
        if hasattr(self, "_pan_start") and (self.is_space_pressed or self.tool_mode == "pan" or event.buttons() == Qt.MouseButton.MiddleButton):
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
            
        if self.tool_mode == "select":
            if self.is_dragging_item and self.selected_element:
                dx = sp.x() - self.drag_start_pos.x()
                dy = sp.y() - self.drag_start_pos.y()
                new_rect = self.element_initial_rect.translated(dx, dy)
                self.selected_element.set_rect(new_rect)
                self.draw_element_on_scene(self.selected_element)
                self.gizmo.update_geometry()
                
            elif self.is_resizing_handle and self.selected_element:
                dx = sp.x() - self.drag_start_pos.x()
                dy = sp.y() - self.drag_start_pos.y()
                init = self.element_initial_rect
                
                h = self.active_handle_idx
                new_x, new_y = init.x(), init.y()
                new_w, new_h = init.width(), init.height()
                
                if h in [HANDLE_TOP_LEFT, HANDLE_LEFT, HANDLE_BOTTOM_LEFT]:
                    new_x = min(init.right() - 10, init.x() + dx)
                    new_w = init.right() - new_x
                if h in [HANDLE_TOP_LEFT, HANDLE_TOP, HANDLE_TOP_RIGHT]:
                    new_y = min(init.bottom() - 10, init.y() + dy)
                    new_h = init.bottom() - new_y
                if h in [HANDLE_TOP_RIGHT, HANDLE_RIGHT, HANDLE_BOTTOM_RIGHT]:
                    new_w = max(10.0, init.width() + dx)
                if h in [HANDLE_BOTTOM_LEFT, HANDLE_BOTTOM, HANDLE_BOTTOM_RIGHT]:
                    new_h = max(10.0, init.height() + dy)
                    
                new_rect = QRectF(new_x, new_y, new_w, new_h)
                self.selected_element.set_rect(new_rect)
                self.draw_element_on_scene(self.selected_element)
                self.gizmo.update_geometry()
            else:
                if self.selected_element:
                    h_idx = self.gizmo.hit_test_handle(sp)
                    if h_idx in [HANDLE_TOP_LEFT, HANDLE_BOTTOM_RIGHT]:
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif h_idx in [HANDLE_TOP_RIGHT, HANDLE_BOTTOM_LEFT]:
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    elif h_idx in [HANDLE_TOP, HANDLE_BOTTOM]:
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    elif h_idx in [HANDLE_LEFT, HANDLE_RIGHT]:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif self.selected_element.get_rect().contains(sp):
                        self.setCursor(Qt.CursorShape.SizeAllCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                        
        elif self.tool_mode in ["pen", "highlighter"]:
            if self.current_drawing_element and isinstance(self.current_drawing_element, DrawingElement):
                if self.current_drawing_element.points:
                    last_pt = self.current_drawing_element.points[-1]
                    dx = sp.x() - last_pt[0]
                    dy = sp.y() - last_pt[1]
                    if math.hypot(dx, dy) >= 1.5:
                        self.current_drawing_element.add_point((sp.x(), sp.y()))
                        self.draw_element_on_scene(self.current_drawing_element)
                
        elif self.tool_mode in ["rect", "ellipse", "line", "arrow", "redact"]:
            if self.current_drawing_element:
                x = min(self.shape_start_pt.x(), sp.x())
                y = min(self.shape_start_pt.y(), sp.y())
                w = abs(sp.x() - self.shape_start_pt.x())
                h = abs(sp.y() - self.shape_start_pt.y())
                
                if self.tool_mode in ["line", "arrow"]:
                    self.current_drawing_element.x = self.shape_start_pt.x()
                    self.current_drawing_element.y = self.shape_start_pt.y()
                    self.current_drawing_element.width = sp.x() - self.shape_start_pt.x()
                    self.current_drawing_element.height = sp.y() - self.shape_start_pt.y()
                else:
                    self.current_drawing_element.set_rect(QRectF(x, y, max(5, w), max(5, h)))
                    
                self.draw_element_on_scene(self.current_drawing_element)
                
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, "_pan_start"):
            del self._pan_start
            if self.is_space_pressed or self.tool_mode == "pan":
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.set_tool_mode(self.tool_mode)
                
        if self.is_dragging_item and self.selected_element:
            self.is_dragging_item = False
            current_rect = self.selected_element.get_rect()
            if current_rect != self.element_initial_rect:
                cmd = TransformElementCommand(self, self.selected_element, self.element_initial_rect, current_rect)
                self.undo_stack.push(cmd)
                
        if self.is_resizing_handle and self.selected_element:
            self.is_resizing_handle = False
            current_rect = self.selected_element.get_rect()
            if current_rect != self.element_initial_rect:
                cmd = TransformElementCommand(self, self.selected_element, self.element_initial_rect, current_rect)
                self.undo_stack.push(cmd)
                
        if self.current_drawing_element:
            cmd = AddElementCommand(self, self.current_page_idx, self.current_drawing_element)
            self.undo_stack.push(cmd)
            self.current_drawing_element = None
            if self.tool_mode in ["rect", "ellipse", "line", "arrow", "redact"]:
                self.set_tool_mode("select")
                
        super().mouseReleaseEvent(event)
