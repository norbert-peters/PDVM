# 🔧 V2.0 GIT-SETUP - Schritt-für-Schritt Anleitung

**Ziel:** Parallele Entwicklung V0.9 (stable) und V2.0 (Neuaufbau) im selben Repository

---

## 📋 ÜBERSICHT

```
PDVM Repository
│
├── Branch: funktionierender-stand-29sept (✅ V0.9 STABLE)
│   └── Tag: v0.9-stable-2025-10-30
│       └── Nur noch Bugfixes!
│
└── Branch: v2.0-neuaufbau (🚀 V2.0 ENTWICKLUNG)
    └── Kompletter Neuaufbau mit Code-Übernahme aus V0.9
```

---

## 🚀 SETUP-SCHRITTE

### **SCHRITT 1: Aktuellen Stand sichern**

```powershell
# In MyApplication Verzeichnis
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication"

# Aktuellen Branch prüfen
git branch
# → sollte "funktionierender-stand-29sept" zeigen

# Alle Änderungen committen
git status
# Falls Änderungen vorhanden:
git add .
git commit -m "V0.9: Finaler Stand vor V2.0 Neuaufbau (30.10.2025)"

# Backup-Tag erstellen
git tag v0.9-stable-2025-10-30
git push origin v0.9-stable-2025-10-30
```

---

### **SCHRITT 2: V2.0 Branch erstellen**

```powershell
# Neuen Branch für V2.0 erstellen (basierend auf aktuellem Stand)
git checkout -b v2.0-neuaufbau

# Branch auf Server pushen (falls gewünscht)
git push -u origin v2.0-neuaufbau

# Bestätigung
git branch
# → sollte zeigen:
#   funktionierender-stand-29sept
# * v2.0-neuaufbau (← aktiver Branch)
```

---

### **SCHRITT 3: V2.0 Projekt-Dateien erstellen**

```powershell
# README für V2.0 erstellen
@"
# PDVM V2.0 - Neuaufbau mit linearer Architektur

**Branch:** v2.0-neuaufbau  
**Basis:** V0.9 (Tag: v0.9-stable-2025-10-30)  
**Status:** 📋 PLANUNG & DESIGN

## Siehe:
- V2_PROJEKT_PLAN.md - Vollständiger Projekt-Plan
- V2_ARCHITEKTUR.md - Detaillierte Architektur (TODO)
- V2_MENU_SYSTEM.md - Lineares Menü-Design (TODO)
"@ | Out-File -Encoding UTF8 README_V2.md

# Committen
git add README_V2.md V2_PROJEKT_PLAN.md V2_GIT_SETUP.md
git commit -m "V2.0: Initial Branch Setup + Projekt-Plan"
git push
```

---

## 🔄 ARBEITS-WORKFLOW

### **Zwischen Branches wechseln**

```powershell
# Zu V0.9 wechseln (z.B. um Code anzuschauen)
git checkout funktionierender-stand-29sept

# Zurück zu V2.0
git checkout v2.0-neuaufbau
```

### **Code aus V0.9 übernehmen**

```powershell
# Auf V2.0 Branch sein
git checkout v2.0-neuaufbau

# Einzelne Datei aus V0.9 holen
git checkout funktionierender-stand-29sept -- pdvm_datetime.py

# Umbenennen für V2.0
git mv pdvm_datetime.py v2_datetime.py

# Committen
git add v2_datetime.py
git commit -m "V2.0: Übernommen aus V0.9 - pdvm_datetime.py → v2_datetime.py"
```

### **Code vergleichen (V0.9 vs V2.0)**

```powershell
# Auf V2.0 Branch
git checkout v2.0-neuaufbau

# Datei mit V0.9 Version vergleichen
git diff funktionierender-stand-29sept -- pdvm_matrix_pipeline.py

# Kompletten Branch-Diff
git diff funktionierender-stand-29sept
```

---

## 🛡️ SICHERHEITS-REGELN

### **V0.9 Branch schützen**

```powershell
# Auf V0.9 wechseln
git checkout funktionierender-stand-29sept

# NUR BUGFIXES committen, keine neuen Features!
# Format: "V0.9 BUGFIX: Beschreibung"

git add bugfix_datei.py
git commit -m "V0.9 BUGFIX: Matrix-Pipeline Fehler bei leeren Zeilen"
git push
```

### **V2.0 Branch - Freie Entwicklung**

```powershell
# Auf V2.0 wechseln
git checkout v2.0-neuaufbau

# Beliebige Änderungen möglich
git add .
git commit -m "V2.0: Lineares Menü-System implementiert"
git push
```

---

## 📂 VERZEICHNIS-STRUKTUR (Empfehlung)

### **Während Entwicklung (beide Branches parallel nutzen)**

