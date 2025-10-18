# 🎯 GENERELLER DIALOG - GRUNDGERÜST V1.0

**Datum**: 18.10.2025  
**Version**: 1.0.0 (Grundgerüst)  
**Status**: ✅ IMPLEMENTIERT - Bereit zum Testen

---

## 📋 ÜBERSICHT

Der **Generelle Dialog** ist das Herzstück für alle Datenänderungen im PDVM-System.

### Konzept

```
┌─────────────────────────────────────────────────────────┐
│  GENERELLER DIALOG                                      │
├─────────────────────────────────────────────────────────┤
│  Tab 1: ÜBERSICHT (View)                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │  • Alle Datensätze in Tabellenansicht            │ │
│  │  • Filter, Sortierung, Gruppierung               │ │
│  │  • Doppelklick → Tab 2 öffnen                    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Tab 2: BEARBEITEN (Edit)                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │  • Stichtagsgenaue Daten des ausgewählten Satzes│ │
│  │  • Inputcontrols, Menü-Editor, etc.             │ │
│  │  • Speichern → Aktualisierung in View           │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ ARCHITEKTUR

### Datenfluss

```
Menü → start_dialog(frame_guid)
  ↓
Framedaten laden (ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
  ↓
Dialogdaten laden/erstellen (Tab-Konfiguration)
  ↓
Tab 1: View initialisieren
  ↓
User: Doppelklick auf Datensatz
  ↓
Tab 2: Edit-Bereich mit GUID
```

### Komponenten

```
pdvm_systemstart.py
  └── start_dialog(frame_guid)
      └── PdvmGenerellerDialog
          ├── Framedaten-DB (frame_guid)
          │   └── ROOT: ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT
          │
          ├── Dialogdaten-DB (dialog_guid)
          │   ├── ROOT: active_tab, tab_count
          │   ├── Tab01: tab_type, tab_title, view_guid
          │   └── Tab02: tab_type, tab_title, selected_guid
          │
          └── QTabWidget
              ├── Tab 1: View (PdvmViewController)
              └── Tab 2: Edit (Phase 1: GUID-Anzeige)
```

---

## ✅ IMPLEMENTIERT (Phase 1)

### 1. Start-Methode ✅

**Datei**: `pdvm_systemstart.py`

```python
def start_dialog(self, frame_guid):
    """
    🎯 GENERELLER DIALOG - Herzstück für alle Datenänderungen
    
    Aufruf aus Menü:
        main_app.start_dialog("frame-guid-hier")
    """
```

**Features**:
- Lazy Import von `PdvmGenerellerDialog`
- Content-Bereich löschen
- Dialog erstellen und anzeigen
- Dialog-Instanz speichern (`self.current_dialog`)
- Fehler-Handling mit Log-Output

### 2. PdvmGenerellerDialog Klasse ✅

**Datei**: `pdvm_genereller_dialog.py`

**Initialisierung**:
```python
def __init__(self, frame_guid, parent=None):
    # GCS-Zugriff prüfen
    # Framedaten laden
    # Dialogdaten laden/erstellen
    # Tabs initialisieren
```

**Komponenten**:
- ✅ GCS-Integration
- ✅ Framedaten-DB Instanz
- ✅ Dialogdaten-DB Instanz
- ✅ Header-Frame mit HEADER_TEXT
- ✅ QTabWidget mit Styling
- ✅ Signal-System (`datensatz_ausgewaehlt`)

### 3. Framedaten laden ✅

**Methode**: `_load_framedaten()`

**Liest aus ROOT-Gruppe**:
| Feld | Beschreibung | Beispiel |
|------|--------------|----------|
| `ROOT_TABLE` | Tabellenname für Daten | `"persondaten"` |
| `VIEW_GUID` | GUID der View-Konfiguration | `"0d10a0d0-b1a5-4544-b284-e8a09ca979b5"` |
| `DIALOG_GUID` | GUID für Dialog-Persistierung | `"65d48641-250e-440c-8c70-0b6d0703df30"` |
| `HEADER_TEXT` | Überschrift des Dialogs | `"Persönliche Daten - Test"` |

**Auto-Generierung**:
- Wenn `DIALOG_GUID` leer → neue UUID generieren
- GUID zurück in Framedaten speichern

### 4. Dialogdaten-Instanz ✅

**Methode**: `_load_or_create_dialogdaten()`

**Persistiert in `anwendungsdaten`**:

**Gruppe ROOT**:
```python
{
    "active_tab": 0,        # Letzter aktiver Tab
    "tab_count": 2          # Anzahl Tabs
}
```

**Gruppe Tab01** (View):
```python
{
    "tab_type": "view",
    "tab_title": "Übersicht",
    "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
}
```

**Gruppe Tab02** (Edit):
```python
{
    "tab_type": "edit",
    "tab_title": "Bearbeiten",
    "selected_guid": None  # Wird bei Auswahl gesetzt
}
```

### 5. 2-Tab Layout ✅

**Methode**: `_init_tabs()`

**Tab 1: Übersicht**:
- View-Controller initialisieren
- View-Widget in Container
- Signal-Verbindung (`row_double_clicked`)
- Tab hinzufügen

**Tab 2: Bearbeiten**:
- Info-Label (Phase 1)
- GUID-Anzeige (versteckt)
- Tab hinzufügen

**Features**:
- Aktiven Tab wiederherstellen
- Tab-Wechsel persistieren

### 6. View im ersten Tab ✅

**Methode**: `_create_view_tab()`

**Integration**:
```python
from pdvm_view_controller import PdvmViewController

call_daten = {
    'frame_guid': self.frame_guid,
    'view_guid': self.view_guid,
    'root_table': self.root_table,
    'title': tab_title
}

self.view_controller = PdvmViewController(call_daten, parent=view_container)
init_success = self.view_controller.initialize()
view_widget = self.view_controller.get_widget()
```

**Erwartung**:
- View funktioniert wie standalone
- Filter, Sortierung, Gruppierung funktionieren
- Stichtag-Integration über GCS

### 7. Datensatz-Auswahl Handler ✅

**Methoden**:
- `_on_view_row_selected(row_data)` - View-Signal empfangen
- `_on_datensatz_ausgewaehlt(selected_guid)` - GUID verarbeiten

**Workflow**:
```python
View: Doppelklick
  ↓
row_double_clicked Signal
  ↓
_on_view_row_selected(row_data)
  ↓
GUID extrahieren (versucht: guid, GUID, id, ID)
  ↓
datensatz_ausgewaehlt.emit(selected_guid)
  ↓
_on_datensatz_ausgewaehlt(selected_guid)
  ↓
- GUID speichern (self.current_selected_guid)
  ↓
- GUID in Dialogdaten persistieren
  ↓
- GUID-Label aktualisieren
  ↓
- Tab 2 öffnen
```

**Phase 1**:
- ✅ GUID wird angezeigt
- ⏳ Edit-Controls (Phase 2)

### 8. Dialog im Parent anzeigen ✅

**Integration in pdvm_systemstart.py**:
```python
# Inhalt löschen
self.clear_content_layout()

# Dialog erstellen
dialog = PdvmGenerellerDialog(frame_guid=frame_guid, parent=self.content_frame)

# Dialog anzeigen
self.content_layout.addWidget(dialog)

# Instanz speichern
self.current_dialog = dialog
```

**Header**:
- Dunkler Hintergrund (#2c3e50)
- Weißer Text, 18px, bold
- HEADER_TEXT aus Framedaten

**Tab-Widget**:
- Moderne Tab-Optik
- Blauer Border oben (#3498db)
- Hover-Effekt

---

## 🧪 TEST-ANLEITUNG

### Voraussetzungen

1. **Framedaten vorhanden**:
   ```python
   frame_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
   
   # In framedaten.db unter frame_guid, Gruppe ROOT:
   ROOT_TABLE = "persondaten"
   VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
   DIALOG_GUID = "" # (wird auto-generiert wenn leer)
   HEADER_TEXT = "Persönliche Daten - Test"
   ```

2. **View funktioniert**:
   - VIEW_GUID ist korrekt konfiguriert
   - View zeigt Daten an

### Test-Schritte

1. **Dialog öffnen**:
   ```python
   # Aus Menü aufrufen
   main_app.start_dialog("0d10a0d0-b1a5-4544-b284-e8a09ca979b5")
   ```

2. **Prüfen**:
   - ✅ Header zeigt HEADER_TEXT
   - ✅ Tab 1 "Übersicht" ist sichtbar
   - ✅ View zeigt Daten
   - ✅ Tab 2 "Bearbeiten" ist sichtbar
   - ✅ Tab 2 zeigt Info-Text

3. **Datensatz auswählen**:
   - Doppelklick auf Zeile in View
   - **WICHTIG**: View-Controller muss `row_double_clicked` Signal haben!

4. **Prüfen nach Auswahl**:
   - ✅ Tab 2 öffnet automatisch
   - ✅ GUID wird angezeigt
   - ✅ GUID-Label ist sichtbar

5. **Tab-Wechsel**:
   - Zwischen Tab 1 und Tab 2 wechseln
   - Dialog schließen und neu öffnen
   - ✅ Letzter aktiver Tab wird wiederhergestellt

### Erwartete Ausgabe in main.log

```
🎯 === GENERELLER DIALOG - START ===
📋 Frame-GUID: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
🔧 Initialisiere Generellen Dialog...
✅ GENERELLER DIALOG gestartet

🎯 === GENERELLER DIALOG - INITIALISIERUNG ===
📋 Frame-GUID: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
🔧 Initialisiere UI...
✅ UI-Grundstruktur erstellt

📂 Lade Framedaten...
  📋 ROOT_TABLE: persondaten
  📋 VIEW_GUID: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
  📋 DIALOG_GUID: 65d48641-250e-440c-8c70-0b6d0703df30
  📋 HEADER_TEXT: Persönliche Daten - Test
✅ Framedaten erfolgreich geladen

📂 Lade/Erstelle Dialogdaten...
  ✅ Dialogdaten existieren bereits
✅ Dialogdaten erfolgreich geladen/erstellt

🔧 Initialisiere Tabs...
  📊 Tab-Anzahl: 2
🔧 Erstelle View-Tab...
  ✅ Signal 'row_double_clicked' verbunden
✅ View-Tab erstellt: 'Übersicht'
  📊 View-GUID: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
  📋 Root-Table: persondaten

🔧 Erstelle Edit-Tab...
✅ Edit-Tab erstellt: 'Bearbeiten' (Phase 1: GUID-Anzeige)
  ✅ Aktiver Tab wiederhergestellt: 0
✅ Tabs erfolgreich initialisiert

✅ Genereller Dialog erfolgreich initialisiert
```

---

## ⚠️ BEKANNTE EINSCHRÄNKUNGEN (Phase 1)

### 1. View-Signal fehlt
**Problem**: `PdvmViewController` hat möglicherweise kein `row_double_clicked` Signal

**Lösung**:
```python
# In pdvm_view_controller.py oder pdvm_view_ui.py
from PyQt5.QtCore import pyqtSignal

class PdvmViewController(QWidget):
    row_double_clicked = pyqtSignal(dict)  # row_data
    
    def _on_row_double_clicked(self, row, column):
        # row_data aus Matrix holen
        row_data = self.get_row_data(row)
        self.row_double_clicked.emit(row_data)
```

### 2. GUID-Feld in row_data
**Problem**: Welches Feld enthält die GUID?

**Aktuelle Lösung**: Versucht mehrere Felder
```python
for key in ['guid', 'GUID', 'id', 'ID']:
    if key in row_data:
        selected_guid = row_data[key]
        break
```

**TODO**: Standardisieren - z.B. immer `guid` verwenden

### 3. Nur GUID-Anzeige
**Problem**: Phase 1 zeigt nur GUID, keine Edit-Controls

**Nächste Phase**: 
- Inputcontrols laden
- Daten stichtagsgenau laden
- Speichern-Button
- Validierung

---

## 🔮 ROADMAP

### Phase 2: Edit-Controls
- [ ] Inputcontrols in Tab 2 laden
- [ ] Daten stichtagsgenau aus ROOT_TABLE laden
- [ ] Controls mit Daten befüllen
- [ ] Speichern-Funktionalität
- [ ] Validierung

### Phase 3: Mehr Tabs
- [ ] Tab 3: Menü-Editor (wenn ROOT_TABLE = menu)
- [ ] Tab 4: Frame-Editor (wenn ROOT_TABLE = framedaten)
- [ ] Tab 5: View-Editor (wenn ROOT_TABLE = viewdaten)
- [ ] Dynamische Tab-Anzahl

### Phase 4: Advanced Features
- [ ] Änderungs-Historie
- [ ] Undo/Redo
- [ ] Multi-User Locks
- [ ] Export/Import
- [ ] Batch-Editing

---

## 📁 DATEIEN

### Neu erstellt (2 Dateien)

| Datei | Zeilen | Beschreibung |
|-------|--------|--------------|
| `pdvm_genereller_dialog.py` | ~600 | Haupt-Klasse |
| `GENERELLER_DIALOG_GRUNDGERÜST.md` | ~500 | Diese Dokumentation |

### Geändert (1 Datei)

| Datei | Änderung | Beschreibung |
|-------|----------|--------------|
| `pdvm_systemstart.py` | `+90` | `start_dialog()` Methode hinzugefügt |

---

## 📊 STATISTIK

### Code

- **Gesamt Zeilen**: ~700 (Dialog + Doku)
- **Python-Code**: ~600 Zeilen
- **Dokumentation**: ~500 Zeilen (diese Datei)

### Komponenten

- **Methoden**: 11
  - `__init__`
  - `_init_ui`
  - `_load_framedaten`
  - `_load_or_create_dialogdaten`
  - `_init_tabs`
  - `_create_view_tab`
  - `_create_edit_tab`
  - `_on_view_row_selected`
  - `_on_datensatz_ausgewaehlt`
  - `_on_tab_changed`
  - `start_dialog` (in pdvm_systemstart.py)

- **Signals**: 1
  - `datensatz_ausgewaehlt(str)`

- **Properties**: 11
  - `frame_guid`
  - `gcs`
  - `framedaten_db`
  - `dialogdaten_db`
  - `root_table`
  - `view_guid`
  - `dialog_guid`
  - `header_text`
  - `tab_widget`
  - `view_controller`
  - `current_selected_guid`

---

## ✅ STATUS

**Phase 1: GRUNDGERÜST** - ✅ FERTIG

Alle 8 geplanten Schritte sind implementiert:

1. ✅ start_dialog() in pdvm_systemstart.py
2. ✅ PdvmGenerellerDialog Klasse
3. ✅ Framedaten laden
4. ✅ Dialogdaten-Instanz
5. ✅ 2-Tab Layout
6. ✅ View im ersten Tab
7. ✅ Datensatz-Auswahl Handler
8. ✅ Dialog im Parent anzeigen

**Bereit zum Testen!** 🧪

---

**Erstellt**: 18.10.2025  
**Version**: 1.0.0  
**Status**: ✅ IMPLEMENTIERT - Bereit zum Testen
