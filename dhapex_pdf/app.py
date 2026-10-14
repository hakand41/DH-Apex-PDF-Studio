"""
Nexora PDF Studio - Uygulama Başlatıcı
High-DPI ayarları, QSS tema yüklemesi ve ana döngü.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication

from dhapex_pdf import APP_NAME, APP_VERSION, APP_ORGANIZATION
from dhapex_pdf.styles import DARK_THEME_QSS
from dhapex_pdf.main_window import MainWindow
from dhapex_pdf.icons import IconFactory

def main():
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    if hasattr(QGuiApplication, "setHighDpiScaleFactorRoundingPolicy"):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setWindowIcon(IconFactory.get("app_icon", 64))
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    app.setStyleSheet(DARK_THEME_QSS)
    
    window = MainWindow()
    
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.open_pdf(sys.argv[1])
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
