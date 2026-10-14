"""
Nexora PDF Studio - Adobe Acrobat Tarzı Tam Metin Arama Paneli
Tüm belgede anında arama, sonuç listesi ve sayfada vurgulama.
"""

from typing import Optional, List
import pymupdf as fitz
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from dhapex_pdf.icons import IconFactory

class SearchPanel(QWidget):
    result_selected = pyqtSignal(int, list) # page_num, rects

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc: Optional[fitz.Document] = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Belgede ara...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.btn_search = QPushButton()
        self.btn_search.setIcon(IconFactory.get("search", 16))
        self.btn_search.setToolTip("Ara")
        self.btn_search.clicked.connect(self.perform_search)
        
        search_bar.addWidget(self.search_input)
        search_bar.addWidget(self.btn_search)
        layout.addLayout(search_bar)
        
        self.cb_case = QCheckBox("Büyük/Küçük Harfe Duyarlı")
        layout.addWidget(self.cb_case)
        
        self.lbl_status = QLabel("Aramak için kelime girin.")
        self.lbl_status.setStyleSheet("color: #8E8E98; font-size: 11px;")
        layout.addWidget(self.lbl_status)
        
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.results_list)

    def load_document(self, doc: fitz.Document):
        self.doc = doc
        self.results_list.clear()
        self.lbl_status.setText("Aramak için kelime girin.")

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query or not self.doc:
            return
            
        self.results_list.clear()
        case_sensitive = self.cb_case.isChecked()
        flags = 0 if case_sensitive else fitz.TEXT_DEHYPHENATE
        
        total_hits = 0
        
        for page_idx in range(len(self.doc)):
            page = self.doc.load_page(page_idx)
            rects = page.search_for(query, flags=flags)
            if rects:
                total_hits += len(rects)
                text = page.get_text("text")
                snippet = self.extract_snippet(text, query)
                
                item = QListWidgetItem()
                item.setText(f"Sayfa {page_idx + 1} ({len(rects)} eşleşme)\n\"{snippet}\"")
                item.setIcon(IconFactory.get("search", 16))
                item.setData(Qt.ItemDataRole.UserRole, (page_idx, rects))
                self.results_list.addItem(item)
                
        if total_hits > 0:
            self.lbl_status.setText(f"Toplam {total_hits} eşleşme bulundu.")
        else:
            self.lbl_status.setText(f"'{query}' bulunamadı.")

    def extract_snippet(self, text: str, query: str) -> str:
        idx = text.lower().find(query.lower())
        if idx == -1:
            return query
        start = max(0, idx - 30)
        end = min(len(text), idx + len(query) + 30)
        snippet = text[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet

    def on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            page_idx, rects = data
            self.result_selected.emit(page_idx, rects)
