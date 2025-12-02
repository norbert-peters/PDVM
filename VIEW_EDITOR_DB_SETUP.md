# View-Editor Datenbank-Setup

## Benötigte Datensätze

### 1. Control-Templates (sys_viewdaten)
**GUID:** `55555555-5555-5555-5555-555555555555`

```sql
INSERT INTO sys_viewdaten (uid, daten, name, created_at, modified_at, historisch)
VALUES (
  '55555555-5555-5555-5555-555555555555',
  '{"ROOT": {}, "METADATEN": {"TEMPLATES": {"base_text": {"type": "string", "default": "", "dropdown": null, "control_type": "base", "expert_mode": true, "show": true, "searchable": true, "sortable": true, "sortDirection": "asc", "sortByOriginal": false, "filterType": "contains"}, "base_date": {"type": "date", "default": null, "dropdown": null, "control_type": "base", "expert_mode": true, "show": true, "searchable": true, "sortable": true, "sortDirection": "desc", "sortByOriginal": true, "filterType": "dateRange"}, "base_number": {"type": "number", "default": 0, "dropdown": null, "control_type": "base", "expert_mode": true, "show": true, "searchable": true, "sortable": true, "sortDirection": "asc", "sortByOriginal": false, "filterType": "range"}, "base_dropdown": {"type": "dropdown", "default": "", "dropdown": {"table": "dropdowndaten", "key": "", "value": ""}, "control_type": "base", "expert_mode": true, "show": true, "searchable": true, "sortable": true, "sortDirection": "asc", "sortByOriginal": false, "filterType": "dropdown"}, "show_text": {"type": "string", "default": "", "dropdown": null, "control_type": "show", "expert_mode": false, "show": true, "searchable": false, "sortable": true, "sortDirection": "asc", "sortByOriginal": false, "filterType": "none"}}}}',
  'Control-Templates',
  datetime('now'),
  datetime('now'),
  0
);
```

### 2. Frame-Daten (sys_framedaten)
**GUID:** `3be5d463-c0ea-4b71-b486-f2d9f647d527`

```sql
INSERT INTO sys_framedaten (uid, daten, name, created_at, modified_at, historisch)
VALUES (
  '3be5d463-c0ea-4b71-b486-f2d9f647d527',
  '{"ROOT": {"ROOT_TABLE": "sys_viewdaten", "VIEW_GUID": "ce843d57-ec60-4814-9c7c-118aec7deab0", "DIALOG_GUID": "0e1cf621-38bc-4671-8027-eaae9b9ec327", "HEADER_TEXT": "Views pflegen", "EDIT_TYPE": "view_editor", "EDIT_TABS": 2, "EDIT_TAB_LABEL_01": "Basis", "EDIT_TAB_LABEL_02": "Felder & Controls", "DISPLAY_ST": "only_date", "DISPLAY_TIME_SHORT": true}, "METADATEN": {"ROOT_CONTROLS": [{"control_key": "VIEW_TABLE", "gruppe": "ROOT", "feld": "VIEW_TABLE", "label": "View-Tabelle", "control_type": "text", "readonly": false, "display_order": 1}, {"control_key": "NO_DATA", "gruppe": "ROOT", "feld": "NO_DATA", "label": "Keine Datenstruktur (System-Tabelle)", "control_type": "checkbox", "readonly": false, "display_order": 2}], "CONTROL_PROPERTIES": [{"property": "gruppe", "label": "Gruppe", "control_type": "text", "required": true, "display_order": 1}, {"property": "feld", "label": "Feld", "control_type": "text", "required": true, "display_order": 2}, {"property": "name", "label": "Anzeigename", "control_type": "text", "required": true, "display_order": 3}, {"property": "type", "label": "Datentyp", "control_type": "dropdown", "options": ["string", "date", "number", "dropdown"], "required": true, "display_order": 4}, {"property": "control_type", "label": "Control-Typ", "control_type": "dropdown", "options": ["base", "show"], "required": true, "display_order": 5}, {"property": "show", "label": "Anzeigen", "control_type": "checkbox", "required": false, "display_order": 6}, {"property": "expert_mode", "label": "Expert-Modus", "control_type": "checkbox", "required": false, "display_order": 7}, {"property": "display_order", "label": "Anzeigereihenfolge", "control_type": "number", "required": false, "display_order": 8}, {"property": "searchable", "label": "Durchsuchbar", "control_type": "checkbox", "required": false, "display_order": 9}, {"property": "sortable", "label": "Sortierbar", "control_type": "checkbox", "required": false, "display_order": 10}, {"property": "sortDirection", "label": "Sort-Richtung", "control_type": "dropdown", "options": ["asc", "desc"], "required": false, "display_order": 11}, {"property": "filterType", "label": "Filter-Typ", "control_type": "dropdown", "options": ["contains", "exact", "dateRange", "range", "dropdown", "none"], "required": false, "display_order": 12}]}}',
  'View-Editor Frame',
  datetime('now'),
  datetime('now'),
  0
);
```

