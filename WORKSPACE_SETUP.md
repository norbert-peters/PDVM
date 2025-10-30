# 🗂️ WORKSPACE-STRUKTUR - PDVM V0.9 & V2.0

**Erstellt:** 30.10.2025  
**Status:** ✅ SETUP ABGESCHLOSSEN

---

## 📂 VERZEICHNIS-ÜBERSICHT

```
C:\Users\norbe\OneDrive\Dokumente\
│
├── MyApplication\              🚀 V2.0 NEUAUFBAU (AKTIV)
│   ├── .git/
│   ├── Branch: v2.0-neuaufbau
│   ├── README_V2.md
│   ├── V2_PROJEKT_PLAN.md
│   ├── V2_GIT_SETUP.md
│   ├── main.py                (wird V2 werden)
│   ├── v2_*                   (neue V2.0 Dateien)
│   └── Daten/
│       └── datenbank.db       ⚠️ PRODUKTIV-DB (mit Vorsicht!)
│
└── MyApplication_V0.9\         ✅ V0.9 STABLE (REFERENZ)
    ├── .git/
    ├── Branch: funktionierender-stand-29sept
    ├── Tag: v0.9-stable-2025-10-30
    ├── main.py                (V0.9 Original)
    ├── pdvm_*                 (alle V0.9 Module)
    └── Daten/
        └── datenbank.db       ✅ V0.9 Produktiv-DB
```

---

## 🎯 VERWENDUNG

### **V2.0 Entwicklung** (HAUPTARBEIT)
```powershell
# In VS Code öffnen
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication"
code .

# Starten
python main.py  # Später: python v2_main.py
```

### **V0.9 Referenz** (NUR LESEN / BUGFIXES)
```powershell
# In separatem VS Code-Fenster öffnen
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication_V0.9"
code .

# Starten (zum Testen/Vergleichen)
python main.py
```

---

## 🔄 CODE-ÜBERNAHME aus V0.9

### **Methode 1: Git Checkout (EMPFOHLEN)**
```powershell
# Im V2.0 Workspace (MyApplication/)
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication"

# Datei aus V0.9 holen
git checkout funktionierender-stand-29sept -- pdvm_datetime.py

# Umbenennen für V2.0
git mv pdvm_datetime.py v2_datetime.py
git commit -m "V2.0: Übernommen - pdvm_datetime.py → v2_datetime.py"
```

### **Methode 2: Direktes Kopieren**
```powershell
# Datei kopieren von V0.9 nach V2.0
Copy-Item `
  "C:\Users\norbe\OneDrive\Dokumente\MyApplication_V0.9\pdvm_matrix_pipeline.py" `
  "C:\Users\norbe\OneDrive\Dokumente\MyApplication\v2_matrix_pipeline.py"
```

---

## 🛡️ DATENBANK-STRATEGIE

### **PROBLEM:** Beide Workspaces nutzen gleiche DB!

### **LÖSUNG 1: Separate Test-DB für V2.0 erstellen**
```powershell
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication"

# Produktiv-DB als V2-Test-DB kopieren
Copy-Item Daten\datenbank.db Daten\datenbank_v2_test.db

# In V2.0 Code: DB-Pfad anpassen
# Alter Code: db = PdvmDatenbank("Daten/datenbank.db")
# Neuer Code: db = V2Database("Daten/datenbank_v2_test.db")
```

### **LÖSUNG 2: Backup vor jedem Test**
```powershell
# Vor V2.0 Tests: Backup erstellen
Copy-Item Daten\datenbank.db "Daten\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

---

## ⚠️ WICHTIGE REGELN

### **V0.9 Workspace (MyApplication_V0.9/)**
- ✅ Nur für Referenz und Bugfixes
- ✅ Keine experimentellen Änderungen
- ✅ NUR auf Branch `funktionierender-stand-29sept`
- ✅ Commits mit "V0.9 BUGFIX:" Prefix

### **V2.0 Workspace (MyApplication/)**
- ✅ Freie Entwicklung
- ✅ Nur auf Branch `v2.0-neuaufbau`
- ✅ Commits mit "V2.0:" Prefix
- ⚠️ Test-Datenbank verwenden!

---

## 🔍 GIT-BEFEHLE

### **Status prüfen**
```powershell
# Im jeweiligen Workspace
git status
git branch --show-current
```

### **Zwischen Workspaces wechseln**
```powershell
# Zu V2.0 wechseln
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication"

# Zu V0.9 wechseln
cd "C:\Users\norbe\OneDrive\Dokumente\MyApplication_V0.9"
```

### **Updates holen**
```powershell
# In beiden Workspaces regelmäßig:
git pull
```

---

## 🚀 NÄCHSTE SCHRITTE

1. ✅ Workspace-Setup abgeschlossen
2. ⏳ Test-Datenbank für V2.0 erstellen
3. ⏳ V2_ARCHITEKTUR.md schreiben
4. ⏳ Ersten V2.0 Prototyp erstellen

---

## 🔧 VS CODE SETUP

### **Beide Workspaces in VS Code öffnen**

**Option A: Multi-Root Workspace**
```
File → Add Folder to Workspace...
→ MyApplication hinzufügen
→ MyApplication_V0.9 hinzufügen
→ Workspace speichern als: PDVM_V09_V20.code-workspace
```

**Option B: Zwei VS Code Fenster**
```powershell
# Fenster 1: V2.0
code "C:\Users\norbe\OneDrive\Dokumente\MyApplication"

# Fenster 2: V0.9
code "C:\Users\norbe\OneDrive\Dokumente\MyApplication_V0.9"
```

---

## 📊 SPEICHERPLATZ

**HINWEIS:** Beide Workspaces teilen Git-Objekte via Hardlinks.
- Tatsächlicher Mehrverbrauch: ~10-20% statt 100%
- Volle Git-Historie in beiden Verzeichnissen verfügbar

---

**Bei Fragen:** Siehe [V2_GIT_SETUP.md](V2_GIT_SETUP.md) oder [V2_PROJEKT_PLAN.md](V2_PROJEKT_PLAN.md)

**Happy Coding! 🚀**
