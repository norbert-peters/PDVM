# 🎯 LINEARES MENÜ-SYSTEM V2.0

**Status**: ✅ **VOLLSTÄNDIG IMPLEMENTIERT**  
**Datum**: 09.11.2025

---

## 📋 Übersicht

Das neue Menü-System ist **linear, robust und einfach** aufgebaut. Es folgt dem bewährten Pipeline-Pattern des View-Systems.

### ✅ Kernprinzipien

1. **Linear**: BASIS → PROJECT → UI (keine If-Then-Verschachtelungen)
2. **Singleton**: Eine Pipeline-Instanz pro Menü-GUID (VERTIKAL, GRUND, ZUSATZ)
3. **Zentral**: GCS verwaltet System-Menü-Instanz (wie _db, _app_db, _man_db)
4. **Datenbank-basiert**: sys_menudaten ohne History (get_static_value/set_static_value)
5. **Wiederverwendbar**: Gleiche Pipeline für System-Menü UND MenuEditor

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│ GCS (PdvmCentralSystemsteuerung)                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ _menu_system_db (PdvmCentralDatenbank)              │ │
│ │  - Tabelle: sys_menudaten                           │ │
│ │  - KEINE History                                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Menu-Pipelines (Lazy Init, Singleton)               │ │
│ │  - _menu_pipeline_vertikal                          │ │
│ │  - _menu_pipeline_grund                             │ │
│ │  - _menu_pipeline_zusatz                            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PdvmMenuPipeline (pdvm_menu_pipeline.py)                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ PHASE 1: BASIS                                      │ │
│ │  - Lädt alle Items aus Gruppe (VERTIKAL/GRUND)     │ │
│ │  - JSON-Parse: feld_guid → item_data                │ │
│ │  - Befüllt matrix_base[]                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                        ↓                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ PHASE 2: PROJECT                                    │ │
│ │  - Sortiert nach parent_guid + sort_order           │ │
│ │  - Baut Hierarchie (rekursiv)                       │ │
│ │  - Befüllt matrix_project[]                         │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ UI-Komponente (MainApp / MenuEditor)                    │
│  - Rendert matrix_project als Button-Menü              │ │
│  - Bei Click: execute_command(item['command'])          │ │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PdvmMenuHandler (pdvm_menu_handler.py)                  │
│  - Handler-Registry: command → function                 │ │
│  - Führt Aktionen aus (open_view, show_dialog, ...)    │ │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Dateistruktur

### **Neue Dateien** (09.11.2025)

| Datei | Zweck | Status |
|-------|-------|--------|
| `pdvm_menu_pipeline.py` | Lineare Menu-Pipeline (BASIS → PROJECT) | ✅ Fertig |
| `pdvm_menu_handler.py` | Menu-Action Handler (open_view, show_dialog, ...) | ✅ Fertig |

### **Modifizierte Dateien**

| Datei | Änderung | Status |
|-------|----------|--------|
| `pdvm_central_systemsteuerung.py` | `_menu_system_db` + `get_system_menu_pipeline()` | ✅ Fertig |
| `pdvm_central_datenbank.py` | `get_value_by_group()` Methode hinzugefügt | ✅ Fertig |

### **Backup** (archive_menu_backup_20251109/)

Alle alten Menü-Dateien wurden gesichert:
- `pdvm_menu_handler_OLD.py`
- `pdvm_menu_builder*.py`
- `pdvm_menu_editor*.py`
- `v3_menu_handler.py`

---

## 🚀 Usage-Beispiele

### 1. System-Menü in MainApp

```python
from pdvm_central_systemsteuerung import get_gcs
from pdvm_menu_handler import get_menu_handler

class MainApp:
    def __init__(self):
        self.gcs = get_gcs()
        self.menu_handler = get_menu_handler(self)
        
        # System-Menü laden (GRUND = Horizontal)
        self._load_system_menu('GRUND')
    
    def _load_system_menu(self, menu_guid):
        # 1. Pipeline holen (Singleton!)
        pipeline = self.gcs.get_system_menu_pipeline(menu_guid)
        
        # 2. Pipeline ausführen
        pipeline.run('BASIS')
        
        # 3. Daten holen
        matrix, info = pipeline.get_projected_data()
        
        # 4. UI rendern
        self._render_menu_buttons(matrix)
        
        logger.info(f"✅ Menü geladen: {info['total_items']} Items")
    
    def _render_menu_buttons(self, matrix):
        """Rendert Menu-Items als Buttons"""
        for item in matrix:
            # Prüfe Sichtbarkeit
            if not item.get('visible', True):
                continue
            
            # Erstelle Button
            button = QPushButton(item.get('label', 'N/A'))
            button.setEnabled(item.get('enabled', True))
            
            # Click-Handler
            command = item.get('command')
            if command:
                button.clicked.connect(
                    lambda checked, cmd=command: self.menu_handler.execute_command(cmd)
                )
            
            # Füge zu Layout hinzu (abhängig von parent_guid)
            self._add_button_to_layout(button, item)
```

