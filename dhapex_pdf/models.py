"""
Nexora PDF Studio - Veri Modelleri ve Eleman Tanımları
Metin, resim, şekil, serbest çizim, karartma ve filigran elemanları.
"""

import uuid
import math
import copy
from typing import List, Tuple, Optional, Dict, Any
import pymupdf as fitz
from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QColor

def hex_to_rgb_float(hex_code: str) -> Optional[Tuple[float, float, float]]:
    """#RRGGBB formatını (0.0-1.0, 0.0-1.0, 0.0-1.0) aralığına çevirir."""
    if not hex_code or hex_code == "transparent" or hex_code == "none":
        return None
    c = QColor(hex_code)
    return (c.redF(), c.greenF(), c.blueF())

class BaseElement:
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 100.0, height: float = 50.0):
        self.id = str(uuid.uuid4())
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.opacity = 1.0
        self.type = "base"

    def get_rect(self) -> QRectF:
        return QRectF(self.x, self.y, self.width, self.height)

    def set_rect(self, rect: QRectF):
        self.x = rect.x()
        self.y = rect.y()
        self.width = max(5.0, rect.width())
        self.height = max(5.0, rect.height())

    def clone(self):
        new_el = copy.deepcopy(self)
        new_el.id = str(uuid.uuid4())
        return new_el

    def apply_to_pdf_page(self, page: fitz.Page):
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "opacity": self.opacity
        }

import os

WINDOWS_FONT_DIR = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")

def get_system_font_file(family: str, bold: bool = False, italic: bool = False) -> Optional[str]:
    """Windows sistem yazı tiplerinden Türkçe ve Unicode destekli TTF dosyasını bulur."""
    family_lower = (family or "").lower()
    
    candidates = []
    if "times" in family_lower or "serif" in family_lower:
        if bold and italic:
            candidates = ["timesbi.ttf", "timesbd.ttf", "timesi.ttf", "times.ttf"]
        elif bold:
            candidates = ["timesbd.ttf", "times.ttf"]
        elif italic:
            candidates = ["timesi.ttf", "times.ttf"]
        else:
            candidates = ["times.ttf"]
    elif "courier" in family_lower or "mono" in family_lower:
        if bold and italic:
            candidates = ["courbi.ttf", "courbd.ttf", "couri.ttf", "cour.ttf"]
        elif bold:
            candidates = ["courbd.ttf", "cour.ttf"]
        elif italic:
            candidates = ["couri.ttf", "cour.ttf"]
        else:
            candidates = ["cour.ttf"]
    elif "calibri" in family_lower:
        if bold and italic:
            candidates = ["calibriz.ttf", "calibrib.ttf", "calibrii.ttf", "calibri.ttf"]
        elif bold:
            candidates = ["calibrib.ttf", "calibri.ttf"]
        elif italic:
            candidates = ["calibrii.ttf", "calibri.ttf"]
        else:
            candidates = ["calibri.ttf"]
    elif "segoe" in family_lower:
        if bold and italic:
            candidates = ["segoeuiz.ttf", "segoeuib.ttf", "segoeuii.ttf", "segoeui.ttf"]
        elif bold:
            candidates = ["segoeuib.ttf", "segoeui.ttf"]
        elif italic:
            candidates = ["segoeuii.ttf", "segoeui.ttf"]
        else:
            candidates = ["segoeui.ttf"]
    else: # Arial / Helvetica / Varsayılan
        if bold and italic:
            candidates = ["arialbi.ttf", "arialbd.ttf", "ariali.ttf", "arial.ttf"]
        elif bold:
            candidates = ["arialbd.ttf", "arial.ttf"]
        elif italic:
            candidates = ["ariali.ttf", "arial.ttf"]
        else:
            candidates = ["arial.ttf"]
            
    for c in candidates:
        full_path = os.path.join(WINDOWS_FONT_DIR, c)
        if os.path.isfile(full_path):
            return full_path
            
    fallback = os.path.join(WINDOWS_FONT_DIR, "arial.ttf")
    if os.path.isfile(fallback):
        return fallback
    return None

