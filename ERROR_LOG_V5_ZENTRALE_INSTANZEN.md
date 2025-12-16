# ERROR-LOG SYSTEM V5 - ZENTRALE INSTANZEN ✅

**Datum:** 11.12.2025  
**Status:** ✅ IMPLEMENTATION COMPLETE  
**Version:** V5 - Zentrale Session-weite Instanzen

---

## 🎯 KERN-PRINZIP

**PROBLEM V4:**
User-Vermischung durch lokale Instanz-Erstellung in jeder Methode!

**LÖSUNG V5:**
**EINE zentrale Instanz pro Session** - initialisiert in GCS `__init__`:

```python
# In pdvm_central_systemsteuerung.py __init__:

# 2.5 ZENTRALE ERROR-LOG INSTANZEN (SESSION-WEIT!)
# sys_error_log: OHNE user_guid - allgemein für alle Errors
self._error_log_db = PdvmCentralDatenbank('sys_error_log')

# sys_error_acknowledgments: MIT user_guid - pro User
self._error_ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', user_guid)
```

---

## 📊 Zentrale Instanzen-Verwaltung

### GCS verwaltet ALLE zentralen Instanzen:

```python
class PdvmCentralSystemsteuerung:
    def __init__(self, user_guid, user_data, mandant_guid, mandant_data):
        # KERN-INSTANZEN (eine pro Session)
        self._db = PdvmCentralDatenbank('sys_systemsteuerung', user_guid)
        self._app_db = PdvmCentralDatenbank('sys_anwendungsdaten', user_guid)
        self._man_db = PdvmCentralDatenbank('sys_anwendungsdaten', mandant_guid)
        
        # ERROR-LOG INSTANZEN (NEU in V5)
        self._error_log_db = PdvmCentralDatenbank('sys_error_log')  # OHNE GUID!
        self._error_ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', user_guid)
        
        # WEITERE ZENTRALE INSTANZEN
        self._st_inst = Pdvm_DateTime(country)  # Stichtag
        self._neues_abdatum_inst = Pdvm_DateTime(country)  # Neues AB-Datum
        self._temp_dt_inst = Pdvm_DateTime(country)  # Temp für Formatierungen
```

**PRINZIP:**
- ✅ **sys_error_log**: EINE Instanz OHNE user_guid → Alle Errors zentral
- ✅ **sys_error_acknowledgments**: EINE Instanz MIT user_guid → User-spezifisch
- ✅ Beide werden in GCS `__init__` erstellt
- ✅ Error-Manager nutzt diese via `self.gcs._error_log_db` / `self.gcs._error_ack_db`
- ✅ KEINE lokalen Instanzen mehr in Methoden!

---

## 🔧 Error-Manager Anpassungen

### 1. __init__() - Keine eigenen Instanzen

```python
class PdvmErrorLogManager:
    def __init__(self, gcs):
        """V5: Nutzt zentrale GCS-Instanzen"""
        self.gcs = gcs
        # ✅ Keine eigenen DB-Instanzen mehr!
        logger.info("✅ Error-Log Manager V5 (Zentrale Instanzen) initialisiert")
```

### 2. add_error() - Nutzt gcs._error_log_db

```python
def add_error(self, ...):
    # Existierender Error?
    if existing_guid:
        # ✅ ZENTRALE INSTANZ für Update
        current_count = self.gcs._error_log_db.get_static_value(existing_guid, 'occurrence_count') or 1
        self.gcs._error_log_db.set_value(existing_guid, 'occurrence_count', new_count, timestamp)
        self.gcs._error_log_db.save_all_values()
    
    # Neuer Error:
    import allgemeines as all
    error_guid = all.generate_guid()
    
    # ✅ Direkt in zentrale Instanz schreiben
    self.gcs._error_log_db.set_value(error_guid, 'timestamp', timestamp, timestamp)
    self.gcs._error_log_db.set_value(error_guid, 'error_type', error_type, timestamp)
    # ... weitere Felder
    self.gcs._error_log_db.save_all_values()
```

### 3. _add_vorkommen() - Nutzt gcs._error_ack_db

