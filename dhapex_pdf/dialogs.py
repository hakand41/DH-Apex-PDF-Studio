"""
Nexora PDF Studio - Adobe Acrobat Seviyesi Diyaloglar
Filigran, Sayfa Ekleme, Belge Özellikleri (Metadata), Sayfa Çıkarma ve PDF Birleştirme.
"""

from typing import List, Dict, Any, Tuple
import pymupdf as fitz
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QPushButton, QCheckBox, QSlider,
    QColorDialog, QGroupBox, QFileDialog, QRadioButton,
    QListWidget, QMessageBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from dhapex_pdf.icons import IconFactory
from dhapex_pdf import APP_NAME, APP_VERSION, APP_COPYRIGHT

class WatermarkDialog(QDialog):
    def __init__(self, current_page: int, total_pages: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filigran Ekle (Watermark)")
        self.setFixedSize(400, 380)
        self.current_page = current_page
        self.total_pages = total_pages
        self.color = "#E5252A"
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        gb_text = QGroupBox("Filigran Metni")
        gbl_text = QVBoxLayout(gb_text)
        self.txt_watermark = QLineEdit("GİZLİ & ÇOK GİZLİ")
        gbl_text.addWidget(self.txt_watermark)
        layout.addWidget(gb_text)
        
        gb_app = QGroupBox("Görünüm Ayarları")
        gbl_app = QVBoxLayout(gb_app)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Boyut (pt):"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(20, 160)
        self.spin_size.setValue(60)
        row1.addWidget(self.spin_size)
        
        row1.addWidget(QLabel("Açı (°):"))
        self.spin_angle = QSpinBox()
        self.spin_angle.setRange(-180, 180)
        self.spin_angle.setValue(45)
        row1.addWidget(self.spin_angle)
        gbl_app.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Saydamlık:"))
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(5, 100)
        self.slider_opacity.setValue(30)
        self.lbl_opacity = QLabel("%30")
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity.setText(f"%{v}"))
        row2.addWidget(self.slider_opacity)
        row2.addWidget(self.lbl_opacity)
        gbl_app.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Renk:"))
        self.btn_color = QPushButton("■ Renk Seç")
        self.btn_color.setStyleSheet(f"background-color: {self.color}; color: white;")
        self.btn_color.clicked.connect(self.choose_color)
        row3.addWidget(self.btn_color)
        gbl_app.addLayout(row3)
        layout.addWidget(gb_app)
        
        gb_pages = QGroupBox("Uygulama Alanı")
        gbl_pages = QVBoxLayout(gb_pages)
        self.rb_all = QRadioButton("Tüm Sayfalara Uygula")
        self.rb_all.setChecked(True)
        self.rb_current = QRadioButton(f"Yalnızca Geçerli Sayfaya Uygula (Sayfa {current_page + 1})")
        gbl_pages.addWidget(self.rb_all)
        gbl_pages.addWidget(self.rb_current)
        layout.addWidget(gb_pages)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Uygula")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def choose_color(self):
        c = QColorDialog.getColor(QColor(self.color), self, "Filigran Rengi")
        if c.isValid():
            self.color = c.name()
            self.btn_color.setStyleSheet(f"background-color: {self.color}; color: white;")

    def get_settings(self) -> Dict[str, Any]:
        return {
            "text": self.txt_watermark.text().strip(),
            "size": self.spin_size.value(),
            "angle": self.spin_angle.value(),
            "opacity": self.slider_opacity.value() / 100.0,
            "color": self.color,
            "apply_all": self.rb_all.isChecked()
        }


