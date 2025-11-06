# 🚀 V2 Dialog-System - Schnell-Referenz

**Für AI-Assistenten & Entwickler**

---

## 📋 Kritische Informationen

### Tabellennamen (IMMER beachten!)

```python
# ❌ V1 (ALT)
'framedaten'   # Frame-Konfiguration
'dialogdaten'  # Dialog-UI-Status
'viewdaten'    # View-Definitionen
'menudaten'    # Menü-Struktur

# ✅ V2 (NEU)
'sys_framedaten'   # Frame-Konfiguration
'sys_dialogdaten'  # Dialog-UI-Status  
'sys_viewdaten'    # View-Definitionen
'sys_menudaten'    # Menü-Struktur
```

### Datenbank-Zugriffe (Nicht-historische Tabellen!)

```python
# ❌ V1 - Mit Tuple-Unpacking
value, abdatum = db.get_value('ROOT', 'FIELD')

# ✅ V2 - Direkt ohne Tuple (sys_* Tabellen sind NICHT historisch)
value = db.get_static_value('ROOT', 'FIELD')
```

**Welche Tabellen sind NICHT historisch?**
- `sys_framedaten` → get_static_value ✅
- `sys_dialogdaten` → get_static_value ✅
- `sys_viewdaten` → get_static_value ✅
- `sys_menudaten` → get_static_value ✅
- GCS `_db` (systemsteuerung) → get_static_value ✅

**Welche Tabellen SIND historisch?**
- Geschäftsdaten (persondaten, finanzdaten, etc.) → get_value + tuple ✅

### GCS-Zugriff

```python
# ❌ V1
from global_gcs import gcs
if not gcs:
    ...
self.gcs = gcs

# ✅ V2
from v2_central_systemsteuerung import get_gcs
self.gcs = get_gcs()
if not self.gcs:
    ...
```

---

## 🎯 Dialog-System Datenfluss

```
1. Frame-GUID (Parameter)
   ↓
2. sys_framedaten.db/<frame_guid>/ROOT
   - ROOT_TABLE: "persondaten"
   - VIEW_GUID: "0d10a0d0-..."
   - DIALOG_GUID: "65d48641-..."
   - HEADER_TEXT: "Persönliche Daten"
   - EDIT_TYPE: "input_controls"
   ↓
3. sys_dialogdaten.db/<dialog_guid>/
   - ROOT: {active_tab: 0, tab_count: 2}
   - TAB01: {tab_type: "view", tab_title: "Übersicht", view_guid: "..."}
   - TAB02: {tab_type: "edit", tab_title: "Bearbeiten", selected_guid: null}
   ↓
4. sys_viewdaten.db/<view_guid>/
   - ROOT: {VIEW_TABLE: "persondaten", NO_DATA: false}
   - METADATEN: {controls configuration}
   ↓
5. UI-Anzeige
   - TAB01: View mit Daten aus VIEW_TABLE
   - TAB02: Edit-Modul basierend auf EDIT_TYPE
```

---

## 🔧 Verwendung

### Dialog öffnen (in Handler)

```python
# handlers/handler_show_dialog.py
def execute(self, main_app, parameters):
    frame_guid = parameters.get('frame_guid')
    mode = parameters.get('mode', 0)
    selected_id = parameters.get('selected_id')
    
    return main_app.pdvm_dialog(frame_guid, mode, selected_id)
```

### Dialog öffnen (in MainApp)

```python
# v2_systemstart.py
def pdvm_dialog(self, dialog_guid, mode=0, selected_id=None):
    from v2_pdvm_genereller_dialog import V2PdvmGenerellerDialog
    
    # Welcome-Widget verstecken
    if hasattr(self, 'welcome_widget') and self.welcome_widget:
        self.welcome_widget.hide()
    
    # Dialog erstellen
    dialog_widget = V2PdvmGenerellerDialog(
        frame_guid=dialog_guid,  # ✅ WICHTIG: frame_guid!
        parent=self.content_frame,
        main_app=self
    )
    
    # Anzeigen
    self.content_layout.addWidget(dialog_widget)
    self.current_dialog_widget = dialog_widget
```

### Neues Edit-Modul registrieren

