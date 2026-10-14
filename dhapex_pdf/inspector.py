"""
Nexora PDF Studio - Adobe Acrobat Tarzı Özellik Denetçisi (Properties Inspector)
Seçili öğenin (metin, resim, şekil, çizim) özelliklerini dinamik olarak düzenler.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QPushButton, QCheckBox, QSlider,
    QColorDialog, QGroupBox, QFileDialog, QStackedWidget
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

from dhapex_pdf.models import (
    BaseElement, TextElement, ImageElement, ShapeElement, DrawingElement, RedactionElement, WatermarkElement
)
from dhapex_pdf.icons import IconFactory

class InspectorPanel(QWidget):
    property_changed = pyqtSignal(object, str, object)
    delete_element_requested = pyqtSignal(object)
    apply_redaction_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element: Optional[BaseElement] = None
        self._block_updates = False
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        self.lbl_header = QLabel("Özellikler")
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #FFFFFF;")
        
        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(IconFactory.get("delete_item", 16))
        self.btn_delete.setToolTip("Seçili Öğeyi Sil (Del)")
        self.btn_delete.setStyleSheet("background-color: #382020; border: 1px solid #602525;")
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_delete.setEnabled(False)
        
        header_layout.addWidget(self.lbl_header)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_delete)
        main_layout.addLayout(header_layout)
        
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.page_none = self.create_none_page()
        self.page_text = self.create_text_page()
        self.page_shape = self.create_shape_page()
        self.page_drawing = self.create_drawing_page()
        self.page_image = self.create_image_page()
        self.page_redact = self.create_redact_page()
        
        self.stack.addWidget(self.page_none)    # Index 0
        self.stack.addWidget(self.page_text)    # Index 1
        self.stack.addWidget(self.page_shape)   # Index 2
        self.stack.addWidget(self.page_drawing) # Index 3
        self.stack.addWidget(self.page_image)   # Index 4
        self.stack.addWidget(self.page_redact)  # Index 5
        
        main_layout.addStretch()

    def create_none_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(4, 12, 4, 4)
        
        gb = QGroupBox("Belge Bilgisi")
        gbl = QVBoxLayout(gb)
        self.lbl_doc_info = QLabel("Düzenlemek için belgede bir öğe seçin veya üst araç çubuğundan bir araç kullanın.\n\nİpucu: Metin kutularına çift tıklayarak doğrudan düzenleyebilirsiniz.")
        self.lbl_doc_info.setWordWrap(True)
        self.lbl_doc_info.setStyleSheet("color: #8E8E98; font-size: 11px;")
        gbl.addWidget(self.lbl_doc_info)
        
        l.addWidget(gb)
        l.addStretch()
        return w

    def create_text_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)
        
        gb = QGroupBox("Metin Ayarları")
        gbl = QVBoxLayout(gb)
        
        gbl.addWidget(QLabel("Metin İçeriği:"))
        self.txt_content = QPlainTextEdit()
        self.txt_content.setMaximumHeight(80)
        self.txt_content.textChanged.connect(self.on_text_content_changed)
        gbl.addWidget(self.txt_content)
        
        gbl.addWidget(QLabel("Yazı Tipi:"))
        self.cb_font = QComboBox()
        self.cb_font.addItems(["Arial", "Calibri", "Segoe UI", "Times New Roman", "Courier New", "Georgia", "Verdana"])
        self.cb_font.currentTextChanged.connect(lambda f: self.emit_change("font_family", f))
        gbl.addWidget(self.cb_font)
        
        row_size = QHBoxLayout()
        row_size.addWidget(QLabel("Boyut:"))
        self.spin_font_size = QDoubleSpinBox()
        self.spin_font_size.setRange(6, 120)
        self.spin_font_size.setSingleStep(1.0)
        self.spin_font_size.setSuffix(" pt")
        self.spin_font_size.setValue(12)
        self.spin_font_size.valueChanged.connect(lambda s: self.emit_change("font_size", s))
        row_size.addWidget(self.spin_font_size)
        gbl.addLayout(row_size)
        
        row_col = QHBoxLayout()
        row_col.addWidget(QLabel("Renk:"))
        self.btn_text_color = QPushButton("■ Seç")
        self.btn_text_color.clicked.connect(self.pick_text_color)
        row_col.addWidget(self.btn_text_color)
        gbl.addLayout(row_col)
        
        row_style = QHBoxLayout()
        self.cb_bold = QCheckBox("Kalın (Bold)")
        self.cb_bold.toggled.connect(lambda b: self.emit_change("bold", b))
        self.cb_italic = QCheckBox("İtalik")
        self.cb_italic.toggled.connect(lambda i: self.emit_change("italic", i))
        row_style.addWidget(self.cb_bold)
        row_style.addWidget(self.cb_italic)
        gbl.addLayout(row_style)
        
        l.addWidget(gb)
        return w

    def on_text_content_changed(self):
        if self._block_updates or not self.current_element:
            return
        t = self.txt_content.toPlainText()
        self.emit_change("text", t)

    def create_shape_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)
        
        gb = QGroupBox("Şekil Özellikleri")
        gbl = QVBoxLayout(gb)
        
        row_stroke = QHBoxLayout()
        row_stroke.addWidget(QLabel("Çizgi Kalınlığı:"))
        self.spin_stroke_width = QDoubleSpinBox()
        self.spin_stroke_width.setRange(0.5, 30.0)
        self.spin_stroke_width.setSingleStep(0.5)
        self.spin_stroke_width.setSuffix(" pt")
        self.spin_stroke_width.setValue(2.0)
        self.spin_stroke_width.valueChanged.connect(lambda sw: self.emit_change("stroke_width", sw))
        row_stroke.addWidget(self.spin_stroke_width)
        gbl.addLayout(row_stroke)
        
        row_scol = QHBoxLayout()
        row_scol.addWidget(QLabel("Çizgi Rengi:"))
        self.btn_stroke_color = QPushButton("■ Seç")
        self.btn_stroke_color.clicked.connect(self.pick_stroke_color)
        row_scol.addWidget(self.btn_stroke_color)
        gbl.addLayout(row_scol)
        
        row_fcol = QHBoxLayout()
        row_fcol.addWidget(QLabel("Dolgu Rengi:"))
        self.btn_fill_color = QPushButton("■ Seç")
        self.btn_fill_color.clicked.connect(self.pick_fill_color)
        row_fcol.addWidget(self.btn_fill_color)
        gbl.addLayout(row_fcol)
        
        self.cb_no_fill = QCheckBox("Dolgu Yok (Şeffaf)")
        self.cb_no_fill.toggled.connect(self.on_no_fill_toggled)
        gbl.addWidget(self.cb_no_fill)
        
        l.addWidget(gb)
        return w

    def create_drawing_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        gb = QGroupBox("Çizim Ayarları")
        gbl = QVBoxLayout(gb)
        
        row_w = QHBoxLayout()
        row_w.addWidget(QLabel("Kalınlık:"))
        self.spin_draw_width = QDoubleSpinBox()
        self.spin_draw_width.setRange(0.5, 50.0)
        self.spin_draw_width.setSingleStep(0.5)
        self.spin_draw_width.setSuffix(" pt")
        self.spin_draw_width.setValue(2.0)
        self.spin_draw_width.valueChanged.connect(lambda w: self.emit_change("stroke_width", w))
        row_w.addWidget(self.spin_draw_width)
        gbl.addLayout(row_w)
        
        row_col = QHBoxLayout()
        row_col.addWidget(QLabel("Renk:"))
        self.btn_draw_color = QPushButton("■ Seç")
        self.btn_draw_color.clicked.connect(self.pick_drawing_color)
        row_col.addWidget(self.btn_draw_color)
        gbl.addLayout(row_col)
        
        l.addWidget(gb)
        return w

    def create_image_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        gb = QGroupBox("Resim / İmza Ayarları")
        gbl = QVBoxLayout(gb)
        
        self.btn_change_image = QPushButton("Resmi Değiştir...")
        self.btn_change_image.clicked.connect(self.change_image_file)
        gbl.addWidget(self.btn_change_image)
        
        self.cb_aspect = QCheckBox("En/Boy Oranını Koru")
        self.cb_aspect.setChecked(True)
        self.cb_aspect.toggled.connect(lambda a: self.emit_change("keep_aspect_ratio", a))
        gbl.addWidget(self.cb_aspect)
        
        l.addWidget(gb)
        return w

    def create_redact_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        gb = QGroupBox("Sansür / Karartma")
        gbl = QVBoxLayout(gb)
        
        lbl = QLabel("Bu alan PDF kaydedildiğinde kalıcı olarak silinecek ve altındaki metin/grafikler kurtarılamaz hale gelecektir.")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #FF9800; font-size: 11px;")
        gbl.addWidget(lbl)
        
        self.btn_apply_redact = QPushButton("Sansürü Hemen Uygula")
        self.btn_apply_redact.setStyleSheet("background-color: #881111; color: white; font-weight: bold;")
        self.btn_apply_redact.clicked.connect(self.on_apply_redact_clicked)
        gbl.addWidget(self.btn_apply_redact)
        
        l.addWidget(gb)
        return w

    def set_element(self, el: Optional[BaseElement]):
        self.current_element = el
        self._block_updates = True
        
        if not el:
            self.lbl_header.setText("Özellikler")
            self.btn_delete.setEnabled(False)
            self.stack.setCurrentIndex(0)
            self._block_updates = False
            return
            
        self.btn_delete.setEnabled(True)
        
        if isinstance(el, TextElement):
            self.lbl_header.setText("Metin Özellikleri")
            self.stack.setCurrentIndex(1)
            self.txt_content.setPlainText(el.text)
            self.cb_font.setCurrentText(el.font_family)
            self.spin_font_size.setValue(el.font_size)
            self.cb_bold.setChecked(el.bold)
            self.cb_italic.setChecked(el.italic)
            self.btn_text_color.setStyleSheet(f"background-color: {el.color}; color: white;")
            
        elif isinstance(el, ShapeElement):
            self.lbl_header.setText(f"Şekil: {el.shape_type.capitalize()}")
            self.stack.setCurrentIndex(2)
            self.spin_stroke_width.setValue(el.stroke_width)
            self.btn_stroke_color.setStyleSheet(f"background-color: {el.stroke_color}; color: white;")
            if el.fill_color:
                self.btn_fill_color.setStyleSheet(f"background-color: {el.fill_color}; color: white;")
                self.cb_no_fill.setChecked(False)
            else:
                self.btn_fill_color.setStyleSheet("background-color: transparent; color: #888;")
                self.cb_no_fill.setChecked(True)
                
        elif isinstance(el, DrawingElement):
            self.lbl_header.setText("Çizim / Vurgulayıcı")
            self.stack.setCurrentIndex(3)
            self.spin_draw_width.setValue(getattr(el, "stroke_width", 2.0))
            self.btn_draw_color.setStyleSheet(f"background-color: {el.color}; color: black;")
            
        elif isinstance(el, ImageElement):
            self.lbl_header.setText("Resim / Damga")
            self.stack.setCurrentIndex(4)
            self.cb_aspect.setChecked(el.keep_aspect_ratio)
            
        elif isinstance(el, RedactionElement):
            self.lbl_header.setText("Sansür Alanı")
            self.stack.setCurrentIndex(5)
            
        self._block_updates = False

    def emit_change(self, prop: str, val):
        if self._block_updates or not self.current_element:
            return
        setattr(self.current_element, prop, val)
        self.property_changed.emit(self.current_element, prop, val)

    def pick_text_color(self):
        if not self.current_element: return
        c = QColorDialog.getColor(QColor(getattr(self.current_element, "color", "#E5252A")), self, "Metin Rengi")
        if c.isValid():
            hex_c = c.name()
            self.btn_text_color.setStyleSheet(f"background-color: {hex_c}; color: white;")
            self.emit_change("color", hex_c)

    def pick_stroke_color(self):
        if not self.current_element: return
        c = QColorDialog.getColor(QColor(getattr(self.current_element, "stroke_color", "#E5252A")), self, "Çizgi Rengi")
        if c.isValid():
            hex_c = c.name()
            self.btn_stroke_color.setStyleSheet(f"background-color: {hex_c}; color: white;")
            self.emit_change("stroke_color", hex_c)

    def pick_fill_color(self):
        if not self.current_element: return
        c = QColorDialog.getColor(QColor(getattr(self.current_element, "fill_color", "#FFFFFF") or "#FFFFFF"), self, "Dolgu Rengi")
        if c.isValid():
            hex_c = c.name()
            self.cb_no_fill.setChecked(False)
            self.btn_fill_color.setStyleSheet(f"background-color: {hex_c}; color: white;")
            self.emit_change("fill_color", hex_c)

    def on_no_fill_toggled(self, checked: bool):
        if checked:
            self.btn_fill_color.setStyleSheet("background-color: transparent; color: #888;")
            self.emit_change("fill_color", None)
        else:
            self.emit_change("fill_color", "#FFFFFF")

    def pick_drawing_color(self):
        if not self.current_element: return
        c = QColorDialog.getColor(QColor(getattr(self.current_element, "color", "#1E88E5")), self, "Çizim Rengi")
        if c.isValid():
            hex_c = c.name()
            self.btn_draw_color.setStyleSheet(f"background-color: {hex_c}; color: white;")
            self.emit_change("color", hex_c)

    def change_image_file(self):
        if not self.current_element: return
        path, _ = QFileDialog.getOpenFileName(self, "Yeni Resim Seç", "", "Resimler (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.emit_change("image_path", path)

    def on_delete_clicked(self):
        if self.current_element:
            self.delete_element_requested.emit(self.current_element)

    def on_apply_redact_clicked(self):
        if self.current_element:
            self.apply_redaction_requested.emit(self.current_element)
