# Frame-Struktur Migration - Zusammenfassung

## ✅ ABGESCHLOSSEN (18.11.2025)

### 1. Template-System erstellt
- **Datei**: `create_frame_templates.py`
- **Datenbank**: `pdvm_system.db` (nicht datenbank.db!)
- **Template-GUID**: `55555555-5555-5555-5555-555555555555`
- **Inhalt**:
  - 5 Control-Templates (text, dropdown, datetime, viewtable, number)
  - 15 ROOT_CONTROLS (Frame-Konfiguration)
  - 17 CONTROL_PROPERTIES (für Frame-Editor)

### 2. Migration durchgeführt
- **Datei**: `migrate_frame_structure.py`
- **Status**: ✅ LIVE-Migration erfolgreich
- **Ergebnis**: 5 Frames migriert
  - 3 Frames: PERSONDATEN/FINANZDATEN Controls (GUID-basiert)
  - 2 Spezial-Frames: Template + View-Editor (unverändert)

### 3. Frame-Editor implementiert
- **Datei**: `pdvm_frame_editor.py`
- **Architektur**: Adaptation von PdvmViewEditor
- **Features**:
  - 2 Tabs: ROOT-Felder + Tabellen & Controls
  - Hierarchische Baumstruktur (Tabellen → Controls)
  - Drag & Drop (nur innerhalb derselben Tabelle)
  - GUID-basierte Control-Verwaltung
  - Template-System für neue Controls
  - Automatisches display_order Management
- **Status**: ✅ Registriert in `pdvm_genereller_dialog.py`

### 4. Input-Controls angepasst
- **Datei**: `pdvm_input_controls_manager.py`
- **Methode**: `_load_controls_meta()` komplett überarbeitet
- **Änderungen**:
  - Liest neue Struktur: `METADATEN[TABELLE][controls][GUID]`
  - Extrahiert Properties: table, gruppe, feld, label, display_order, etc.
  - Generiert field_key für Kompatibilität: `f"{table}_{gruppe}_{feld}"`
  - Sortiert nach display_order

- **Datei**: `pdvm_input_control.py`
- **Änderungen**:
  - Liest table/gruppe/feld direkt aus meta
  - Fallback: Parst field_key (Kompatibilität)

## Neue Frame-Struktur

### ALT (vor Migration):
```python
METADATEN = {
    'PERSONDATEN_PERSDATEN_ANREDE': {
        'label': 'Anrede',
        'order': 10,
        'tab': 1,
        'type': 'dropdown',
        ...
    }
}
```

### NEU (nach Migration):
```python
METADATEN = {
    'PERSONDATEN': {
        'controls': {
            '41e53555-020c-4f3d-91f9-729268d78065': {
                'table': 'PERSONDATEN',
                'gruppe': 'PERSDATEN',
                'feld': 'ANREDE',
                'label': 'Anrede',
                'display_order': 10,
                'tab': 1,
                'type': 'dropdown',
                ...
            }
        }
    },
    'FINANZDATEN': {
        'controls': {
            ...
        }
    }
}
```

## Vorteile der neuen Struktur

1. **GUID-basierte Keys**: Keine Namenskonflikte, bessere Referenzierbarkeit
2. **Hierarchische Organisation**: Tabellen → Controls (klarer strukturiert)
3. **Einheitliche Architektur**: View-Editor + Frame-Editor nutzen gleiche Patterns
4. **Metadaten als Properties**: table/gruppe/feld nicht mehr im Key, sondern als Eigenschaften
5. **Flexiblere Verwaltung**: display_order statt order (konsistent mit Views)
6. **Editor-Unterstützung**: Vollständiger grafischer Editor verfügbar

## Getestete Komponenten

✅ Template-Erstellung funktioniert
✅ Migration läuft (dry-run + live)
✅ Frame-Editor registriert
✅ Input-Controls lesen neue Struktur

## Nächste Schritte

1. **Testen**: Input-Controls im UI testen (User macht das)
2. **Frame-Editor testen**: Neues Frame erstellen/bearbeiten
3. **Validierung**: Sicherstellen dass alle Controls korrekt dargestellt werden

## Dateien

### Neue Dateien:
- `create_frame_templates.py` - Template-Initialisierung
- `migrate_frame_structure.py` - Migrations-Skript
- `pdvm_frame_editor.py` - Frame-Editor UI
- `inspect_frame_structure.py` - Debug-Tool
- `test_frame_structure_read.py` - Test-Skript

### Modifizierte Dateien:
- `pdvm_genereller_dialog.py` - Frame-Editor registriert
- `pdvm_input_controls_manager.py` - Neue Struktur lesen
- `pdvm_input_control.py` - Properties direkt verwenden

### Datenbanken:
- `pdvm_system.db` - Enthält sys_framedaten (System-Tabelle)
- Migration hat bestehende Frames aktualisiert (mit Backup in daten_backup)

## Rückgängig machen (falls nötig)

Falls Probleme auftreten, kann die Migration zurückgerollt werden:
```sql
-- In pdvm_system.db
UPDATE sys_framedaten 
SET daten = daten_backup 
WHERE uid IN (
    '4078079f-4028-45ed-879c-3c779ecf3d0d',
    '487dc202-4853-4d77-96cd-dd6b4a7330f3',
    '794cbfc3-ccb6-4681-b432-efa9f44682c8'
);
```

---

**Status**: ✅ BEREIT FÜR USER-TEST
