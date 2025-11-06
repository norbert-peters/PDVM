# ✅ V2 Namenskonvention Korrektur

**Datum**: 04.11.2025  
**Status**: ✅ **KORRIGIERT**

---

## 🎯 Problem & Lösung

In V2 gibt es eine **spezifische Namenskonvention**:
- **Gruppennamen**: GROSSBUCHSTABEN (z.B. `ROOT`, `TAB01`, `TAB02`)
- **Feldnamen**: **unterschiedlich je nach Gruppe!**
  - `ROOT` Gruppe: Felder in **GROSSBUCHSTABEN** (z.B. `ACTIVE_TAB`, `TAB_COUNT`)
  - `TAB01/TAB02` Gruppen: Felder in **kleinbuchstaben** (z.B. `tab_type`, `tab_title`, `view_guid`)

**Beispiel aus echten V2-Daten**:
```json
{
  "ROOT": {
    "ACTIVE_TAB": 0,           // ✅ ROOT-Felder in GROSS
    "TAB_COUNT": 2             // ✅ ROOT-Felder in GROSS
  },
  "TAB01": {
    "tab_type": "view",        // ✅ TAB-Felder in klein!
    "tab_title": "Übersicht",  // ✅ TAB-Felder in klein!
    "view_guid": "0d10a0d0..." // ✅ TAB-Felder in klein!
  },
  "TAB02": {
    "tab_type": "edit",        // ✅ TAB-Felder in klein!
    "tab_title": "Bearbeiten", // ✅ TAB-Felder in klein!
    "selected_guid": "58c0a..." // ✅ TAB-Felder in klein!
  }
}
```

Die Dialog-Migration hatte inkonsistente Feldnamen:
- ❌ `'active_tab'` → ✅ `'ACTIVE_TAB'` (ROOT-Gruppe)
- ❌ `'tab_count'` → ✅ `'TAB_COUNT'` (ROOT-Gruppe)
- ❌ `'TAB_TYPE'` → ✅ `'tab_type'` (TAB01/TAB02-Gruppen)
- ❌ `'TAB_TITLE'` → ✅ `'tab_title'` (TAB01/TAB02-Gruppen)
- ❌ `'VIEW_GUID'` → ✅ `'view_guid'` (TAB01/TAB02-Gruppen)
- ❌ `'SELECTED_GUID'` → ✅ `'selected_guid'` (TAB01/TAB02-Gruppen)

---

## 🔧 Durchgeführte Korrekturen

### 1. sys_dialogdaten - ROOT Gruppe

**Zeile 296**: Prüfung ob Dialogdaten existieren
```python
# ❌ ALT
active_tab_test = self.dialogdaten_db.get_static_value('ROOT', 'active_tab')

# ✅ NEU
active_tab_test = self.dialogdaten_db.get_static_value('ROOT', 'ACTIVE_TAB')
```

**Zeile 302-304**: Initiale ROOT-Parameter erstellen
```python
# ❌ ALT
self.dialogdaten_db.set_value('ROOT', 'active_tab', 0)
self.dialogdaten_db.set_value('ROOT', 'tab_count', 2)

# ✅ NEU
self.dialogdaten_db.set_value('ROOT', 'ACTIVE_TAB', 0)
self.dialogdaten_db.set_value('ROOT', 'TAB_COUNT', 2)
```

### 2. sys_dialogdaten - TAB01 Gruppe

**Zeile 306-309**: Tab01 (View) Parameter erstellen
```python
# ❌ ALT
self.dialogdaten_db.set_value('Tab01', 'tab_type', 'view')
self.dialogdaten_db.set_value('Tab01', 'tab_title', 'Übersicht')
self.dialogdaten_db.set_value('Tab01', 'view_guid', self.view_guid)

# ✅ NEU - Gruppe GROSS, Felder klein!
self.dialogdaten_db.set_value('TAB01', 'tab_type', 'view')
self.dialogdaten_db.set_value('TAB01', 'tab_title', 'Übersicht')
self.dialogdaten_db.set_value('TAB01', 'view_guid', self.view_guid)
```

**WICHTIG**: Gruppennamen GROSS (`'TAB01'`), aber Feldnamen **klein** (`'tab_type'`)!

### 3. sys_dialogdaten - TAB02 Gruppe

