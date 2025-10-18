# 🎯 GENERELLER DIALOG - PHASE 2: INPUT-CONTROLS INTEGRATION

**Datum**: 18.10.2025  
**Status**: PLANUNG - Basierend auf bestehender Input-Control Architektur

---

## 📋 AKTUELLE SITUATION

### ✅ PHASE 1 ABGESCHLOSSEN (Grundgerüst V1.0)

**Implementiert**:
- ✅ `start_dialog(frame_guid)` in pdvm_systemstart.py
- ✅ `PdvmGenerellerDialog` Klasse (~540 Zeilen)
- ✅ Framedaten-Laden (ROOT_TABLE, VIEW_GUID, DIALOG_GUID, HEADER_TEXT)
- ✅ Dialogdaten-Persistierung (dialogdaten.db)
- ✅ 2-Tab Layout (QTabWidget)
- ✅ View im Tab 1 (PdvmViewController Integration)
- ✅ Datensatz-Auswahl via Doppelklick (uid_original aus matrix_sort)
- ✅ Signal-System: View → Controller → Dialog
- ✅ Stichtag-Signal-System (GCS → ALLE Views)
- ✅ Instanzen-Reload bei Stichtag-Änderung

**Tab 2 (aktuell)**:
- Nur GUID-Anzeige (Platzhalter)
- Kein Edit-Bereich

---

## 🏗️ BESTEHENDE INPUT-CONTROL ARCHITEKTUR

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────┐
│ PdvmFrameManager                                │
│ - Lädt Framedaten (frame_guid)                  │
│ - Verwaltet Steuerungsdaten (last_guid)         │
│ - Erstellt PdvmInputFrame oder Auswahl-Widget   │
└─────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────┐
│ PdvmInputFrame (pdvm_input_control.py?)         │
│ - Lädt Controls aus Framedaten                  │
│ - Erstellt PdvmInputControlWidget pro Feld      │
│ - Verwaltet Layout (Grid, Gruppen)              │
└─────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────┐
│ PdvmInputControlWidget                          │
│ - UI-Widget für EIN Control                     │
│ - Label + Wert + Buttons                        │
│ - Feldtypen: Text, Dropdown, DateTime, ViewTable│
│ - Delegiert Daten-Ops an ControlObject          │
└─────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────┐
│ ControlObject                                    │
│ - meta: Feld-Metadaten                          │
│ - display_value: Aktueller Wert                 │
│ - manager: Referenz zum InputManager            │
│ - value_inst: Pdvm_DateTime für Datum-Felder    │
└─────────────────────────────────────────────────┘
```

### Datenfluss (Original)

```
START: frame_guid + last_guid
  ↓
PdvmFrameManager
  ↓ Lädt framedaten.db
  ├── ROOT_TABLE
  ├── VIEW_GUID
  └── CONTROLS { control_key: { gruppe, feld, type, label, ... } }
  ↓
PdvmInputFrame
  ↓ Lädt Datensatz aus ROOT_TABLE.db
  ├── PdvmDatenbank(ROOT_TABLE, selected_guid, historisch=True)
  ├── get_value(gruppe, feld, stichtag) → (wert, abdatum)
  └── Erstellt ControlObjects mit Werten
  ↓
UI: Controls anzeigen, Bearbeiten, Speichern
```

---

## 🎯 PHASE 2 ZIEL: INTEGRATION IN GENERELLER DIALOG

### Anforderungen

1. **Tab 2: Edit-Bereich**
   - Zeigt Input-Controls für ausgewählten Datensatz
   - Lädt Controls aus Framedaten (METADATEN)
   - Befüllt Controls mit Daten aus ROOT_TABLE (stichtagsgenau)
   - Ermöglicht Bearbeitung und Speichern

2. **Datensatz-Auswahl**
   - Doppelklick in View (Tab 1) → `selected_guid` → Tab 2 Refresh
   - Tab 2 lädt Daten für `selected_guid`

3. **Stichtag-Unterstützung**
   - Verwendet `gcs.st_inst.PdvmDateTime` für historische Daten
   - Refresh bei Stichtag-Änderung

4. **Persistierung**
   - Speichert `selected_guid` in dialogdaten.db
   - Speichert geänderte Werte zurück in ROOT_TABLE.db

---

## 📐 ARCHITEKTUR-UNTERSCHIEDE

### Original (PdvmFrameManager)
```python
# Standalone-Verwendung
call_daten = {
    "user_guid": user_guid,
    "framedaten": {"GUID": frame_guid, "HIST": True},
    "stichtag": 2025310.0,
    "mode": 0
}
frame_manager = PdvmFrameManager(call_daten)
widget = frame_manager.widget_for_input_frame()
```

### Neu (GenerellerDialog Integration)
```python
# Integration in Dialog (Tab 2)
self.edit_manager = PdvmEditManager(
    frame_guid=self.frame_guid,
    root_table=self.root_table,
    gcs=self.gcs
)

