# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_editor.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'pymupdf',
        'PIL',
        'dhapex_pdf',
        'dhapex_pdf.styles',
        'dhapex_pdf.icons',
        'dhapex_pdf.models',
        'dhapex_pdf.commands',
        'dhapex_pdf.canvas',
        'dhapex_pdf.thumbnails',
        'dhapex_pdf.search',
        'dhapex_pdf.inspector',
        'dhapex_pdf.dialogs',
        'dhapex_pdf.main_window',
        'dhapex_pdf.app',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DHApexPDFStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',
)
