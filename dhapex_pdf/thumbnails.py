"""
Nexora PDF Studio - Adobe Acrobat Tarzı Sayfa Küçük Resimleri (Thumbnails) Paneli
Sayfa önizlemeleri, hızlı geçiş, sağ tık sayfa işlemleri (döndürme, silme, ekleme, çıkarma).
"""

from typing import Optional
import pymupdf as fitz
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from dhapex_pdf.icons import IconFactory

class ThumbnailsPanel(QWidget):
    page_selected = pyqtSignal(int)
    rotate_requested = pyqtSignal(int, int) # page_num, degrees
    delete_requested = pyqtSignal(int)      # page_num
    insert_requested = pyqtSignal(int)      # after_page_num
    extract_requested = pyqtSignal(int)     # page_num
    move_page_requested = pyqtSignal(int, int) # from_idx, to_idx

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc: Optional[fitz.Document] = None
        self.current_page = 0
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(130, 180))
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_clicked)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.list_widget)

    def load_document(self, doc: fitz.Document):
        self.doc = doc
        self.refresh_thumbnails()

    def refresh_thumbnails(self):
        self.list_widget.clear()
        if not self.doc or len(self.doc) == 0:
            return
            
        thumb_width = 130
        for i in range(len(self.doc)):
            page = self.doc.load_page(i)
            rect = page.rect
            scale = thumb_width / max(1.0, rect.width)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
            qpix = QPixmap.fromImage(qimg)
            
            item = QListWidgetItem()
            item.setIcon(QIcon(qpix))
            item.setText(f"{i + 1}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, i)
            
            self.list_widget.addItem(item)
            
        self.set_current_page(self.current_page)

    def set_current_page(self, page_num: int):
        self.current_page = page_num
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == page_num:
                self.list_widget.blockSignals(True)
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                self.list_widget.blockSignals(False)
                break

    def on_item_clicked(self, item: QListWidgetItem):
        page_num = item.data(Qt.ItemDataRole.UserRole)
        self.current_page = page_num
        self.page_selected.emit(page_num)

    def show_context_menu(self, pos):
        if not self.doc or len(self.doc) == 0:
            return
            
        item = self.list_widget.itemAt(pos)
        page_num = item.data(Qt.ItemDataRole.UserRole) if item else self.current_page
        
        menu = QMenu(self)
        
        act_cw = menu.addAction(IconFactory.get("rotate_cw", 16), "Sağa Döndür (90°)")
        act_ccw = menu.addAction(IconFactory.get("rotate_ccw", 16), "Sola Döndür (90°)")
        menu.addSeparator()
        act_insert = menu.addAction(IconFactory.get("page_add", 16), "Sonrasına Boş Sayfa Ekle")
        act_extract = menu.addAction(IconFactory.get("page_extract", 16), "Bu Sayfayı Dışa Aktar (PDF)")
        menu.addSeparator()
        act_up = menu.addAction(IconFactory.get("prev_page", 16), "Yukarı Taşı")
        act_down = menu.addAction(IconFactory.get("next_page", 16), "Aşağı Taşı")
        if page_num == 0:
            act_up.setEnabled(False)
        if page_num == len(self.doc) - 1:
            act_down.setEnabled(False)
        menu.addSeparator()
        act_del = menu.addAction(IconFactory.get("page_delete", 16), "Bu Sayfayı Sil")
        if len(self.doc) <= 1:
            act_del.setEnabled(False)
            
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        if action == act_cw:
            self.rotate_requested.emit(page_num, 90)
        elif action == act_ccw:
            self.rotate_requested.emit(page_num, -90)
        elif action == act_insert:
            self.insert_requested.emit(page_num)
        elif action == act_extract:
            self.extract_requested.emit(page_num)
        elif action == act_up:
            self.move_page_requested.emit(page_num, page_num - 1)
        elif action == act_down:
            self.move_page_requested.emit(page_num, page_num + 1)
        elif action == act_del:
            self.delete_requested.emit(page_num)
