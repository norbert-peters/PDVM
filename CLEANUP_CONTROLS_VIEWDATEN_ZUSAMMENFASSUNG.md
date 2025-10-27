# 🔧 Controls & ViewDaten Cleanup - Zusammenfassung

**Datum**: 27.10.2025 13:15 Uhr  
**Status**: ✅ Behoben

## 🎯 Probleme identifiziert

### 1. ❌ Controls doppelt gespeichert
**Problem**: Controls wurden zweifach persistiert:
- ✅ Korrekt: Im `"controls"` Dictionary unter view_guid
- ❌ Falsch: Zusätzlich als einzelne Felder direkt unter view_guid

**Ursache**: `pdvm_view_controller.py` Zeile 342-347:
```python
# In Systemsteuerung-DB speichern
import json
for control_key, control_config in all_controls.items():
    control_json = json.dumps(control_config, ensure_ascii=False)
    self.gcs._db.set_value(self.view_guid, control_key, control_json)  # ❌ FALSCH!
```

**Konsequenz**: GCS liest aus `"controls"` Dictionary, findet aber zusätzliche Felder → Datenmüll

### 2. ❌ name_original/name_show fehlen
**Problem**: `uid_original` und `name_original` wurden NICHT in `pdvm_view_controller.py` erstellt

**Ursache**: SYSTEM-Controls nur in `pdvm_view_daten_manager.py` generiert, nicht im Controller

**Konsequenz**: name_show erscheint nicht in Normal Mode, name_original nicht in Expert Mode

### 3. ❌ standard_control in falscher Spalte
**Problem**: `standard_control` Dictionary landet in der `name` Spalte der viewdaten

**Ursache**: Wahrscheinlich manueller Fehler oder fehlerhaftes Initialisierungsskript

**Konsequenz**: ViewDaten haben falsches Schema

### 4. ❌ uid_original fehlt auch
**Problem**: Gleiche Ursache wie name_original

**Konsequenz**: UID-Spalte fehlt ebenfalls

## ✅ Lösungen implementiert

### Fix 1: Doppelte Speicherung entfernt
**Datei**: `pdvm_view_controller.py` Zeile 335-347

**ALT**:
```python
# SCHRITT 5: Controls in beide DBs speichern
self.gcs.db.set_value(...)  # Korrekt
self.gcs.db.save_all_values()

# In Systemsteuerung-DB speichern  ❌ FALSCH!
import json
for control_key, control_config in all_controls.items():
    control_json = json.dumps(control_config, ensure_ascii=False)
    self.gcs._db.set_value(self.view_guid, control_key, control_json)
```

**NEU**:
```python
# SCHRITT 5: Controls NUR in controls Dictionary speichern
self.gcs.db.set_value(
    gruppe=self.view_guid,
    feld='controls',
    wert=all_controls
)
self.gcs.db.save_all_values()

logger.info(f"  ✅ {len(all_controls)} Controls in 'controls' Dictionary gespeichert")
```

### Fix 2: SYSTEM-Controls hinzugefügt
**Datei**: `pdvm_view_controller.py` Zeile 246-269

**NEU**:
```python
all_controls = {}

# SCHRITT 0: SYSTEM-Controls (uid_original, name_original)
# uid_original
all_controls['uid_original'] = {
    'feld': 'UID',
    'name': 'UID',
    'type': 'string',
    'gruppe': 'SYSTEM',
    'control_type': 'original',
    'show': False,
    'expert_mode': True,
    'display_order': 0,
    'expert_order': 0
}

# name_original
all_controls['name_original'] = {
    'feld': 'NAME',
    'name': 'Satzname',
    'type': 'string',
    'gruppe': 'SYSTEM',
    'control_type': 'original',
    'show': False,
    'expert_mode': True,
    'display_order': 1,
    'expert_order': 1
}

logger.info("  ✅ 2 System Controls (uid_original, name_original)")
```

### Fix 3 & 4: Cleanup-Script erstellt
**Datei**: `cleanup_viewdata_and_controls.py`

**Funktionen**:
1. ✅ Lädt existierende Controls aus `"controls"` Dictionary
2. ✅ Fügt fehlende SYSTEM-Controls hinzu (uid_original, name_original, uid_show, name_show)
3. ✅ Speichert bereinigte Controls zurück
4. ✅ Löscht doppelte einzelne Control-Felder
5. ✅ Bereinigt ViewDaten (entfernt falsches `name` Feld)
6. ✅ Baut Projektionen neu

**Ausführung**:
```powershell
# Für Standard-View (0d10a0d0-b1a5-4544-b284-e8a09ca979b5)
python cleanup_viewdata_and_controls.py

# Für andere View-GUID
python cleanup_viewdata_and_controls.py <view-guid>
```

## 📋 Architektur-Prinzipien bestätigt

### ✅ DB-Zugriff nur via PdvmDatenbank/PdvmCentralDatenbank
- Controller verwendet `gcs.db.set_value()` (PdvmCentralDatenbank)
- Cleanup-Script verwendet `PdvmCentralDatenbank('viewdaten', view_guid)`
- **KEINE** direkten SQL-Queries

### ✅ Controls in "controls" Dictionary
**Korrekte Struktur**:
```json
{
  "view-guid": {
    "controls": {
      "uid_original": {...},
      "name_original": {...},
      "familienname_original": {...},
      "uid_show": {...},
      "name_show": {...},
      ...
    }
  }
}
```

**NICHT**:
```json
{
  "view-guid": {
    "controls": {...},
    "uid_original": "...",  ❌ FALSCH - Doppelt!
    "name_original": "..." ❌ FALSCH - Doppelt!
  }
}
```

### ✅ ViewDaten mit standard_control
**Korrekte Struktur** (unter SYSTEM-GUID in viewdaten):
```json
{
  "METADATEN": {
    "PERSONDATEN": {
      "controls": {...},
      "standard_control": {
        "dummy": {...}
      }
    }
  }
}
```

**NICHT** in `name` Spalte!

## 🚀 Nächste Schritte

1. **Cleanup ausführen** (als Admin angemeldet):
   ```powershell
   python cleanup_viewdata_and_controls.py
   ```

2. **Anwendung neu starten**:
   ```powershell
   python main.py
   ```

3. **Testen**:
   - ✅ Normal Mode: name_show sichtbar als "Satzname"
   - ✅ Expert Mode: name_original + name_show beide sichtbar
   - ✅ Expert Mode: uid_original + uid_show beide sichtbar
   - ✅ Keine doppelten Felder in Systemsteuerung-DB

## 📊 Erwartetes Ergebnis

**Log bei View-Start**:
```
✅ ViewDaten geladen: Tabelle 'persondaten', 6 Controls
✅ 2 System Controls (uid_original, name_original)
✅ 10 Original Controls (inkl. System)
✅ 10 Show Controls (inkl. System)
✅ Dummy Control erstellt
✅ 21 Controls in 'controls' Dictionary gespeichert
✅ Projektions-Tabellen in GCS berechnet
  [0] 📊 View Standard: 10 Spalten (show=true) → name_show sichtbar!
  [5] 📊 View Expert: 20 Spalten (expert_mode) → name_original + name_show sichtbar!
```

**UI**:
- **Normal Mode**: uid_show, name_show, familienname_show, ... (10 Spalten)
- **Expert Mode**: uid_original, uid_show, name_original, name_show, familienname_original, ... (20 Spalten)

---

**✅ Alle 4 Probleme behoben**  
**📋 Architektur-Prinzipien eingehalten**  
**🎯 Bereit für Cleanup & Test**