# Bei Datensatz-Auswahl
self.edit_manager.load_datensatz(selected_guid)
edit_widget = self.edit_manager.get_widget()
self.edit_tab_layout.addWidget(edit_widget)
```

---

## 🔧 IMPLEMENTIERUNGS-PLAN

### Option A: ADAPTER-PATTERN (Empfohlen)

**Idee**: Neuer `PdvmEditManager` adaptiert bestehende Input-Control Architektur

```python
# pdvm_edit_manager.py (NEU)
class PdvmEditManager:
    """
    Adapter für Input-Controls im GenerellerDialog
    
    Vereinfacht und linearisiert bestehende Frame-Architektur:
    - Nutzt PdvmInputControlWidget (unverändert)
    - Vereinfacht Control-Erstellung (keine View-Auswahl)
    - Integriert mit GCS (Stichtag, User-GUID)
    - Persistiert in dialogdaten.db
    """
    
    def __init__(self, frame_guid, root_table, gcs):
        self.frame_guid = frame_guid
        self.root_table = root_table
        self.gcs = gcs
        
        # Framedaten laden
        self._load_framedaten()
        
        # Controls-Konfiguration
        self.controls_config = {}
        self.selected_guid = None
        
    def _load_framedaten(self):
        """Lädt Framedaten (METADATEN für Controls)"""
        framedaten_db = PdvmCentralDatenbank('framedaten', self.frame_guid)
        
        # Controls aus Framedaten (wie in PdvmFrameManager)
        # TODO: Struktur analysieren
        
    def load_datensatz(self, guid):
        """Lädt Datensatz und befüllt Controls"""
        self.selected_guid = guid
        
        # Datenbank-Instanz für Datensatz
        instance = PdvmCentralDatenbank(
            table_name=self.root_table,
            guid=guid,
            historisch=True  # Wichtig für Stichtag!
        )
        
        # Controls mit Daten befüllen
        for control_key, control_config in self.controls_config.items():
            gruppe = control_config.get('gruppe', 'SYSTEM')
            feld = control_config.get('feld')
            
            # Wert laden (stichtagsgenau!)
            wert, abdatum = instance.get_value(
                gruppe, 
                feld, 
                self.gcs.st_inst.PdvmDateTime
            )
            
            # ControlObject erstellen/aktualisieren
            # TODO: PdvmInputControlWidget Integration
    
    def get_widget(self):
        """Gibt QWidget mit allen Controls zurück"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Controls hinzufügen
        for control in self.controls:
            widget = PdvmInputControlWidget(control)
            layout.addWidget(widget)
        
        return container
    
    def save_changes(self):
        """Speichert geänderte Werte zurück"""
        # TODO: Ähnlich wie Original save_all_controls()
```

**Integration in GenerellerDialog**:
```python
def _create_edit_tab(self):
    """Erstellt Tab 2 mit Edit-Bereich"""
    # Edit-Manager erstellen
    self.edit_manager = PdvmEditManager(
        frame_guid=self.frame_guid,
        root_table=self.root_table,
        gcs=self.gcs
    )
    
    # Container
    edit_container = QWidget()
    edit_layout = QVBoxLayout(edit_container)
    
    # Controls-Widget (wird bei Auswahl befüllt)
    self.edit_widget_container = QWidget()
    self.edit_widget_layout = QVBoxLayout(self.edit_widget_container)
    edit_layout.addWidget(self.edit_widget_container)
    
    # Speichern-Button
    save_btn = QPushButton("💾 Speichern")
    save_btn.clicked.connect(self.edit_manager.save_changes)
    edit_layout.addWidget(save_btn)
    
    self.tab_widget.addTab(edit_container, "Bearbeiten")

def _on_datensatz_ausgewaehlt(self, selected_guid):
    """Handler für Datensatz-Auswahl"""
    # Datensatz laden
    self.edit_manager.load_datensatz(selected_guid)
    
    # Widget aktualisieren
    # Clear old widgets
    while self.edit_widget_layout.count():
        child = self.edit_widget_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
    # New widget
    edit_widget = self.edit_manager.get_widget()
    self.edit_widget_layout.addWidget(edit_widget)
    
    # Tab 2 öffnen
    self.tab_widget.setCurrentIndex(1)
```

### Option B: DIREKTE INTEGRATION

**Idee**: Verwende bestehende Klassen direkt, ohne Adapter

**Vorteile**:
- Weniger Code
- Schneller zu implementieren

**Nachteile**:
- Komplexe Abhängigkeiten (PdvmFrameManager, PdvmInputFrame)
- Weniger linear
- Schwerer wartbar

**Empfehlung**: ❌ Nicht verwenden

---

## 📝 OFFENE FRAGEN

### 1. Framedaten-Struktur
**Frage**: Wie sind Controls in framedaten.db strukturiert?

**Vermutung** (aus pdvm_frame_manager.py):
```python
framedaten = {
    'ROOT': {
        'root_table': 'persondaten',
        'view_guid': '<view-guid>',
        'header_text': 'Persönliche Daten'
    },
    'Controls': {
        'familienname': {
            'gruppe': 'SYSTEM',
            'feld': 'familienname',
            'type': 'text',
            'label': 'Familienname',
            'label_width': 120,
            'value_width': 200
        },
        'geburtsdatum': {
            'gruppe': 'SYSTEM',
            'feld': 'geburtsdatum',
            'type': 'datetime',
            'label': 'Geburtsdatum',
            'display_val': 'all'  # Anzeige-Format
        }
        # ...
    }
}
```

**TODO**: Framedaten-Struktur analysieren und dokumentieren

### 2. ControlObject-Erstellung
**Frage**: Wie wird ein ControlObject aus Config erstellt?

**TODO**: PdvmInputFrame analysieren für Control-Factory Pattern

### 3. Speichern-Logik
**Frage**: Wie werden geänderte Werte persistiert?

**Vermutung**:
```python
# Jedes ControlObject hat value_inst (Pdvm_DateTime) oder display_value
# Bei Speichern: instance.set_value(gruppe, feld, neuer_wert, abdatum)
```

**TODO**: Save-Logik aus Original extrahieren

---

## 🚀 NÄCHSTE SCHRITTE

### Phase 2.1: ANALYSE (JETZT)
- [ ] `pdvm_input_control.py` vollständig lesen
- [ ] Framedaten-Struktur dokumentieren
- [ ] ControlObject-Factory identifizieren
- [ ] Save-Logik dokumentieren

### Phase 2.2: ADAPTER ERSTELLEN
- [ ] `pdvm_edit_manager.py` erstellen
- [ ] Framedaten-Laden implementieren
- [ ] Datensatz-Laden implementieren
- [ ] Widget-Erstellung implementieren

### Phase 2.3: INTEGRATION
- [ ] `_create_edit_tab()` vervollständigen
- [ ] `_on_datensatz_ausgewaehlt()` vervollständigen
- [ ] Speichern-Button verbinden
- [ ] Stichtag-Refresh implementieren

### Phase 2.4: TESTING
- [ ] Controls anzeigen
- [ ] Daten laden
- [ ] Bearbeiten und Speichern
- [ ] Stichtag-Wechsel

---

## 📚 RELEVANTE DATEIEN

### Bestehend (Analyse)
- `pdvm_frame_manager.py` - Frame-Verwaltung
- `pdvm_input_control_widget.py` - Control-UI
- `pdvm_input_control.py` (?)- InputFrame Logik
- `pdvm_frame_data_manager.py` - Daten-Verwaltung
- `pdvm_frame_manager_widget.py` - Widget-Wrapper

### Neu (Phase 2)
- `pdvm_edit_manager.py` - Adapter für Dialog
- `pdvm_genereller_dialog.py` - Tab 2 Integration

### Doku
- `GENERELLER_DIALOG_GRUNDGERÜST.md` - Phase 1
- `GENERELLER_DIALOG_PHASE2_PLAN.md` - Dieser Plan

---

## 💡 DESIGN-ENTSCHEIDUNGEN

### 1. ADAPTER-PATTERN verwenden
**Grund**: 
- Trennt Dialog-Logik von Original-Architektur
- Ermöglicht Vereinfachungen und Linearisierung
- Leichter wartbar und testbar

### 2. GCS direkt verwenden
**Grund**:
- Kein separates call_daten Dict
- Direkter Zugriff auf st_inst.PdvmDateTime
- Konsistent mit View-Controller

### 3. dialogdaten.db für Persistierung
**Grund**:
- Trennung von Geschäftsdaten (ROOT_TABLE.db)
- Dialog-spezifische Daten (selected_guid, tab_status)
- Konsistent mit Phase 1

### 4. Schrittweise Migration
**Grund**:
- Phase 2.1: Analyse (ohne Code-Änderung)
- Phase 2.2: Adapter (neuer Code, keine Änderung am Original)
- Phase 2.3: Integration (nur Dialog ändern)
- Phase 2.4: Testing und Refinement

---

**Status**: ✅ Plan erstellt - Bereit für Phase 2.1 (Analyse)