class TextElement(BaseElement):
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 180.0, height: float = 40.0, text: str = "Metin Girin"):
        super().__init__(x, y, width, height)
        self.type = "text"
        self.text = text
        self.font_family = "Arial"
        self.font_size = 12.0
        self.color = "#000000"
        self.bold = False
        self.italic = False
        self.align = 0 # 0: left, 1: center, 2: right

    def apply_to_pdf_page(self, page: fitz.Page):
        rect = fitz.Rect(self.x, self.y, self.x + self.width, self.y + self.height)
        color_rgb = hex_to_rgb_float(self.color) or (0, 0, 0)
        
        font_file = get_system_font_file(self.font_family, self.bold, self.italic)
        fontname_tag = f"f_{uuid.uuid4().hex[:8]}"
        
        used_fontname = None
        if font_file and os.path.isfile(font_file):
            try:
                page.insert_font(fontname=fontname_tag, fontfile=font_file)
                used_fontname = fontname_tag
            except Exception as ef:
                print(f"Font yükleme hatası: {ef}")
                used_fontname = None
                
        if not used_fontname:
            font_base = "helv"
            family_lower = (self.font_family or "").lower()
            if "times" in family_lower or "serif" in family_lower:
                font_base = "times"
            elif "courier" in family_lower or "mono" in family_lower:
                font_base = "couri"
            suffix = ""
            if self.bold and self.italic:
                suffix = "bi"
            elif self.bold:
                suffix = "bo"
            elif self.italic:
                suffix = "it"
            used_fontname = font_base if not suffix else f"{font_base}-{suffix}"

        try:
            rc = page.insert_textbox(
                rect, 
                self.text, 
                fontsize=self.font_size, 
                fontname=used_fontname, 
                color=color_rgb, 
                align=self.align
            )
            # Taşma durumunda kesin yerleşim için satır bazında insert_text kullanılır
            if rc < 0:
                lines = self.text.split("\n")
                line_height = max(10.0, self.font_size * 1.25)
                for idx, line in enumerate(lines):
                    pt_y = self.y + (idx + 1) * line_height
                    page.insert_text(
                        fitz.Point(self.x, pt_y),
                        line,
                        fontsize=self.font_size,
                        fontname=used_fontname,
                        color=color_rgb
                    )
        except Exception:
            try:
                page.insert_text(
                    fitz.Point(self.x, self.y + self.font_size),
                    self.text,
                    fontsize=self.font_size,
                    fontname="helv",
                    color=color_rgb
                )
            except Exception as e:
                print(f"Metin eklenirken hata: {e}")

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "text": self.text,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic,
            "align": self.align
        })
        return d

class ImageElement(BaseElement):
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 150.0, height: float = 100.0, image_path: str = ""):
        super().__init__(x, y, width, height)
        self.type = "image"
        self.image_path = image_path
        self.keep_aspect_ratio = True

    def apply_to_pdf_page(self, page: fitz.Page):
        if not self.image_path or not os.path.isfile(self.image_path):
            return
        rect = fitz.Rect(self.x, self.y, self.x + self.width, self.y + self.height)
        rect.normalize()
        try:
            page.insert_image(rect, filename=self.image_path, keep_proportion=self.keep_aspect_ratio)
        except Exception:
            try:
                from PIL import Image
                import io
                with Image.open(self.image_path) as im:
                    buf = io.BytesIO()
                    # Saydam PNG'leri koru veya RGB'ye çevir
                    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                        im.convert("RGBA").save(buf, format="PNG")
                    else:
                        im.convert("RGB").save(buf, format="JPEG", quality=95)
                    page.insert_image(rect, stream=buf.getvalue(), keep_proportion=self.keep_aspect_ratio)
            except Exception as e:
                print(f"Resim eklenirken hata: {e}")

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "image_path": self.image_path,
            "keep_aspect_ratio": self.keep_aspect_ratio
        })
        return d

class ShapeElement(BaseElement):
    def __init__(self, shape_type: str = "rectangle", x: float = 0.0, y: float = 0.0, width: float = 100.0, height: float = 60.0):
        super().__init__(x, y, width, height)
        self.type = "shape"
        self.shape_type = shape_type
        self.stroke_color = "#E5252A"
        self.stroke_width = 2.0
        self.fill_color = None
        self.dash_style = "solid"

    def apply_to_pdf_page(self, page: fitz.Page):
        shape = page.new_shape()
        stroke_rgb = hex_to_rgb_float(self.stroke_color) or (0, 0, 0)
        fill_rgb = hex_to_rgb_float(self.fill_color) if self.fill_color else None
        
        rect = fitz.Rect(self.x, self.y, self.x + self.width, self.y + self.height)
        
        if self.shape_type == "rectangle":
            shape.draw_rect(rect)
        elif self.shape_type == "ellipse":
            shape.draw_oval(rect)
        elif self.shape_type == "line":
            p1 = fitz.Point(self.x, self.y)
            p2 = fitz.Point(self.x + self.width, self.y + self.height)
            shape.draw_line(p1, p2)
        elif self.shape_type == "arrow":
            p1 = fitz.Point(self.x, self.y)
            p2 = fitz.Point(self.x + self.width, self.y + self.height)
            shape.draw_line(p1, p2)
            
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            length = math.hypot(dx, dy)
            if length > 4:
                ux = dx / length
                uy = dy / length
                arrow_len = min(15.0, length * 0.4)
                arrow_w = arrow_len * 0.5
                
                left_x = p2.x - arrow_len * ux + arrow_w * uy
                left_y = p2.y - arrow_len * uy - arrow_w * ux
                right_x = p2.x - arrow_len * ux - arrow_w * uy
                right_y = p2.y - arrow_len * uy + arrow_w * ux
                
                shape.draw_line(p2, fitz.Point(left_x, left_y))
                shape.draw_line(p2, fitz.Point(right_x, right_y))
                
        shape.finish(
            color=stroke_rgb, 
            fill=fill_rgb, 
            width=self.stroke_width
        )
        shape.commit()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "shape_type": self.shape_type,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "fill_color": self.fill_color,
            "dash_style": self.dash_style
        })
        return d