### 2. Menü-Editor Dialog

```python
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_menu_pipeline import get_menu_pipeline

class MenuEditorDialog:
    def __init__(self, user_guid):
        # Eigene DB-Instanz für Editor
        self.menu_db = PdvmCentralDatenbank('sys_menudaten', user_guid)
        
        # Pipeline holen (wird auch in GCS verwendet, aber separate Instanz!)
        self.pipeline = get_menu_pipeline('GRUND', self.menu_db)
        
        # Menü laden
        self.load_menu()
    
    def load_menu(self):
        # Pipeline ausführen
        self.pipeline.run('BASIS')
        
        # Daten für Editor holen
        matrix, info = self.pipeline.get_projected_data()
        
        # Tree-View befüllen
        self._populate_tree(matrix)
    
    def add_menu_item(self, parent_guid, label):
        """Fügt neues Item hinzu"""
        import uuid
        
        new_item = {
            'guid': str(uuid.uuid4()),
            'type': 'BUTTON',
            'label': label,
            'parent_guid': parent_guid,
            'sort_order': 0,
            'visible': True,
            'enabled': True,
            'command': None
        }
        
        # Zu Pipeline hinzufügen
        self.pipeline.add_item(new_item)
        
        # Speichern
        self.pipeline.save_menu()
        
        # Neu laden
        self.pipeline.run('BASIS')
        
        logger.info(f"✅ Item hinzugefügt: {label}")
```

### 3. Menü-Umschaltung (VERTIKAL ↔ GRUND)

```python
class MainApp:
    def toggle_menu_display(self):
        """Schaltet zwischen VERTIKAL und GRUND um"""
        # Aktuelles Menü ermitteln
        current = self.current_menu_guid  # 'VERTIKAL' oder 'GRUND'
        
        # Umschalten
        new_menu = 'GRUND' if current == 'VERTIKAL' else 'VERTIKAL'
        
        # Neues Menü laden
        self._load_system_menu(new_menu)
        
        # Aktualisieren
        self.current_menu_guid = new_menu
        
        logger.info(f"🔄 Menü gewechselt: {current} → {new_menu}")
```

---

## 🔧 Pipeline-API

### **PdvmMenuPipeline**

```python
from pdvm_menu_pipeline import get_menu_pipeline

# Pipeline holen (Singleton pro menu_guid)
pipeline = get_menu_pipeline('VERTIKAL', menu_db_instance)

# METHODEN
pipeline.run('BASIS')      # Komplett neu laden (BASIS → PROJECT)
pipeline.run('PROJECT')    # Nur Projektion neu

# Daten abrufen
matrix, info = pipeline.get_projected_data()
# matrix = [item1, item2, ...]
# info = {'menu_guid': 'VERTIKAL', 'total_items': 15, ...}

# Items manipulieren (vor save_menu!)
pipeline.add_item(item_dict)
pipeline.update_item(item_guid, updated_dict)
pipeline.delete_item(item_guid)

# Speichern
pipeline.save_menu()
```

### **PdvmMenuHandler**

```python
from pdvm_menu_handler import get_menu_handler

# Handler erstellen
handler = get_menu_handler(main_window)

# Command ausführen
handler.execute_command({
    'handler': 'open_view',
    'params': {'view_guid': '0d10a0d0-...'}
})

# Eigene Handler registrieren
def my_custom_handler(params):
    print(f"Custom: {params}")

handler.register_handler('my_custom', my_custom_handler)
```

---

## 📊 Datenbank-Struktur

### **sys_menudaten Tabelle**

| guid (TEXT) | gruppe (TEXT) | feld (TEXT) | wert (TEXT/JSON) |
|-------------|---------------|-------------|------------------|
| user-guid-1 | VERTIKAL | guid-123 | `{"guid": "guid-123", "label": "Apps", ...}` |
| user-guid-1 | GRUND | guid-456 | `{"guid": "guid-456", "label": "MeineApps", ...}` |

**WICHTIG**:
- `gruppe` = Menu-Typ (VERTIKAL, GRUND, ZUSATZ)
- `feld` = Item-GUID
- `wert` = JSON mit allen Item-Properties

### **Item-Properties**