**Zeile 311-314**: Tab02 (Edit) Parameter erstellen
```python
# ❌ ALT
self.dialogdaten_db.set_value('Tab02', 'tab_type', 'edit')
self.dialogdaten_db.set_value('Tab02', 'tab_title', 'Bearbeiten')
self.dialogdaten_db.set_value('Tab02', 'selected_guid', None)

# ✅ NEU - Gruppe GROSS, Felder klein!
self.dialogdaten_db.set_value('TAB02', 'tab_type', 'edit')
self.dialogdaten_db.set_value('TAB02', 'tab_title', 'Bearbeiten')
self.dialogdaten_db.set_value('TAB02', 'selected_guid', None)
```

### 4. Tab-Initialisierung

**Zeile 331**: Tab-Anzahl laden
```python
# ❌ ALT
tab_count, _ = self.dialogdaten_db.get_value('ROOT', 'tab_count')

# ✅ NEU
tab_count = self.dialogdaten_db.get_static_value('ROOT', 'TAB_COUNT')
```

**BONUS**: Auch `get_value()` → `get_static_value()` korrigiert (dialogdaten ist NICHT historisch!)

### 5. View-Tab Titel

**Zeile 377**: Tab01-Titel laden
```python
# ❌ ALT
tab_title, _ = self.dialogdaten_db.get_value('Tab01', 'tab_title')

# ✅ NEU - Gruppe GROSS, Feld klein!
tab_title = self.dialogdaten_db.get_static_value('TAB01', 'tab_title')
```

### 6. Edit-Tab Titel

**Zeile 449**: Tab02-Titel laden
```python
# ❌ ALT
tab_title, _ = self.dialogdaten_db.get_value('Tab02', 'tab_title')

# ✅ NEU - Gruppe GROSS, Feld klein!
tab_title = self.dialogdaten_db.get_static_value('TAB02', 'tab_title')
```

### 7. Tab-Wechsel Handler

**Zeile 706**: Aktiven Tab speichern
```python
# ❌ ALT
self.dialogdaten_db.set_value('ROOT', 'active_tab', index)

# ✅ NEU
self.dialogdaten_db.set_value('ROOT', 'ACTIVE_TAB', index)
```

---

## 📊 Korrektur-Übersicht

| Bereich | Alte Namen | Neue Namen | Status |
|---------|------------|------------|--------|
| **ROOT Gruppe** | `'Root'` + `'active_tab'`, `'tab_count'` | `'ROOT'` + `'ACTIVE_TAB'`, `'TAB_COUNT'` | ✅ |
| **TAB01 Gruppe** | `'Tab01'` + `'tab_type'`, `'tab_title'`, `'view_guid'` | `'TAB01'` + `'tab_type'`, `'tab_title'`, `'view_guid'` | ✅ |
| **TAB02 Gruppe** | `'Tab02'` + `'tab_type'`, `'tab_title'`, `'selected_guid'` | `'TAB02'` + `'tab_type'`, `'tab_title'`, `'selected_guid'` | ✅ |
| **sys_framedaten** | Bereits korrekt | `'ROOT'` + `'ROOT_TABLE'`, `'VIEW_GUID'`, `'DIALOG_GUID'`, `'HEADER_TEXT'`, `'EDIT_TYPE'` | ✅ |

---

## 🔍 Zusätzliche Korrekturen

### get_value() → get_static_value()

Alle `get_value()` Aufrufe für **sys_dialogdaten** wurden auf `get_static_value()` korrigiert:

```python
# ❌ ALT - Tuple-Unpacking für nicht-historische Tabelle
tab_count, _ = self.dialogdaten_db.get_value('ROOT', 'TAB_COUNT')

# ✅ NEU - Direkt ohne Tuple
tab_count = self.dialogdaten_db.get_static_value('ROOT', 'TAB_COUNT')
```

**Grund**: `sys_dialogdaten` ist **NICHT historisch** (keine AB-Daten), daher `get_static_value()` verwenden.

---

## ✅ Validierung

### Keine Syntax-Fehler
```
✅ v2_pdvm_genereller_dialog.py: No errors found
```