class DrawingElement(BaseElement):
    def __init__(self, points: List[Tuple[float, float]] = None, is_highlighter: bool = False, stroke_width: Optional[float] = None, color: Optional[str] = None):
        super().__init__(0, 0, 0, 0)
        self.type = "drawing"
        self.points = points or []
        self.is_highlighter = is_highlighter
        if is_highlighter:
            self.color = color or "#FFEB3B"
            self.stroke_width = float(stroke_width) if stroke_width is not None else 16.0
            self.opacity = 0.4
        else:
            self.color = color or "#1E88E5"
            self.stroke_width = float(stroke_width) if stroke_width is not None else 2.0
            self.opacity = 1.0
        self.calculate_bounds()

    def add_point(self, pt: Tuple[float, float]):
        self.points.append(pt)
        self.calculate_bounds()

    def calculate_bounds(self):
        if not self.points:
            self.x, self.y, self.width, self.height = 0.0, 0.0, 0.0, 0.0
            return
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        pad = max(2.0, self.stroke_width / 2.0)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        self.x = min_x - pad
        self.y = min_y - pad
        self.width = max(10.0, (max_x - min_x) + pad * 2.0)
        self.height = max(10.0, (max_y - min_y) + pad * 2.0)

    def apply_to_pdf_page(self, page: fitz.Page):
        if not self.points:
            return
        color_rgb = hex_to_rgb_float(self.color) or (0, 0, 0)
        
        if len(self.points) == 1:
            pt = self.points[0]
            shape = page.new_shape()
            shape.draw_circle(fitz.Point(pt[0], pt[1]), max(0.5, self.stroke_width / 2.0))
            shape.finish(color=color_rgb, fill=color_rgb, width=0.1)
            shape.commit(overlay=not self.is_highlighter)
            return

        if self.is_highlighter:
            shape = page.new_shape()
            pts = [fitz.Point(p[0], p[1]) for p in self.points]
            shape.draw_polyline(pts)
            shape.finish(color=color_rgb, width=self.stroke_width)
            shape.commit(overlay=False)
        else:
            pts = [(float(p[0]), float(p[1])) for p in self.points]
            annot = page.add_ink_annot([pts])
            annot.set_colors(stroke=color_rgb)
            annot.set_border(width=self.stroke_width)
            annot.set_opacity(self.opacity)
            annot.update()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "points": self.points,
            "is_highlighter": self.is_highlighter,
            "color": self.color,
            "stroke_width": self.stroke_width,
            "opacity": self.opacity
        })
        return d

class RedactionElement(BaseElement):
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 120.0, height: float = 30.0):
        super().__init__(x, y, width, height)
        self.type = "redaction"
        self.fill_color = "#000000"
        self.applied = False

    def apply_to_pdf_page(self, page: fitz.Page):
        # Kalıcı sansür uygulama (altındaki metin ve görselleri tamamen siler)
        rect = fitz.Rect(self.x, self.y, self.x + self.width, self.y + self.height)
        annot = page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "fill_color": self.fill_color,
            "applied": self.applied
        })
        return d

class WatermarkElement(BaseElement):
    def __init__(self, text: str = "GİZLİ", font_size: float = 60.0, angle: float = 45.0, opacity: float = 0.3, color: str = "#E5252A"):
        super().__init__(0, 0, 0, 0)
        self.type = "watermark"
        self.text = text
        self.font_size = font_size
        self.angle = angle
        self.opacity = opacity
        self.color = color

    def apply_to_pdf_page(self, page: fitz.Page):
        r = page.rect
        center = fitz.Point(r.width * 0.2, r.height * 0.5)
        color_rgb = hex_to_rgb_float(self.color) or (0.9, 0.1, 0.1)
        font_file = get_system_font_file("Arial", bold=True, italic=False)
        fontname_tag = f"wm_{uuid.uuid4().hex[:8]}"
        used_font = None
        if font_file and os.path.isfile(font_file):
            try:
                page.insert_font(fontname=fontname_tag, fontfile=font_file)
                used_font = fontname_tag
            except Exception:
                used_font = None
        try:
            morph = (center, fitz.Matrix(self.angle))
            if used_font:
                page.insert_text(center, self.text, fontsize=self.font_size, fontname=used_font, morph=morph, color=color_rgb, overlay=True)
            else:
                page.insert_text(center, self.text, fontsize=self.font_size, morph=morph, color=color_rgb, overlay=True)
        except Exception as e:
            print(f"Filigran uygulanırken hata: {e}")

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "text": self.text,
            "font_size": self.font_size,
            "angle": self.angle,
            "color": self.color
        })
        return d
