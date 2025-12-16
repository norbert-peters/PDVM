# PDVM ERROR LOG SYSTEM - DOKUMENTATION
## Automatisches Fehlerprotokoll mit Pop-up Warnung

**Datum:** 09.12.2025  
**Version:** 1.0  
**Status:** ✅ Implementiert

---

## 🎯 PROBLEMSTELLUNG

### **Problem 1: Stille Datenverluste**
- Korrupte JSON-Datensätze werden **stillschweigend übersprungen**
- User sieht **keine Warnung** → denkt Datensatz ist verloren
- User **legt Datensatz neu an** → Duplikate

### **Problem 2: Template-Robustheit**
- Templates (55555...) können korruptes JSON enthalten
- `convert_from_time()` erwartet `dict`, bekommt `str` → **Crash**
- Fehler: `'str' object has no attribute 'items'`

---

## 🔧 LÖSUNG: ERROR LOG SYSTEM

### **Architektur-Übersicht**

```
┌─────────────────────────────────────────────────────────────┐
│                    FEHLER TRITT AUF                          │
│  (JSON Parse Error, AttributeError, TypeError, etc.)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               pdvm_datenbank.py: alle_lesen()                │
│  - Fehler wird gefangen (try-except erweitert)              │
│  - Typ-Validierung nach json.loads() hinzugefügt            │
│  - log_error() aufgerufen                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          pdvm_error_log_manager.py: log_error()              │
│  - Erstellt Log-Eintrag in sys_error_log Tabelle            │
│  - Speichert: Context, Fehlertyp, Zeitstempel, GUID, etc.   │
│  - Setzt acknowledged=False (unbestätigt)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              APP-START: pdvm_main.py                         │
│  [2.6/3] Error-Log Manager initialisieren                    │
│  [3.5/3] check_new_errors() → Pop-up falls Fehler vorhanden │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         USER SIEHT POP-UP MIT FEHLERPROTOKOLL                │
│  - Alle unbestätigten Fehler aufgelistet                     │
│  - Details: Typ, Zeitpunkt, Tabelle, Datensatz-GUID         │
│  - Button: "Alle Fehler bestätigen"                          │
│  → acknowledged=True in DB gesetzt                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 DATENBANK-STRUKTUR

### **Tabelle: sys_error_log**

```sql
CREATE TABLE sys_error_log (
    uid TEXT PRIMARY KEY,       -- GUID des Log-Eintrags
    name TEXT DEFAULT '',       -- Kurzbezeichnung (für Übersicht)
    daten TEXT NOT NULL,        -- JSON mit allen Details
    modified_at TEXT            -- Zeitstempel
)
```

### **JSON-Struktur (daten Spalte)**

```json
{
  "ROOT": {
    "timestamp": 2025343.123456,
    "context_guid": "view-guid-oder-table-name",
    "context_type": "view|dialog|frame|menu|table",
    "error_type": "json_parse|data_corruption|attribute|type",
    "error_message": "Vollständige Fehlermeldung",
    "record_guid": "guid-des-betroffenen-datensatzes",
    "table_name": "persondaten",
    "severity": "warning|error|critical",
    "user_guid": "user-guid",
    "acknowledged": false,
    "additional_info": {}
  }
}
```

---

## 🚀 VERWENDUNG

### **1. Error-Logging (automatisch in pdvm_datenbank.py)**

```python
# In pdvm_datenbank.py (alle_lesen):
try:
    data = json.loads(raw_json)
    
    # ✅ NEU: Typ-Validierung
    if not isinstance(data, dict):
        raise TypeError(f"Erwartete dict, bekam {type(data).__name__}")
    
    if self.historisch:
        data = all.convert_from_time(data)
    
