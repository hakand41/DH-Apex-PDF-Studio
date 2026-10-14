"""
DH-Apex PDF Studio - Ana Çalıştırma Dosyası
Adobe Acrobat Seviyesinde Profesyonel PDF Düzenleme ve Yönetim Stüdyosu
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dhapex_pdf.app import main

if __name__ == "__main__":
    main()