```json
{
    "guid": "12345678-1234-1234-1234-123456789abc",
    "type": "BUTTON",
    "label": "Personen",
    "parent_guid": "parent-guid",
    "sort_order": 10,
    "visible": true,
    "enabled": true,
    "icon": null,
    "tooltip": "Öffnet Personen-View",
    "command": {
        "handler": "open_view",
        "params": {
            "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        }
    }
}
```

### **Item-Typen**

| Type | Beschreibung | Command |
|------|--------------|---------|
| `BUTTON` | Klickbarer Button | Ja |
| `SUBMENU` | Parent für Child-Items | Optional |
| `SEPARATOR` | Trenn-Linie | Nein |
| `SPACER` | Leerraum | Nein |

---

## 🎨 Handler-Typen

| Handler | Beschreibung | Parameter |
|---------|--------------|-----------|
| `open_view` | Öffnet View-Dialog | `view_guid`, `mode` |
| `show_dialog` | Öffnet Dialog | `dialog_guid` |
| `toggle_menu` | Schaltet Menü um | - |
| `open_app_menu` | Öffnet App-Menü | `app_name` |
| `show_info` | Info-Dialog | `title`, `message` |
| `reload_view` | Lädt View neu | - |

**Eigene Handler**:
```python
handler.register_handler('custom_action', my_function)
```

---

## ✅ Vorteile des neuen Systems

| Aspekt | Verbesserung |
|--------|--------------|
| **Komplexität** | ✅ Linear statt verschachtelt |
| **Wartbarkeit** | ✅ Ein System für alles (System + Editor) |
| **Performance** | ✅ Singleton-Pattern, keine doppelten Instanzen |
| **Erweiterbarkeit** | ✅ Neue Handler einfach registrierbar |
| **Konsistenz** | ✅ Wie View-Pipeline-Pattern |
| **Robustheit** | ✅ DB-basiert, keine JSON-Dateien |

---

## 🔄 Migration von Alt → Neu

### **Was wurde ersetzt?**

| Alt | Neu |
|-----|-----|
| `pdvm_menu_handler_V2.py` | `pdvm_menu_handler.py` |
| `pdvm_menu_builder_v3.py` | `pdvm_menu_pipeline.py` |
| `v3_menu_handler.py` | `pdvm_menu_pipeline.py` |
| JSON-Dateien | `sys_menudaten` DB-Tabelle |

### **Was muss angepasst werden?**

1. **MainApp (`pdvm_systemstart.py`)**:
   ```python
   # ALT
   from v3_menu_handler import V3MenuHandler
   self.menu_handler = V3MenuHandler(...)
   
   # NEU
   from pdvm_menu_handler import get_menu_handler
   self.menu_handler = get_menu_handler(self)
   ```

2. **Menü laden**:
   ```python
   # ALT
   menu_builder.load_menu_from_json()
   
   # NEU
   pipeline = gcs.get_system_menu_pipeline('GRUND')
   pipeline.run('BASIS')
   matrix, info = pipeline.get_projected_data()
   ```

3. **Menü speichern**:
   ```python
   # ALT
   menu_storage.save_to_json()
   
   # NEU
   pipeline.save_menu()  # Schreibt automatisch in sys_menudaten
   ```

---

## 🧪 Testing

### **Standalone Pipeline-Test**

```bash
cd C:\Users\norbe\OneDrive\Dokumente\MyApplication
python pdvm_menu_pipeline.py
```

### **Standalone Handler-Test**

```bash
python pdvm_menu_handler.py
```

### **Integration-Test**

```python
# In main.py oder pdvm_systemstart.py
from pdvm_central_systemsteuerung import get_gcs

gcs = get_gcs()
pipeline = gcs.get_system_menu_pipeline('GRUND')
pipeline.run('BASIS')

matrix, info = pipeline.get_projected_data()
print(f"✅ {info['total_items']} Items geladen")
for item in matrix:
    print(f"  - {item['label']} ({item['type']})")
```

---

## 📝 TODO: Integration in MainApp

**Nächste Schritte**:

1. ✅ Pipeline implementiert
2. ✅ Handler implementiert  
3. ✅ GCS-Integration fertig
4. ⏳ **MainApp anpassen** (`pdvm_systemstart.py`):
   - Alten Menu-Code entfernen
   - Neues System integrieren
   - Button-Rendering anpassen
5. ⏳ **MenuEditor anpassen**:
   - Eigene Pipeline-Instanz
   - CRUD-Operationen

---

## 📞 Support & Fragen

Bei Fragen zum neuen System:
- Siehe `pdvm_menu_pipeline.py` (ausführliche Dokumentation)
- Siehe `pdvm_menu_handler.py` (Handler-Beispiele)
- Siehe `.github/copilot-instructions.md` (Architektur-Übersicht)

**Autor**: PDVM-System  
**Version**: 2.0  
**Datum**: 09.11.2025
