# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für PDVM-System v0.9
===========================================

Erstellt eine standalone EXE-Datei mit allen Abhängigkeiten.

VERWENDUNG:
-----------
pyinstaller pdvm.spec

AUSGABE:
--------
dist/PDVM-System-v0.9.exe (ca. 80-100 MB)

AUTHOR: Norbert Peters
DATE: 06.11.2025
VERSION: 0.9
"""

block_cipher = None

# Alle Python-Dateien sammeln
a = Analysis(
    ['pdvm_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Daten-Verzeichnis (Datenbanken)
        ('Daten', 'Daten'),
        
        # Handlers-Verzeichnis (KRITISCH!)
        ('handlers', 'handlers'),
        
        # Dokumentation
        ('VERSION_0_9_RELEASE.md', '.'),
        ('README.md', '.'),
        ('INSTALLATION_GUIDE.md', '.'),
        
        # Copilot Instructions (optional)
        ('.github/copilot-instructions.md', '.github'),
    ],
    hiddenimports=[
        # PyQt5 Module
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtSql',
        
        # Security
        'bcrypt',
        
        # Standard Library (explizit für PyInstaller)
        'sqlite3',
        'json',
        'logging',
        'datetime',
        'pathlib',
        're',
        'uuid',
        'hashlib',
        
        # PDVM Module (alle pdvm_* Dateien)
        'pdvm_central_systemsteuerung',
        'pdvm_datenbank',
        'pdvm_central_datenbank',
        'pdvm_datetime',
        'pdvm_systemstart',
        'pdvm_login_dialog',
        'pdvm_mandanten_dialog',
        'pdvm_menu_handler',
        'pdvm_menu_builder',
        'pdvm_menu_storage',
        'pdvm_menu_schema',
        'pdvm_command_handler',
        'pdvm_view_controller',
        'pdvm_view_dialog',
        'pdvm_view_ui',
        'pdvm_pipeline',
        'pdvm_input_control',
        'pdvm_input_controls_manager',
        'pdvm_input_type_base',
        'pdvm_input_type_text',
        'pdvm_input_type_datetime',
        'pdvm_input_type_dropdown',
        'pdvm_input_type_viewtable',
        'pdvm_einfach_filter_dialog',
        'pdvm_komplex_filter_dialog',
        'pdvm_schnellsuche_manager',
        'pdvm_filter_reset_manager',
        'pdvm_genereller_dialog',
        'pdvm_dialog_widget',
        'pdvm_autonome_view',
        
        # Handlers
        'handlers.handler_open_view',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Ungenutzte Module ausschließen (reduziert Größe)
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Python Bytecode
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable erstellen
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDVM-System-v0.9',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX Kompression (reduziert Größe)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Kein Konsolen-Fenster (nur GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Icon-Datei hinzufügen wenn vorhanden
    version_file=None,  # TODO: Version-Info hinzufügen
)

# Optionale Sammlung (für --onedir Modus)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='PDVM-System-v0.9',
# )
