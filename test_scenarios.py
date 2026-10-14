"""
DH-Apex PDF Studio - Kapsamlı Otomasyon Test Senaryoları Paketi
Tüm araçların, dosya işlemlerinin, sayfa yönetiminin ve güvenlik motorunun uçtan uca doğrulanması.
"""

import sys
import os
import shutil
import tempfile
import unittest
import pymupdf as fitz

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QRectF, QPointF

# DH-Apex PDF Studio modüllerini içe aktar
from dhapex_pdf.main_window import MainWindow
from dhapex_pdf.models import (
    TextElement, ImageElement, ShapeElement, DrawingElement, RedactionElement, WatermarkElement
)
from dhapex_pdf.commands import (
    AddElementCommand, DeleteElementCommand, TransformElementCommand
)

# Qt Uygulamasını bir kez başlat
app = QApplication.instance() or QApplication(sys.argv)

class TestDHApexPDFStudio(unittest.TestCase):
    def setUp(self):
        self.win = MainWindow()
        self.temp_dir = tempfile.mkdtemp(prefix="DH-Apex_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_document_lifecycle_and_windows_file_lock(self):
        """Senaryo 1: Belge Yaşam Döngüsü ve Windows Dosya Kilidi Aşımı"""
        test_pdf = os.path.join(self.temp_dir, "lifecycle_test.pdf")
        
        # 1. Yeni belgeye metin ekle ve kaydet
        el = TextElement(x=50, y=50, width=200, height=40, text="DH-Apex Ilk Surum")
        self.win.canvas_view.add_element_internal(0, el)
        self.win.save_to_path(test_pdf, show_dialog=False)
        self.assertTrue(os.path.exists(test_pdf), "PDF dosyası diske kaydedilemedi!")

        # 2. Var olan dosyayı belleğe aç (Windows kilitsiz)
        self.win.open_pdf(test_pdf)
        self.assertEqual(len(self.win.doc), 1, "Açılan belge sayfa sayısı 1 olmalı")
        
        # 3. Dosyaya yeni bir eleman ekle
        el2 = TextElement(x=50, y=120, width=200, height=40, text="Ikinci Satir Metin")
        self.win.canvas_view.add_element_internal(0, el2)

        # 4. Doğrudan AYNI dosya yolunun üzerine kaydet (Windows kilit çakışması testi)
        try:
            self.win.save_to_path(test_pdf, show_dialog=False)
            save_success = True
        except Exception as e:
            save_success = False
            print(f"Windows kilit hatası: {e}")

        self.assertTrue(save_success, "Windows'ta açık dosya üzerine yazma başarısız oldu!")

        # 5. Kaydedilen dosyayı doğrula
        verify_doc = fitz.open(test_pdf)
        raw_content = verify_doc[0].get_text("text")
        verify_doc.close()
        content = raw_content.replace("\xa0", " ").replace("\xad", "-")
        
        self.assertIn("DH-Apex Ilk Surum", content)
        self.assertIn("Ikinci Satir Metin", content)

    def test_02_element_rendering_and_burnin(self):
        """Senaryo 2: Vektörel Şekiller, Serbest Çizim ve Filigran"""
        test_pdf = os.path.join(self.temp_dir, "elements_test.pdf")
        
        # Dikdörtgen
        rect_el = ShapeElement(shape_type="rectangle", x=60, y=60, width=120, height=80)
        rect_el.stroke_color = "#00AA00"
        rect_el.fill_color = "#EEEEEE"
        self.win.canvas_view.add_element_internal(0, rect_el)

        # Elips
        ellipse_el = ShapeElement(shape_type="ellipse", x=220, y=60, width=80, height=80)
        ellipse_el.stroke_color = "#0000FF"
        self.win.canvas_view.add_element_internal(0, ellipse_el)

        # Çizgi ve Ok
        line_el = ShapeElement(shape_type="line", x=50, y=200, width=150, height=50)
        self.win.canvas_view.add_element_internal(0, line_el)
        
        arrow_el = ShapeElement(shape_type="arrow", x=250, y=200, width=100, height=100)
        self.win.canvas_view.add_element_internal(0, arrow_el)

        # Serbest Çizim (Mürekkep)
        draw_el = DrawingElement(points=[(100, 350), (120, 370), (140, 360), (160, 380)])
        self.win.canvas_view.add_element_internal(0, draw_el)

        # Fosforlu Kalem
        hi_el = DrawingElement(points=[(100, 420), (250, 420)], is_highlighter=True)
        self.win.canvas_view.add_element_internal(0, hi_el)

        # Filigran
        wm_el = WatermarkElement(text="TEST_WATERMARK", font_size=40, angle=30)
        self.win.canvas_view.add_element_internal(0, wm_el)

        # Kaydet ve doğrula
        self.win.save_to_path(test_pdf, show_dialog=False)
        self.assertTrue(os.path.exists(test_pdf))

        doc = fitz.open(test_pdf)
        text_content = doc[0].get_text("text")
        doc.close()
        self.assertIn("TEST_WATERMARK", text_content)

    def test_03_undo_redo_stack(self):
        """Senaryo 3: Geri Al (Undo) ve Yinele (Redo) Yığını"""
        pno = self.win.canvas_view.current_page_idx
        
        # 1. Ekleme ve Geri Alma
        el = TextElement(x=10, y=10, width=100, height=30, text="Undo Test")
        cmd_add = AddElementCommand(self.win.canvas_view, pno, el)
        self.win.undo_stack.push(cmd_add)
        self.assertEqual(len(self.win.canvas_view.page_elements[pno]), 1)

        self.win.undo_stack.undo()
        self.assertEqual(len(self.win.canvas_view.page_elements[pno]), 0)

        self.win.undo_stack.redo()
        self.assertEqual(len(self.win.canvas_view.page_elements[pno]), 1)

        # 2. Silme ve Geri Alma
        cmd_del = DeleteElementCommand(self.win.canvas_view, pno, el)
        self.win.undo_stack.push(cmd_del)
        self.assertEqual(len(self.win.canvas_view.page_elements[pno]), 0)

        self.win.undo_stack.undo()
        self.assertEqual(len(self.win.canvas_view.page_elements[pno]), 1)

        # 3. Taşıma / Boyutlandırma ve Geri Alma
        old_r = el.get_rect()
        new_r = QRectF(50, 50, 150, 50)
        cmd_trans = TransformElementCommand(self.win.canvas_view, el, old_r, new_r)
        self.win.undo_stack.push(cmd_trans)
        self.assertEqual(el.x, 50)

        self.win.undo_stack.undo()
        self.assertEqual(el.x, 10)

    def test_04_page_management_and_element_sync(self):
        """Senaryo 4: Sayfa Ekleme, Silme ve Eleman İndeks Kaydırması"""
        # 3 sayfa oluştur
        self.win.doc.new_page(1, width=595, height=842)
        self.win.doc.new_page(2, width=595, height=842)
        self.assertEqual(len(self.win.doc), 3)

        # Sayfa 1 ve Sayfa 2'ye eleman ekle
        el_p1 = TextElement(text="Sayfa 1 Elemani")
        el_p2 = TextElement(text="Sayfa 2 Elemani")
        self.win.canvas_view.add_element_internal(1, el_p1)
        self.win.canvas_view.add_element_internal(2, el_p2)

        # Sayfa 1'den sonrasına boş sayfa ekle (yeni sayfa indeksi: 2)
        # Bu işlemde eski Sayfa 2'nin indeksinin 3'e kayması gerekir!
        self.win.insert_blank_page_after(1)
        self.assertEqual(len(self.win.doc), 4)
        self.assertIn(3, self.win.canvas_view.page_elements, "Sayfa eklenirken eleman indeksi kaydırılmadı!")
        self.assertEqual(self.win.canvas_view.page_elements[3][0].text, "Sayfa 2 Elemani")

        # Sayfa 0'ı sil
        # Bu işlemde Sayfa 1 -> Sayfa 0, Sayfa 3 -> Sayfa 2 olmalıdır
        self.win.doc.delete_page(0)
        # Indeksleri senkronize et
        new_elements = {}
        for k, v in self.win.canvas_view.page_elements.items():
            if k > 0:
                new_elements[k - 1] = v
        self.win.canvas_view.page_elements = new_elements

        self.assertEqual(len(self.win.doc), 3)
        self.assertEqual(self.win.canvas_view.page_elements[0][0].text, "Sayfa 1 Elemani")
        self.assertEqual(self.win.canvas_view.page_elements[2][0].text, "Sayfa 2 Elemani")

        # Sayfayı 90 derece döndür
        self.win.rotate_page_degrees(0, 90)
        self.assertEqual(self.win.doc[0].rotation, 90)

    def test_05_permanent_redaction_engine(self):
        """Senaryo 5: Kalıcı Güvenlikli Sansürleme (Redaction Sanitization)"""
        test_pdf = os.path.join(self.temp_dir, "redact_test.pdf")
        
        # 1. Sayfaya gizli metin ekle
        self.win.doc[0].insert_text((100, 100), "KART_NUMARASI_5555_4444_3333_2222", fontsize=12)
        self.win.save_to_path(test_pdf, show_dialog=False)

        # Metnin kaydedildiğini doğrula
        chk = fitz.open(test_pdf)
        self.assertIn("KART_NUMARASI_5555_4444_3333_2222", chk[0].get_text("text"))
        chk.close()

        # 2. Tam o koordinat üzerine Sansür Elemanı yerleştir ve uygula
        redact = RedactionElement(x=90, y=85, width=320, height=30)
        redact.apply_to_pdf_page(self.win.doc[0])
        self.win.save_to_path(test_pdf, show_dialog=False)

        # 3. İncele: Gizli veri PDF kaynak kodundan TAMAMEN silinmiş olmalı
        chk2 = fitz.open(test_pdf)
        sanitized_text = chk2[0].get_text("text")
        chk2.close()

        self.assertNotIn(
            "KART_NUMARASI_5555_4444_3333_2222", 
            sanitized_text, 
            "Sansürlenen veri PDF içeriğinden kalıcı olarak temizlenemedi!"
        )

    def test_06_search_and_highlight(self):
        """Senaryo 6: Belge İçi Arama ve Vurgu Koordinatları"""
        self.win.doc[0].insert_text((50, 80), "DH-Apex Arama Testi Kelimesi", fontsize=14)
        self.win.search_panel.load_document(self.win.doc)
        
        self.win.search_panel.search_input.setText("Arama Testi")
        self.win.search_panel.perform_search()
        
        self.assertGreater(self.win.search_panel.results_list.count(), 0, "Arama sonucu bulunamadı!")
        
        item = self.win.search_panel.results_list.item(0)
        data = item.data(Qt.ItemDataRole.UserRole)
        page_idx, rects = data
        self.assertEqual(page_idx, 0)
        self.assertGreater(len(rects), 0)

        # Tuvalde vurgulama
        self.win.canvas_view.highlight_search_rects(rects)
        self.assertEqual(len(self.win.canvas_view.search_highlight_items), len(rects))

    def test_07_clipboard_operations(self):
        """Senaryo 7: Kopyala, Yapıştır, Çoğalt (Ctrl+C, Ctrl+V, Ctrl+D)"""
        el = TextElement(x=100, y=100, width=150, height=40, text="Kopyalanacak Metin")
        self.win.canvas_view.add_element_internal(0, el)
        self.win.canvas_view.selected_element = el
        
        # Kopyala
        self.win.canvas_view.copy_selected()
        self.assertIsNotNone(self.win.canvas_view.clipboard_element)
        self.assertEqual(self.win.canvas_view.clipboard_element.text, "Kopyalanacak Metin")

        # Yapıştır
        self.win.canvas_view.paste_copied()
        self.assertEqual(len(self.win.canvas_view.page_elements[0]), 2)
        pasted = self.win.canvas_view.page_elements[0][-1]
        self.assertNotEqual(pasted.id, el.id, "Yapıştırılan elemanın benzersiz ID'si olmalı!")
        self.assertEqual(pasted.x, el.x + 15.0)

        # Çoğalt (Duplicate)
        self.win.canvas_view.duplicate_selected()
        self.assertEqual(len(self.win.canvas_view.page_elements[0]), 3)

    def test_08_export_capabilities(self):
        """Senaryo 8: PNG Resim ve TXT Metin Olarak Dışa Aktarma"""
        self.win.doc[0].insert_text((50, 50), "Disa Aktarma Testi Icerigi", fontsize=12)
        
        # 1. Resim (PNG) Dışa Aktarma
        png_path = os.path.join(self.temp_dir, "sayfa_1.png")
        p = self.win.doc.load_page(0)
        pix = p.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        pix.save(png_path)
        self.assertTrue(os.path.exists(png_path))
        self.assertGreater(os.path.getsize(png_path), 500)

        # 2. Metin (TXT) Dışa Aktarma
        txt_path = os.path.join(self.temp_dir, "icerik.txt")
        full_text = self.win.doc[0].get_text("text")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        self.assertTrue(os.path.exists(txt_path))
        
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Disa Aktarma Testi Icerigi", content)

    def test_09_pdf_merge_operation(self):
        """Senaryo 9: Birden Fazla PDF Belgesini Birleştirme"""
        p1 = os.path.join(self.temp_dir, "doc1.pdf")
        p2 = os.path.join(self.temp_dir, "doc2.pdf")
        p_merged = os.path.join(self.temp_dir, "merged.pdf")

        d1 = fitz.open()
        p = d1.new_page()
        p.insert_text((50, 50), "Doc 1 Page 1")
        p = d1.new_page()
        p.insert_text((50, 50), "Doc 1 Page 2")
        d1.save(p1)
        d1.close()

        d2 = fitz.open()
        p = d2.new_page()
        p.insert_text((50, 50), "Doc 2 Page 1")
        d2.save(p2)
        d2.close()

        # Birleştirme simülasyonu
        m_doc = fitz.open()
        for f in [p1, p2]:
            t = fitz.open(f)
            m_doc.insert_pdf(t)
            t.close()
        m_doc.save(p_merged)
        m_doc.close()

        res = fitz.open(p_merged)
        self.assertEqual(len(res), 3, "Birleştirilmiş belge 3 sayfa olmalı!")
        res.close()

    def test_10_metadata_management(self):
        """Senaryo 10: PDF Meta Verilerini Okuma ve Güncelleme"""
        meta = {
            "title": "DH-Apex Raporu",
            "author": "DH-Apex Muhendislik",
            "subject": "Finansal Analiz",
            "keywords": "pdf, editor, DH-Apex, pro"
        }
        self.win.doc.set_metadata(meta)
        
        test_pdf = os.path.join(self.temp_dir, "meta_test.pdf")
        self.win.save_to_path(test_pdf, show_dialog=False)

        chk = fitz.open(test_pdf)
        self.assertEqual(chk.metadata.get("title"), "DH-Apex Raporu")
        self.assertEqual(chk.metadata.get("author"), "DH-Apex Muhendislik")
        self.assertEqual(chk.metadata.get("subject"), "Finansal Analiz")
        chk.close()

    def test_11_page_extraction(self):
        """Senaryo 11: Belirli Sayfaları Dışa Aktarma (Extract Pages)"""
        # 4 sayfalık doküman
        for i in range(3):
            p = self.win.doc.new_page()
            p.insert_text((50, 50), f"Sayfa {i + 2}")
        self.assertEqual(len(self.win.doc), 4)

        # Sayfa 0 ve 2'yi dışa aktar
        extract_pdf = os.path.join(self.temp_dir, "extracted.pdf")
        out = fitz.open()
        for pno in [0, 2]:
            out.insert_pdf(self.win.doc, from_page=pno, to_page=pno)
        out.save(extract_pdf)
        out.close()

        chk = fitz.open(extract_pdf)
        self.assertEqual(len(chk), 2, "Çıkarılan belge tam 2 sayfa olmalı!")
        chk.close()

    def test_12_keyboard_nudge_nudge(self):
        """Senaryo 12: Klavye Ok Tuşlarıyla Konum Kaydırma (Nudge)"""
        el = TextElement(x=100.0, y=100.0, width=100.0, height=30.0)
        self.win.canvas_view.add_element_internal(0, el)
        self.win.canvas_view.selected_element = el

        # Sağa ve Aşağı kaydırma
        old_r = el.get_rect()
        new_r = old_r.translated(10.0, 5.0)
        cmd = TransformElementCommand(self.win.canvas_view, el, old_r, new_r)
        self.win.undo_stack.push(cmd)

        self.assertEqual(el.x, 110.0)
        self.assertEqual(el.y, 105.0)

        # Geri al
        self.win.undo_stack.undo()
        self.assertEqual(el.x, 100.0)
        self.assertEqual(el.y, 100.0)

    def test_13_text_element_auto_expansion(self):
        """Senaryo 13: Uzun Metin Girildiğinde Otomatik Kutu Genişlemesi"""
        long_text = "Bu çok uzun bir paragraf metnidir ve kutunun sınırlarını aşmaması için otomatik genişletilmelidir."
        el = TextElement(x=50, y=50, width=50, height=20, text=long_text)
        self.win.canvas_view.add_element_internal(0, el)

        # draw_element_on_scene tetiklendiğinde genişliğin ve yüksekliğin arttığını doğrula
        self.assertGreater(el.width, 50, "Metin kutusu metin uzunluğuna göre genişletilmedi!")
        self.assertGreater(el.height, 20, "Metin kutusu yüksekliği otomatik ayarlanmadı!")

    def test_14_drawing_thickness_isolation(self):
        """Senaryo 14: Çizim Yaparken Kalınlığın Sabit Kalması (Büyümemesi)"""
        draw_el = DrawingElement(points=[(10, 10)], is_highlighter=False, stroke_width=2.5)
        self.assertEqual(draw_el.stroke_width, 2.5)
        
        # Fareyi 500 piksel sağa doğru sürükle (birçok nokta ekle)
        for x in range(20, 500, 10):
            draw_el.add_point((float(x), 50.0))
            
        # Bounding box genişlemiş olmalı, ancak stroke_width KESİNLİKLE 2.5 kalmalı!
        self.assertGreater(draw_el.width, 400.0)
        self.assertEqual(draw_el.stroke_width, 2.5, "Çizim yaparken stroke_width büyüdü! İzolasyon başarısız!")

    def test_15_turkish_unicode_text_burnin(self):
        """Senaryo 15: Türkçe Karakterlerin (ç, ğ, ı, ö, ş, ü, İ, Ğ, Ş, Ç, Ö, Ü) Bozulmadan PDF'e Yazılması"""
        test_pdf = os.path.join(self.temp_dir, "turkish_test.pdf")
        turkish_text = "Şeker, Çağlayan, Iğdır, ömür, ümit, İSTANBUL, Ğaziantep, Çiçek"
        
        el = TextElement(x=50, y=100, width=400, height=50, text=turkish_text)
        el.font_family = "Arial"
        el.font_size = 14.0
        self.win.canvas_view.add_element_internal(0, el)
        
        self.win.save_to_path(test_pdf, show_dialog=False)
        self.assertTrue(os.path.exists(test_pdf))
        
        doc = fitz.open(test_pdf)
        raw_text = doc[0].get_text("text")
        doc.close()
        
        # Karakterlerin soru işareti veya noktaya dönüşmediğini doğrula
        for char in ["Ş", "ç", "ğ", "ı", "ö", "ü", "İ", "Ğ", "Ç"]:
            self.assertIn(char, raw_text, f"Türkçe karakter '{char}' PDF çıktısında bozuldu!")

    def test_16_inline_text_editing_and_toolbar_sync(self):
        """Senaryo 16: Satır İçi Metin Düzenleme ve Araç Çubuğu Senkronizasyonu"""
        # Yeni metin öğesi başlat
        el = TextElement(x=100, y=100, width=150, height=40, text="")
        self.win.canvas_view.start_inline_text_editing(el, is_new=True)
        self.assertIsNotNone(self.win.canvas_view.inline_editor)
        
        # Metin yaz ve onayla
        self.win.canvas_view.inline_editor.setPlainText("Yeni Satır İçi Metin")
        self.win.canvas_view.finish_inline_text_editing(commit=True)
        
        self.assertIsNone(self.win.canvas_view.inline_editor)
        self.assertIn(el, self.win.canvas_view.page_elements[0])
        self.assertEqual(el.text, "Yeni Satır İçi Metin")
        
        # Araç çubuğu senkronizasyon testi
        self.win.on_canvas_element_selected(el)
        self.assertEqual(self.win.cb_quick_font.currentText(), el.font_family)
        self.assertEqual(self.win.spin_quick_font_size.value(), el.font_size)

    def test_17_canvas_element_visibility_and_autosave_commit(self):
        """Senaryo 17: Tuval Üzerinde Görünürlük (Sahneye Eklenme) ve Kaydederken Otomatik Onaylama"""
        # 1. Tuval görünürlük kontrolü: Her elemanın QGraphicsItem'ı sahneye bağlı (visible) olmalı
        txt = TextElement(x=50, y=50, width=100, height=30, text="Görünür Metin")
        self.win.canvas_view.add_element_internal(0, txt)
        item = self.win.canvas_view.element_items.get(txt.id)
        self.assertIsNotNone(item, "TextElement için sahne öğesi oluşturulamadı!")
        self.assertIsNotNone(item.scene(), "TextElement sahneden koparılmış (görünmez) durumda!")

        draw = DrawingElement(points=[(10, 10), (20, 20)], stroke_width=3.0)
        self.win.canvas_view.add_element_internal(0, draw)
        draw_item = self.win.canvas_view.element_items.get(draw.id)
        self.assertIsNotNone(draw_item, "DrawingElement için sahne öğesi oluşturulamadı!")
        self.assertIsNotNone(draw_item.scene(), "DrawingElement sahneye eklenmemiş!")

        arrow = ShapeElement(shape_type="arrow", x=30, y=30, width=50, height=50)
        self.win.canvas_view.add_element_internal(0, arrow)
        arrow_item = self.win.canvas_view.element_items.get(arrow.id)
        self.assertIsNotNone(arrow_item, "Ok şekli sahne öğesi oluşturulamadı!")
        self.assertIsNotNone(arrow_item.scene(), "Ok şekli sahneye eklenmemiş!")

        # 2. Kaydederken bekleyen satır içi metnin otomatik onaylanması
        pending_el = TextElement(x=120, y=120, width=150, height=40, text="")
        self.win.canvas_view.start_inline_text_editing(pending_el, is_new=True)
        self.win.canvas_view.inline_editor.setPlainText("Kaydetmeden Once Onaylanan Metin")
        
        test_pdf = os.path.join(self.temp_dir, "autosave_inline_test.pdf")
        self.win.save_to_path(test_pdf, show_dialog=False)
        
        # Editörün kapanmış ve metnin PDF'e yazılmış olduğunu doğrula
        self.assertIsNone(self.win.canvas_view.inline_editor)
        doc = fitz.open(test_pdf)
        pdf_content = doc[0].get_text("text").replace("\xa0", " ")
        doc.close()
        self.assertIn("Kaydetmeden Once Onaylanan Metin", pdf_content)

    def test_18_image_insertion_rendering_and_pdf_burnin(self):
        """Senaryo 18: Resim / İmza Ekleme, Tuvalde Görüntüleme, Taşıma ve PDF'e Gömme"""
        # 1. Test resmi oluştur
        img_path = os.path.join(self.temp_dir, "test_logo.png")
        from PyQt6.QtGui import QImage, QColor
        qimg = QImage(160, 120, QImage.Format.Format_ARGB32)
        qimg.fill(QColor(30, 136, 229)) # Mavi resim
        qimg.save(img_path)
        self.assertTrue(os.path.exists(img_path))

        # 2. Resim ekle
        self.win.add_image_from_path(img_path)
        page_elems = self.win.canvas_view.page_elements.get(0, [])
        img_elems = [e for e in page_elems if isinstance(e, ImageElement)]
        self.assertGreater(len(img_elems), 0, "Resim elemanı sayfaya eklenemedi!")
        
        img_el = img_elems[-1]
        self.assertEqual(img_el.image_path, img_path)

        # 3. Tuval sahnesinde öğenin varlığını ve ebeveynsiz/görünür olduğunu doğrula
        item = self.win.canvas_view.element_items.get(img_el.id)
        self.assertIsNotNone(item, "Resim için QGraphicsPixmapItem oluşturulamadı!")
        self.assertIsNotNone(item.scene(), "Resim sahneye eklenmedi!")

        # 4. Seçim ve Denetçi Senkronizasyonu
        self.win.canvas_view.selected_element = img_el
        self.win.on_canvas_element_selected(img_el)
        self.assertEqual(self.win.inspector_panel.stack.currentIndex(), 4, "Denetçi Resim sekmesine geçmedi!")

        # 5. PDF'e kaydet ve gömülen resmi doğrula
        test_pdf = os.path.join(self.temp_dir, "image_test_out.pdf")
        self.win.save_to_path(test_pdf, show_dialog=False)
        self.assertTrue(os.path.exists(test_pdf))

        chk = fitz.open(test_pdf)
        images = chk[0].get_images()
        chk.close()
        self.assertGreater(len(images), 0, "Resim PDF belgesine kalıcı olarak gömülemedi!")

if __name__ == "__main__":
    unittest.main()


