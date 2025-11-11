# 📦 PDVM-System v0.9 - Installations-Anleitung

## 🎯 INSTALLATION VOM GITHUB RELEASE

### Variante A: Direkt von GitHub (Empfohlen)

```powershell
# 1. Release herunterladen und entpacken
# Gehen Sie zu: https://github.com/norbert-peters/PDVM/releases/tag/v0.9
# Klicken Sie auf "Source code (zip)" oder "Source code (tar.gz)"
# Entpacken Sie das Archiv in ein Verzeichnis Ihrer Wahl, z.B.:
# C:\Programme\PDVM-v0.9\

# 2. In das Verzeichnis wechseln
cd C:\Programme\PDVM-v0.9

# 3. Virtual Environment erstellen (empfohlen)
python -m venv .venv

# 4. Virtual Environment aktivieren
.venv\Scripts\Activate.ps1

# 5. Abhängigkeiten installieren
pip install PyQt5 bcrypt

# 6. Datenbank initialisieren
python pdvm_init_auth_database.py
python pdvm_init_mandanten_databases.py

# 7. Anwendung starten
python pdvm_main.py
```

### Variante B: Mit Git Clone

```powershell
# 1. Repository klonen
git clone https://github.com/norbert-peters/PDVM.git
cd PDVM

# 2. Zum Tag v0.9 wechseln
git checkout v0.9

# 3. Virtual Environment erstellen
python -m venv .venv
.venv\Scripts\Activate.ps1

# 4. Abhängigkeiten installieren
pip install PyQt5 bcrypt

# 5. Datenbank initialisieren
python pdvm_init_auth_database.py
python pdvm_init_mandanten_databases.py

# 6. Anwendung starten
python pdvm_main.py
```

---

## 🚀 STANDALONE EXE ERSTELLEN (Option 2)

Wenn Sie eine **ausführbare .exe-Datei** erstellen möchten, die ohne Python-Installation läuft:

### Mit PyInstaller

```powershell
# 1. PyInstaller installieren
pip install pyinstaller

# 2. EXE erstellen
pyinstaller --name="PDVM-System-v0.9" `
            --onefile `
            --windowed `
            --icon=icon.ico `
            --add-data "Daten;Daten" `
            pdvm_main.py

# Die EXE befindet sich dann in: dist\PDVM-System-v0.9.exe
```

### Erweiterte PyInstaller-Konfiguration

Erstellen Sie eine `pdvm.spec` Datei für mehr Kontrolle:

```python
# pdvm.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdvm_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Daten', 'Daten'),
        ('*.md', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'bcrypt',
        'sqlite3',
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
    name='PDVM-System-v0.9',
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
    icon='icon.ico',
)
```

Dann ausführen:
```powershell
pyinstaller pdvm.spec
```

---

## 📦 INSTALLER ERSTELLEN (Option 3)

### Mit Inno Setup (Windows Installer)

1. **Inno Setup herunterladen**: https://jrsoftware.org/isdl.php

2. **Installer-Script erstellen** (`setup.iss`):

```iss
[Setup]
AppName=PDVM-System
AppVersion=0.9
DefaultDirName={autopf}\PDVM-System
DefaultGroupName=PDVM-System
OutputBaseFilename=PDVM-System-v0.9-Setup
Compression=lzma2
SolidCompression=yes
OutputDir=installer

[Files]
Source: "dist\PDVM-System-v0.9.exe"; DestDir: "{app}"
Source: "Daten\*"; DestDir: "{app}\Daten"; Flags: recursesubdirs
Source: "README.md"; DestDir: "{app}"
Source: "VERSION_0_9_RELEASE.md"; DestDir: "{app}"

[Icons]
Name: "{group}\PDVM-System"; Filename: "{app}\PDVM-System-v0.9.exe"
Name: "{autodesktop}\PDVM-System"; Filename: "{app}\PDVM-System-v0.9.exe"

[Run]
Filename: "{app}\PDVM-System-v0.9.exe"; Description: "PDVM-System starten"; Flags: postinstall nowait skipifsilent
```

3. **Kompilieren**: Öffnen Sie `setup.iss` in Inno Setup und klicken Sie auf "Compile"

---

## 🐳 DOCKER CONTAINER (Option 4)

Falls Sie Docker bevorzugen:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Datenbank initialisieren
RUN python pdvm_init_auth_database.py && \
    python pdvm_init_mandanten_databases.py

# Port exposieren (falls Web-UI geplant)
EXPOSE 8000

# Startkommando
CMD ["python", "pdvm_main.py"]
```

```powershell
# Build
docker build -t pdvm-system:v0.9 .

# Run
docker run -it -v ${PWD}/Daten:/app/Daten pdvm-system:v0.9
```

---

## 📋 REQUIREMENTS.TXT ERSTELLEN

Erstellen Sie eine `requirements.txt` für einfache Installation:

```powershell
# Aktuelle Abhängigkeiten exportieren
pip freeze > requirements.txt
```

Oder manuell erstellen:

```txt
PyQt5>=5.15.0
bcrypt>=4.0.0
```

---

## 🎁 GITHUB RELEASE MIT BINARIES

Nachdem Sie die EXE erstellt haben, können Sie sie zum Release hinzufügen:

### 1. EXE hochladen

```powershell
# Mit GitHub CLI
gh release upload v0.9 dist/PDVM-System-v0.9.exe

# Oder manuell:
# - Gehen Sie zu: https://github.com/norbert-peters/PDVM/releases/tag/v0.9
# - Klicken Sie auf "Edit release"
# - Ziehen Sie die EXE-Datei in den "Attach binaries" Bereich
```

### 2. Installer hochladen

```powershell
gh release upload v0.9 installer/PDVM-System-v0.9-Setup.exe
```

---

## ✅ EMPFOHLENER WORKFLOW

### Für End-User (Nicht-Entwickler):

1. **Standalone EXE erstellen** (PyInstaller)
2. **Windows Installer erstellen** (Inno Setup)
3. **Zum GitHub Release hochladen**

Benutzer können dann einfach:
- `PDVM-System-v0.9-Setup.exe` herunterladen
- Installer ausführen
- Anwendung starten

### Für Entwickler:

1. **Source Code vom Release herunterladen**
2. **Virtual Environment erstellen**
3. **Dependencies installieren**
4. **Python direkt ausführen**

---

## 🔧 TROUBLESHOOTING

### Problem: "Python nicht gefunden"
```powershell
# Python installieren
winget install Python.Python.3.11
```

### Problem: "PyQt5 Installation fehlgeschlagen"
```powershell
# Aktualisiere pip
python -m pip install --upgrade pip

# Installiere Build-Tools
pip install wheel setuptools
```

### Problem: "Datenbank nicht gefunden"
```powershell
# Datenbank neu initialisieren
python pdvm_init_auth_database.py
```

---

## 📞 SUPPORT

Bei Problemen:
- **Issues**: https://github.com/norbert-peters/PDVM/issues
- **Dokumentation**: `VERSION_0_9_RELEASE.md`

---

**Version**: 0.9  
**Datum**: 06.11.2025  
**Status**: Production Ready (Beta)