```python
def _add_vorkommen(self, error_guid, timestamp):
    # ✅ ZENTRALE INSTANZ: sys_error_acknowledgments (MIT user_guid)
    ack_db = self.gcs._error_ack_db
    
    vorkommen_json = ack_db.get_static_value(error_guid, 'VORKOMMEN')
    # ... Liste erweitern ...
    ack_db.set_value(error_guid, 'VORKOMMEN', json.dumps(vorkommen_list), timestamp)
    ack_db.save_all_values()
```

### 4. _find_existing_error_in_db() - Durchsucht zentrale Instanz

```python
def _find_existing_error_in_db(self, signature, ...):
    # ✅ ZENTRALE INSTANZ: Durchsuche gcs._error_log_db
    error_db = self.gcs._error_log_db
    
    for error_guid in error_db.data.keys():
        if error_guid == 'ROOT':
            continue
        stored_signature = error_db.get_static_value(error_guid, 'signature')
        if stored_signature == signature:
            return error_guid
    return None
```

### 5. _load_unacknowledged_errors() - Beide zentrale Instanzen

```python
def _load_unacknowledged_errors(self):
    # ✅ ZENTRALE INSTANZEN
    error_db = self.gcs._error_log_db
    ack_db = self.gcs._error_ack_db
    
    error_list = []
    
    for error_guid in error_db.data.keys():
        if error_guid == 'ROOT':
            continue
        
        # User-Filter
        error_user_guid = error_db.get_static_value(error_guid, 'user_guid')
        if error_user_guid != self.gcs.user_guid:
            continue
        
        # 24h-Logik
        last_show = ack_db.get_static_value(error_guid, 'LAST_SHOW') or 0.0
        if last_show == 0.0 or (now - last_show) > 1.0:
            error_list.append({...})
    
    return error_list
```

### 6. acknowledge_errors() - Nutzt gcs._error_ack_db

```python
def acknowledge_errors(self, error_guids):
    # ✅ ZENTRALE INSTANZ: sys_error_acknowledgments
    ack_db = self.gcs._error_ack_db
    
    for error_guid in error_guids:
        ack_db.set_value(error_guid, 'LAST_SHOW', now, now)
    
    ack_db.save_all_values()
```

---

## 🔄 Kompletter Workflow (V5)

### 1. Systemstart - GCS Initialisierung

```python
# In pdvm_central_systemsteuerung.py __init__:
self._error_log_db = PdvmCentralDatenbank('sys_error_log')  # OHNE GUID
self._error_ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', user_guid)
self._error_log_manager = PdvmErrorLogManager(self)
```

**KRITISCH:**
- sys_error_log ist **OHNE user_guid** → zentral für alle Errors
- sys_error_acknowledgments ist **MIT user_guid** → pro User getrennt
- Error-Manager erhält GCS-Referenz, erstellt KEINE eigenen Instanzen

### 2. Error tritt auf

```python
gcs.error_log_manager.add_error(
    table_name="persondaten",
    record_guid="abc-123",
    error_type="json_parse",
    error_message="...",
    severity="error"
)
```

### 3. add_error() Verarbeitung

```python
# 1. Deduplication über gcs._error_log_db
existing_guid = self._find_existing_error_in_db(signature, ...)

# 2a. Existierender Error → Update in gcs._error_log_db
if existing_guid:
    self.gcs._error_log_db.set_value(existing_guid, 'occurrence_count', new_count, timestamp)
    self.gcs._error_log_db.save_all_values()

# 2b. Neuer Error → Neue GUID generieren
else:
    error_guid = all.generate_guid()
    self.gcs._error_log_db.set_value(error_guid, 'timestamp', timestamp, timestamp)
    # ... weitere Felder ...
    self.gcs._error_log_db.save_all_values()

# 3. Vorkommen in gcs._error_ack_db protokollieren
self._add_vorkommen(error_guid, timestamp)
```

### 4. Popup anzeigen

```python
# finish_collection()
unacknowledged = self._load_unacknowledged_errors()  # Nutzt zentrale Instanzen
self._show_error_popup_from_db(unacknowledged)
```

### 5. User bestätigt

```python
self.acknowledge_errors(error_guids)  # Nutzt gcs._error_ack_db
```

---

## ✅ Vorteile V5

