# 🚀 PDVM V2.0 - PROJEKT-PLAN

**Erstellt:** 30.10.2025  
**Status:** 📋 PLANUNG  
**Ziel:** Kompletter Neuaufbau mit linearer Architektur

---

## 🎯 HAUPTZIELE

### 1. Lineares Menü-System
**PROBLEM V0.9:**
- Multi-Tree Struktur (`PD_grund`, `PD_menu`, `PD_zusatz`)
- Komplexer CommandHandler
- Template-System schwer wartbar

**LÖSUNG V2.0:**
- Flache JSON-Struktur mit Parent-Referenzen
- Einheitlicher Command-Dispatcher
- Menü-Editor als Standard-View mit Controls

### 2. System-Tabellen-Konvention
**PROBLEM V0.9:**
- Keine Trennung System vs. User-Tabellen
- Verwechslungsgefahr

**LÖSUNG V2.0:**
```
sys_menudaten       # System-Tabellen mit 'sys_' Prefix
sys_viewdaten
sys_framedaten
sys_dialogdaten
sys_users           # NEU: Zentrale User-Verwaltung

kunde               # User-Tabellen OHNE Prefix
artikel
rechnung
```

### 3. Zentrale Authentifizierung
**PROBLEM V0.9:**
- Login direkt in Datenbank
- Keine Mandantentrennung
- Keine HTTP-API

**LÖSUNG V2.0:**
```
┌─────────────────┐
│  Login-Service  │ ← HTTP REST API
│  (Flask/FastAPI)│
└────────┬────────┘
         │
         ├─→ sys_users (Authentifizierung)
         ├─→ sys_mandanten (Mandanten-Liste)
         └─→ sys_berechtigungen (Rollen)

User wählt → Mandant → App lädt mandantenspezifische DB
```

### 4. Security-Layer (sec_id)
**PROBLEM V0.9:**
- Keine Datensatz-Berechtigungen
- Nur User-Level Rechte

**LÖSUNG V2.0:**
```sql
-- JEDE User-Tabelle bekommt:
CREATE TABLE kunde (
    uid TEXT PRIMARY KEY,
    sec_id TEXT NOT NULL,  -- GUID → sys_security_profiles
    name TEXT,
    ...
);

-- Security-Profile
CREATE TABLE sys_security_profiles (
    uid TEXT PRIMARY KEY,
    name TEXT,              -- z.B. "Vertrieb Lesen", "Admin Vollzugriff"
    read_roles TEXT,        -- JSON: ["vertrieb", "admin"]
    write_roles TEXT,       -- JSON: ["admin"]
    delete_roles TEXT       -- JSON: ["admin"]
);
```

---

## 📁 PROJEKT-STRUKTUR

### GIT-STRATEGIE: Branch-Modell

```
Repository: PDVM
│
├── Branch: funktionierender-stand-29sept
│   └── Tag: v0.9-stable-2025-10-30
│       ├── main.py                    ✅ FROZEN (nur Bugfixes)
│       ├── pdvm_*.py                  ✅ Referenz für Code-Übernahme
│       └── Daten/datenbank.db         ✅ Produktiv-Daten
│
└── Branch: v2.0-neuaufbau             🚀 AKTIVE ENTWICKLUNG
    ├── README_V2.md
    ├── V2_ARCHITEKTUR.md
    ├── v2_main.py                     NEU: Entry Point V2
    ├── v2_auth_service/               NEU: HTTP Auth
    │   ├── __init__.py
    │   ├── api.py                     (Flask/FastAPI)
    │   └── models.py
    ├── v2_core/                       NEU: Kern-System
    │   ├── database_manager.py        (sys_ Tabellen)
    │   ├── security_manager.py        (sec_id Logik)
    │   ├── menu_system.py             (Linear!)
    │   └── command_dispatcher.py
    ├── v2_ui/                         NEU: UI-Layer
    │   ├── view_controller.py         (aus V0.9 übernehmen)
    │   ├── dialog_manager.py
    │   └── matrix_pipeline.py         ✅ AUS V0.9 ÜBERNEHMEN!
    ├── migrations/                    NEU: Daten-Migration
    │   ├── migrate_v09_to_v20.py
    │   └── test_migration.py
    └── tests/                         NEU: Tests
        ├── test_menu_system.py
        ├── test_auth.py
        └── test_security.py
```

---

## 📅 ZEITPLAN (Vorschlag)

### **PHASE 1: SETUP & PLANUNG** (1 Woche) ← WIR SIND HIER
- [x] Branch erstellen
- [x] Projekt-Plan dokumentieren
- [ ] Architektur-Dokumente erstellen
- [ ] Datenbank-Schema entwerfen
- [ ] API-Spezifikation (Auth-Service)

### **PHASE 2: PROOF-OF-CONCEPT** (2-3 Wochen)
- [ ] Lineares Menü-System prototypisch
- [ ] HTTP Auth-Service (Flask Minimal)
- [ ] sys_ Tabellen Prototyp
- [ ] sec_id Security-Test

### **PHASE 3: KERN-ENTWICKLUNG** (2-3 Monate)
- [ ] Database Manager (sys_ Tabellen)
- [ ] Auth-Service produktiv
- [ ] Security-Layer (sec_id)
- [ ] Lineares Menü-System
- [ ] Command-Dispatcher

### **PHASE 4: UI-INTEGRATION** (1-2 Monate)
- [ ] View-System (Matrix-Pipeline aus V0.9)
- [ ] Dialog-System
- [ ] Menü-Editor als View

### **PHASE 5: MIGRATION & TESTING** (1 Monat)
- [ ] Daten-Migration V0.9 → V2.0
- [ ] Parallelbetrieb-Tests
- [ ] User-Acceptance-Tests

