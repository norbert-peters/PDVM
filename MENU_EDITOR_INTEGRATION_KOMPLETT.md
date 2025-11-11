# 🎯 Menu-Editor Integration - KOMPLETT

## ✅ Was wurde erstellt

### 1. **pdvm_menu_editor_module.py** - Dialog-Plugin
- Wrapper-Klasse `PdvmMenuEditorModule(QWidget)`
- Erfüllt Dialog-Konventionen:
  - `__init__(selected_guid, parent=None)`
  - `save_data()` → bool
  - `has_unsaved_changes()` → bool
  - `undo_changes()`
- Kein GCS-Parameter → verwendet globalen GCS
- Lädt und verwaltet Menu-Editor-Widget

### 2. **pdvm_menu_editor_widget.py** - Editor-Widget
- Eigenständiges Widget für Menü-Bearbeitung
- 3 Tabs: Vertikalmenü, Grundmenü, Zusatzmenü
- Drag & Drop Sortierung
- Buttons: ➕ Neu, 📋 Duplizieren, 🗑️ Löschen
- Splitter: Liste (60%) | Item-Editor (40%)
- Lädt/Speichert JSON aus sys_menudaten.daten

### 3. **MENU_EDITOR_METADATEN.md** - Template
- Komplett-JSON für sys_framedaten (GUID: 794cbfc3...)
- MenuItem-Template mit allen Feldern
- Zum Einfügen in Datenbank bereit

### 4. **pdvm_genereller_dialog.py** - Angepasst
- Platzhalter-Code entfernt
- Menu-Editor wird jetzt vollständig geladen

## 🔄 Linearer Ablauf

```
1. User öffnet Dialog (Frame: 794cbfc3...)
   ↓
2. TAB01 (Übersicht) zeigt sys_menudaten View
   ↓
3. User wählt Menü aus → GUID: z.B. 113c6a2c...
   ↓
4. Dialog erkennt EDIT_TYPE='menu_editor'
   ↓
5. Dialog lädt: pdvm_menu_editor_module.PdvmMenuEditorModule
   ↓
6. Modul erstellt: PdvmMenuEditorWidget(selected_guid)
   ↓
7. Widget lädt JSON aus sys_menudaten.daten
   ↓
8. User bearbeitet in 3 Tabs
   ↓
9. Save → JSON zurück in Datenbank
   ↓
10. Fertig!
```

## 📂 Datenstruktur

### sys_menudaten.daten (JSON):
```json
{
  "VERTIKAL": [
    {
      "guid": "...",
      "label": "Personen",
      "type": "BUTTON",
      "icon": "👤",
      "command_guid": "...",
      "sort_order": 0,
      "visible": true,
      "enabled": true,
      "tooltip": "Personenverwaltung öffnen"
    },
    {
      "type": "SEPARATOR"
    },
    {
      "guid": "...",
      "label": "Finanzen",
      "type": "SUBMENU",
      "zusatz_guid": "...",
      "sort_order": 2
    }
  ],
  "GRUND": [...],
  "ZUSATZ": [...]
}
```

## 🔌 Dialog-Integration

### Modul-Registry (pdvm_genereller_dialog.py):
```python
self.edit_modules = {
    'input_controls': 'pdvm_input_controls_manager.PdvmInputControlsManager',
    'menu_editor': 'pdvm_menu_editor_module.PdvmMenuEditorModule',  # ✅ NEU!
}
```

### Dynamisches Laden:
```python
# Dialog macht automatisch:
module_name = 'pdvm_menu_editor_module'
class_name = 'PdvmMenuEditorModule'
module = importlib.import_module(module_name)
ModuleClass = getattr(module, class_name)

# Modul erstellen
editor = ModuleClass(selected_guid='113c6a2c...', parent=tab)

# In Tab einfügen - FERTIG!
```

## 🎯 Widget-Features

### Linke Seite (Listen):
- **DraggableMenuList** mit InternalMove
- Automatisches sort_order Update nach Drag & Drop
- Signal `items_reordered` bei Änderung
- Signal `item_selected` bei Auswahl

### Rechte Seite (Editor):
- **MenuItemEditor** (template-basiert)
- Lädt Item-Daten bei Auswahl
- Dynamische Controls (TODO: aus Metadaten)

### Funktionen:
```python
# Widget
widget.save_data()              # → Speichert JSON in DB
widget.undo_changes()           # → Verwirft Änderungen
widget.has_unsaved_changes()   # → True/False

# Modul (Wrapper)
module.save_data()              # → Ruft widget.save_data()
module.undo_changes()           # → Ruft widget.undo_changes()
module.has_unsaved_changes()   # → Ruft widget.has_unsaved_changes()
```

## ⚠️ TODO (Optional)

### Phase 2 - Template-Controls:
- [ ] Dynamische Controls aus METADATEN generieren
- [ ] QLineEdit für 'label'
- [ ] QComboBox für 'type' (BUTTON/SUBMENU/SEPARATOR/SPACER)
- [ ] Conditional Fields (command_guid nur bei BUTTON)
- [ ] Icon-Picker Dialog
- [ ] Command-GUID Auswahl via View

### Phase 3 - Preview:
- [ ] Live-Preview Widget (rechte Seite unten)
- [ ] Simuliertes Vertikalmenü
- [ ] Simuliertes Grundmenü

### Phase 4 - Validation:
- [ ] Pflichtfeld-Prüfung (label required)
- [ ] GUID-Validierung (command_guid/zusatz_guid existieren)
- [ ] Duplicate-Check

## 🧪 Test-Anleitung

### Schritt 1: Metadaten einfügen
```sql
-- In sys_framedaten für GUID: 794cbfc3-ccb6-4681-b432-efa9f44682c8
-- json_data Feld mit JSON aus MENU_EDITOR_METADATEN.md befüllen
```

### Schritt 2: Anwendung starten
```powershell
python pdvm_main.py
```

### Schritt 3: Dialog öffnen
1. Menü → "Systemtools" → "Menüs pflegen"
2. TAB01 zeigt Liste der Menüs
3. Menü auswählen (z.B. "Vertikal-Hauptmenü")
4. Dialog wechselt automatisch zu TAB02

### Schritt 4: Bearbeiten
1. Tab wählen (Vertikalmenü/Grundmenü/Zusatzmenü)
2. Items mit Drag & Drop sortieren
3. ➕ Neu / 📋 Duplizieren / 🗑️ Löschen
4. Item auswählen → Editor (rechts) zeigt Details

### Schritt 5: Speichern
- "Speichern" Button → Schreibt JSON zurück
- "Rückgängig" Button → Verwirft Änderungen
- "Abbrechen" Button → Schließt Dialog

## 📊 Status

### ✅ Implementiert:
- Modul-Struktur komplett
- Widget-Grundfunktionen
- Laden/Speichern JSON
- Drag & Drop Sortierung
- Neu/Duplizieren/Löschen
- Dialog-Integration

### ⏳ In Arbeit:
- Template-basierte Controls
- Item-Editor Felder
- Validierung

### 📋 Geplant:
- Live-Preview
- Icon-Picker
- Command-Auswahl

---

**Status**: BEREIT ZUM TESTEN! 🚀