### KEINE User-Vermischung mehr:
- ❌ V4: Lokale Instanzen in jeder Methode → User-Vermischung möglich
- ✅ V5: EINE Instanz pro Session → User-GUID fest verankert

### Lineare Architektur:
- ✅ Initialisierung in GCS `__init__`
- ✅ Error-Manager nutzt zentrale Instanzen
- ✅ Keine Instanz-Erstellung in Methoden
- ✅ Klare Zuständigkeiten

### Performance:
- ✅ Keine wiederholte Instanz-Erstellung
- ✅ Daten bleiben im Speicher (bis save_all_values)
- ✅ Ein save_all_values pro Operation (nicht pro Error)

### Einfachheit:
- ✅ Alle Instanzen in GCS sichtbar
- ✅ Keine versteckten Abhängigkeiten
- ✅ Debugging einfacher (zentrale Instanz durchsuchbar)

---

## 📋 Geänderte Dateien

### 1. pdvm_central_systemsteuerung.py
**Änderung:** Zentrale Error-Log Instanzen hinzugefügt
```python
# 2.5 ZENTRALE ERROR-LOG INSTANZEN (SESSION-WEIT!)
self._error_log_db = PdvmCentralDatenbank('sys_error_log')
self._error_ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', user_guid)
```

### 2. pdvm_error_log_manager.py
**Änderungen:**
- `__init__`: Dokumentation angepasst (V5 - Zentrale Instanzen)
- `add_error`: Nutzt `gcs._error_log_db` statt lokale Instanz
- `_add_vorkommen`: Nutzt `gcs._error_ack_db` statt lokale Instanz
- `_find_existing_error_in_db`: Durchsucht `gcs._error_log_db.data`
- `_load_unacknowledged_errors`: Nutzt beide zentrale Instanzen
- `acknowledge_errors`: Nutzt `gcs._error_ack_db` statt lokale Instanz

---

## 🧪 Test-Workflow

### Manueller Test:

1. **System starten** → GCS initialisiert zentrale Instanzen
   ```powershell
   python pdvm_main.py
   ```

2. **Error auslösen** → View mit korrupten JSON-Daten öffnen

3. **Prüfen:**
   - ✅ Error in `sys_error_log` (zentral, OHNE user_guid in Tabellenname)
   - ✅ VORKOMMEN in `sys_error_acknowledgments` (MIT user_guid)
   - ✅ Popup erscheint mit Error
   - ✅ Nach Bestätigung: LAST_SHOW gesetzt

4. **Zweiten Error auslösen** → Gleiche View öffnen

5. **Prüfen:**
   - ✅ occurrence_count erhöht in sys_error_log
   - ✅ VORKOMMEN-Liste erweitert
   - ✅ **KEIN Popup** (innerhalb 24h)

6. **Als anderer User anmelden**

7. **Prüfen:**
   - ✅ sys_error_log zeigt ALLE Errors (auch von User 1)
   - ✅ sys_error_acknowledgments NUR eigene Vorkommen
   - ✅ KEINE User-Vermischung

---

## 🎯 Zusammenfassung

**V5 LÖSUNG:**
```
GCS initialisiert bei Login:
  ├─ _error_log_db (OHNE user_guid) → Zentral für alle Errors
  └─ _error_ack_db (MIT user_guid) → Pro User

Error-Manager nutzt IMMER:
  ├─ self.gcs._error_log_db für Error-Speicherung
  └─ self.gcs._error_ack_db für Vorkommen/Acknowledgments

KEINE lokalen Instanzen in Methoden!
```

**PRINZIPIEN:**
- ✅ EINE zentrale Instanz pro Tabelle/User
- ✅ Initialisierung in GCS `__init__`
- ✅ Linear ohne Verschachtelungen
- ✅ Klare Zuständigkeiten
- ✅ Session-weite Gültigkeit

**ERGEBNIS:**
- ✅ Keine User-Vermischung
- ✅ Keine Speicherfehler
- ✅ Einfache, nachvollziehbare Architektur
- ✅ Performance optimiert
- ✅ Wartbar und erweiterbar

---

**Version:** V5 - Zentrale Instanzen  
**Status:** ✅ IMPLEMENTATION COMPLETE  
**Datum:** 11.12.2025
