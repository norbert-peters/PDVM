# 🔧 GitHub Release v0.9.1 - Handler Bugfix

## KRITISCHER BUGFIX für v0.9

**Problem in v0.9**: Handler-Verzeichnis fehlte in standalone EXE → Menü-Aktionen funktionierten nicht

**Behoben in v0.9.1**: Handler werden jetzt korrekt eingebettet → Alle Menü-Aktionen funktionieren

---

## 📋 Release erstellen (GitHub Web UI)

### Schritt 1: GitHub öffnen
```
https://github.com/norbert-peters/PDVM/releases/new
```

### Schritt 2: Tag auswählen
- **Choose a tag**: `v0.9.1`
- Tag ist bereits gepusht (06.11.2025)

### Schritt 3: Release-Titel
```
🔧 PDVM-System Version 0.9.1 - Handler Bugfix
```

### Schritt 4: Release-Beschreibung (kopieren)

```markdown
## 🔧 Bugfix Release v0.9.1

**Kritischer Fix für standalone EXE** - Upgrade von v0.9 dringend empfohlen!

### 🐛 Behobener Bug

**Problem in v0.9**:
- Handler-Verzeichnis fehlte in PyInstaller-Build
- Menü-Aktionen funktionierten nicht (Testbereich, Administration, Logout)
- Fehlermeldung: `Handler 'open_app_menu' nicht registriert!`

**Root Cause**:
```python
# pdvm.spec v0.9 (FALSCH)
datas=[
    ('Daten', 'Daten'),
    # handlers/ fehlte! ❌
]

# pdvm.spec v0.9.1 (KORRIGIERT)
datas=[
    ('Daten', 'Daten'),
    ('handlers', 'handlers'),  # ✅ Hinzugefügt!
]
```

### ✅ Was wurde korrigiert

1. **pdvm.spec**: `('handlers', 'handlers')` zu `datas` hinzugefügt
2. **INSTALLATION_STANDALONE_EXE.md**: Vollständige Installationsanleitung
3. **Tests**: Alle Handler funktionieren jetzt korrekt

### 🧪 Getestet

- ✅ EXE startet korrekt
- ✅ Login funktioniert
- ✅ Handler werden gefunden
- ✅ Testbereich öffnet sich
- ✅ Administration öffnet sich
- ✅ Logout funktioniert
- ✅ Alle Menü-Aktionen verfügbar

### 📦 Installation

#### Upgrade von v0.9
```
1. Alte EXE löschen
2. Neue v0.9.1 EXE herunterladen
3. Fertig! (keine weiteren Schritte)
```

#### Neuinstallation
```
1. PDVM-System-v0.9.1.exe herunterladen
2. In beliebiges Verzeichnis kopieren
3. Doppelklick zum Starten
```

**Keine zusätzlichen Dateien erforderlich!**

### ⚠️ Bekannte Einschränkungen

**Datenbank im TEMP-Verzeichnis**:
- Datenbank wird nach `%TEMP%\_MEI[random]\Daten\` entpackt
- Daten gehen nach jedem EXE-Neustart verloren
- **Wird in v1.0 behoben**: Persistente Datenbank im Benutzerverzeichnis

### 📊 EXE-Details

- **Datei**: PDVM-System-v0.9.1.exe
- **Größe**: 38,12 MB
- **Python**: 3.12.8
- **PyInstaller**: 6.16.0
- **Modus**: Single-file (--onefile)
- **Handler**: ✅ Alle eingebettet

### 🔗 Commits

- Commit: `b736eff5` - Handler-Verzeichnis in EXE einbetten
- Tag: `v0.9.1` - Bugfix Release

### 📚 Dokumentation

Siehe [INSTALLATION_STANDALONE_EXE.md](INSTALLATION_STANDALONE_EXE.md) für:
- Detaillierte Installationsanleitung
- Troubleshooting
- Dateistruktur (intern)
- Roadmap v1.0

### 🎯 Roadmap v1.0

**Geplante Features**:
1. Persistente Datenbank außerhalb TEMP
2. Konfigurations-Datei für Pfade
3. Windows Installer (.msi)
4. Icon für die EXE
5. Automatische Updates

### 💬 Support

Bei Problemen bitte Issue erstellen:
https://github.com/norbert-peters/PDVM/issues

---

**Version**: 0.9.1  
**Datum**: 06.11.2025  
**Autor**: Norbert Peters  
**Lizenz**: Proprietär
```

### Schritt 5: Asset hochladen

**WICHTIG**: EXE-Datei zum Release hinzufügen!

```
1. Klick auf "Attach binaries by dropping them here or selecting them"
2. Datei auswählen: dist\PDVM-System-v0.9.exe
3. Hochladen warten
4. Umbenennen zu: PDVM-System-v0.9.1.exe (für Klarheit)
```

### Schritt 6: Release veröffentlichen

- **This is a pre-release**: ❌ NICHT ankreuzen (v0.9.1 ist stabil)
- **Set as the latest release**: ✅ Ankreuzen
- Klick auf **Publish release**

---

## 🎯 Alternative: GitHub CLI

Falls Sie `gh` CLI installiert haben:

```powershell
# Release erstellen
gh release create v0.9.1 `
  --title "🔧 PDVM-System Version 0.9.1 - Handler Bugfix" `
  --notes-file GITHUB_RELEASE_v0.9.1_INSTRUCTIONS.md `
  dist/PDVM-System-v0.9.exe#PDVM-System-v0.9.1.exe

# Release als latest markieren
gh release edit v0.9.1 --latest
```

---

## ✅ Verifizierung

Nach Veröffentlichung prüfen:

1. **Release-Seite**: https://github.com/norbert-peters/PDVM/releases/tag/v0.9.1
2. **Asset verfügbar**: PDVM-System-v0.9.1.exe (38,12 MB)
3. **Latest Badge**: ✅ Grün (latest release)
4. **Download-Link funktioniert**

---

## 📢 Changelog v0.9 → v0.9.1

```
CHANGED:
- pdvm.spec: handlers/ zu datas hinzugefügt

ADDED:
- INSTALLATION_STANDALONE_EXE.md: Vollständige Anleitung

FIXED:
- Handler wurden nicht in EXE eingebettet
- Menü-Aktionen funktionierten nicht
- Fehlermeldung "Handler nicht registriert"

TESTED:
- Login: ✅
- Mandanten-Auswahl: ✅
- Startmenü: ✅
- Testbereich: ✅
- Administration: ✅
- Logout: ✅
```

---

## 🚀 Nächste Schritte

1. **Release erstellen** (oben beschrieben)
2. **EXE hochladen** als Asset
3. **Testen**: Download von GitHub testen
4. **Ankündigen**: ggf. in Projekt-README verlinken

---

**Status**: Commit & Tag gepusht ✅  
**Bereit für**: Release-Erstellung  
**Priorität**: HOCH (kritischer Bugfix)