except (json.JSONDecodeError, AttributeError, TypeError) as e:
    logger.error(f"Fehler beim Laden von Datensatz {uid}: {e}")
    
    # ✅ NEU: Error-Logging
    from pdvm_error_log_manager import log_error
    log_error(
        context_guid=self.table_name,
        context_type="table",
        error_type="json_parse",
        error_message=str(e),
        record_guid=uid,
        table_name=self.table_name,
        severity="error"
    )
    
    continue  # Datensatz überspringen
```

### **2. App-Start (automatisch in pdvm_main.py)**

```python
# [2.6/3] Error-Log Manager initialisieren
from pdvm_error_log_manager import initialize_error_log_manager, check_new_errors
error_manager = initialize_error_log_manager(gcs)

# [3.5/3] Nach Hauptfenster-Anzeige: Fehler-Check
if check_new_errors(parent=main_window):
    print("⚠️ Fehler wurden dem Benutzer angezeigt")
```

### **3. Manuelles Logging (in eigenem Code)**

```python
from pdvm_error_log_manager import log_error

log_error(
    context_guid="meine-view-guid",
    context_type="view",
    error_type="custom_error",
    error_message="Meine Fehlermeldung",
    record_guid="datensatz-guid",
    table_name="meine_tabelle",
    severity="warning",  # oder "error", "critical"
    additional_info={"custom_key": "custom_value"}
)
```

### **4. Fehler bestätigen**

```python
from pdvm_error_log_manager import get_error_log_manager

manager = get_error_log_manager()

# Einzelnen Fehler bestätigen
manager.acknowledge_error(log_guid="error-guid")

# Alle Fehler bestätigen
manager.acknowledge_all_errors()
```

---

## 🔍 POP-UP DIALOG

### **Erscheinungsbild**

```
╔═══════════════════════════════════════════════════════════╗
║         ⚠️ PDVM Fehlerprotokoll                           ║
╠═══════════════════════════════════════════════════════════╣
║  ⚠️ 3 Fehler protokolliert                                ║
║                                                            ║
║  Die folgenden Fehler sind während der Daten-              ║
║  verarbeitung aufgetreten. Betroffene Datensätze          ║
║  wurden übersprungen und sind möglicherweise nicht         ║
║  sichtbar.                                                 ║
║                                                            ║
║  ┌─────────────────────────────────────────────────────┐  ║
║  │ ══════════════════════════════════════════════════  │  ║
║  │ FEHLER #1 [ERROR]                                   │  ║
║  │ ══════════════════════════════════════════════════  │  ║
║  │ Typ:       json_parse                                │  ║
║  │ Kontext:   table                                     │  ║
║  │ Zeitpunkt: 09.12.2025 - 11:22:16                    │  ║
║  │ Tabelle:   persondaten                               │  ║
║  │ Datensatz: ce2fa4be-23b4-40b9-9281-242c7f8a961e     │  ║
║  │                                                       │  ║
║  │ Fehlermeldung:                                       │  ║
║  │ Expecting property name enclosed in double quotes    │  ║
║  │ ...                                                   │  ║
║  └─────────────────────────────────────────────────────┘  ║
║                                                            ║
║  [✅ Alle Fehler bestätigen und schließen]                ║
║  [Schließen (ohne Bestätigung)]                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## ✅ VORTEILE

### **1. Sichtbarkeit**
- ✅ User sieht **sofort** beim Start, dass Fehler aufgetreten sind
- ✅ Keine stillen Datenverluste mehr
- ✅ Klare Information welcher Datensatz betroffen ist

### **2. Nachvollziehbarkeit**
- ✅ Alle Fehler werden **persistiert** in Datenbank
- ✅ Zeitstempel → nachvollziehbar wann Fehler aufgetreten
- ✅ Context-GUID → nachvollziehbar wo Fehler aufgetreten

### **3. Wartung**
- ✅ Admin kann **sys_error_log Tabelle** direkt prüfen
- ✅ Fehler-GUIDs können für **Fehleranalyse** verwendet werden
- ✅ Bestätigungsstatus verhindert **wiederkehrende Pop-ups**

