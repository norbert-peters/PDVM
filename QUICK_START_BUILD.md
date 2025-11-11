# 🚀 PDVM-System v0.9 - Quick Start Guide

## ⚡ SCHNELLSTART: Standalone EXE erstellen

### Schritt 1: Vorbereitung

```powershell
# 1. Virtual Environment aktivieren (falls vorhanden)
.\.venv\Scripts\Activate.ps1

# 2. PyInstaller installieren
pip install pyinstaller

# 3. UPX herunterladen (optional, für kleinere EXE)
# https://upx.github.io/
# UPX in PATH oder ins Projekt-Verzeichnis entpacken
```

### Schritt 2: EXE erstellen

**Option A: Mit Build-Script (empfohlen)**
```powershell
.\build_exe.ps1
```

**Option B: Manuell**
```powershell
pyinstaller pdvm.spec
```

### Schritt 3: Testen
```powershell
.\dist\PDVM-System-v0.9.exe
```

### Schritt 4: Windows-Installer erstellen (optional)

```powershell
# 1. Inno Setup installieren
winget install JRSoftware.InnoSetup

# 2. Installer kompilieren
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss

# Installer befindet sich in: installer\PDVM-System-v0.9-Setup.exe
```

### Schritt 5: Zum GitHub Release hochladen

```powershell
# Mit GitHub CLI
gh release upload v0.9 dist/PDVM-System-v0.9.exe
gh release upload v0.9 installer/PDVM-System-v0.9-Setup.exe

# Oder manuell auf GitHub:
# https://github.com/norbert-peters/PDVM/releases/edit/v0.9
```

---

## 📦 OPTION 2: Als Python-Package installieren

### Für End-User

```powershell
# 1. Release herunterladen
# https://github.com/norbert-peters/PDVM/releases/tag/v0.9

# 2. Entpacken
# Rechtsklick auf ZIP → "Alle extrahieren"

# 3. In Verzeichnis wechseln
cd PDVM-0.9

# 4. Abhängigkeiten installieren
pip install -r requirements.txt

# 5. Datenbank initialisieren
python pdvm_init_auth_database.py
python pdvm_init_mandanten_databases.py

# 6. Starten
python pdvm_main.py
```

---

## 🎯 EMPFOHLENER WORKFLOW

### Für Distribution:

1. ✅ **Standalone EXE erstellen** → `build_exe.ps1`
2. ✅ **Windows Installer erstellen** → Inno Setup
3. ✅ **Beide zum Release hochladen**

### Downloads für User:

- **Einfach**: `PDVM-System-v0.9-Setup.exe` (ca. 80-100 MB)
- **Portabel**: `PDVM-System-v0.9.exe` (ca. 80-100 MB)
- **Entwickler**: Source Code (ZIP/TAR.GZ)

---

## 🐛 TROUBLESHOOTING

### Problem: "Failed to execute script"
```powershell
# Lösung: Console-Modus aktivieren für Fehler-Meldungen
# In pdvm.spec ändern: console=True
pyinstaller pdvm.spec
```

### Problem: "ModuleNotFoundError"
```powershell
# Lösung: Modul zu hiddenimports hinzufügen
# In pdvm.spec unter hiddenimports ergänzen
```

### Problem: "EXE zu groß"
```powershell
# Lösung 1: UPX Kompression
# UPX herunterladen und in PATH

# Lösung 2: Ausschließen ungenutzte Module
# In pdvm.spec unter excludes ergänzen
```

### Problem: "Datenbank nicht gefunden"
```powershell
# Lösung: Daten-Ordner muss mit kopiert werden
# Prüfen: datas=[('Daten', 'Daten'), ...]
```

---

## 📊 DATEIGRÖSSEN (Ungefähr)

- Source Code (ZIP): ~5 MB
- Standalone EXE: ~80-100 MB
- Installer: ~85-105 MB
- Nach Installation: ~120-150 MB

---

## ✅ CHECKLISTE FÜR RELEASE

- [ ] EXE mit `build_exe.ps1` erstellt
- [ ] EXE getestet (Login, View öffnen, Dialog)
- [ ] Installer mit Inno Setup erstellt
- [ ] Installer getestet (Installation, Deinstallation)
- [ ] Beide Dateien zum GitHub Release hochgeladen
- [ ] Release Notes aktualisiert mit Download-Links
- [ ] Test-Zugänge dokumentiert (admin@super.de / admin)

---

## 🎁 RELEASE-BESCHREIBUNG AKTUALISIEREN

Nach Upload der Binaries, Release-Beschreibung erweitern:

```markdown
## 📦 Downloads

### Windows Installer (Empfohlen)
- **PDVM-System-v0.9-Setup.exe** (85 MB)
  - Automatische Installation
  - Startmenü-Eintrag
  - Desktop-Icon (optional)
  
### Portable EXE
- **PDVM-System-v0.9.exe** (80 MB)
  - Keine Installation nötig
  - Direkt ausführbar
  - Für USB-Stick geeignet

### Source Code
- **Source code (zip)** - Für Entwickler
- **Source code (tar.gz)** - Für Entwickler

## 🔐 Test-Zugänge
- Admin: `admin@super.de` / `admin`
- User: `user@super.de` / `user`
```

---

**Quick Commands:**

```powershell
# Alles auf einmal (wenn Inno Setup installiert)
.\build_exe.ps1
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
gh release upload v0.9 dist/PDVM-System-v0.9.exe installer/PDVM-System-v0.9-Setup.exe
```
