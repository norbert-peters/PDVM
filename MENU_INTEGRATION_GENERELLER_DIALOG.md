# Menü-Integration: Generellen Dialog erstellen

## Handler-Datei
**Pfad**: `handlers/handler_create_genereller_dialog.py`

## Menü-Eintrag Beispiel

### SQL-Insert für sys_menudaten

```sql
-- 1. Command erstellen
INSERT INTO sys_commanddaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
VALUES (
    '<neue-command-guid>',
    'Generellen Dialog erstellen',
    '{"COMMAND": {"HANDLER": "handler_create_genereller_dialog", "PARAMS": {}}}',
    <timestamp>,
    <timestamp>,
    0,
    '',
    0,
    999999999.0
);

-- 2. Menü-Item erstellen
INSERT INTO sys_menudaten (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
VALUES (
    '<neue-item-guid>',
    'Generellen Dialog erstellen',
    '{
        "GRUND": {
            "<item-guid>": {
                "GUID": "<item-guid>",
                "TYPE": "COMMAND",
                "LABEL": "Generellen Dialog erstellen",
                "SORT_ORDER": 100,
                "ICON": "🔧",
                "COMMAND_GUID": "<neue-command-guid>",
                "VISIBLE": true,
                "ENABLED": true,
                "TOOLTIP": "Erstellt neue Frame/View/Dialog-Kombination für generelle Dialoge"
            }
        }
    }',
    <timestamp>,
    <timestamp>,
    0,
    '',
    0,
    999999999.0
);
```

### JSON-Struktur (für Menü-Editor)

```json
{
    "COMMAND": {
        "HANDLER": "handler_create_genereller_dialog",
        "PARAMS": {}
    }
}
```

## Verwendung

### Im Menü eintragen:
1. **Handler**: `handler_create_genereller_dialog`
2. **Parameter**: `{}` (leer)
3. **Icon**: 🔧
4. **Label**: "Generellen Dialog erstellen"

### Workflow beim Aufruf:
1. System ruft `execute(params, context, gcs)` auf
2. Wizard öffnet sich mit GCS-Zugriff
3. User gibt Namen ein
4. User wählt bestehende View ODER erstellt neue
5. User wählt Dialog (last_selected wird vorgeschlagen)
6. System erstellt Frame/View mit Template-Methode `anlegen_mit_template()`
7. Erfolgs-Message mit allen GUIDs

## Features

### Template-basierte Satz-Erstellung
```python
# View erstellen
view_db = PdvmCentralDatenbank('sys_viewdaten')
view_guid = view_db.anlegen_mit_template()  # ← verwendet Template 55555...
view_db.set_value('ROOT', 'TABLE', table_name)
view_db.save_all_values()

# Frame erstellen
frame_db = PdvmCentralDatenbank('sys_framedaten')
frame_guid = frame_db.anlegen_mit_template()  # ← verwendet Template 55555...
frame_db.set_value('ROOT', 'VIEW_GUID', view_guid)
frame_db.save_all_values()
```

### Last-Selected Mechanismus
```python
# Aus GCS laden
last_guid = gcs.field_value('LAST_DIALOG_GUID')

# In GCS speichern
gcs.set_field_value('LAST_DIALOG_GUID', dialog_guid)
gcs._db.save_all_values()
```

## Voraussetzungen

### Benötigte Templates (55555...)
- ✅ **sys_viewdaten**: ROOT_CONTROLS mit TABLE, VIEW_GUID, etc.
- ✅ **sys_framedaten**: ROOT_CONTROLS mit VIEW_GUID, DIALOG_GUID, etc.

### GCS-Systemsteuerung
- ✅ GCS muss initialisiert sein (nach Login)
- ✅ `LAST_DIALOG_GUID` für Vortrag (optional)

## Test

### Manueller Test:
```python
# Im System-Menü aufrufen
# → Dialog öffnet sich
# → Namen eingeben: "Test Dialog"
# → Neue View: "test_tabelle"
# → Dialog auswählen
# → Ausführen

# Ergebnis:
# ✅ Frame-GUID: xxxxx...
# ✅ View-GUID: yyyyy...
# ✅ Dialog-GUID: zzzzz...
```

## Empfohlene Menü-Position

```
System
├─ Einstellungen
├─ Benutzerverwaltung
├─ 🔧 Generellen Dialog erstellen  ← NEU
└─ Beenden
```

## Nächste Schritte

1. ✅ Handler erstellt: `handler_create_genereller_dialog.py`
2. ⏳ Menü-Eintrag erstellen (Command + Item)
3. ⏳ Test über Menü
4. ⏳ sys_mandanten Frame über Handler erstellen
