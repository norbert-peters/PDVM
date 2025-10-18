# 🔍 GENERELLER DIALOG - ANALYSE ZUSAMMENFASSUNG

**Datum**: 18.10.2025  
**Phase**: 2.1 - ANALYSE ABGESCHLOSSEN

---

## 📊 BESTEHENDE INPUT-CONTROL ARCHITEKTUR

### Komponenten-Hierarchie

```
┌─────────────────────────────────────────────────┐
│ PdvmInputWidget (UI-Container)                  │
│ - Erstellt Manager mit call_data               │
│ - Baut Layout (Header, Stichtag, Controls)     │
│ - Speichern/Refresh Buttons                     │
└─────────────────────────────────────────────────┘
            ↓ verwendet
┌─────────────────────────────────────────────────┐
│ PdvmInputManager (Daten-Logik)                  │
│ - Lädt Framedaten aus framedaten.db            │
│ - Parst Metadaten → FieldMeta Objekte          │
│ - Verwaltet Datenbank-Instanzen                │
│ - get_value() / set_value() Operationen        │
└─────────────────────────────────────────────────┘
            ↓ verwaltet
┌─────────────────────────────────────────────────┐
│ PdvmInstanceManager (Instanz-Verwaltung)        │
│ - Erstellt PdvmCentralDatenbank Instanzen      │
│ - Verwaltet Instanzen pro Tabelle + Path       │
│ - Cache-System für Instanzen                   │
└─────────────────────────────────────────────────┘
            ↓ nutzt
┌─────────────────────────────────────────────────┐
│ PdvmCentralDatenbank (Datenzugriff)            │
│ - Historische Daten (stichtagsgenau)           │
│ - get_value(gruppe, feld, ab_zeit)             │
│ - set_value(gruppe, feld, wert)                │
└─────────────────────────────────────────────────┘
            ↓ angezeigt in
┌─────────────────────────────────────────────────┐
│ PdvmInputControlWidget (UI pro Feld)           │
│ - Label + Wert-Display + Buttons               │
│ - Unterstützt: Text, Dropdown, DateTime        │
│ - Delegiert Daten-Ops an ControlObject         │
└─────────────────────────────────────────────────┘
            ↓ steuert
┌─────────────────────────────────────────────────┐
│ ControlObject (Feld-Daten + Meta)              │
│ - meta: FieldMeta (Label, Type, etc.)          │
│ - display_value: Aktueller Wert                │
│ - manager: Referenz zu PdvmInputManager        │
│ - data_instance: PdvmCentralDatenbank Instanz  │
└─────────────────────────────────────────────────┘
```

---

## 🗄️ FRAMEDATEN-STRUKTUR (Analysiert)

### framedaten.db Format

```json
{
  "ROOT": {
    "root_table": "persondaten",
    "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
    "header_text": "Persönliche Daten",
    "display_st": "all",
    "display_time_short": false,
    "width_frame": 600,
    "width_label": 150,
    "width_control": 200,
    "width_button": 100,
    "width_indent_ab": 50
  },
  "Metadaten": {
    "PERSONDATEN_SYSTEM_ANREDE": {
      "source_path": "root",
      "table": "persondaten",
      "historical": true,
      "label": "Anrede",
      "type": "dropdown",
      "tooltip": "Anrede bitte auswählen",
      "abdatum": true,
      "display_ab": "all",
      "display_val": null,
      "dropdown": {
        "table": "dropdowndaten",
        "key": "ddaa6590-6d08-461b-a061-75faec26f4ba",
        "value": "anrede",
        "source_path": "root"
      },
      "help": {
        "table": "hilfetexte",
        "key": "help-guid-anrede",
        "source_path": "root"
      },
      "ui_width_label": 120,
      "ui_width_value": 200,
      "ui_width_button": 80
    },
    "PERSONDATEN_SYSTEM_VORNAME": {
      "source_path": "root",
      "table": "persondaten",
      "historical": true,
      "label": "Vorname",
      "type": "text",
      "tooltip": "Bitte alle Vornamen eingeben",
      "abdatum": true,
      "display_ab": "all"
    },
    "PERSONDATEN_SYSTEM_GEBURTSDATUM": {
      "source_path": "root",
      "table": "persondaten",
      "historical": true,
      "label": "Geburtsdatum",
      "type": "datetime",
      "tooltip": "Geburtsdatum der Person",
      "abdatum": true,
      "display_ab": "all",
      "display_val": "all"
    }
  }
}
```

### ✅ WICHTIGE ERKENNTNIS: KEY-FORMAT

**User-Info**: "der Key besagt woher die Daten für das Feld kommen: `tabelle_gruppe_feld`"

