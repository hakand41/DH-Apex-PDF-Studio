"""
Nexora PDF Studio - Geri Al / Yinele (Undo / Redo) Komut Sistemi
QUndoCommand tabanlı tam geri alma altyapısı.
"""

from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QRectF
from typing import Any

class AddElementCommand(QUndoCommand):
    def __init__(self, canvas_view, page_num: int, element, description: str = "Öğe Ekle"):
        super().__init__(description)
        self.canvas_view = canvas_view
        self.page_num = page_num
        self.element = element

    def redo(self):
        self.canvas_view.add_element_internal(self.page_num, self.element)

    def undo(self):
        self.canvas_view.remove_element_internal(self.page_num, self.element)


class DeleteElementCommand(QUndoCommand):
    def __init__(self, canvas_view, page_num: int, element, description: str = "Öğe Sil"):
        super().__init__(description)
        self.canvas_view = canvas_view
        self.page_num = page_num
        self.element = element

    def redo(self):
        self.canvas_view.remove_element_internal(self.page_num, self.element)

    def undo(self):
        self.canvas_view.add_element_internal(self.page_num, self.element)


class TransformElementCommand(QUndoCommand):
    def __init__(self, canvas_view, element, old_rect: QRectF, new_rect: QRectF, description: str = "Öğe Konumu/Boyutu"):
        super().__init__(description)
        self.canvas_view = canvas_view
        self.element = element
        self.old_rect = old_rect
        self.new_rect = new_rect

    def redo(self):
        self.element.set_rect(self.new_rect)
        self.canvas_view.update_element_visual(self.element)

    def undo(self):
        self.element.set_rect(self.old_rect)
        self.canvas_view.update_element_visual(self.element)


class ChangePropertyCommand(QUndoCommand):
    def __init__(self, canvas_view, element, prop_name: str, old_val: Any, new_val: Any, description: str = "Özellik Değiştir"):
        super().__init__(description)
        self.canvas_view = canvas_view
        self.element = element
        self.prop_name = prop_name
        self.old_val = old_val
        self.new_val = new_val

    def redo(self):
        setattr(self.element, self.prop_name, self.new_val)
        self.canvas_view.update_element_visual(self.element)

    def undo(self):
        setattr(self.element, self.prop_name, self.old_val)
        self.canvas_view.update_element_visual(self.element)
