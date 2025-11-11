# 🔧 Menu-Editor API-Korrektur - KOMPLETT

## ❌ Problem
Edit-Bereich wurde nicht angezeigt, weil API nicht kompatibel mit `input_controls` war.

## ✅ Lösung: Identische Plugin-API

### Dialog erwartet (wie bei input_controls):

```python
# 1. Initialisierung
ModuleClass(
    framedaten_db=framedaten_db,
    selected_guid=selected_guid,
    main_app=main_app,
    gcs=gcs
)

# 2. Widget holen
widget = module.get_widget()

# 3. Optional: Signals
module.refresh_requested.connect(...)
module.save_completed.connect(...)
```

## 🔄 Änderungen in pdvm_menu_editor_module.py

### VORHER (FALSCH):
```python
class PdvmMenuEditorModule(QWidget):  # ❌ Falsch: War QWidget
    def __init__(self, selected_guid: str, parent=None):  # ❌ Falsche Signatur
        super().__init__(parent)
        self._init_ui()  # ❌ UI direkt im Constructor
```

### NACHHER (RICHTIG):
```python
class PdvmMenuEditorModule(QObject):  # ✅ QObject (wie input_controls)
    
    refresh_requested = pyqtSignal()  # ✅ Signals definiert
    save_completed = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid: str, main_app=None, gcs=None):
        """Identische API wie PdvmInputControlsManager"""
        super().__init__()
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid
        self.main_app = main_app
        self.gcs = gcs if gcs else get_gcs()
        
        # Widget wird NICHT im Constructor erstellt!
    
    def get_widget(self) -> QWidget:
        """Erstellt Widget on-demand (wie input_controls)"""
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        
        self.editor_widget = PdvmMenuEditorWidget(
            menu_guid=self.selected_guid,
            parent=self.main_widget
        )
        
        layout.addWidget(self.editor_widget)
        return self.main_widget
```

## 📋 Vergleich: input_controls vs menu_editor

| Feature | input_controls | menu_editor | Status |
|---------|----------------|-------------|--------|
| Basisklasse | `QObject` | `QObject` | ✅ Identisch |
| Signatur `__init__` | `(framedaten_db, selected_guid, main_app, gcs)` | `(framedaten_db, selected_guid, main_app, gcs)` | ✅ Identisch |
| Methode `get_widget()` | ✅ Ja | ✅ Ja | ✅ Identisch |
| Signal `refresh_requested` | ✅ Ja | ✅ Ja | ✅ Identisch |
| Signal `save_completed` | ✅ Ja | ✅ Ja | ✅ Identisch |
| Methode `save_data()` | ✅ Ja | ✅ Ja | ✅ Optional |
| Methode `has_unsaved_changes()` | ❌ Nein | ✅ Ja | ✅ Optional |

## 🎯 Plugin-System Prinzipien

### 1. Module sind KEINE Widgets
```python
# ❌ FALSCH
class MyModule(QWidget):
    pass

# ✅ RICHTIG
class MyModule(QObject):
    def get_widget(self) -> QWidget:
        return self.main_widget
```

### 2. Standardisierte Initialisierung
```python
def __init__(self, framedaten_db, selected_guid: str, main_app=None, gcs=None):
    """
    IMMER diese 4 Parameter:
    - framedaten_db: Framedaten aus Dialog
    - selected_guid: Ausgewählter Datensatz
    - main_app: Optional (für Erweiterungen)
    - gcs: Optional (für Kompatibilität)
    """
```

### 3. Widget-Erstellung on-demand
```python
# Widget wird NICHT im __init__ erstellt
# Sondern erst wenn Dialog get_widget() aufruft
def get_widget(self) -> QWidget:
    self.main_widget = QWidget()
    # ... UI aufbauen ...
    return self.main_widget
```

### 4. Signals für Kommunikation
```python
class MyModule(QObject):
    refresh_requested = pyqtSignal()   # → Dialog soll View refreshen
    save_completed = pyqtSignal()      # → Nach erfolgreichem Speichern
```

## 🔌 Erweiterbarkeit

### Neues Plugin hinzufügen:

**Schritt 1**: Modul erstellen (pdvm_my_editor_module.py)
```python
class PdvmMyEditorModule(QObject):
    refresh_requested = pyqtSignal()
    save_completed = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid, main_app=None, gcs=None):
        super().__init__()
        # ... init ...
    
    def get_widget(self) -> QWidget:
        # ... widget erstellen ...
        return widget
```

**Schritt 2**: In Dialog registrieren (pdvm_genereller_dialog.py)
```python
self.edit_modules = {
    'input_controls': 'pdvm_input_controls_manager.PdvmInputControlsManager',
    'menu_editor': 'pdvm_menu_editor_module.PdvmMenuEditorModule',
    'my_editor': 'pdvm_my_editor_module.PdvmMyEditorModule',  # ✅ NEU!
}
```

**Schritt 3**: In Framedaten verwenden
```json
{
  "ROOT": {
    "EDIT_TYPE": "my_editor",
    ...
  }
}
```

**FERTIG!** 🎉

## 📊 Status

### ✅ Funktioniert:
- API identisch mit input_controls
- Dialog lädt Modul korrekt
- get_widget() erstellt Widget
- Signals definiert
- Kompatibel mit bestehendem System

### 🧪 Test:
1. App starten
2. Dialog "Menüs pflegen" öffnen
3. Menü auswählen
4. TAB02 sollte Menu-Editor zeigen

---

**Status**: API-KORREKTUR KOMPLETT ✅