### Alle Feldnamen konsistent
```python
# sys_framedaten (ROOT Gruppe) - Felder in GROSS
✅ 'ROOT' + 'ROOT_TABLE'
✅ 'ROOT' + 'VIEW_GUID'
✅ 'ROOT' + 'DIALOG_GUID'
✅ 'ROOT' + 'HEADER_TEXT'
✅ 'ROOT' + 'EDIT_TYPE'

# sys_dialogdaten (ROOT Gruppe) - Felder in GROSS
✅ 'ROOT' + 'ACTIVE_TAB'
✅ 'ROOT' + 'TAB_COUNT'

# sys_dialogdaten (TAB01 Gruppe) - Felder in klein!
✅ 'TAB01' + 'tab_type'
✅ 'TAB01' + 'tab_title'
✅ 'TAB01' + 'view_guid'

# sys_dialogdaten (TAB02 Gruppe) - Felder in klein!
✅ 'TAB02' + 'tab_type'
✅ 'TAB02' + 'tab_title'
✅ 'TAB02' + 'selected_guid'

# GCS Systemsteuerung - Felder in GROSS
✅ '<frame_guid>' + 'LAST_SELECTION'
```

---

## 🎯 Wichtige Erkenntnisse

### V2 Namenskonventionen (WICHTIG!)

**Tabellennamen**: Präfix `sys_` + Kleinbuchstaben
```python
'sys_framedaten'
'sys_dialogdaten'
'sys_viewdaten'
'sys_menudaten'
```

**Gruppennamen**: IMMER GROSSBUCHSTABEN
```python
'ROOT'           # Hauptgruppe
'TAB01', 'TAB02', 'TAB03', ...  # Tab-Gruppen
'METADATEN'      # Metadaten-Gruppe
```

**Feldnamen**: **Unterschiedlich je nach Gruppe!**

**ROOT-Gruppe** → Felder in **GROSSBUCHSTABEN**:
```python
'ROOT_TABLE'      # sys_framedaten
'VIEW_GUID'       # sys_framedaten
'ACTIVE_TAB'      # sys_dialogdaten
'TAB_COUNT'       # sys_dialogdaten
```

**TAB-Gruppen (TAB01, TAB02, ...)** → Felder in **kleinbuchstaben**:
```python
'tab_type'        # "view" oder "edit"
'tab_title'       # "Übersicht", "Bearbeiten"
'view_guid'       # View-GUID für TAB01
'selected_guid'   # Ausgewählter Datensatz für TAB02
```

### Historische vs. Nicht-Historische Tabellen

**Nicht-historisch** (get_static_value):
- `sys_framedaten` ✅
- `sys_dialogdaten` ✅
- `sys_viewdaten` ✅
- `sys_menudaten` ✅
- GCS `_db` (systemsteuerung) ✅

**Historisch** (get_value + tuple):
- Geschäftsdaten (persondaten, finanzdaten, etc.) ✅
- Matrix-Daten mit AB-Datum ✅

---

## 📝 Checkliste für zukünftige Module

Bei Migration von V1 nach V2:

- [ ] Tabellennamen: `framedaten` → `sys_framedaten`
- [ ] Gruppennamen: `Root` → `ROOT`, `Tab01` → `TAB01` (IMMER GROSS!)
- [ ] Feldnamen in ROOT-Gruppe: `active_tab` → `ACTIVE_TAB` (GROSS!)
- [ ] Feldnamen in TAB-Gruppen: Bleiben **klein** (`tab_type`, `tab_title`, `view_guid`)
- [ ] DB-Zugriff: `get_value()` → `get_static_value()` für sys_* Tabellen
- [ ] Tuple-Unpacking entfernen bei get_static_value
- [ ] GCS Import: `global_gcs` → `v2_central_systemsteuerung`

---

## 🚀 Nächste Schritte

1. ✅ Dialog-System mit korrekten Feldnamen testen
2. ⏳ Input-Controls-Manager auf V2 migrieren (Feldnamen beachten!)
3. ⏳ Menu-Editor auf V2 migrieren (Feldnamen beachten!)

---

**Status**: ✅ **V2 NAMENSKONVENTION KORREKT ANGEWENDET**  

**Regel**: 
- Gruppen: **IMMER GROSS** (`ROOT`, `TAB01`, `TAB02`)
- Felder in ROOT: **GROSS** (`ACTIVE_TAB`, `TAB_COUNT`)
- Felder in TABs: **klein** (`tab_type`, `tab_title`, `view_guid`, `selected_guid`)

**Datei**: `v2_pdvm_genereller_dialog.py` ist bereit für Testing!