**OPTION 1: Branch-Wechsel (EINFACHER)**
```
C:\Users\norbe\OneDrive\Dokumente\MyApplication\
├── .git/                          # Git-Repository
├── main.py                        # Wechselt je nach Branch
├── pdvm_*.py                      # V0.9 Dateien (wenn auf V0.9 Branch)
├── v2_*.py                        # V2.0 Dateien (wenn auf V2.0 Branch)
└── Daten/
    └── datenbank.db               # Gemeinsame Datenbank (VORSICHT!)
```

**OPTION 2: Zwei separate Checkouts (SICHERER)**
```
C:\Users\norbe\OneDrive\Dokumente\
├── MyApplication\                 # V0.9 (checkout auf stable Branch)
│   ├── .git/ → Branch: funktionierender-stand-29sept
│   ├── main.py
│   └── Daten/datenbank.db
│
└── MyApplication_V2\              # V2.0 (checkout auf v2.0 Branch)
    ├── .git/ → Branch: v2.0-neuaufbau
    ├── v2_main.py
    └── Daten/datenbank_v2.db      # Separate Test-DB!
```

**Setup für Option 2:**
```powershell
cd "C:\Users\norbe\OneDrive\Dokumente"

# V2.0 Arbeitsbereich clonen
git clone "C:\Users\norbe\OneDrive\Dokumente\MyApplication" MyApplication_V2
cd MyApplication_V2
git checkout v2.0-neuaufbau

# Test-Datenbank kopieren
Copy-Item ..\MyApplication\Daten\datenbank.db Daten\datenbank_v2.db
```

---

## 🔍 NÜTZLICHE GIT-BEFEHLE

### **Status prüfen**
```powershell
git status                         # Geänderte Dateien
git branch                         # Alle Branches
git log --oneline --graph --all   # Grafische Historie
```

### **Branch-Vergleich**
```powershell
# Unterschiede zwischen Branches
git diff funktionierender-stand-29sept v2.0-neuaufbau

# Nur Datei-Namen (was ist unterschiedlich?)
git diff --name-only funktionierender-stand-29sept v2.0-neuaufbau

# Nur neue Dateien in V2.0
git diff --name-status funktionierender-stand-29sept v2.0-neuaufbau | Select-String "^A"
```

### **Code-Übernahme selektiv**
```powershell
# Mehrere Dateien auf einmal
git checkout funktionierender-stand-29sept -- pdvm_datetime.py pdvm_matrix_pipeline.py

# Ganzes Verzeichnis
git checkout funktionierender-stand-29sept -- pdvm_ui/
```

---

## ⚠️ HÄUFIGE PROBLEME

### **Problem 1: Ungespeicherte Änderungen beim Branch-Wechsel**
```powershell
# Fehler: "Please commit your changes or stash them before you switch branches"

# LÖSUNG A: Committen
git add .
git commit -m "WIP: Zwischenstand"

# LÖSUNG B: Stashen (temporär weglegen)
git stash
git checkout anderer-branch
git stash pop  # Änderungen zurückholen
```

### **Problem 2: Datenbank-Konflikte**
```powershell
# PROBLEM: Beide Branches nutzen gleiche datenbank.db

# LÖSUNG: Separate DBs für V2.0
Copy-Item Daten\datenbank.db Daten\datenbank_v2.db

# In V2.0 Code: DB-Pfad anpassen
# V0.9: db = PdvmDatenbank("Daten/datenbank.db")
# V2.0: db = V2Database("Daten/datenbank_v2.db")
```

### **Problem 3: Merge-Konflikte**
```powershell
# Falls versehentlich merged wurde
git merge --abort

# V0.9 und V2.0 sollten NIEMALS gemerged werden!
# Nur einzelne Dateien mit "git checkout" übernehmen
```

---

## 🎯 CHECKLISTE: Setup abgeschlossen?

- [ ] Tag `v0.9-stable-2025-10-30` erstellt
- [ ] Branch `v2.0-neuaufbau` erstellt und gepusht
- [ ] `README_V2.md` existiert
- [ ] `V2_PROJEKT_PLAN.md` committet
- [ ] Kann zwischen Branches wechseln (`git checkout`)
- [ ] Weiß wie Code aus V0.9 übernommen wird
- [ ] Separate Datenbank für V2.0 vorbereitet (Option 2)

---

## 📞 NÄCHSTE SCHRITTE

Nach erfolgreichem Setup:

1. ✅ Git-Setup abgeschlossen
2. ⏳ `V2_ARCHITEKTUR.md` erstellen (Detailplanung)
3. ⏳ `V2_MENU_SYSTEM.md` erstellen (Lineares Menü-Design)
4. ⏳ Ersten Prototyp coden (`v2_menu_system.py`)

---

**WICHTIG:** Falls Probleme auftauchen:
```powershell
# Aktuellen Zustand sichern
git status
git log --oneline -n 5

# Screenshot machen und Fehlermeldung notieren
```

**KONTAKT:** Bei Fragen einfach melden! 🚀
