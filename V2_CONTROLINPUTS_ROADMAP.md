# V2 ControlInputs Integration - Roadmap
## Datum: 04.11.2025

## 🎯 Ziel
Integration von Input-Controls in V2-Dialog-System für echte Datenerfassung

## 📊 Aktuelle Situation

### Alte Version (pdvm_input_widget.py)
**Komponenten-Hierarchie**:
```
PdvmInputWidget (QWidget)
  ↓ verwendet
PdvmInputManager
  ↓ verwaltet
PdvmInstanceManager
  ↓ nutzt
FieldMeta (Metadaten pro Feld)
PdvmInputControlWidget (einzelne Controls)
```

**Abhängigkeiten**:
- `pdvm_input_manager.py` - Field-Management
- `pdvm_instance_manager.py` - Daten-Instanzen  
- `pdvm_input_control_widget.py` - UI-Controls
- `pdvm_date_time_picker.py` - Datum/Zeit-Picker
- `pdvm_dropdown_picker.py` - Dropdown-Auswahl
- `pdvm_field_widget.py` - Feld-Widget mit History

**Komplexität**:
- ~764 Zeilen in pdvm_input_widget.py
- Verschachtelte Manager-Struktur
- Template-GUID-System
- History-Management mit AB-Datum
- Signal/Slot-Mechanismus für Updates

## 🏗️ V2-Architektur Empfehlung

### Phase 1: Minimale Controls (JETZT MACHBAR)
**Ziel**: Einfache Textfelder und Buttons funktionsfähig

```python
# v2_input_controls.py

class V2SimpleTextInput(QLineEdit):
    """Einfaches Texteingabe-Feld für V2"""
    
    def __init__(self, field_name, initial_value="", parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.setText(initial_value)
        self.setPlaceholderText(f"Eingabe für {field_name}")
    
    def get_value(self):
        return self.text()
    
    def set_value(self, value):
        self.setText(str(value) if value else "")


class V2DateTimeInput(QDateTimeEdit):
    """Datum/Zeit-Eingabe für V2"""
    
    def __init__(self, field_name, initial_datetime=None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.setDisplayFormat("dd.MM.yyyy HH:mm:ss")
        self.setCalendarPopup(True)
        
        if initial_datetime:
            self.setDateTime(initial_datetime)
    
    def get_value(self):
        return self.dateTime()
```

**Integration in V2PdvmDialogWidget**:
```python
def _create_controls_from_config(self, frame_data):
    """Erstellt Controls aus Frame-Konfiguration"""
    
    # Felder aus sys_framedaten extrahieren (V2)
    fields = frame_data.get('fields', {})
    
    for field_name, field_config in fields.items():
        field_type = field_config.get('type', 'text')
        field_label = field_config.get('label', field_name)
        
        # Label
        label = QLabel(f"{field_label}:")
        self.content_layout.addWidget(label)
        
        # Control je nach Typ
        if field_type == 'text':
            control = V2SimpleTextInput(field_name)
        elif field_type == 'datetime':
            control = V2DateTimeInput(field_name)
        else:
            control = V2SimpleTextInput(field_name)
        
        self.content_layout.addWidget(control)
        
        # Control registrieren
        self.controls[field_name] = control
```

### Phase 2: GCS-Integration (NÄCHSTER SCHRITT)
**Ziel**: Controls mit GCS-Datenbank verbinden

```python
class V2InputManager:
    """Verwaltet Input-Felder mit GCS-Integration"""
    
    def __init__(self, dialog_guid):
        from v2_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        self.dialog_guid = dialog_guid
        
        # Datenbank für Dialog-Daten
        from pdvm_central_datenbank import PdvmCentralDatenbank
        self.data_db = PdvmCentralDatenbank('sys_dialogdaten', dialog_guid)  # V2!
    
    def load_field_value(self, field_name):
        """Lädt Wert aus Datenbank"""
        value = self.data_db.get_value('DATEN', field_name)
        return value
    
    def save_field_value(self, field_name, value):
        """Speichert Wert in Datenbank"""
        # Mit AB-Datum
        abdatum = self.gcs.st_inst.PdvmDateTime
        self.data_db.set_value('DATEN', field_name, value)
        self.data_db.set_value('ABDATUM', field_name, abdatum)
        self.data_db.save_all_values()
```

### Phase 3: Advanced Controls (SPÄTER)
**Features**:
- Dropdown mit Datenbank-Auswahl
- View-Picker (öffnet View zur Auswahl)
- History-Anzeige mit AB-Datum
- Validierung mit Fehler-Anzeige
- Auto-Complete für Textfelder

## 📝 Schritt-für-Schritt Migration

### Schritt 1: Basis-Controls erstellen ✅ BEREIT
```powershell
# Neue Datei erstellen
# v2_input_controls.py

# Enthält:
- V2SimpleTextInput
- V2DateTimeInput
- V2CheckboxInput
- V2DropdownInput (basic)
```