**Beispiele**:
- `PERSONDATEN_SYSTEM_ANREDE` → Tabelle: persondaten, Gruppe: SYSTEM, Feld: ANREDE
- `FINANZDATEN_KONTO_KONTONUMMER` → Tabelle: finanzdaten, Gruppe: KONTO, Feld: KONTONUMMER
- `PERSONDATEN_SYSTEM_FINANZDATEN-FINANZDATEN` → ViewTable-Referenz (Bindestrich!)

**Parsing**:
```python
key = "PERSONDATEN_SYSTEM_ANREDE"
parts = key.split('_')
table = parts[0].lower()  # "persondaten"
gruppe = parts[1].upper()  # "SYSTEM"
feld = '_'.join(parts[2:]).upper()  # "ANREDE"
```

**GUID-Quelle**:
- **ROOT_TABLE**: Verwendet `root_guid` (vom Dialog übergeben)
- **ViewTable**: Verwendet GUID aus Referenz-Feld (z.B. FINANZDATEN-FINANZDATEN)
- **Dropdown**: Verwendet feste GUID aus Metadaten (dropdown.key)
- **Help**: Verwendet feste GUID aus Metadaten (help.key)

---

## 🔄 DATENFLUSS (Original-Architektur)

### 1. Initialisierung

```python
# call_data Struktur
call_data = {
    "frame_guid": "abc-123-...",         # Framedaten-GUID
    "root_guid": "xyz-789-...",          # Datensatz-GUID
    "stichtag_inst": Pdvm_DateTime(...), # Stichtag-Instanz
    "language": "de"
}

# Widget erstellen
widget = PdvmInputWidget(call_data, parent=...)
```

**Was passiert**:
1. `PdvmInputWidget.__init__(call_data)`
2. Lädt Framedaten aus `framedaten.db` (frame_guid)
3. Erstellt `PdvmInstanceManager` mit Metadaten
4. Erstellt `PdvmInputManager(call_data, instance_manager)`
5. Manager lädt ROOT-Instanz: `PdvmCentralDatenbank(root_table, root_guid, historisch=True)`
6. Manager parst Metadaten → `FieldMeta` Objekte
7. Für jedes Feld: Erstellt `data_instance`, `dropdown_instance`, `help_instance`

### 2. Wert laden (get_value)

```python
# Im Manager
def get_value(self, key: str):
    meta = self.fields[key]  # FieldMeta
    
    # Parse key: tabelle_gruppe_feld
    parts = key.split('_')
    table = parts[0].lower()
    gruppe = parts[1].upper()
    feld = '_'.join(parts[2:]).upper()
    
    # Instanz holen (via InstanceManager)
    instance = meta.data_instance
    
    # Wert laden (stichtagsgenau!)
    wert, abdatum = instance.get_value(
        gruppe, 
        feld, 
        self.st_inst.PdvmDateTime  # Aktueller Stichtag!
    )
    
    return wert, abdatum
```

### 3. Wert speichern (set_value)

```python
# Im Manager
def set_value(self, key: str, wert, abdatum):
    meta = self.fields[key]
    
    # Parse key
    parts = key.split('_')
    gruppe = parts[1].upper()
    feld = '_'.join(parts[2:]).upper()
    
    # Instanz holen
    instance = meta.data_instance
    
    # Wert speichern
    instance.set_value(gruppe, feld, wert, abdatum)
    instance.save_all_values()  # Persistieren!
```

### 4. Stichtag-Änderung

```python
# Im Widget
def _on_refresh(self):
    # 1. Stichtag aus Picker holen
    self.st_picker.save()  # Schreibt in self.st_inst
    
    # 2. Manager-Stichtag aktualisieren
    self.manager.st_inst = self.st_inst
    
    # 3. Alle Instanzen neu laden
    self.manager.refresh_instances_for_stichtag()
    
    # 4. UI neu bauen
    self.build_fields_and_values()
```

---

## 🎯 UNTERSCHIEDE: ORIGINAL vs. GENERELLER DIALOG

### Original (Standalone)

```python
# Verwendung
call_data = {
    "frame_guid": frame_guid,
    "root_guid": selected_guid,
    "stichtag_inst": Pdvm_DateTime(...),
    "language": "de"
}
widget = PdvmInputWidget(call_data, parent=None)
widget.show()
```

**Eigenschaften**:
- ✅ Eigenständiges Widget
- ✅ Eigener Stichtag-Picker
- ✅ Eigene Speichern/Refresh Buttons
- ✅ Komplettes call_data Dict

### Genereller Dialog (Integration)

