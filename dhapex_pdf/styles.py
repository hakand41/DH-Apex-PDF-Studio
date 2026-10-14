"""
Nexora PDF Studio - Profesyonel Adobe Acrobat Tarzı Arayüz Temaları
"""

DARK_THEME_QSS = """
/* Genel Pencere ve Zemin */
QWidget {
    background-color: #202023;
    color: #E2E2E6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 12px;
    selection-background-color: #E5252A;
    selection-color: #FFFFFF;
}

QMainWindow {
    background-color: #18181A;
}

/* Menü Çubuğu */
QMenuBar {
    background-color: #1C1C1F;
    color: #E0E0E0;
    border-bottom: 1px solid #2D2D32;
    padding: 2px 6px;
    font-size: 12px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #2E2E34;
    color: #FFFFFF;
}

QMenuBar::item:pressed {
    background-color: #E5252A;
    color: #FFFFFF;
}

/* Açılır Menüler */
QMenu {
    background-color: #25252A;
    color: #E0E0E0;
    border: 1px solid #383840;
    border-radius: 6px;
    padding: 4px 0px;
}

QMenu::item {
    padding: 6px 28px 6px 24px;
    border-radius: 3px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #E5252A;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background-color: #383840;
    margin: 4px 8px;
}

/* Araç Çubukları */
QToolBar {
    background-color: #25252A;
    border-top: 1px solid #2D2D32;
    border-bottom: 1px solid #2D2D32;
    border-left: none;
    border-right: none;
    spacing: 3px;
    padding: 4px 8px;
}

QToolBar::separator {
    width: 1px;
    background-color: #3D3D45;
    margin: 4px 6px;
}

QToolButton {
    background-color: transparent;
    color: #D6D6DC;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 8px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #323238;
    color: #FFFFFF;
    border: 1px solid #454550;
}

QToolButton:pressed {
    background-color: #E5252A;
    color: #FFFFFF;
}

QToolButton:checked {
    background-color: #E5252A;
    color: #FFFFFF;
    border: 1px solid #FF4B50;
    font-weight: bold;
}

/* Butonlar */
QPushButton {
    background-color: #2E2E34;
    color: #EAEAEF;
    border: 1px solid #42424C;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #3A3A42;
    color: #FFFFFF;
    border: 1px solid #585866;
}

QPushButton:pressed {
    background-color: #E5252A;
    color: #FFFFFF;
    border: 1px solid #FF4B50;
}

QPushButton:disabled {
    background-color: #1E1E22;
    color: #656570;
    border: 1px solid #2A2A30;
}

QPushButton#PrimaryButton {
    background-color: #E5252A;
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid #FF3B40;
}

QPushButton#PrimaryButton:hover {
    background-color: #F03439;
}

QPushButton#PrimaryButton:pressed {
    background-color: #C01B20;
}

/* Yan Paneller (Dock Widgets) */
QDockWidget {
    color: #E0E0E6;
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(float.png);
    font-weight: bold;
}

QDockWidget::title {
    background-color: #1F1F22;
    padding: 7px 10px;
    border-bottom: 1px solid #33333A;
    text-align: left;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Sekmeler (Tab Widget) */
QTabWidget::pane {
    border: 1px solid #33333A;
    background-color: #242428;
    border-radius: 0 0 4px 4px;
}

QTabBar::tab {
    background-color: #1C1C1F;
    color: #A0A0A8;
    padding: 7px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:hover {
    background-color: #2B2B30;
    color: #FFFFFF;
}

QTabBar::tab:selected {
    background-color: #242428;
    color: #FFFFFF;
    border-top: 2px solid #E5252A;
}

/* Giriş Kutuları ve Açılır Kutular */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1A1A1D;
    color: #F0F0F5;
    border: 1px solid #3A3A44;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #E5252A;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #E5252A;
    background-color: #222226;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #3A3A44;
}

QComboBox QAbstractItemView {
    background-color: #25252A;
    color: #EAEAEA;
    border: 1px solid #444450;
    selection-background-color: #E5252A;
}

/* Kaydırma Çubukları (Modern ve Zarif) */
QScrollBar:vertical {
    background-color: #18181A;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #383840;
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555562;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #18181A;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #383840;
    min-width: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555562;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Kaydırıcı (Slider) */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background-color: #383842;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background-color: #E5252A;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #FFFFFF;
    border: 2px solid #E5252A;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background-color: #FF7B80;
}

/* Durum Çubuğu */
QStatusBar {
    background-color: #18181A;
    color: #9C9CA6;
    border-top: 1px solid #2D2D32;
    font-size: 11px;
    padding: 3px 8px;
}

QStatusBar::item {
    border: none;
    padding: 2px 6px;
}

/* Etiketler ve Grup Kutuları */
QGroupBox {
    border: 1px solid #363640;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #D0D0DA;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: #202023;
}

/* Liste Görünümleri & Ağaçlar (Thumbnails vs.) */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #1A1A1D;
    border: 1px solid #303038;
    border-radius: 4px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    border-radius: 4px;
    padding: 6px;
    margin: 3px 2px;
}

QListWidget::item:hover {
    background-color: #2A2A32;
}

QListWidget::item:selected {
    background-color: #383844;
    border: 1px solid #E5252A;
    color: #FFFFFF;
}

/* İpucu (Tooltip) */
QToolTip {
    background-color: #141416;
    color: #FFFFFF;
    border: 1px solid #484855;
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 11px;
}
"""