### Schritt 2: Controls in Dialog integrieren
```python
# In v2_pdvm_dialog_widget.py erweitern:

def _load_dialog_config(self):
    # ... existing code ...
    
    # Controls aus Config erstellen
    fields_config = frame_db.get_value('CONFIG', 'fields')
    if fields_config:
        self._create_controls_from_config(fields_config)

def _create_controls_from_config(self, fields_config):
    """Erstellt Controls dynamisch"""
    for field_name, config in fields_config.items():
        # Control erstellen basierend auf config
        # Layout hinzufügen
        # Wert laden
        pass

def _on_save(self):
    """Speichert alle Control-Werte"""
    for field_name, control in self.controls.items():
        value = control.get_value()
        self.input_manager.save_field_value(field_name, value)
```

### Schritt 3: Manager-System aufbauen
```python
# v2_input_manager.py erstellen

class V2InputManager:
    def __init__(self, dialog_guid):
        # GCS-Integration
        # DB-Zugriff
        pass
    
    def load_values(self):
        """Lädt alle Werte aus DB"""
        pass
    
    def save_values(self, values_dict):
        """Speichert alle Werte in DB"""
        pass
```

### Schritt 4: History-System (optional)
```python
# v2_field_history.py

class V2FieldHistory(QWidget):
    """Zeigt History eines Feldes mit AB-Datum"""
    
    def __init__(self, field_name, dialog_guid):
        # Liste aller Änderungen mit Zeitstempel
        # Anzeige in Tabelle
        # Restore-Funktion
        pass
```

## 🧪 Test-Strategie

### Test 1: Minimale Controls
```python
# test_v2_controls_minimal.py

def test_text_input():
    from v2_input_controls import V2SimpleTextInput
    
    widget = V2SimpleTextInput("testfeld", "Initialwert")
    assert widget.get_value() == "Initialwert"
    
    widget.set_value("Neuer Wert")
    assert widget.get_value() == "Neuer Wert"
```

### Test 2: Dialog mit Controls
```python
# test_v2_dialog_with_controls.py

def test_dialog_save_load():
    # Dialog öffnen
    # Werte eingeben
    # Speichern
    # Dialog schließen
    
    # Dialog erneut öffnen
    # Werte prüfen (sollten geladen sein)
    pass
```

### Test 3: GCS-Integration
```python
def test_gcs_persistence():
    # Wert speichern mit AB-Datum
    # GCS-Check: Wert in DB?
    # Stichtag ändern
    # Historischen Wert abrufen
    pass
```

## 📦 Erforderliche Dateien

### Neu zu erstellen:
1. `v2_input_controls.py` - Basis-Controls
2. `v2_input_manager.py` - Manager für Input-Felder
3. `v2_field_history.py` - History-Anzeige (optional)

### Zu erweitern:
1. `v2_pdvm_dialog_widget.py` - Control-Integration
2. `v2_central_systemsteuerung.py` - ggf. Helper-Methoden

### Optional portieren:
1. `pdvm_date_time_picker.py` → `v2_date_time_picker.py`
2. `pdvm_dropdown_picker.py` → `v2_dropdown_picker.py`

## 🎯 Prioritäten

### HIGH (sofort):
- [ ] V2SimpleTextInput implementieren
- [ ] V2DateTimeInput implementieren  
- [ ] V2InputManager grundlegend
- [ ] Integration in v2_pdvm_dialog_widget.py
- [ ] Speichern/Laden mit GCS

### MEDIUM (bald):
- [ ] V2CheckboxInput
- [ ] V2DropdownInput (basic)
- [ ] Validierung
- [ ] Fehleranzeige

### LOW (später):
- [ ] History-Anzeige
- [ ] View-Picker für Auswahl
- [ ] Auto-Complete
- [ ] Advanced Dropdowns mit DB-Query

## 💡 Design-Prinzipien für V2

1. **Einfachheit vor Features**
   - Starte mit minimalen Controls
   - Erweitere nur wenn benötigt

2. **GCS-First**
   - Alle Daten über GCS
   - Keine direkte DB-Zugriffe ohne GCS

3. **Linear statt verschachtelt**
   - Flache Hierarchien
   - Klare Datenflüsse

4. **Test-Driven**
   - Jede Control-Klasse einzeln testbar
   - Integration-Tests für Workflows

5. **Schrittweise Migration**
   - Alte Version läuft weiter
   - V2 parallel aufbauen
   - Später zusammenführen

## 🚀 Quick-Start (wenn Controls gebraucht werden)

```powershell
# 1. Basis-Controls erstellen
New-Item v2_input_controls.py

# 2. Einfache Implementierung
# siehe Phase 1 oben

# 3. In Dialog integrieren
# v2_pdvm_dialog_widget.py erweitern

# 4. Testen
python test_v2_controls_minimal.py

# 5. Iterativ erweitern
```

---
**Status**: 📋 Roadmap erstellt - Bereit für Implementation wenn benötigt
**Nächster Schritt**: User-Feedback ob Controls jetzt oder später
