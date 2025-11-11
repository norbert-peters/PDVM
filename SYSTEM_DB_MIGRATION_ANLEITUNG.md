# System-Datenbank Migration - Anleitung

## 🎯 Überblick

Das PDVM-System wurde erweitert um eine **zentrale System-Datenbank** (`pdvm_system.db`), die von allen Mandanten gemeinsam genutzt wird.

### Vorteile:
- ✅ **Keine Duplikation** von System-Daten pro Mandant
- ✅ **Zentrale Updates** von Views, Dialogen, Menüs
- ✅ **Flexibel** - Mehrere System-DBs möglich (Test/Prod)
- ✅ **Transparent** - Keine Code-Änderungen nötig

---

## 📋 System-Tabellen

Alle Tabellen verwenden die **vollständige PDVM-Struktur**:

```sql
CREATE TABLE <tabellenname> (
    uid          TEXT    PRIMARY KEY,
    daten        TEXT    NOT NULL,
    name         TEXT,
    historisch   INTEGER DEFAULT 0,
    source_hash  TEXT,
    sec_id       TEXT,
    gilt_bis     TEXT    DEFAULT '9999365.00000',
    created_at   TEXT,
    modified_at  TEXT,
    daten_backup TEXT
);
```

### In `pdvm_system.db` (zentral):
- `sys_beschreibungen` - Feldbezeichnungen
- `sys_dialogdaten` - Dialog-Konfigurationen
- `sys_dropdowndaten` - Dropdown-Listen
- `sys_framedaten` - Frame-Konfigurationen
- `sys_menudaten` - Menü-Strukturen
- `sys_viewdaten` - View-Konfigurationen

### In Mandanten-DB (lokal):
- `sys_anwendungsdaten` - User-spezifische Einstellungen (Filter, Sortierungen)
- `sys_systemsteuerung` - Mandanten-spezifische Konfiguration

---

## 🛠️ Setup-Schritte

### **1. System-Datenbank erstellen**

```powershell
python create_pdvm_system_db.py
```

**Was passiert:**
- Erstellt `Daten/pdvm_system.db`
- Legt Schema für 6 System-Tabellen an
- Tabellen sind leer (werden im nächsten Schritt befüllt)

---

### **2. System-Tabellen kopieren**

```powershell
python copy_system_tables_to_system_db.py
```

**Eingabe:** Pfad zur Mandanten-DB (z.B. `Daten/datenbank.db`)

**Was passiert:**
- Kopiert Daten aus den 6 System-Tabellen von Mandanten-DB nach `pdvm_system.db`
- Alte Daten in Ziel-DB werden überschrieben
- Mandanten-DB bleibt unverändert

---

### **3. Mandanten konfigurieren**

In der **Mandanten-Datenbank** (`datenbank.db`) muss das Feld `METADATEN.SYSTEM_DB` gesetzt werden.

**SQL-Befehl:**
```sql
-- In Tabelle sys_mandanten, Spalte daten (JSON)
-- Füge METADATEN.SYSTEM_DB = 'pdvm_system' hinzu

UPDATE sys_mandanten
SET daten = json_set(daten, '$.METADATEN.SYSTEM_DB', 'pdvm_system')
WHERE uid = '<mandant-guid>';
```

**Oder manuell in JSON:**
```json
{
  "ROOT": {
    "BEZEICHNUNG": "Mein Mandant"
  },
  "METADATEN": {
    "MANDANT_ID": "mandant_001",
    "SYSTEM_DB": "pdvm_system"
  }
}
```

---

### **4. System testen**

```powershell
python pdvm_main.py
```

**Was überprüfen:**
- ✅ Login funktioniert
- ✅ Menüs werden geladen (aus `pdvm_system.db`)
- ✅ Views öffnen (aus `pdvm_system.db`)
- ✅ Dialoge öffnen (aus `pdvm_system.db`)
- ✅ Keine Fehler im Log

---

## 🔍 Fehlerbehandlung

### **Fehler: "SYSTEM_DB nicht konfiguriert"**

**Ursache:** `METADATEN.SYSTEM_DB` fehlt in Mandanten-Daten

**Lösung:** Schritt 3 ausführen (Mandanten konfigurieren)

---

### **Fehler: "System-Datenbank nicht gefunden"**

**Ursache:** `pdvm_system.db` existiert nicht

**Lösung:** Schritt 1 ausführen (System-DB erstellen)

---

### **Fehler: "Tabelle ... nicht gefunden"**

**Ursache:** System-Tabellen sind leer oder nicht kopiert

**Lösung:** Schritt 2 ausführen (Tabellen kopieren)

---

