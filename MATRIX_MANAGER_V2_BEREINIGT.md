# ✅ MATRIX MANAGER BEREINIGT - V2 Filter-Persistierung

## Was wurde geändert

### pdvm_view_matrix_manager.py

#### 1. `rebuild_pipeline()` - Vereinfacht
**ALT**:
```python
def rebuild_pipeline(self, filter_config: Optional[Dict] = None):
    if filter_config is None:
        self._apply_filter_from_gcs()  # Komplexe Konvertierung
    else:
        self.apply_filter(filter_config)
```

**NEU**:
```python
def rebuild_pipeline(self, search_string: Optional[str] = None):
    """Parameter ist jetzt search_string statt filter_config!"""
    if search_string is None:
        search_string = self._load_search_string_from_gcs()  # EINFACH!
    
    self.apply_filter(search_string)  # Direkt anwenden
```

#### 2. `_load_search_string_from_gcs()` - NEU und EINFACH
```python
def _load_search_string_from_gcs(self) -> Optional[str]:
    """Lädt search_string DIREKT - KEINE Konvertierung!"""
    gcs = get_gcs()
    search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
    return search_string  # So einfach ist das!
```

#### 3. ENTFERNT - Komplexe Methoden
- ❌ `_apply_filter_from_gcs()` - Nicht mehr nötig
- ❌ `_convert_filter_config_to_search_string()` - Wird in Dialogen gemacht
- ❌ `_load_filter_config_from_gcs()` - Nicht mehr nötig

## Status

✅ **Matrix Manager**: BEREINIGT und VEREINFACHT
⏳ **Dialoge**: Müssen noch angepasst werden
⏳ **View Controller**: Muss noch angepasst werden
⏳ **Linear Filter Manager**: Muss noch bereinigt werden

## Nächste Schritte

### 1. Einfacher Filter-Dialog anpassen (search_parameter_dialog.py)
```python
def on_apply(self):
    # 1. Erstelle search_string
    search_string = f"{field_name}_show:{search_value}"
    
    # 2. Speichere Parameter + search_string
    gcs._app_db.set_value(self.view_guid, 'einfach', {
        'field_name': field_name,
        'search_value': search_value,
        'operator': operator
    })
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()
    
    # 3. Pipeline neu
    matrix_manager.rebuild_pipeline()  # Keine Parameter!
```

### 2. Komplexer Filter-Dialog anpassen (extended_filter_engine.py)
```python
def on_apply(self):
    # 1. Erstelle search_string aus Bedingungen
    search_string = self._build_search_string(conditions)
    
    # 2. Speichere
    gcs._app_db.set_value(self.view_guid, 'komplex', conditions_dict)
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()
    
    # 3. Pipeline neu
    matrix_manager.rebuild_pipeline()
```

### 3. View Controller - Gesamt-Filter (pdvm_view_controller.py)
```python
def on_global_search(self, search_text):
    # 1. search_string = search_text (global)
    # 2. Speichere unter 'gesamt'
    gcs._app_db.set_value(self.view_guid, 'gesamt', {'search_text': search_text})
    gcs._app_db.set_value(self.view_guid, 'search_string', search_text)
    gcs._app_db.save_all_values()
    
    # 3. Pipeline neu
    self.matrix_manager.rebuild_pipeline()
```

## Test-Plan

1. ✅ Matrix Manager bereinigt
2. ⏳ Teste Einfachen Filter
3. ⏳ Teste Komplexen Filter
4. ⏳ Teste Gesamt-Suche
5. ⏳ Teste App-Neustart (Persistierung)

**Bereit für Dialog-Anpassungen!** 🚀