### **PHASE 6: ROLLOUT** (2 Wochen)
- [ ] Dokumentation
- [ ] Schulung
- [ ] Produktiv-Umstellung

**GESAMT: ca. 6-8 Monate**

---

## 🔄 CODE-ÜBERNAHME aus V0.9

### ✅ **DIREKT ÜBERNEHMEN** (funktioniert super)
- `pdvm_datetime.py` → `v2_datetime.py`
- `pdvm_matrix_pipeline.py` → `v2_matrix_pipeline.py`
- `pdvm_view_controller.py` → `v2_view_controller.py` (mit Anpassungen)
- `pdvm_view_widget_with_tooltips.py` → `v2_view_widget.py`
- Schnellsuche-System
- Filter-Manager

### 🔧 **ÜBERARBEITEN**
- Menü-System → Komplett neu (linear)
- CommandHandler → Command-Dispatcher (vereinfacht)
- Login-System → HTTP Auth-Service
- Datenbank-Zugriff → sys_ Tabellen

### ❌ **NICHT ÜBERNEHMEN**
- `pdvm_menu.py` (Multi-Tree)
- `pdvm_menu_handler.py` (zu komplex)
- `pdvm_menu_template_handler.py` (nicht mehr nötig)
- Alte Login-Dialoge

---

## 🛠️ TECHNOLOGIE-STACK V2.0

### **Backend**
- **Python 3.11+** (aktuell beibehalten)
- **SQLite** (für Mandanten-DBs)
- **PostgreSQL** (optional für zentrale sys_users DB)

### **Auth-Service (NEU)**
- **FastAPI** (modern, schnell) ODER
- **Flask** (einfacher, bekannter)
- **JWT** (JSON Web Tokens für Sessions)
- **bcrypt** (Password Hashing)

### **Frontend**
- **PyQt5** (beibehalten - UI funktioniert gut!)
- **Requests** (für HTTP Auth-Calls)

### **Testing (NEU)**
- **pytest** (Unit-Tests)
- **pytest-qt** (UI-Tests)

---

## 📊 MIGRATION-STRATEGIE

### **SCHRITT 1: Tabellen-Umbenennung**
```sql
-- Alte V0.9 DB
menudaten → sys_menudaten
viewdaten → sys_viewdaten
framedaten → sys_framedaten
...

-- User-Tabellen bleiben gleich
kunde → kunde
artikel → artikel
```

### **SCHRITT 2: Security-Spalten hinzufügen**
```sql
ALTER TABLE kunde ADD COLUMN sec_id TEXT;
UPDATE kunde SET sec_id = 'default-read-write-guid';
```

### **SCHRITT 3: Menü-Struktur konvertieren**
```python
# V0.9: Multi-Tree
{
  "PD_grund": {"Datei": {...}, "Bearbeiten": {...}},
  "PD_menu": {"Modul1": {...}},
  "PD_commands": {...}
}

# V2.0: Linear mit Parent-Referenzen
[
  {"id": "1", "parent": null, "name": "Datei", "command": null},
  {"id": "2", "parent": "1", "name": "Neu", "command": "file.new"},
  {"id": "3", "parent": "1", "name": "Öffnen", "command": "file.open"}
]
```

---

## 🚀 NÄCHSTE SCHRITTE

### **DIESE WOCHE:**
1. ✅ Branch `v2.0-neuaufbau` erstellen
2. ✅ Dieses Dokument erstellen
3. ⏳ `V2_ARCHITEKTUR.md` - Detaillierte Architektur
4. ⏳ `V2_MENU_SYSTEM.md` - Lineares Menü-Design
5. ⏳ `V2_AUTH_SERVICE.md` - HTTP Auth Spezifikation

### **NÄCHSTE WOCHE:**
6. Datenbank-Schema entwerfen (`V2_DATABASE_SCHEMA.md`)
7. Security-Model definieren (`V2_SECURITY_MODEL.md`)
8. Ersten Prototyp: Lineares Menü-System

---

## 💡 WICHTIGE ENTSCHEIDUNGEN

### **FRAGE 1: Auth-Service Technologie?**
- **FastAPI** (modern, async, auto-docs) ← EMPFEHLUNG
- **Flask** (einfacher, mehr Beispiele)
- **Django REST** (overkill für unseren Use-Case)

### **FRAGE 2: Zentrale User-DB?**
- **SQLite** (einfach, lokales File)
- **PostgreSQL** (professioneller, Multi-Client) ← LANGFRISTIG
- **Cloud** (Firebase, AWS Cognito) ← SPÄTER

### **FRAGE 3: Migration-Zeitpunkt?**
- **Big Bang** (V0.9 → V2.0 an einem Tag) ← RISKANT
- **Parallel** (Beide Systeme parallel, schrittweise) ← EMPFOHLEN
- **Hybrid** (V2.0 Features schrittweise in V0.9) ← KOMPLIZIERT

---

## 📝 OFFENE FRAGEN

1. Sollen V0.9 und V2.0 die **gleiche Datenbank** teilen? (Empfehlung: JA, aber sys_ Trennung)
2. Wie viele **Mandanten** erwarten wir? (wichtig für DB-Design)
3. Soll Auth-Service **lokal** laufen oder auf **Server**?
4. Wann ist **frühester Produktiv-Termin** für V2.0?
5. Gibt es **kritische Features** die sofort in V0.9 müssen?

---

**AUTOR:** Norbert Peters  
**ASSISTENT:** GitHub Copilot  
**VERSION:** 1.0  
**LETZTES UPDATE:** 30.10.2025