## 📊 Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                        auth.db                              │
│  ┌─────────────────┐  ┌──────────────────┐                 │
│  │ sys_benutzer    │  │ sys_mandanten    │                 │
│  │  - user_guid    │  │  - mandant_guid  │                 │
│  │  - username     │  │  - METADATEN     │                 │
│  │  - password     │  │    └─SYSTEM_DB   │                 │
│  └─────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ Login
            ┌─────────────────┴─────────────────┐
            │                                   │
┌───────────▼──────────────┐    ┌──────────────▼──────────────┐
│   pdvm_system.db         │    │  Mandant A: datenbank.db    │
│  (ZENTRAL)               │    │  (LOKAL)                    │
│                          │    │                             │
│  • sys_beschreibungen    │    │  • stammdaten               │
│  • sys_dialogdaten       │    │  • finanzen                 │
│  • sys_dropdowndaten     │    │  • sys_anwendungsdaten      │
│  • sys_framedaten        │◄───┤  • sys_systemsteuerung      │
│  • sys_menudaten         │    │  • ...                      │
│  • sys_viewdaten         │    └─────────────────────────────┘
└──────────────────────────┘
            ▲
            │
            └──────────────────────┐
                                   │
                   ┌───────────────▼─────────────┐
                   │  Mandant B: mandant_b.db    │
                   │  (LOKAL)                    │
                   │                             │
                   │  • stammdaten               │
                   │  • finanzen                 │
                   │  • sys_anwendungsdaten      │
                   │  • sys_systemsteuerung      │
                   │  • ...                      │
                   └─────────────────────────────┘
```

---

## 🔧 Technische Details

### **Routing in `pdvm_datenbank.py`**

```python
SYSTEM_TABLES = {
    'sys_beschreibungen',
    'sys_dialogdaten',
    'sys_dropdowndaten',
    'sys_framedaten',
    'sys_menudaten',
    'sys_viewdaten'
}

def __init__(self, table_name):
    if table_name in SYSTEM_TABLES:
        # System-DB aus Mandanten-METADATEN
        self.db_name = self._get_system_db_path(gcs)
    else:
        # Mandanten-DB
        self.db_name = gcs.db_path
```

### **DB-Pfad Ermittlung**

```python
def _get_system_db_path(self, gcs):
    metadaten = gcs._mandant_data.get('METADATEN', {})
    system_db_name = metadaten.get('SYSTEM_DB')  # z.B. 'pdvm_system'
    
    if not system_db_name:
        raise RuntimeError("SYSTEM_DB nicht konfiguriert!")
    
    db_dir = os.path.dirname(gcs.db_path)  # 'Daten'
    return os.path.join(db_dir, f"{system_db_name}.db")  # 'Daten/pdvm_system.db'
```

---

## 📝 Checkliste für Migration

- [ ] **Schritt 1:** `create_pdvm_system_db.py` ausgeführt
- [ ] **Schritt 2:** `copy_system_tables_to_system_db.py` ausgeführt  
- [ ] **Schritt 3:** `METADATEN.SYSTEM_DB = 'pdvm_system'` in Mandanten-Daten gesetzt
- [ ] **Schritt 4:** System getestet (Login, Menüs, Views, Dialoge)
- [ ] **Backup:** Alte Mandanten-DB gesichert (vor dem Test)

---

## ⚠️ Wichtige Hinweise

1. **Kein Fallback:** Wenn `METADATEN.SYSTEM_DB` fehlt, wird System **nicht** gestartet
2. **Rückwärtskompatibilität:** Alte Mandanten ohne System-DB funktionieren **nicht** mehr
3. **Mehrere System-DBs möglich:** z.B. `pdvm_system_test`, `pdvm_system_prod`
4. **Berechtigungen:** Zugriff wird über Menüs gesteuert, nicht über DB-Level
5. **Cache:** System-Daten können gecacht werden (später implementiert)

---

## 🚀 Vorteile nach Migration

✅ **Updates einfacher:** Nur eine System-DB aktualisieren statt alle Mandanten  
✅ **Konsistenz:** Alle Mandanten haben gleiche System-Daten  
✅ **Flexibilität:** Test-System und Produktiv-System können unterschiedliche System-DBs nutzen  
✅ **Performance:** Weniger Duplikation = weniger Speicher  
✅ **Wartung:** Zentrale Verwaltung von Views, Dialogen, Menüs  

---

## 📞 Support

Bei Problemen:
1. Log-Datei prüfen (`main.log`)
2. Checkliste oben durchgehen
3. Fehlerbehandlung-Abschnitt konsultieren

---

**Stand:** 11.11.2025  
**Version:** 2.0  
**Autor:** PDVM System