### **4. Robustheit**
- ✅ **Typ-Validierung** nach `json.loads()` verhindert Template-Crashes
- ✅ **Erweiterte Exception-Behandlung** (JSONDecodeError, AttributeError, TypeError)
- ✅ **Graceful Degradation** → App läuft auch mit korrupten Daten weiter

---

## 🔧 ERWEITERUNGSMÖGLICHKEITEN

### **Optional: Error-Log View**

Später kann eine **View für sys_error_log** erstellt werden:

```python
# sys_viewdaten Eintrag für Error-Log View
{
    "TABLE": "sys_error_log",
    "NO_DATA": False,
    "ROOT_CONTROLS": {
        "timestamp": {...},
        "context_type": {...},
        "error_type": {...},
        "error_message": {...},
        "record_guid": {...},
        "table_name": {...},
        "severity": {...},
        "acknowledged": {...}
    }
}
```

**Features:**
- ✅ Alle Fehler in Tabellenansicht
- ✅ Filter nach Severity, Context-Type, Table
- ✅ Sortierung nach Timestamp
- ✅ Doppelklick → Details-Dialog
- ✅ Batch-Bestätigung ausgewählter Fehler

### **Optional: Error-Statistics Dashboard**

```python
# Statistiken für Admin-Bereich
- Fehler pro Tag (Diagramm)
- Häufigste Fehlertypen
- Betroffene Tabellen (Top 10)
- Nicht bestätigte Fehler (Anzahl)
```

---

## 📊 SEVERITY-LEVELS

### **warning**
- ℹ️ Informative Warnung
- ℹ️ Kein Datenverlust
- ℹ️ Wird **nicht** im Pop-up angezeigt

### **error** (Standard)
- ⚠️ Fehler bei Datenverarbeitung
- ⚠️ Datensatz übersprungen
- ⚠️ Wird im Pop-up angezeigt

### **critical**
- 🔴 Kritischer Fehler
- 🔴 Systemfunktion beeinträchtigt
- 🔴 **Immer** im Pop-up angezeigt

---

## 🧪 TESTING

### **Test 1: Korruptes JSON**

```python
# Manuell korruptes JSON in DB einfügen
import sqlite3
conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

# Korruptes JSON (fehlendes Closing-Brace)
corrupt_json = '{"ROOT": {"test": "value"'

cursor.execute(
    "INSERT INTO persondaten (uid, name, daten) VALUES (?, ?, ?)",
    ("test-corrupt-guid", "Test Corrupt", corrupt_json)
)
conn.commit()
conn.close()

# App starten → Fehler sollte geloggt werden → Pop-up erscheint
```

### **Test 2: Typ-Fehler (String statt Dict)**

```python
# JSON ist valide, aber String statt Dict
string_json = '"this_is_a_string_not_a_dict"'

cursor.execute(
    "INSERT INTO persondaten (uid, name, daten) VALUES (?, ?, ?)",
    ("test-type-error", "Test Type", string_json)
)

# App starten → TypeError wird gefangen → Error-Log
```

### **Test 3: Bestätigung**

```python
# 1. App starten → Pop-up erscheint
# 2. "Alle Fehler bestätigen" klicken
# 3. App neu starten → Kein Pop-up (Fehler bestätigt)
```

---

## 📝 ZUSAMMENFASSUNG

✅ **Problem gelöst**: Stille Datenverluste durch korruptes JSON  
✅ **Problem gelöst**: Template-Crashes durch Typ-Fehler  
✅ **Implementiert**: Zentrales Error-Log System  
✅ **Implementiert**: Pop-up Warnung bei App-Start  
✅ **Implementiert**: Bestätigungs-Tracking  
✅ **Robust**: Erweiterte Exception-Behandlung  
✅ **Erweiterbar**: View/Dashboard für Error-Log optional

**Status:** ✅ Produktionsbereit