```python
# In V2PdvmGenerellerDialog.__init__()
self.edit_modules = {
    'input_controls': 'v2_pdvm_input_controls_manager.V2PdvmInputControlsManager',
    'menu_editor': 'v2_pdvm_menu_editor_module.V2PdvmMenuEditorModule',
    'custom_editor': 'v2_custom_editor.V2CustomEditor',  # ✅ Neues Modul
}
```

**Edit-Modul Interface**:
```python
class V2CustomEditor(QWidget):
    def __init__(self, root_table, selected_guid, gcs, main_app, parent=None):
        super().__init__(parent)
        self.root_table = root_table      # z.B. "persondaten"
        self.selected_guid = selected_guid # z.B. "abc-123-..."
        self.gcs = gcs                     # GCS-Instanz
        self.main_app = main_app           # MainApp-Referenz
        
        # UI aufbauen
        self._init_ui()
```

---

## 🐛 Häufige Fehler

### 1. Falsche Tabellennamen

```python
# ❌ FEHLER
db = PdvmCentralDatenbank('framedaten', guid)

# ✅ RICHTIG
db = PdvmCentralDatenbank('sys_framedaten', guid)
```

### 2. Falsche DB-Zugriffe

```python
# ❌ FEHLER - Tuple-Unpacking für nicht-historische Tabelle
value, _ = db.get_value('ROOT', 'FIELD')

# ✅ RICHTIG
value = db.get_static_value('ROOT', 'FIELD')
```

### 3. Falscher GCS-Import

```python
# ❌ FEHLER
from global_gcs import gcs

# ✅ RICHTIG
from v2_central_systemsteuerung import get_gcs
gcs = get_gcs()
```

### 4. Dialog-GUID statt Frame-GUID

```python
# ❌ FEHLER - dialog_guid direkt übergeben
dialog = V2PdvmGenerellerDialog(frame_guid=dialog_guid)

# ✅ RICHTIG - frame_guid enthält Verweis auf dialog_guid
# Frame-GUID → sys_framedaten → DIALOG_GUID → sys_dialogdaten
dialog = V2PdvmGenerellerDialog(frame_guid=frame_guid)
```

---

## 📚 Wichtige Dateien

| Datei | Zeilen | Beschreibung |
|-------|--------|--------------|
| `v2_pdvm_genereller_dialog.py` | 710 | **Haupt-Dialog-System** |
| `v2_systemstart.py` | 1606 | MainApp mit `pdvm_dialog()` (Zeile 1299) |
| `handlers/handler_show_dialog.py` | ~30 | Dialog-Handler |
| `V2_DIALOG_MIGRATION_ABGESCHLOSSEN.md` | ~500 | **Vollständige Dokumentation** |
| `V2_DIALOG_SCHNELLREFERENZ.md` | ~200 | **Diese Datei** |

---

## ✅ Migrations-Checkliste für neue Module

Wenn du ein Modul von V1 nach V2 migrierst:

- [ ] Datei kopieren mit `v2_` Präfix
- [ ] Alle `'framedaten'` → `'sys_framedaten'` ersetzen
- [ ] Alle `'dialogdaten'` → `'sys_dialogdaten'` ersetzen
- [ ] Alle `'viewdaten'` → `'sys_viewdaten'` ersetzen
- [ ] Alle `'menudaten'` → `'sys_menudaten'` ersetzen
- [ ] Alle `get_value()` → `get_static_value()` für sys_* Tabellen
- [ ] `from global_gcs import gcs` → `from v2_central_systemsteuerung import get_gcs`
- [ ] `self.gcs = gcs` → `self.gcs = get_gcs()`
- [ ] Klassenname mit `V2` Präfix versehen
- [ ] Import-Pfade in anderen Dateien aktualisieren
- [ ] Testen mit `python v2_main.py`

---

## 🎯 Nächste Schritte

1. **Input-Controls-Manager** nach V2 migrieren
2. **Menu-Editor-Module** nach V2 migrieren
3. **View-System** vollständig testen
4. **Filter/Sort/Projektion** in Dialog-Context testen

---

**Quick Start**: Kopiere diese Datei als Referenz wenn du an V2-Dialog-Modulen arbeitest!
