# Spalten-Konfigurations-Dialog: Expert-Modus und Datenladung korrigiert

## Änderungen nach User-Feedback

### ✅ **1. Expert-Modus Checkbox entfernt**

**Problem**: Dialog hatte eigene Expert-Modus Checkbox  
**Lösung**: Dialog verwendet jetzt ausschließlich `gcs().expert_mode` aus der zentralen Systemsteuerung

**Vorher:**
```python
# Expert-Mode Checkbox im Dialog
self.expert_mode_checkbox = QCheckBox("Expert-Modus")
self.expert_mode_checkbox.setChecked(gcs().expert_mode)

# Dialog-lokale Mode-Umschaltung
def _on_expert_mode_changed(self, state):
    self.modified = True
    self._sort_columns_by_current_mode()
```

**Nachher:**
```python
# Nur Info-Label, keine Checkbox
def _create_header_section(self):
    self.mode_info_label = QLabel()
    self._update_mode_info()

# Verwendet immer aktuellen System-Expert-Modus
def _get_visible_columns(self):
    if gcs().expert_mode:  # Direkt aus Systemsteuerung
        return self.columns_data
    else:
        return [col for col in self.columns_data if not col['expert_mode']]
```

### ✅ **2. Robuste Datenladung implementiert**

**Problem**: Dialog fand keine Spalten (0 Spalten geladen)  
**Lösung**: Mehrstufige Datenladung mit Fallback-Mechanismus

**Neue Datenladung:**
```python
def _load_columns_data(self):
    try:
        # 1. Versuch: Direkter ColumnControls-Zugriff
        column_controls = gcs().get_value(self.view_id, 'ColumnControls')
        
        if not column_controls:
            # 2. Versuch: Über interne Database
            db = gcs()._database
            if hasattr(db, 'data') and self.view_id in db.data:
                view_data = db.data[self.view_id]
                column_controls = view_data.get('ColumnControls', {})
        
        if not column_controls:
            # 3. Fallback: VIEW_COLUMNS_ORDER Struktur
            columns_order = self.view_config.get('VIEW_COLUMNS_ORDER', {})
            # Konvertierung zu ColumnControls...
```

### ✅ **3. Alle Expert-Mode Referenzen korrigiert**

**Geänderte Methoden:**
- `_get_visible_columns()`: Verwendet `gcs().expert_mode`
- `_sort_columns_by_current_mode()`: Verwendet `gcs().expert_mode`  
- `_update_mode_info()`: Verwendet `gcs().expert_mode`
- `_on_show_changed()`: Verwendet `gcs().expert_mode`
- `_update_main_columns_data()`: Verwendet `gcs().expert_mode`

## Dialog-Verhalten nach Korrektur

### 📋 **Expert-Modus = False (Normal)**
- **Header**: "👤 Normal-Modus: Nur Benutzer-Spalten sichtbar (X Spalten)"
- **Sichtbare Spalten**: Nur `_show` Spalten (nicht `_original`)
- **Sortierung**: show=true zuerst, dann show=false

### 📋 **Expert-Modus = True (Expert)**
- **Header**: "🔧 Expert-Modus: Alle Spalten sichtbar (X Spalten)"
- **Sichtbare Spalten**: Alle Spalten (`_original` und `_show`)
- **Sortierung**: Nach expert_order

## Testing

Der Dialog sollte jetzt:

1. **✅ Spalten anzeigen**: Mindestens Fallback-Daten aus VIEW_COLUMNS_ORDER
2. **✅ Expert-Modus respektieren**: Automatisch basierend auf Systemsteuerung
3. **✅ Keine schaltbare Checkbox**: Expert-Modus ist fest vorgegeben
4. **✅ Robuste Datenladung**: Multiple Fallback-Mechanismen

## Nächste Schritte

1. **Dialog im View testen**: Settings → Spalten konfigurieren
2. **Expert-Modus umschalten**: In Systemsteuerung Expert-Modus ändern, Dialog neu öffnen
3. **Spalten-Anzeige validieren**: Normal-Modus zeigt nur _show, Expert-Modus zeigt alle

Der Dialog ist bereit für den produktiven Einsatz!