```python
# Verwendung in Dialog
self.edit_manager = PdvmEditManager(
    frame_guid=self.frame_guid,
    root_table=self.root_table,
    gcs=self.gcs  # Direkter GCS-Zugriff!
)

# Bei Datensatz-Auswahl
self.edit_manager.load_datensatz(selected_guid)
widget = self.edit_manager.get_widget()
```

**Eigenschaften**:
- ✅ **Kein call_data Dict** → Direkt GCS verwenden
- ✅ **Kein eigener Stichtag-Picker** → Nutzt Dialog-Header Picker
- ✅ **Kein Speichern-Button im Widget** → Nutzt Dialog-Button
- ✅ **Adapter-Pattern** → Vereinfacht Original-Architektur

---

## 🔧 ADAPTER-DESIGN: PdvmEditManager

### Konzept

```python
class PdvmEditManager:
    """
    Adapter für PdvmInputWidget im GenerellerDialog
    
    VEREINFACHUNGEN:
    - Kein call_data Dict → Direkt GCS
    - Kein eigener Stichtag-Picker → Nutzt Dialog-Header
    - Kein eigener Speichern-Button → Nutzt Dialog-Button
    - Linear und einfach
    
    VERANTWORTLICHKEITEN:
    - Framedaten laden
    - Metadaten parsen
    - Instanzen verwalten
    - Controls erstellen
    - Werte laden/speichern
    """
    
    def __init__(self, frame_guid, root_table, gcs):
        self.frame_guid = frame_guid
        self.root_table = root_table
        self.gcs = gcs
        
        # Framedaten laden
        self.framedaten_db = PdvmCentralDatenbank('framedaten', frame_guid)
        self.framedaten = self.framedaten_db.lesen()
        
        # Metadaten parsen
        self.metadaten = self.framedaten.get('Metadaten', {})
        self.fields = {}  # {key: FieldMeta}
        
        # Instanzen-Manager
        self.instance_manager = None
        self.selected_guid = None
        
        # Controls (später)
        self.controls = {}
    
    def load_datensatz(self, guid):
        """
        Lädt Datensatz und bereitet Controls vor
        
        Args:
            guid: GUID des zu ladenden Datensatzes (uid_original)
        """
        self.selected_guid = guid
        
        # Instance Manager erstellen
        from pdvm_instance_manager import PdvmInstanceManager
        self.instance_manager = PdvmInstanceManager(
            root_table=self.root_table,
            root_guid=guid,
            stichtag=self.gcs.st_inst.PdvmDateTime,
            metadaten=self.metadaten
        )
        
        # Fields erstellen (wie PdvmInputManager)
        self._create_fields()
        
        # Controls erstellen
        self._create_controls()
    
    def _create_fields(self):
        """Erstellt FieldMeta Objekte aus Metadaten"""
        for key, meta_config in self.metadaten.items():
            key_lower = key.lower()
            
            # Parse key: tabelle_gruppe_feld
            parts = key_lower.split('_')
            table = parts[0]  # z.B. "persondaten"
            
            # FieldMeta erstellen
            field_meta = FieldMeta(key_lower, meta_config)
            
            # data_instance zuweisen
            source_path = meta_config.get('source_path', 'root')
            field_meta.data_instance = self.instance_manager.get_instance(
                table, 
                source_path
            )
            
            # dropdown_instance zuweisen
            if field_meta.dropdown_def:
                dropdown_table = field_meta.dropdown_def.get('table')
                dropdown_source_path = field_meta.dropdown_def.get('source_path', source_path)
                if dropdown_table:
                    field_meta.dropdown_instance = self.instance_manager.get_instance(
                        dropdown_table,
                        dropdown_source_path
                    )
            
            # help_instance zuweisen
            if field_meta.help_def:
                help_table = field_meta.help_def.get('table')
                help_source_path = field_meta.help_def.get('source_path', source_path)
                if help_table:
                    field_meta.help_instance = self.instance_manager.get_instance(
                        help_table,
                        help_source_path
                    )
            
            self.fields[key_lower] = field_meta
    
    def _create_controls(self):
        """Erstellt ControlObjects für UI-Widgets"""
        for key, field_meta in self.fields.items():
            # Parse key für Gruppe/Feld
            parts = key.split('_')
            gruppe = parts[1].upper()
            feld = '_'.join(parts[2:]).upper()
            
            # Wert laden (stichtagsgenau!)
            wert, abdatum = field_meta.data_instance.get_value(
                gruppe,
                feld,
                self.gcs.st_inst.PdvmDateTime
            )
            
            # ControlObject erstellen
            control = ControlObject(
                meta=field_meta,
                display_value=wert,
                abdatum_inst=Pdvm_DateTime(self.gcs.field_value('country')),
                manager=self  # Referenz für Callbacks
            )
            
            # Abdatum setzen
            if abdatum:
                control.abdatum_inst.PdvmDateTime = abdatum
            
            self.controls[key] = control
    
    def get_widget(self):
        """
        Gibt QWidget mit allen Controls zurück
        
        VEREINFACHT: Kein Stichtag-Picker, kein Speichern-Button
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Controls hinzufügen
        for key, control in self.controls.items():
            widget = PdvmInputControlWidget(control)
            layout.addWidget(widget)
        
        layout.addStretch()
        return container
    
    def save_changes(self):
        """Speichert alle geänderten Werte"""
        for key, control in self.controls.items():
            # Parse key
            parts = key.split('_')
            gruppe = parts[1].upper()
            feld = '_'.join(parts[2:]).upper()
            
            # Wert speichern
            instance = control.meta.data_instance
            instance.set_value(
                gruppe,
                feld,
                control.display_value,
                control.abdatum_inst.PdvmDateTime
            )
        
        # Alle Instanzen persistieren
        self.instance_manager.save_all_instances()
    
    def get_value(self, key):
        """Kompatibilität mit PdvmInputManager API"""
        control = self.controls.get(key)
        if control:
            return control.display_value, control.abdatum_inst.PdvmDateTime
        return None, None
    
    def set_value(self, key, wert, abdatum):
        """Kompatibilität mit PdvmInputManager API"""
        control = self.controls.get(key)
        if control:
            control.display_value = wert
            control.abdatum_inst.PdvmDateTime = abdatum
```