### 3. Dialog-Daten (sys_dialogdaten)
**GUID:** `0e1cf621-38bc-4671-8027-eaae9b9ec327`

```sql
INSERT INTO sys_dialogdaten (uid, daten, name, created_at, modified_at, historisch)
VALUES (
  '0e1cf621-38bc-4671-8027-eaae9b9ec327',
  '{"ROOT": {"FRAME_GUID": "3be5d463-c0ea-4b71-b486-f2d9f647d527", "POSITION_X": 100, "POSITION_Y": 100, "WIDTH": 1200, "HEIGHT": 800, "MAXIMIZED": false}, "METADATEN": {}}',
  'View-Editor Dialog',
  datetime('now'),
  datetime('now'),
  0
);
```

### 4. View-Daten für View-Editor (sys_viewdaten)
**GUID:** `ce843d57-ec60-4814-9c7c-118aec7deab0`

```sql
INSERT INTO sys_viewdaten (uid, daten, name, created_at, modified_at, historisch)
VALUES (
  'ce843d57-ec60-4814-9c7c-118aec7deab0',
  '{"ROOT": {"VIEW_TABLE": "sys_viewdaten", "NO_DATA": true}, "METADATEN": {"standard_control": {"dummy": {"gruppe": "SYSTEM", "feld": "DUMMY", "name": "Dummy", "type": "string", "default": "keine Daten", "dropdown": null, "control_type": "base", "expert_mode": true, "show": false, "display_order": 0, "expert_order": 0, "searchable": true, "sortable": true, "sortDirection": "asc", "sortByOriginal": false, "filterType": "contains"}}}}',
  'View-Editor View',
  datetime('now'),
  datetime('now'),
  0
);
```

## Test-Menüpunkt hinzufügen

Um den View-Editor zu testen, füge einen Menüpunkt hinzu:

```sql
-- Neuer Menüpunkt in sys_menudaten
INSERT INTO sys_menudaten (uid, daten, name, created_at, modified_at, historisch)
VALUES (
  'menu-item-view-editor-test',
  '{"ROOT": {"PARENT": "ROOT", "TYPE": "item", "TITLE": "View Editor (Test)", "COMMAND": "open_dialog", "SORT_ORDER": 999}, "METADATEN": {"COMMAND_PARAMS": {"frame_guid": "3be5d463-c0ea-4b71-b486-f2d9f647d527"}}}',
  'View Editor Test',
  datetime('now'),
  datetime('now'),
  0
);
```

## Verwendung

Nach dem Einfügen der Datensätze:

1. **Anwendung starten**: `python pdvm_main.py`
2. **Menü öffnen**: "View Editor (Test)" anklicken
3. **Dialog öffnet sich** mit:
   - Tab 1: Basis (VIEW_TABLE, NO_DATA bearbeiten)
   - Tab 2: Felder & Controls (controls/standard_control verwalten)

## Hinweise

- **Templates** werden aus GUID `55555555...` geladen
- **VIEW_TABLE** muss GROSSBUCHSTABEN verwenden für METADATEN-Key
- **NO_DATA=true** für System-Tabellen ohne Gruppe/Feld-Struktur
- **Controls** werden mit Template-System angelegt
