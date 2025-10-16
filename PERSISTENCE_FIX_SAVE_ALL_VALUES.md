# 🔧 PERSISTENCE FIX: save_all_values() fehlte!

## 🐛 Problem
**Symptom**: Sortierung und Filter wurden nicht persistent gespeichert
- Sort-Config wurde in Dialog gespeichert, aber nicht in DB geschrieben
- Nach App-Neustart waren alle Einstellungen weg
- Logs zeigten "💾 gespeichert", aber `get_value()` gab `None` zurück

**Root Cause**: `save_all_values()` Aufruf fehlte nach `set_value()`!

```python
# ❌ FALSCH (alte Version):
gcs._app_db.set_value(view_guid, 'sort', config)
# → Schreibt nur in Memory, NICHT in DB!

# ✅ RICHTIG (neue Version):
gcs._app_db.set_value(view_guid, 'sort', config)
gcs._app_db.save_all_values()  # Commit to database!
```

## 📚 PdvmCentralDatenbank API-Pattern
Die `PdvmCentralDatenbank` arbeitet mit einem **2-Phasen-Commit**:

### Phase 1: Memory Operations
```python
gcs._app_db.set_value(gruppe, feld, wert)  # Buffered in memory
gcs._app_db.get_value(gruppe, feld)        # Returns from memory OR DB
```

### Phase 2: Database Commit
```python
gcs._app_db.save_all_values()  # Writes all changes to SQLite
```

**Wichtig**: Ohne `save_all_values()` bleiben Änderungen nur im Memory!

## ✅ Korrigierte Dateien

### 1. advanced_sort_dialog.py (Zeile 375)
```python
# In App-DB speichern
gcs._app_db.set_value(self.view_guid, 'sort', sort_config)
gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!

logger.info(f"💾 Sortierung persistent gespeichert: {len(sort_config)} Spalten")
```

### 2. pdvm_view_controller.py → reset_sort() (Zeile 1311)
```python
# 1. Sort-Config in GCS löschen
self.gcs._app_db.set_value(self.view_guid, 'sort', None)
self.gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!
logger.info(f"  🗑️ Sort-Config in GCS gelöscht")
```

## ✅ Bereits korrekt implementiert

### Filter-System
**extended_filter_engine.py** (Zeile 183):
```python
gcs._app_db.set_value(view_guid, field_name, filter_config)
gcs._app_db.save_all_values()  # ✅ VORHANDEN!
```

**search_parameter_dialog.py** (Zeile 414):
```python
gcs._app_db.set_value(self.view_guid, 'einfach', filter_data)
gcs._app_db.save_all_values()  # ✅ VORHANDEN!
```

**pdvm_central_systemsteuerung.py** (Zeile 910-911):
```python
self._app_db.set_value(view_guid, search_name, filters_config)
self._app_db.save_all_values()  # ✅ VORHANDEN!
```

## 🧪 Test-Szenario

### Vor dem Fix
```
1. Dialog öffnen → Sortierung einstellen → "Übernehmen"
   Logs: "💾 Sortierung persistent gespeichert: 2 Spalten"
2. Dialog schließen und neu öffnen
   Result: ❌ Dialog LEER (keine Spalten)
3. DB prüfen: SELECT * FROM anwendungsdaten WHERE gruppe = 'view_guid'
   Result: ❌ KEINE Einträge
```

### Nach dem Fix
```
1. Dialog öffnen → Sortierung einstellen → "Übernehmen"
   Logs: "💾 Sortierung persistent gespeichert: 2 Spalten"
2. Dialog schließen und neu öffnen
   Result: ✅ Dialog zeigt 2 Spalten mit Gruppe-Marker
3. DB prüfen: SELECT * FROM anwendungsdaten WHERE gruppe = 'view_guid'
   Result: ✅ Eintrag mit feld='sort', wert='[{...}]'
```

## 📊 Datenbank-Struktur
```sql
-- anwendungsdaten Tabelle
CREATE TABLE anwendungsdaten (
    gruppe TEXT,      -- z.B. "0d10a0d0-b1a5-4544-b284-e8a09ca979b5" (view_guid)
    feld TEXT,        -- z.B. "sort", "einfach", "komplex"
    wert TEXT,        -- JSON-serialisiertes Config-Object
    abdatum REAL      -- Änderungs-Zeitstempel
);

-- Beispiel-Einträge:
gruppe: "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
feld:   "sort"
wert:   "[{\"column_key\": \"anrede_show\", \"direction\": \"desc\", \"is_group\": true}, ...]"

gruppe: "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
feld:   "einfach"
wert:   "{\"field_name\": \"familienname\", \"search_value\": \"Lau\", ...}"
```

## 🎯 Best Practice: set_value() Pattern
**Überall im Code verwenden**:

```python
from pdvm_central_systemsteuerung import get_gcs

def save_config(view_guid: str, config_key: str, config_data: Any):
    """Speichert Konfiguration persistent"""
    gcs = get_gcs()
    if not gcs:
        logger.warning("⚠️ GCS nicht verfügbar")
        return False
    
    try:
        # PHASE 1: Memory
        gcs._app_db.set_value(view_guid, config_key, config_data)
        
        # PHASE 2: Database Commit
        gcs._app_db.save_all_values()
        
        logger.info(f"💾 {config_key} gespeichert: {len(config_data)} items")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern: {e}")
        return False
```

## 🚀 Impact
✅ **Sortierung**: Jetzt persistent über App-Neustarts
✅ **Gruppierung**: Gruppe-Marker bleibt erhalten
✅ **Filter**: Bereits korrekt (kein Fix nötig)
✅ **Reset**: Löschen funktioniert jetzt auch persistent

## 📝 Checkliste für neue Features
Wenn du irgendwo `set_value()` verwendest:
- [ ] `save_all_values()` direkt danach aufrufen
- [ ] Exception-Handling um beide Aufrufe
- [ ] Logging nach `save_all_values()`
- [ ] Sofort testen mit DB-Prüfung

**Beispiel-Grep**:
```bash
# Finde alle set_value() ohne nachfolgendes save_all_values():
grep -A 1 "set_value" *.py | grep -v "save_all_values"
```

## 🎉 Status
- ✅ Sort-Persistierung: **FIXED**
- ✅ Filter-Persistierung: **War bereits korrekt**
- ✅ Reset-Persistierung: **FIXED**
- ✅ Autonome Pipeline: **Funktioniert jetzt komplett!**

**Migration auf v3-Architektur**: ABGESCHLOSSEN 🎯