---

## 📝 OFFENE FRAGEN (BEANTWORTET)

### ✅ 1. Framedaten-Struktur
**Status**: ANALYSIERT

**Struktur**:
- ROOT: Frame-Parameter (root_table, view_guid, widths, etc.)
- Metadaten: Dict mit Keys im Format `TABELLE_GRUPPE_FELD`
- Jedes Feld: source_path, table, type, label, dropdown, help, etc.

### ✅ 2. Key-Format
**User-Info**: `tabelle_gruppe_feld`

**Parsing**:
```python
key = "PERSONDATEN_SYSTEM_ANREDE"
parts = key.split('_')
table = parts[0].lower()  # "persondaten"
gruppe = parts[1].upper()  # "SYSTEM"
feld = '_'.join(parts[2:]).upper()  # "ANREDE"
```

### ✅ 3. GUID-Quelle
**User-Info**: "die GUID für die Daten kommt bei der ROOT_TABLE aus der übergebenen GUID"

**Regeln**:
- ROOT_TABLE: Nutzt `selected_guid` (vom Dialog übergeben)
- ViewTable: Nutzt GUID aus Referenz-Feld
- Dropdown: Nutzt feste GUID aus Metadaten
- Help: Nutzt feste GUID aus Metadaten

### ✅ 4. ControlObject-Erstellung
**Status**: VERSTANDEN

**Prozess**:
1. FieldMeta aus Metadaten erstellen
2. data_instance vom InstanceManager holen
3. Wert mit `get_value(gruppe, feld, stichtag)` laden
4. ControlObject mit meta, display_value, abdatum_inst erstellen
5. PdvmInputControlWidget mit ControlObject erstellen

### ✅ 5. Speichern-Logik
**Status**: VERSTANDEN

**Prozess**:
1. Für jedes Control: `control.display_value` lesen
2. `instance.set_value(gruppe, feld, wert, abdatum)`
3. `instance.save_all_values()` persistieren

---

## 🚀 NÄCHSTE SCHRITTE (Phase 2.2)

### Phase 2.2: ADAPTER ERSTELLEN

**Dateien**:
- [ ] `pdvm_edit_manager.py` erstellen (Adapter)
- [ ] Import: `FieldMeta`, `PdvmInstanceManager`, `PdvmCentralDatenbank`
- [ ] Implementierung basierend auf Analyse

**Funktionen**:
- [ ] `__init__(frame_guid, root_table, gcs)`
- [ ] `load_datensatz(guid)` - Lädt Datensatz + erstellt Controls
- [ ] `_create_fields()` - Parst Metadaten → FieldMeta
- [ ] `_create_controls()` - Erstellt ControlObjects mit Werten
- [ ] `get_widget()` - Gibt QWidget mit Controls zurück
- [ ] `save_changes()` - Speichert alle Änderungen
- [ ] `get_value(key)` / `set_value(key, wert, abdatum)` - Kompatibilität

**Test-Strategie**:
1. Unit-Test: Framedaten laden
2. Unit-Test: Metadaten parsen
3. Unit-Test: Fields erstellen
4. Integration-Test: Controls erstellen
5. Integration-Test: Werte laden/speichern

---

**Status**: ✅ ANALYSE ABGESCHLOSSEN - Bereit für Phase 2.2 (Implementierung)
