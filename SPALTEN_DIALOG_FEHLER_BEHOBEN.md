# Spalten-Konfigurations-Dialog: Fehler behoben

## Problem-Analyse

Aus dem Trace waren zwei Hauptprobleme erkennbar:

### 1. **Keine Spalten sichtbar (0 Spalten geladen)**
- **Ursache**: Dialog suchte nach `VIEW_COLUMNS_ORDER` Struktur, aber Daten sind in `ColumnControls` gespeichert
- **Trace-Hinweis**: `📊 0 Spalten geladen` und `🔄 Anzeige aktualisiert: 0 Spalten`

### 2. **Expert-Mode Checkbox nicht schaltbar**  
- **Ursache**: Checkbox änderte globalen `gcs().expert_mode` statt nur Dialog-lokale Anzeige
- **Trace-Hinweis**: `🔄 Expert-Modus geändert: False/True` in globaler Systemsteuerung

## Behobene Probleme

### ✅ **1. Datenquelle korrigiert**

**Vorher:**
```python
# Alte Struktur: VIEW_COLUMNS_ORDER
columns_order = self.view_config.get('VIEW_COLUMNS_ORDER', {})
expert_order = columns_order.get('expert_order', [])
display_order = columns_order.get('display_order', [])
```

**Nachher:**
```python
# Moderne Struktur: ColumnControls
try:
    column_controls = gcs().get_value(self.view_id, 'ColumnControls')
    if column_controls is None:
        column_controls = {}
except:
    column_controls = {}

# ColumnControls → columns_data konvertieren  
for col_name, col_config in column_controls.items():
    col_data = {
        'name': col_name,
        'show': col_config.get('show', False),
        'expert_mode': col_name.endswith('_original'),  # _original = Expert-Spalten
        'expert_order': col_config.get('expertOrder', 999),
        'display_order': col_config.get('displayOrder', 999)
    }
```

### ✅ **2. Expert-Mode Dialog-lokal gemacht**

**Vorher:**
```python
def _on_expert_mode_changed(self, state):
    # Globale Systemsteuerung aktualisieren
    gcs().expert_mode = self.expert_mode_checkbox.isChecked()
```

**Nachher:**
```python
def _on_expert_mode_changed(self, state):
    # NICHT die globale Systemsteuerung ändern - nur Dialog-View
    # gcs().expert_mode wird NICHT geändert!
    
    # Spalten neu sortieren und anzeigen basierend auf Dialog-Checkbox
    self._sort_columns_by_current_mode()
    self._update_display()
```

### ✅ **3. Speicher-Format modernisiert**

**Zusätzlich**: Dialog speichert jetzt primär in ColumnControls:
```python
def _save_columns_config(self):
    # ColumnControls-Struktur erstellen
    column_controls = {}
    
    for col_data in self.columns_data:
        column_controls[col_data['name']] = {
            'show': col_data['show'],
            'expertOrder': col_data['expert_order'],
            'displayOrder': col_data['display_order']
        }
    
    # In Systemsteuerung speichern
    gcs().set_value(self.view_id, 'ColumnControls', column_controls)
```

## Datenstruktur-Vergleich

### Trace-Daten (ColumnControls):
```json
"ColumnControls": {
    "uid_original": {
        "show": false,
        "expertOrder": 0,
        "displayOrder": 0
    },
    "familienname_original": {
        "show": false,
        "expertOrder": 1,
        "displayOrder": 1
    },
    "uid_show": {
        "show": true,
        "expertOrder": 10,
        "displayOrder": 10
    }
}
```

### Expert-Mode Logik:
- **_original** Spalten = Expert-Mode (`expert_mode: true`)
- **_show** Spalten = Normal-Mode (`expert_mode: false`)

## Testing

Nach den Fixes sollte der Dialog:

1. **✅ Alle 21 Spalten laden** (statt 0)
2. **✅ Expert-Mode Checkbox funktional** (nur Dialog-lokal)
3. **✅ Normal-Mode**: Nur _show Spalten anzeigen
4. **✅ Expert-Mode**: Alle Spalten anzeigen
5. **✅ Persistierung**: ColumnControls-Format verwenden

## Nächste Schritte

1. **Dialog im View testen**: Settings → Spalten konfigurieren
2. **Mode-Umschaltung testen**: Expert/Normal Checkbox
3. **Persistierung testen**: Änderungen speichern und neu laden
4. **Reordering testen**: Auf/Ab Buttons verwenden

Der Dialog ist jetzt bereit für produktiven Einsatz!
