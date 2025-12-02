# PFAD-SYSTEM Implementierung - Zusammenfassung

## 🎯 Ziel

Flexibles System für variable METADATEN-Strukturen im Editor, unabhängig von Datentyp (Views, Frames, etc.).

## 🏗️ Architektur

### Template-PFADE (55555...)
```json
{
  "METADATEN": {
    "PFADE": {
      "normal": "{ROOT_TABLE}.controls",
      "standard": "{ROOT_TABLE}.standard_controls",
      "template": "TEMPLATES"
    }
  }
}
```

### Platzhalter
- `{ROOT_TABLE}` → wird ersetzt durch ROOT.ROOT_TABLE in GROSSBUCHSTABEN
- Beispiel: `{ROOT_TABLE}.controls` → `PERSONDATEN.controls`

### Datenfluss
```
1. Editor initialisiert
   ↓
2. Template-PFADE laden (aus 55555...)
   ↓
3. Platzhalter ersetzen ({ROOT_TABLE} → PERSONDATEN)
   ↓
4. Struktur sicherstellen (_ensure_path_exists)
   ↓
5. Controls aus Pfad laden (_navigate_path)
   ↓
6. Tree-View befüllen
```

## 📁 Implementierte Methoden

### `_initialize_metadata_structure()`
- Lädt PFADE aus Template
- Erstellt Struktur für jeden Pfad
- Fehler wenn PFADE fehlen im Template

### `_resolve_path_template(pfad_template)`
- Ersetzt `{ROOT_TABLE}` durch aktuellen Wert
- Beispiel: `"{ROOT_TABLE}.controls"` → `"PERSONDATEN.controls"`

### `_ensure_path_exists(pfad)`
- Erstellt fehlende Struktur in METADATEN
- Navigiert durch Pfad-Teile
- Erstellt Dict für jede Ebene

### `_navigate_path(pfad)`
- Navigiert durch METADATEN anhand Pfad
- Gibt Controls-Dict zurück
- Fehler-sicher mit Logging

### `_set_control_value_by_path(pfad, control_key, property_key, value)`
- Setzt Control-Property über Pfad
- Verwendet `_navigate_path()` intern
- Logging für Nachvollziehbarkeit

## 🔄 Änderungen

### `_load_data()`
- ✅ Ruft `_initialize_metadata_structure()` auf
- ✅ Erstellt Pfad-Struktur automatisch

### `_refresh_field_list()`
- ✅ Verwendet Template-PFADE
- ✅ Durchläuft alle Pfade (normal, standard, etc.)
- ✅ Zeigt Pfad im Tree: `"📁 normal (PERSONDATEN.controls)"`

### `_on_tree_item_clicked()`
- ✅ Speichert Pfad in item_data
- ✅ Verwendet Pfad statt field_type

### `_create_control_group()`
- ✅ Parameter: `pfad` statt `field_type`
- ✅ Callbacks verwenden `_set_control_value_by_path()`

## ✅ Vorteile

1. **Flexibel**: Beliebige METADATEN-Strukturen möglich
2. **Zentral**: Pfade im Template definiert (55555...)
3. **Automatisch**: Struktur wird erstellt wenn nicht vorhanden
4. **Sicher**: Fehler wenn Template-PFADE fehlen
5. **Erweiterbar**: Neue Pfade ohne Code-Änderung

## 📝 Nutzung

### Neuer Datensatz
```python
# Editor initialisiert mit frame_guid + table_name
editor = PdvmSystemEditor(frame_guid, 'persondaten')

# → PFADE aus Template laden
# → {ROOT_TABLE} ersetzen durch PERSONDATEN
# → Struktur erstellen: METADATEN.PERSONDATEN.controls
# → Struktur erstellen: METADATEN.PERSONDATEN.standard_controls
```

### Pfad nicht vorhanden
```python
# _ensure_path_exists() erstellt automatisch:
data['METADATEN']['PERSONDATEN'] = {}
data['METADATEN']['PERSONDATEN']['controls'] = {}
```

### Template-PFADE fehlen
```python
# → ValueError mit klarer Fehlermeldung
# → Benutzer muss Template (55555...) korrigieren
```

## 🧪 Migration

**Datei**: `migrate_add_template_pfade.py`

Fügt PFADE in Templates hinzu:
- sys_viewdaten (55555...)
- sys_framedaten (55555...)

Verwendet direkten SQLite-Zugriff (kein GCS nötig).

**Ausführung**: `python migrate_add_template_pfade.py`

## 🔧 Technische Details

### Pfad-Navigation
```python
# Pfad: "PERSONDATEN.controls"
parts = ["PERSONDATEN", "controls"]
current = data['METADATEN']
current = current['PERSONDATEN']  # 1. Ebene
current = current['controls']     # 2. Ebene (Controls-Dict)
```

### Platzhalter-Ersetzung
```python
pfad_template = "{ROOT_TABLE}.controls"
root_table = "persondaten"
root_table_upper = root_table.upper()  # "PERSONDATEN"
pfad = pfad_template.replace('{ROOT_TABLE}', root_table_upper)
# → "PERSONDATEN.controls"
```

## 🚀 Nächste Schritte

1. ✅ Migration ausgeführt (PFADE in Templates)
2. ⏸️ Testen mit echter Anwendung
3. ⏸️ Weitere Pfade bei Bedarf (z.B. für Menüs)
4. ⏸️ Pfad-Editor im Template-Modus?

---

**Status**: ✅ Implementierung abgeschlossen  
**Datum**: 23.11.2025
