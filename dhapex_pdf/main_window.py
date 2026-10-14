"""
Nexora PDF Studio - Ana Pencere (Main Window)
Adobe Acrobat Seviyesinde Modern Ribbon, Dock Panelleri, Vektörel Araçlar, Yazdırma ve Güvenli Dosya İşleme.
"""

import os
import shutil
import tempfile
from typing import Optional, List, Dict
import pymupdf as fitz

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QMenuBar, QMenu, QStatusBar, QDockWidget, QFileDialog, QMessageBox,
    QInputDialog, QLabel, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QPushButton, QColorDialog, QTabWidget, QApplication, QToolButton
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QKeySequence, QPixmap, QImage, QCloseEvent,
    QDragEnterEvent, QDropEvent, QColor
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from dhapex_pdf import APP_NAME, APP_VERSION
from dhapex_pdf.icons import IconFactory
from dhapex_pdf.canvas import PDFCanvasView
from dhapex_pdf.thumbnails import ThumbnailsPanel
from dhapex_pdf.search import SearchPanel
from dhapex_pdf.inspector import InspectorPanel
from dhapex_pdf.models import (
    BaseElement, TextElement, ImageElement, ShapeElement, DrawingElement, RedactionElement, WatermarkElement
)
from dhapex_pdf.dialogs import (
    WatermarkDialog, MetadataDialog, InsertPageDialog, ExtractPagesDialog,
    MergeDialog, AboutDialog
)
from dhapex_pdf.commands import (
    AddElementCommand, DeleteElementCommand, ChangePropertyCommand
)
from PyQt6.QtGui import QUndoStack

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1360, 840)
        self.setMinimumSize(960, 640)
        self.setAcceptDrops(True)
        
        self.setWindowIcon(IconFactory.get("app_icon", 64))
        
        self.doc: Optional[fitz.Document] = None
        self.current_file_path: Optional[str] = None
        self.is_dirty: bool = False
        
        self.undo_stack = QUndoStack(self)
        
        self.canvas_view = PDFCanvasView(self.undo_stack, self)
        self.setCentralWidget(self.canvas_view)
        
        self.setup_docks()
        self.setup_menu_bar()
        self.setup_toolbars()
        self.setup_status_bar()
        self.connect_signals()
        
        self.new_document()

    def make_action(self, text: str, slot=None, shortcut=None, icon=None) -> QAction:
        act = QAction(text, self)
        if icon is not None:
            act.setIcon(icon)
        if shortcut is not None:
            act.setShortcut(shortcut)
        if slot is not None:
            act.triggered.connect(slot)
        return act

    def setup_docks(self):
        # Sol Panel (Sayfa Küçük Resimleri ve Arama)
        self.left_dock = QDockWidget("Gezinme & Sayfalar", self)
        self.left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.left_dock.setMinimumWidth(180)
        
        self.left_tabs = QTabWidget()
        self.thumbnails_panel = ThumbnailsPanel(self)
        self.search_panel = SearchPanel(self)
        
        self.left_tabs.addTab(self.thumbnails_panel, IconFactory.get("first_page", 14), "Sayfalar")
        self.left_tabs.addTab(self.search_panel, IconFactory.get("search", 14), "Arama")
        self.left_dock.setWidget(self.left_tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)
        
        # Sağ Panel (Özellik Denetçisi)
        self.right_dock = QDockWidget("Özellik Denetçisi", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_dock.setMinimumWidth(240)
        
        self.inspector_panel = InspectorPanel(self)
        self.right_dock.setWidget(self.inspector_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

    def setup_menu_bar(self):
        mb = self.menuBar()
        
        # Dosya Menüsü
        m_file = mb.addMenu("&Dosya")
        m_file.addAction(self.make_action("Yeni PDF (Boş Belge)", self.new_document, QKeySequence.StandardKey.New, IconFactory.get("new_file", 16)))
        m_file.addAction(self.make_action("Aç...", self.open_pdf_dialog, QKeySequence.StandardKey.Open, IconFactory.get("open_file", 16)))
        m_file.addSeparator()
        m_file.addAction(self.make_action("Kaydet", self.save_pdf, QKeySequence.StandardKey.Save, IconFactory.get("save_file", 16)))
        m_file.addAction(self.make_action("Farklı Kaydet...", self.save_as_pdf, QKeySequence.StandardKey.SaveAs, IconFactory.get("save_as", 16)))
        m_file.addSeparator()
        
        m_file.addAction(self.make_action("Yazdır...", self.print_document, QKeySequence.StandardKey.Print, IconFactory.get("print", 16)))
        m_file.addSeparator()
        
        m_export = m_file.addMenu(IconFactory.get("export", 16), "Dışa Aktar")
        m_export.addAction(self.make_action("Geçerli Sayfayı Resim Olarak (PNG)...", self.export_page_as_image))
        m_export.addAction(self.make_action("Tüm Sayfaları Resim Olarak...", self.export_all_pages_as_images))
        m_export.addAction(self.make_action("Belge Metnini Çıkar (.txt)...", self.export_text))
        
        m_file.addAction(self.make_action("PDF Dosyalarını Birleştir...", self.open_merge_dialog, icon=IconFactory.get("merge", 16)))
        m_file.addSeparator()
        m_file.addAction(self.make_action("Belge Özellikleri...", self.open_metadata_dialog, icon=IconFactory.get("metadata", 16)))
        m_file.addSeparator()
        m_file.addAction(self.make_action("Çıkış", self.close, QKeySequence.StandardKey.Quit))
        
        # Düzenle Menüsü
        m_edit = mb.addMenu("&Düzenle")
        self.act_undo = self.undo_stack.createUndoAction(self, "Geri Al")
        self.act_undo.setIcon(IconFactory.get("undo", 16))
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        m_edit.addAction(self.act_undo)
        
        self.act_redo = self.undo_stack.createRedoAction(self, "Yinele")
        self.act_redo.setIcon(IconFactory.get("redo", 16))
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        m_edit.addAction(self.act_redo)
        m_edit.addSeparator()
        
        m_edit.addAction(self.make_action("Kopyala", self.canvas_view.copy_selected, QKeySequence.StandardKey.Copy))
        m_edit.addAction(self.make_action("Yapıştır", self.canvas_view.paste_copied, QKeySequence.StandardKey.Paste))
        m_edit.addAction(self.make_action("Çoğalt", self.canvas_view.duplicate_selected, QKeySequence("Ctrl+D")))
        m_edit.addSeparator()
        m_edit.addAction(self.make_action("Seçiliyi Sil", self.delete_selected_element, QKeySequence.StandardKey.Delete, IconFactory.get("delete_item", 16)))
        
        # Görünüm Menüsü
        m_view = mb.addMenu("&Görünüm")
        m_view.addAction(self.make_action("Yakınlaştır", self.canvas_view.zoom_in, QKeySequence.StandardKey.ZoomIn, IconFactory.get("zoom_in", 16)))
        m_view.addAction(self.make_action("Uzaklaştır", self.canvas_view.zoom_out, QKeySequence.StandardKey.ZoomOut, IconFactory.get("zoom_out", 16)))
        m_view.addAction(self.make_action("Sayfaya Sığdır", self.canvas_view.fit_page, QKeySequence("Ctrl+0"), IconFactory.get("zoom_fit", 16)))
        m_view.addAction(self.make_action("Genişliğe Sığdır", self.canvas_view.fit_width, QKeySequence("Ctrl+1"), IconFactory.get("zoom_width", 16)))
        m_view.addSeparator()
        m_view.addAction(self.left_dock.toggleViewAction())
        m_view.addAction(self.right_dock.toggleViewAction())
        
        # Araçlar Menüsü
        m_tools = mb.addMenu("&Araçlar")
        m_tools.addAction(self.make_action("Seçim Aracı", lambda: self.set_tool("select"), QKeySequence("V")))
        m_tools.addAction(self.make_action("El / Kaydırma Aracı", lambda: self.set_tool("pan"), QKeySequence("H")))
        m_tools.addSeparator()
        m_tools.addAction(self.make_action("Metin Ekle", lambda: self.set_tool("text"), QKeySequence("T")))
        m_tools.addAction(self.make_action("Resim Ekle", lambda: self.set_tool("image"), QKeySequence("I")))
        m_tools.addAction(self.make_action("Serbest Kalem", lambda: self.set_tool("pen"), QKeySequence("P")))
        m_tools.addAction(self.make_action("Vurgulayıcı", lambda: self.set_tool("highlighter"), QKeySequence("U")))
        m_tools.addSeparator()
        m_tools.addAction(self.make_action("Dikdörtgen Çiz", lambda: self.set_tool("rect"), QKeySequence("R")))
        m_tools.addAction(self.make_action("Elips Çiz", lambda: self.set_tool("ellipse"), QKeySequence("E")))
        m_tools.addAction(self.make_action("Çizgi Çiz", lambda: self.set_tool("line"), QKeySequence("L")))
        m_tools.addAction(self.make_action("Ok İşareti Çiz", lambda: self.set_tool("arrow"), QKeySequence("A")))
        m_tools.addSeparator()
        m_tools.addAction(self.make_action("Karartma / Sansür (Redaction)", lambda: self.set_tool("redact"), QKeySequence("X")))
        m_tools.addAction(self.make_action("Filigran Ekle (Watermark)...", self.open_watermark_dialog))
        m_tools.addAction(self.make_action("Belgede Ara...", self.focus_search, QKeySequence.StandardKey.Find))
        
        # Sayfalar Menüsü
        m_pages = mb.addMenu("&Sayfalar")
        m_pages.addAction(self.make_action("Sağa Döndür (90°)", lambda: self.rotate_page(90), icon=IconFactory.get("rotate_cw", 16)))
        m_pages.addAction(self.make_action("Sola Döndür (90°)", lambda: self.rotate_page(-90), icon=IconFactory.get("rotate_ccw", 16)))
        m_pages.addSeparator()
        m_pages.addAction(self.make_action("Boş Sayfa Ekle...", self.open_insert_page_dialog, icon=IconFactory.get("page_add", 16)))
        m_pages.addAction(self.make_action("Geçerli Sayfayı Sil", self.delete_current_page, icon=IconFactory.get("page_delete", 16)))
        m_pages.addAction(self.make_action("Sayfaları Dışa Aktar...", self.open_extract_dialog, icon=IconFactory.get("page_extract", 16)))
        
        # Yardım Menüsü
        m_help = mb.addMenu("&Yardım")
        m_help.addAction(self.make_action("Klavye Kısayolları", self.show_shortcuts_guide))
        m_help.addSeparator()
        m_help.addAction(self.make_action(f"Hakkında - {APP_NAME}", self.show_about_dialog, icon=IconFactory.get("app_icon", 16)))

    def setup_toolbars(self):
        # 1. Dosya ve Düzenleme Araç Çubuğu
        tb_main = QToolBar("Temel İşlemler", self)
        tb_main.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb_main)
        
        tb_main.addAction(self.make_action("Aç", self.open_pdf_dialog, icon=IconFactory.get("open_file", 20)))
        tb_main.addAction(self.make_action("Kaydet", self.save_pdf, icon=IconFactory.get("save_file", 20)))
        tb_main.addAction(self.make_action("Yazdır", self.print_document, icon=IconFactory.get("print", 20)))
        tb_main.addSeparator()
        tb_main.addAction(self.act_undo)
        tb_main.addAction(self.act_redo)
        tb_main.addSeparator()
        
        # Sayfa Gezinme Butonları
        tb_main.addAction(self.make_action("İlk Sayfa", self.first_page, icon=IconFactory.get("first_page", 20)))
        tb_main.addAction(self.make_action("Önceki Sayfa", self.prev_page, icon=IconFactory.get("prev_page", 20)))
        
        self.spin_page = QSpinBox()
        self.spin_page.setRange(1, 1)
        self.spin_page.valueChanged.connect(self.on_page_spin_changed)
        tb_main.addWidget(self.spin_page)
        
        self.lbl_page_total = QLabel(" / 1")
        self.lbl_page_total.setStyleSheet("color: #A0A0AA; padding-right: 6px;")
        tb_main.addWidget(self.lbl_page_total)
        
        tb_main.addAction(self.make_action("Sonraki Sayfa", self.next_page, icon=IconFactory.get("next_page", 20)))
        tb_main.addAction(self.make_action("Son Sayfa", self.last_page, icon=IconFactory.get("last_page", 20)))
        tb_main.addSeparator()
        
        # Yakınlaştırma
        tb_main.addAction(self.make_action("Uzaklaştır", self.canvas_view.zoom_out, icon=IconFactory.get("zoom_out", 20)))
        
        self.cb_zoom = QComboBox()
        self.cb_zoom.addItems(["%50", "%75", "%100", "%125", "%150", "%200", "%300", "Sayfaya Sığdır", "Genişliğe Sığdır"])
        self.cb_zoom.setCurrentText("%100")
        self.cb_zoom.currentTextChanged.connect(self.on_zoom_combo_changed)
        tb_main.addWidget(self.cb_zoom)
        
        tb_main.addAction(self.make_action("Yakınlaştır", self.canvas_view.zoom_in, icon=IconFactory.get("zoom_in", 20)))
        tb_main.addAction(self.make_action("Sığdır", self.canvas_view.fit_page, icon=IconFactory.get("zoom_fit", 20)))
        tb_main.addSeparator()
        
        # 2. Düzenleme ve Araçlar Çubuğu
        tb_tools = QToolBar("Düzenleme Araçları", self)
        tb_tools.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb_tools)
        
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        
        self.act_select = self.create_tool_action(tb_tools, "tool_select", "Seçim Aracı (V)", "select")
        self.act_pan = self.create_tool_action(tb_tools, "tool_pan", "El / Kaydırma Aracı (H)", "pan")
        tb_tools.addSeparator()
        self.act_text = self.create_tool_action(tb_tools, "tool_text", "Metin Ekle (T)", "text")
        self.act_image = self.create_tool_action(tb_tools, "tool_image", "Resim / İmza Ekle (I)", "image")
        self.act_pen = self.create_tool_action(tb_tools, "tool_pen", "Serbest Çizim Kalemi (P)", "pen")
        self.act_hi = self.create_tool_action(tb_tools, "tool_highlighter", "Vurgulayıcı (U)", "highlighter")
        tb_tools.addSeparator()
        self.act_rect = self.create_tool_action(tb_tools, "tool_rect", "Dikdörtgen Çiz (R)", "rect")
        self.act_ellipse = self.create_tool_action(tb_tools, "tool_ellipse", "Elips / Daire Çiz (E)", "ellipse")
        self.act_line = self.create_tool_action(tb_tools, "tool_line", "Çizgi Çiz (L)", "line")
        self.act_arrow = self.create_tool_action(tb_tools, "tool_arrow", "Ok İşareti Çiz (A)", "arrow")
        tb_tools.addSeparator()
        self.act_redact = self.create_tool_action(tb_tools, "tool_redact", "Karartma / Sansür (X)", "redact")
        
        tb_tools.addSeparator()
        tb_tools.addAction(self.make_action("Filigran Ekle", self.open_watermark_dialog, icon=IconFactory.get("tool_watermark", 20)))
        tb_tools.addAction(self.make_action("Belgede Ara (Ctrl+F)", self.focus_search, shortcut=QKeySequence.StandardKey.Find, icon=IconFactory.get("search", 20)))
        
        self.act_select.setChecked(True)
        
        # 3. Hızlı Biçimlendirme ve Özellikler Çubuğu
        tb_style = QToolBar("Hızlı Biçimlendirme", self)
        tb_style.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb_style)
        
        # Çizgi Kalınlığı & Rengi
        lbl_stroke = QLabel("  Çizgi: ")
        lbl_stroke.setStyleSheet("color: #A0A0AA; font-weight: bold; font-size: 11px;")
        tb_style.addWidget(lbl_stroke)
        
        self.spin_quick_stroke = QDoubleSpinBox()
        self.spin_quick_stroke.setRange(0.5, 30.0)
        self.spin_quick_stroke.setSingleStep(0.5)
        self.spin_quick_stroke.setSuffix(" pt")
        self.spin_quick_stroke.setValue(2.0)
        self.spin_quick_stroke.setToolTip("Çizgi / Kalem Kalınlığı (pt)")
        self.spin_quick_stroke.valueChanged.connect(self.on_quick_stroke_changed)
        tb_style.addWidget(self.spin_quick_stroke)
        
        self.btn_quick_stroke_color = QPushButton()
        self.btn_quick_stroke_color.setFixedSize(22, 22)
        self.btn_quick_stroke_color.setStyleSheet("background-color: #1E88E5; border: 1px solid #555; border-radius: 3px;")
        self.btn_quick_stroke_color.setToolTip("Çizgi / Kalem Rengi Seç")
        self.btn_quick_stroke_color.clicked.connect(self.pick_quick_stroke_color)
        tb_style.addWidget(self.btn_quick_stroke_color)
        
        tb_style.addSeparator()
        
        # Metin Ayarları
        lbl_text = QLabel("  Metin: ")
        lbl_text.setStyleSheet("color: #A0A0AA; font-weight: bold; font-size: 11px;")
        tb_style.addWidget(lbl_text)
        
        self.cb_quick_font = QComboBox()
        self.cb_quick_font.addItems(["Arial", "Calibri", "Segoe UI", "Times New Roman", "Courier New", "Georgia", "Verdana"])
        self.cb_quick_font.setToolTip("Yazı Tipi (Font)")
        self.cb_quick_font.currentTextChanged.connect(self.on_quick_font_family_changed)
        tb_style.addWidget(self.cb_quick_font)
        
        self.spin_quick_font_size = QDoubleSpinBox()
        self.spin_quick_font_size.setRange(6, 120)
        self.spin_quick_font_size.setSingleStep(1.0)
        self.spin_quick_font_size.setSuffix(" pt")
        self.spin_quick_font_size.setValue(12)
        self.spin_quick_font_size.setToolTip("Yazı Boyutu (pt)")
        self.spin_quick_font_size.valueChanged.connect(self.on_quick_font_size_changed)
        tb_style.addWidget(self.spin_quick_font_size)
        
        self.btn_quick_bold = QPushButton("K")
        self.btn_quick_bold.setCheckable(True)
        self.btn_quick_bold.setFixedSize(22, 22)
        self.btn_quick_bold.setStyleSheet("font-weight: bold;")
        self.btn_quick_bold.setToolTip("Kalın (Bold)")
        self.btn_quick_bold.toggled.connect(self.on_quick_bold_toggled)
        tb_style.addWidget(self.btn_quick_bold)
        
        self.btn_quick_italic = QPushButton("İ")
        self.btn_quick_italic.setCheckable(True)
        self.btn_quick_italic.setFixedSize(22, 22)
        self.btn_quick_italic.setStyleSheet("font-style: italic; font-weight: bold;")
        self.btn_quick_italic.setToolTip("İtalik (Italic)")
        self.btn_quick_italic.toggled.connect(self.on_quick_italic_toggled)
        tb_style.addWidget(self.btn_quick_italic)
        
        self.btn_quick_text_color = QPushButton()
        self.btn_quick_text_color.setFixedSize(22, 22)
        self.btn_quick_text_color.setStyleSheet("background-color: #000000; border: 1px solid #555; border-radius: 3px;")
        self.btn_quick_text_color.setToolTip("Metin Rengi Seç")
        self.btn_quick_text_color.clicked.connect(self.pick_quick_text_color)
        tb_style.addWidget(self.btn_quick_text_color)

    def create_tool_action(self, toolbar: QToolBar, icon_name: str, tooltip: str, mode: str) -> QAction:
        act = QAction(IconFactory.get(icon_name, 20), tooltip, self)
        act.setCheckable(True)
        act.triggered.connect(lambda: self.set_tool(mode))
        self.tool_group.addAction(act)
        toolbar.addAction(act)
        return act

    def setup_status_bar(self):
        sb = self.statusBar()
        
        self.lbl_status_mode = QLabel("Hazır")
        sb.addWidget(self.lbl_status_mode, stretch=1)
        
        self.lbl_page_info = QLabel("A4 (595 x 842 pt)")
        self.lbl_page_info.setStyleSheet("color: #8E8E98; padding: 0 10px;")
        sb.addPermanentWidget(self.lbl_page_info)
        
        self.lbl_coords = QLabel("X: 0 pt  Y: 0 pt")
        self.lbl_coords.setStyleSheet("color: #8E8E98; padding: 0 10px;")
        sb.addPermanentWidget(self.lbl_coords)
        
        self.lbl_zoom_val = QLabel("%100")
        self.lbl_zoom_val.setStyleSheet("color: #E0E0E0; font-weight: bold; padding: 0 5px;")
        sb.addPermanentWidget(self.lbl_zoom_val)

    def connect_signals(self):
        self.canvas_view.zoom_changed.connect(self.on_canvas_zoom_changed)
        self.canvas_view.mouse_moved.connect(self.on_canvas_mouse_moved)
        self.canvas_view.element_selected.connect(self.on_canvas_element_selected)
        self.canvas_view.page_modified.connect(self.on_page_modified)
        
        self.thumbnails_panel.page_selected.connect(self.jump_to_page)
        self.thumbnails_panel.rotate_requested.connect(self.rotate_page_degrees)
        self.thumbnails_panel.delete_requested.connect(self.delete_page_at)
        self.thumbnails_panel.insert_requested.connect(self.insert_blank_page_after)
        self.thumbnails_panel.extract_requested.connect(self.extract_single_page)
        self.thumbnails_panel.move_page_requested.connect(self.move_page)
        
        self.search_panel.result_selected.connect(self.on_search_result_selected)
        
        self.inspector_panel.property_changed.connect(self.on_inspector_property_changed)
        self.inspector_panel.delete_element_requested.connect(self.delete_specific_element)
        self.inspector_panel.apply_redaction_requested.connect(self.apply_redaction_element)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            img_exts = (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tiff")
            for u in event.mimeData().urls():
                f = u.toLocalFile().lower()
                if any(f.endswith(ext) for ext in img_exts):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tiff")
        for u in event.mimeData().urls():
            f = u.toLocalFile()
            f_lower = f.lower()
            if f_lower.endswith(".pdf") and os.path.isfile(f):
                self.open_pdf(f)
                break
            elif any(f_lower.endswith(ext) for ext in img_exts) and os.path.isfile(f):
                self.add_image_from_path(f)
                break
        event.acceptProposedAction()

    def add_image_from_path(self, file_path: str):
        if not self.doc or len(self.doc) == 0:
            return
        pix = QPixmap(file_path)
        w, h = 200.0, 150.0
        if not pix.isNull() and pix.width() > 0:
            ratio = pix.height() / pix.width()
            w = min(300.0, max(80.0, float(pix.width())))
            h = w * ratio
            
        page = self.doc.load_page(self.canvas_view.current_page_idx)
        page_r = page.rect
        center_x = max(20.0, (page_r.width - w) / 2.0)
        center_y = max(20.0, (page_r.height - h) / 2.0)
        
        el = ImageElement(x=center_x, y=center_y, width=w, height=h, image_path=file_path)
        cmd = AddElementCommand(self.canvas_view, self.canvas_view.current_page_idx, el, "Resim Ekle")
        self.undo_stack.push(cmd)
        self.canvas_view.set_tool_mode("select")
        self.statusBar().showMessage(f"Resim eklendi: {os.path.basename(file_path)}", 3000)

    def set_tool(self, mode: str):
        self.canvas_view.set_tool_mode(mode)
        if mode == "pen":
            self.spin_quick_stroke.blockSignals(True)
            self.spin_quick_stroke.setValue(self.canvas_view.current_stroke_width)
            self.spin_quick_stroke.blockSignals(False)
            self.btn_quick_stroke_color.setStyleSheet(f"background-color: {self.canvas_view.current_stroke_color}; border: 1px solid #555; border-radius: 3px;")
        elif mode == "highlighter":
            self.spin_quick_stroke.blockSignals(True)
            self.spin_quick_stroke.setValue(self.canvas_view.current_highlighter_width)
            self.spin_quick_stroke.blockSignals(False)
            self.btn_quick_stroke_color.setStyleSheet(f"background-color: {self.canvas_view.current_highlighter_color}; border: 1px solid #555; border-radius: 3px;")
        elif mode == "text":
            self.spin_quick_font_size.blockSignals(True)
            self.cb_quick_font.blockSignals(True)
            self.btn_quick_bold.blockSignals(True)
            self.btn_quick_italic.blockSignals(True)
            self.spin_quick_font_size.setValue(self.canvas_view.default_font_size)
            self.cb_quick_font.setCurrentText(self.canvas_view.default_font_family)
            self.btn_quick_bold.setChecked(self.canvas_view.default_bold)
            self.btn_quick_italic.setChecked(self.canvas_view.default_italic)
            self.btn_quick_text_color.setStyleSheet(f"background-color: {self.canvas_view.default_text_color}; border: 1px solid #555; border-radius: 3px;")
            self.spin_quick_font_size.blockSignals(False)
            self.cb_quick_font.blockSignals(False)
            self.btn_quick_bold.blockSignals(False)
            self.btn_quick_italic.blockSignals(False)
            
        tips = {
            "select": "Seçim Aracı: Öğeleri seçin, sürükleyin veya 8 tutamaçla yeniden boyutlandırın. (Çift tıkla metin düzenleyin)",
            "pan": "El Aracı: Sayfayı tıklayıp sürükleyerek kaydırın (Space tuşuna basılı tutarak da yapabilirsiniz).",
            "text": "Metin Ekle: Sayfa üzerinde metin eklemek istediğiniz yere tıklayın ve doğrudan yazın.",
            "image": "Resim / İmza Ekle: Sayfa üzerine yerleştirmek istediğiniz yere tıklayın.",
            "pen": "Serbest Kalem: Fareyi sürükleyerek serbest el çizimi yapın veya not alın.",
            "highlighter": "Vurgulayıcı: Metin veya alanların üzerini yarı saydam renkle vurgulayın.",
            "rect": "Dikdörtgen Aracı: Tıklayıp sürükleyerek dikdörtgen çizin.",
            "ellipse": "Elips Aracı: Tıklayıp sürükleyerek elips veya daire çizin.",
            "line": "Çizgi Aracı: Tıklayıp sürükleyerek düz çizgi çizin.",
            "arrow": "Ok Aracı: Tıklayıp sürükleyerek ok işareti çizin.",
            "redact": "Karartma / Sansür: Hassas bilgilerin üzerini kalıcı olarak sansürlemek için kutu çizin."
        }
        self.lbl_status_mode.setText(tips.get(mode, "Hazır"))

    def new_document(self):
        self.doc = fitz.open()
        self.doc.new_page(width=595.0, height=842.0)
        self.current_file_path = None
        self.is_dirty = False
        self.update_doc_title()
        
        self.canvas_view.load_document(self.doc)
        self.thumbnails_panel.load_document(self.doc)
        self.search_panel.load_document(self.doc)
        self.update_page_nav_ui()

    def open_pdf_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF Dosyası Aç", "", "PDF Dosyaları (*.pdf)")
        if path:
            self.open_pdf(path)

    def open_pdf(self, file_path: str):
        try:
            # Windows dosya kilitleme sorununu önlemek için bellek akışıyla açılır
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            self.doc = doc
            self.current_file_path = file_path
            self.is_dirty = False
            self.undo_stack.clear()
            self.update_doc_title()
            
            self.canvas_view.load_document(self.doc)
            self.thumbnails_panel.load_document(self.doc)
            self.search_panel.load_document(self.doc)
            self.update_page_nav_ui()
            self.statusBar().showMessage(f"Açıldı: {os.path.basename(file_path)}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF dosyası açılamadı:\n{e}")

    def save_pdf(self):
        if not self.current_file_path:
            self.save_as_pdf()
        else:
            self.save_to_path(self.current_file_path)

    def save_as_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "PDF Olarak Kaydet", self.current_file_path or "Belge.pdf", "PDF Dosyaları (*.pdf)")
        if path:
            self.current_file_path = path
            self.save_to_path(path)

    def save_to_path(self, target_path: str, show_dialog: bool = True):
        if not self.doc:
            return
            
        try:
            if hasattr(self.canvas_view, "finish_inline_text_editing"):
                self.canvas_view.finish_inline_text_editing(commit=True)

            out_doc = fitz.open()
            out_doc.insert_pdf(self.doc)
            if self.doc.metadata:
                out_doc.set_metadata(self.doc.metadata)
            
            for page_num, elems in self.canvas_view.page_elements.items():
                if 0 <= page_num < len(out_doc):
                    page = out_doc[page_num]
                    for el in elems:
                        el.apply_to_pdf_page(page)
                        
            # Windows'ta açık dosya üzerine yazma çakışmalarını önlemek için güvenli geçici dosya yazımı
            dir_name = os.path.dirname(target_path) or "."
            tmp_fd, tmp_file = tempfile.mkstemp(suffix=".pdf", dir=dir_name)
            os.close(tmp_fd)
            
            out_doc.save(tmp_file, garbage=4, deflate=True)
            out_doc.close()
            
            shutil.move(tmp_file, target_path)
            
            self.is_dirty = False
            self.update_doc_title()
            if show_dialog:
                QMessageBox.showinfo(self, "Başarılı", f"PDF belgesi başarıyla kaydedildi:\n{target_path}")
        except Exception as e:
            if show_dialog:
                QMessageBox.critical(self, "Hata", f"PDF kaydedilirken bir hata oluştu:\n{e}")
            else:
                raise

    def print_document(self):
        if not self.doc: return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            from PyQt6.QtGui import QPainter
            painter = QPainter(printer)
            for i in range(len(self.doc)):
                if i > 0:
                    printer.newPage()
                page = self.doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                painter.drawImage(rect, qimg)
            painter.end()

    def update_doc_title(self):
        name = os.path.basename(self.current_file_path) if self.current_file_path else "Yeni Belge"
        dirty_str = " *" if self.is_dirty else ""
        self.setWindowTitle(f"{APP_NAME} - {name}{dirty_str}")

    def on_page_modified(self, page_idx: int):
        self.is_dirty = True
        self.update_doc_title()

    def jump_to_page(self, page_num: int):
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return
        self.canvas_view.current_page_idx = page_num
        self.canvas_view.render_current_page()
        self.update_page_nav_ui()
        self.thumbnails_panel.set_current_page(page_num)

    def first_page(self):
        self.jump_to_page(0)

    def prev_page(self):
        if self.canvas_view.current_page_idx > 0:
            self.jump_to_page(self.canvas_view.current_page_idx - 1)

    def next_page(self):
        if self.doc and self.canvas_view.current_page_idx < len(self.doc) - 1:
            self.jump_to_page(self.canvas_view.current_page_idx + 1)

    def last_page(self):
        if self.doc:
            self.jump_to_page(len(self.doc) - 1)

    def on_page_spin_changed(self, val: int):
        target = val - 1
        if target != self.canvas_view.current_page_idx:
            self.jump_to_page(target)

    def update_page_nav_ui(self):
        if not self.doc or len(self.doc) == 0:
            self.spin_page.setRange(0, 0)
            self.spin_page.setValue(0)
            self.lbl_page_total.setText(" / 0")
            return
            
        cur = self.canvas_view.current_page_idx + 1
        total = len(self.doc)
        
        self.spin_page.blockSignals(True)
        self.spin_page.setRange(1, total)
        self.spin_page.setValue(cur)
        self.spin_page.blockSignals(False)
        
        self.lbl_page_total.setText(f" / {total}")
        
        page = self.doc.load_page(self.canvas_view.current_page_idx)
        r = page.rect
        w_mm = r.width * 25.4 / 72.0
        h_mm = r.height * 25.4 / 72.0
        self.lbl_page_info.setText(f"Sayfa {cur}: {int(r.width)} x {int(r.height)} pt ({int(w_mm)} x {int(h_mm)} mm)")

    def rotate_page(self, degrees: int):
        if not self.doc: return
        self.rotate_page_degrees(self.canvas_view.current_page_idx, degrees)

    def rotate_page_degrees(self, page_num: int, degrees: int):
        if not self.doc or page_num >= len(self.doc): return
        page = self.doc.load_page(page_num)
        new_rot = (page.rotation + degrees) % 360
        page.set_rotation(new_rot)
        self.is_dirty = True
        self.update_doc_title()
        self.canvas_view.render_current_page()
        self.thumbnails_panel.refresh_thumbnails()

    def delete_current_page(self):
        if not self.doc or len(self.doc) <= 1:
            QMessageBox.warning(self, "Uyarı", "Belgedeki tek sayfayı silemezsiniz!")
            return
        self.delete_page_at(self.canvas_view.current_page_idx)

    def delete_page_at(self, page_num: int):
        if not self.doc or len(self.doc) <= 1:
            QMessageBox.warning(self, "Uyarı", "Belgedeki tek sayfayı silemezsiniz!")
            return
            
        ret = QMessageBox.question(self, "Sayfa Sil", f"{page_num + 1}. sayfayı silmek istediğinizden emin misiniz?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            self.doc.delete_page(page_num)
            
            # Sayfa elemanları indekslerini kaydır
            new_elements = {}
            for k, v in self.canvas_view.page_elements.items():
                if k < page_num:
                    new_elements[k] = v
                elif k > page_num:
                    new_elements[k - 1] = v
            self.canvas_view.page_elements = new_elements
            
            self.is_dirty = True
            self.update_doc_title()
            new_idx = min(page_num, len(self.doc) - 1)
            self.canvas_view.current_page_idx = new_idx
            self.canvas_view.render_current_page()
            self.thumbnails_panel.refresh_thumbnails()
            self.update_page_nav_ui()

    def open_insert_page_dialog(self):
        if not self.doc: return
        dlg = InsertPageDialog(self.canvas_view.current_page_idx, len(self.doc), self)
        if dlg.exec():
            w, h, idx = dlg.get_page_spec()
            self.doc.new_page(idx, width=w, height=h)
            
            # Eleman indekslerini kaydır
            new_elements = {}
            for k, v in self.canvas_view.page_elements.items():
                if k < idx:
                    new_elements[k] = v
                else:
                    new_elements[k + 1] = v
            self.canvas_view.page_elements = new_elements
            
            self.is_dirty = True
            self.update_doc_title()
            self.jump_to_page(idx)
            self.thumbnails_panel.refresh_thumbnails()

    def insert_blank_page_after(self, page_num: int):
        if not self.doc: return
        p = self.doc.load_page(page_num)
        w, h = p.rect.width, p.rect.height
        idx = page_num + 1
        self.doc.new_page(idx, width=w, height=h)
        
        new_elements = {}
        for k, v in self.canvas_view.page_elements.items():
            if k < idx:
                new_elements[k] = v
            else:
                new_elements[k + 1] = v
        self.canvas_view.page_elements = new_elements
        
        self.is_dirty = True
        self.update_doc_title()
        self.jump_to_page(idx)
        self.thumbnails_panel.refresh_thumbnails()

    def move_page(self, from_idx: int, to_idx: int):
        if not self.doc or from_idx == to_idx: return
        if 0 <= to_idx < len(self.doc):
            self.doc.move_page(from_idx, to_idx)
            
            # Elemanları da sayfa ile birlikte taşı
            from_elems = self.canvas_view.page_elements.pop(from_idx, [])
            to_elems = self.canvas_view.page_elements.pop(to_idx, [])
            if from_elems:
                self.canvas_view.page_elements[to_idx] = from_elems
            if to_elems:
                self.canvas_view.page_elements[from_idx] = to_elems
                
            self.is_dirty = True
            self.update_doc_title()
            self.jump_to_page(to_idx)
            self.thumbnails_panel.refresh_thumbnails()

    def open_extract_dialog(self):
        if not self.doc: return
        dlg = ExtractPagesDialog(self.canvas_view.current_page_idx, len(self.doc), self)
        if dlg.exec():
            pages = dlg.get_pages(self.canvas_view.current_page_idx)
            if not pages:
                QMessageBox.warning(self, "Uyarı", "Geçerli bir sayfa seçilmedi!")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Çıkarılan Sayfaları Kaydet", "Cikarilan_Sayfalar.pdf", "PDF Dosyaları (*.pdf)")
            if path:
                out = fitz.open()
                for pno in pages:
                    out.insert_pdf(self.doc, from_page=pno, to_page=pno)
                out.save(path)
                out.close()
                QMessageBox.showinfo(self, "Başarılı", f"{len(pages)} sayfa başarıyla dışa aktarıldı:\n{path}")

    def extract_single_page(self, page_num: int):
        if not self.doc: return
        path, _ = QFileDialog.getSaveFileName(self, f"Sayfa {page_num + 1} Kaydet", f"Sayfa_{page_num + 1}.pdf", "PDF Dosyaları (*.pdf)")
        if path:
            out = fitz.open()
            out.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
            out.save(path)
            out.close()
            QMessageBox.showinfo(self, "Başarılı", f"Sayfa kaydedildi:\n{path}")

    def export_page_as_image(self):
        if not self.doc: return
        path, _ = QFileDialog.getSaveFileName(self, "Sayfayı Resim Olarak Kaydet", f"Sayfa_{self.canvas_view.current_page_idx + 1}.png", "PNG (*.png);;JPEG (*.jpg)")
        if path:
            p = self.doc.load_page(self.canvas_view.current_page_idx)
            pix = p.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            pix.save(path)
            QMessageBox.showinfo(self, "Başarılı", f"Sayfa resim olarak kaydedildi:\n{path}")

    def export_all_pages_as_images(self):
        if not self.doc: return
        folder = QFileDialog.getExistingDirectory(self, "Resimlerin Kaydedileceği Klasörü Seçin")
        if folder:
            for i, p in enumerate(self.doc):
                pix = p.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                out_path = os.path.join(folder, f"Sayfa_{i + 1:03d}.png")
                pix.save(out_path)
            QMessageBox.showinfo(self, "Başarılı", f"Tüm sayfalar klasöre aktarıldı:\n{folder}")

    def export_text(self):
        if not self.doc: return
        path, _ = QFileDialog.getSaveFileName(self, "Metni Kaydet", "Belge_Metni.txt", "Metin Dosyaları (*.txt)")
        if path:
            full_text = []
            for i, p in enumerate(self.doc):
                full_text.append(f"--- SAYFA {i + 1} ---\n" + p.get_text("text"))
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(full_text))
            QMessageBox.showinfo(self, "Başarılı", f"Belge metni kaydedildi:\n{path}")

    def open_merge_dialog(self):
        dlg = MergeDialog(self)
        if dlg.exec():
            files = dlg.files_to_merge
            out_path, _ = QFileDialog.getSaveFileName(self, "Birleştirilmiş PDF'i Kaydet", "Birlestirilmis_Belge.pdf", "PDF Dosyaları (*.pdf)")
            if out_path:
                merged_doc = fitz.open()
                if self.doc:
                    merged_doc.insert_pdf(self.doc)
                for f in files:
                    try:
                        d = fitz.open(f)
                        merged_doc.insert_pdf(d)
                        d.close()
                    except Exception as e:
                        print(f"Hata: {e}")
                merged_doc.save(out_path)
                merged_doc.close()
                QMessageBox.showinfo(self, "Başarılı", f"PDF'ler birleştirildi:\n{out_path}")

    def open_watermark_dialog(self):
        if not self.doc: return
        dlg = WatermarkDialog(self.canvas_view.current_page_idx, len(self.doc), self)
        if dlg.exec():
            s = dlg.get_settings()
            pages_to_apply = range(len(self.doc)) if s["apply_all"] else [self.canvas_view.current_page_idx]
            
            for pno in pages_to_apply:
                wm = WatermarkElement(
                    text=s["text"],
                    font_size=s["size"],
                    angle=s["angle"],
                    opacity=s["opacity"],
                    color=s["color"]
                )
                cmd = AddElementCommand(self.canvas_view, pno, wm, "Filigran Ekle")
                self.undo_stack.push(cmd)
                
            self.is_dirty = True
            self.update_doc_title()
            self.canvas_view.render_current_page()
            self.thumbnails_panel.refresh_thumbnails()

    def open_metadata_dialog(self):
        if not self.doc: return
        dlg = MetadataDialog(self.doc, self)
        if dlg.exec():
            self.is_dirty = True
            self.update_doc_title()

    def show_shortcuts_guide(self):
        msg = (
            f"<b>{APP_NAME} Klavye Kısayolları:</b><br><br>"
            "• <b>Ctrl + O:</b> Belge Aç<br>"
            "• <b>Ctrl + S:</b> Belge Kaydet<br>"
            "• <b>Ctrl + Shift + S:</b> Farklı Kaydet<br>"
            "• <b>Ctrl + P:</b> Yazdır<br>"
            "• <b>Ctrl + Z:</b> Geri Al (Undo)<br>"
            "• <b>Ctrl + Y:</b> Yinele (Redo)<br>"
            "• <b>Ctrl + C / Ctrl + V:</b> Kopyala / Yapıştır<br>"
            "• <b>Ctrl + D:</b> Seçili Öğeyi Çoğalt<br>"
            "• <b>Delete:</b> Seçili Öğeyi Sil<br>"
            "• <b>Ok Tuşları:</b> Seçili Öğeyi 1 pt Kaydır (Shift ile 10 pt)<br>"
            "• <b>Çift Tıklama:</b> Metin Kutusunu Düzenle<br>"
            "• <b>Space + Sürükle:</b> El / Kaydırma Aracı<br>"
            "• <b>Ctrl + Fare Tekerleği:</b> Akıcı Yakınlaştırma<br>"
            "• <b>Ctrl + 0 / Ctrl + 1:</b> Sayfaya / Genişliğe Sığdır<br>"
            "• <b>Ctrl + F:</b> Belgede Arama Yap<br>"
            "• <b>V / H / T / I / P / U / R / E / L / A / X:</b> Hızlı Araç Geçişleri"
        )
        QMessageBox.information(self, "Klavye Kısayolları Kılavuzu", msg)

    def show_about_dialog(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def focus_search(self):
        self.left_dock.setVisible(True)
        self.left_tabs.setCurrentWidget(self.search_panel)
        self.search_panel.search_input.setFocus()
        self.search_panel.search_input.selectAll()

    def on_canvas_zoom_changed(self, zoom_factor: float):
        percent = int(zoom_factor * 100)
        self.lbl_zoom_val.setText(f"%{percent}")
        self.cb_zoom.blockSignals(True)
        self.cb_zoom.setCurrentText(f"%{percent}")
        self.cb_zoom.blockSignals(False)

    def on_zoom_combo_changed(self, text: str):
        if "Sayfaya" in text:
            self.canvas_view.fit_page()
        elif "Genişliğe" in text:
            self.canvas_view.fit_width()
        else:
            val_str = text.replace("%", "").strip()
            try:
                factor = float(val_str) / 100.0
                self.canvas_view.set_zoom(factor)
            except ValueError:
                pass

    def on_canvas_mouse_moved(self, x: float, y: float):
        self.lbl_coords.setText(f"X: {int(x)} pt  Y: {int(y)} pt")

    def on_search_result_selected(self, page_idx: int, rects: list):
        self.jump_to_page(page_idx)
        self.canvas_view.highlight_search_rects(rects)

    def on_inspector_property_changed(self, element, prop: str, val):
        self.canvas_view.update_element_visual(element)
        self.on_canvas_element_selected(element)

    def on_canvas_element_selected(self, el: Optional[BaseElement]):
        self.inspector_panel.set_element(el)
        if not el:
            return
            
        if isinstance(el, TextElement):
            self.cb_quick_font.blockSignals(True)
            self.spin_quick_font_size.blockSignals(True)
            self.btn_quick_bold.blockSignals(True)
            self.btn_quick_italic.blockSignals(True)
            
            self.cb_quick_font.setCurrentText(el.font_family)
            self.spin_quick_font_size.setValue(el.font_size)
            self.btn_quick_bold.setChecked(el.bold)
            self.btn_quick_italic.setChecked(el.italic)
            self.btn_quick_text_color.setStyleSheet(f"background-color: {el.color}; border: 1px solid #555; border-radius: 3px;")
            
            self.cb_quick_font.blockSignals(False)
            self.spin_quick_font_size.blockSignals(False)
            self.btn_quick_bold.blockSignals(False)
            self.btn_quick_italic.blockSignals(False)
            
        elif isinstance(el, DrawingElement):
            self.spin_quick_stroke.blockSignals(True)
            sw = getattr(el, "stroke_width", 2.0)
            self.spin_quick_stroke.setValue(sw)
            self.btn_quick_stroke_color.setStyleSheet(f"background-color: {el.color}; border: 1px solid #555; border-radius: 3px;")
            self.spin_quick_stroke.blockSignals(False)
            
        elif isinstance(el, ShapeElement):
            self.spin_quick_stroke.blockSignals(True)
            self.spin_quick_stroke.setValue(el.stroke_width)
            self.btn_quick_stroke_color.setStyleSheet(f"background-color: {el.stroke_color}; border: 1px solid #555; border-radius: 3px;")
            self.spin_quick_stroke.blockSignals(False)

    def on_quick_stroke_changed(self, val: float):
        self.canvas_view.current_stroke_width = val
        el = self.canvas_view.selected_element
        if el and isinstance(el, DrawingElement):
            el.stroke_width = val
            el.calculate_bounds()
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)
        elif el and isinstance(el, ShapeElement):
            el.stroke_width = val
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)

    def pick_quick_stroke_color(self):
        current_col = self.canvas_view.current_stroke_color
        el = self.canvas_view.selected_element
        if el and isinstance(el, DrawingElement):
            current_col = el.color
        elif el and isinstance(el, ShapeElement):
            current_col = el.stroke_color
            
        c = QColorDialog.getColor(QColor(current_col), self, "Çizgi / Kalem Rengi Seç")
        if c.isValid():
            hex_c = c.name()
            self.canvas_view.current_stroke_color = hex_c
            self.btn_quick_stroke_color.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #555; border-radius: 3px;")
            if el and isinstance(el, DrawingElement):
                el.color = hex_c
                self.canvas_view.update_element_visual(el)
                self.inspector_panel.set_element(el)
            elif el and isinstance(el, ShapeElement):
                el.stroke_color = hex_c
                self.canvas_view.update_element_visual(el)
                self.inspector_panel.set_element(el)

    def on_quick_font_family_changed(self, font_name: str):
        self.canvas_view.default_font_family = font_name
        el = self.canvas_view.selected_element
        if el and isinstance(el, TextElement):
            el.font_family = font_name
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)

    def on_quick_font_size_changed(self, size: float):
        self.canvas_view.default_font_size = size
        el = self.canvas_view.selected_element
        if el and isinstance(el, TextElement):
            el.font_size = size
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)

    def on_quick_bold_toggled(self, checked: bool):
        self.canvas_view.default_bold = checked
        el = self.canvas_view.selected_element
        if el and isinstance(el, TextElement):
            el.bold = checked
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)

    def on_quick_italic_toggled(self, checked: bool):
        self.canvas_view.default_italic = checked
        el = self.canvas_view.selected_element
        if el and isinstance(el, TextElement):
            el.italic = checked
            self.canvas_view.update_element_visual(el)
            self.inspector_panel.set_element(el)

    def pick_quick_text_color(self):
        current_col = self.canvas_view.default_text_color
        el = self.canvas_view.selected_element
        if el and isinstance(el, TextElement):
            current_col = el.color
            
        c = QColorDialog.getColor(QColor(current_col), self, "Metin Rengi Seç")
        if c.isValid():
            hex_c = c.name()
            self.canvas_view.default_text_color = hex_c
            self.btn_quick_text_color.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #555; border-radius: 3px;")
            if el and isinstance(el, TextElement):
                el.color = hex_c
                self.canvas_view.update_element_visual(el)
                self.inspector_panel.set_element(el)

    def delete_selected_element(self):
        if self.canvas_view.selected_element:
            cmd = DeleteElementCommand(self.canvas_view, self.canvas_view.current_page_idx, self.canvas_view.selected_element)
            self.undo_stack.push(cmd)

    def delete_specific_element(self, element):
        cmd = DeleteElementCommand(self.canvas_view, self.canvas_view.current_page_idx, element)
        self.undo_stack.push(cmd)

    def apply_redaction_element(self, element):
        if not self.doc: return
        ret = QMessageBox.warning(
            self, "Sansür Uygula",
            "Bu alanın altındaki metin ve görseller kalıcı olarak silinecek. Devam etmek istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            page = self.doc.load_page(self.canvas_view.current_page_idx)
            element.apply_to_pdf_page(page)
            self.canvas_view.remove_element_internal(self.canvas_view.current_page_idx, element)
            self.canvas_view.render_current_page()
            self.is_dirty = True
            self.update_doc_title()

    def closeEvent(self, event: QCloseEvent):
        if self.is_dirty:
            ret = QMessageBox.question(
                self, "Kaydedilmemiş Değişiklikler",
                "Belgede kaydedilmemiş değişiklikler var. Çıkmadan önce kaydetmek istiyor musunuz?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if ret == QMessageBox.StandardButton.Save:
                self.save_pdf()
                event.accept()
            elif ret == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