class MetadataDialog(QDialog):
    def __init__(self, doc: fitz.Document, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setWindowTitle("Belge Özellikleri & Meta Veriler")
        self.setFixedSize(480, 420)
        
        layout = QVBoxLayout(self)
        meta = doc.metadata or {}
        
        gb = QGroupBox("Açıklama ve Meta Veriler")
        gbl = QVBoxLayout(gb)
        
        gbl.addWidget(QLabel("Başlık (Title):"))
        self.txt_title = QLineEdit(meta.get("title", ""))
        gbl.addWidget(self.txt_title)
        
        gbl.addWidget(QLabel("Yazar (Author):"))
        self.txt_author = QLineEdit(meta.get("author", ""))
        gbl.addWidget(self.txt_author)
        
        gbl.addWidget(QLabel("Konu (Subject):"))
        self.txt_subject = QLineEdit(meta.get("subject", ""))
        gbl.addWidget(self.txt_subject)
        
        gbl.addWidget(QLabel("Anahtar Kelimeler (Keywords):"))
        self.txt_keywords = QLineEdit(meta.get("keywords", ""))
        gbl.addWidget(self.txt_keywords)
        
        lbl_info = QLabel(f"Oluşturan Yazılım: {meta.get('creator', 'Bilinmiyor')}\n"
                          f"PDF Üreticisi: {meta.get('producer', 'Bilinmiyor')}\n"
                          f"Format Versiyonu: PDF {doc.metadata.get('format', '1.7')}\n"
                          f"Toplam Sayfa: {len(doc)}")
        lbl_info.setStyleSheet("color: #8E8E98; font-size: 11px;")
        gbl.addWidget(lbl_info)
        
        layout.addWidget(gb)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Kaydet")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.save_metadata)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def save_metadata(self):
        new_meta = {
            "title": self.txt_title.text().strip(),
            "author": self.txt_author.text().strip(),
            "subject": self.txt_subject.text().strip(),
            "keywords": self.txt_keywords.text().strip(),
            "producer": f"{APP_NAME} {APP_VERSION}"
        }
        self.doc.set_metadata(new_meta)
        self.accept()


class InsertPageDialog(QDialog):
    def __init__(self, current_page: int, total_pages: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Boş Sayfa Ekle")
        self.setFixedSize(360, 300)
        self.current_page = current_page
        self.total_pages = total_pages
        
        layout = QVBoxLayout(self)
        
        gb_size = QGroupBox("Sayfa Boyutu ve Yönü")
        gbl_size = QVBoxLayout(gb_size)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Standart:"))
        self.cb_format = QComboBox()
        self.cb_format.addItems(["A4 (210 x 297 mm)", "Letter (8.5 x 11 in)", "A3 (297 x 420 mm)", "Legal"])
        row1.addWidget(self.cb_format)
        gbl_size.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Yön:"))
        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Dikey (Portrait)", "Yatay (Landscape)"])
        row2.addWidget(self.cb_orientation)
        gbl_size.addLayout(row2)
        layout.addWidget(gb_size)
        
        gb_pos = QGroupBox("Sayfa Konumu")
        gbl_pos = QVBoxLayout(gb_pos)
        self.rb_after = QRadioButton(f"Geçerli Sayfadan Sonra (Sayfa {current_page + 1})")
        self.rb_after.setChecked(True)
        self.rb_before = QRadioButton(f"Geçerli Sayfadan Önce (Sayfa {current_page + 1})")
        self.rb_end = QRadioButton("Belgenin En Sonuna")
        gbl_pos.addWidget(self.rb_after)
        gbl_pos.addWidget(self.rb_before)
        gbl_pos.addWidget(self.rb_end)
        layout.addWidget(gb_pos)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Ekle")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def get_page_spec(self) -> Tuple[float, float, int]:
        fmt = self.cb_format.currentText()
        if "A4" in fmt:
            w, h = 595.0, 842.0
        elif "Letter" in fmt:
            w, h = 612.0, 792.0
        elif "A3" in fmt:
            w, h = 842.0, 1191.0
        else:
            w, h = 612.0, 1008.0
            
        if "Yatay" in self.cb_orientation.currentText():
            w, h = h, w
            
        if self.rb_before.isChecked():
            idx = self.current_page
        elif self.rb_after.isChecked():
            idx = self.current_page + 1
        else:
            idx = self.total_pages
            
        return (w, h, idx)


class ExtractPagesDialog(QDialog):
    def __init__(self, current_page: int, total_pages: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sayfaları Dışa Aktar (Extract)")
        self.setFixedSize(380, 240)
        self.total_pages = total_pages
        
        layout = QVBoxLayout(self)
        
        gb = QGroupBox("Sayfa Aralığı")
        gbl = QVBoxLayout(gb)
        
        self.rb_current = QRadioButton(f"Yalnızca Geçerli Sayfa ({current_page + 1})")
        self.rb_range = QRadioButton("Belirli Sayfalar:")
        self.rb_range.setChecked(True)
        
        self.txt_range = QLineEdit(f"1-{total_pages}")
        self.txt_range.setPlaceholderText("Örnek: 1-3, 5, 8")
        
        gbl.addWidget(self.rb_current)
        gbl.addWidget(self.rb_range)
        gbl.addWidget(self.txt_range)
        layout.addWidget(gb)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Dışa Aktar...")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def get_pages(self, current_page: int) -> List[int]:
        if self.rb_current.isChecked():
            return [current_page]
            
        text = self.txt_range.text().strip()
        pages = set()
        parts = text.split(",")
        for p in parts:
            p = p.strip()
            if "-" in p:
                start_end = p.split("-")
                try:
                    s = int(start_end[0]) - 1
                    e = int(start_end[1]) - 1
                    for i in range(max(0, s), min(self.total_pages, e + 1)):
                        pages.add(i)
                except ValueError:
                    pass
            else:
                try:
                    val = int(p) - 1
                    if 0 <= val < self.total_pages:
                        pages.add(val)
                except ValueError:
                    pass
        return sorted(list(pages))


class MergeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Dosyalarını Birleştir (Merge)")
        self.setFixedSize(500, 380)
        self.files_to_merge = []
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Birleştirilecek PDF dosyalarını ekleyin ve sırasını düzenleyin:")
        layout.addWidget(lbl)
        
        mid = QHBoxLayout()
        self.list_widget = QListWidget()
        mid.addWidget(self.list_widget)
        
        btn_box = QVBoxLayout()
        btn_add = QPushButton("Dosya Ekle...")
        btn_add.clicked.connect(self.add_files)
        btn_remove = QPushButton("Kaldır")
        btn_remove.clicked.connect(self.remove_selected)
        btn_up = QPushButton("Yukarı")
        btn_up.clicked.connect(self.move_up)
        btn_down = QPushButton("Aşağı")
        btn_down.clicked.connect(self.move_down)
        
        btn_box.addWidget(btn_add)
        btn_box.addWidget(btn_remove)
        btn_box.addWidget(btn_up)
        btn_box.addWidget(btn_down)
        btn_box.addStretch()
        mid.addLayout(btn_box)
        layout.addLayout(mid)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Birleştir...")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.on_merge)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "PDF Dosyaları Seç", "", "PDF Dosyaları (*.pdf)")
        for p in paths:
            self.list_widget.addItem(p)

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def move_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def on_merge(self):
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir PDF dosyası seçmelisiniz!")
            return
        self.files_to_merge = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        self.accept()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Hakkında - {APP_NAME}")
        self.setFixedSize(460, 320)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        top = QHBoxLayout()
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconFactory.get("app_icon", 64).pixmap(64, 64))
        top.addWidget(lbl_icon)
        
        v_title = QVBoxLayout()
        lbl_title = QLabel(APP_NAME)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E5252A;")
        lbl_ver = QLabel(f"Sürüm {APP_VERSION}")
        lbl_ver.setStyleSheet("color: #A0A0AA; font-size: 12px;")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_ver)
        top.addLayout(v_title)
        top.addStretch()
        layout.addLayout(top)
        
        lbl_desc = QLabel(
            f"<b>{APP_NAME}</b>, Adobe Acrobat seviyesinde profesyonel bir PDF düzenleme, "
            "açıklama ekleme, sayfa yönetimi ve kalıcı karartma (redaction) yazılımıdır.<br><br>"
            "<b>Öne Çıkan Özellikler:</b><br>"
            "• Gelişmiş Vektörel Metin, Resim ve Şekil Araçları<br>"
            "• Kalıcı Güvenlikli Sansür / Karartma (Redaction Engine)<br>"
            "• Akıcı 8 Noktalı Boyutlandırma ve Dönüştürme Tutamaçları<br>"
            "• Çift Tıklama ile Doğrudan Metin Düzenleme<br>"
            "• Sayfa Küçük Resimleri, Döndürme, Ekleme ve Çıkarma<br>"
            "• Tam Geri Al / Yinele (Undo / Redo) Altyapısı"
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #D6D6DC; font-size: 11px; line-height: 1.4;")
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        lbl_copy = QLabel(APP_COPYRIGHT)
        lbl_copy.setStyleSheet("color: #727280; font-size: 10px;")
        layout.addWidget(lbl_copy)
        
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
