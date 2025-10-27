# PDVM Input-Controls V2 - Architektur-Dokumentation

**AUTOR**: Norbert Peters  
**DATUM**: 21.10.2025  
**VERSION**: 2.0 (Neu-Bau)

---

## 🎯 ZIELE

Die V2-Architektur löst die Komplexität der V1-Implementierung auf durch:

1. **Klare Trennung**: Manager (Steuerung) vs. Control (Autonome Komponente)
2. **Command-Pattern**: Lineare Durchläufe mit klaren Kommandos
3. **Matrix-basiert**: Einfache Erweiterung (Order, Tabs, Gruppen)
4. **GCS-Integration**: Direkte Nutzung von Systemwerten (Stichtag, Neues Abdatum)

---

## 🏗️ ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────────────────────────┐
│           PdvmInputControlsManagerV2                    │
│                                                         │
│  ┌─────────────────┐      ┌──────────────────────┐   │
│  │ Instanzen-Pool  │      │  Controls-Matrix     │   │
│  │                 │      │  [                   │   │
│  │ persondaten.g1  │◄─────┤    {                 │   │
│  │ finanzdaten.g2  │      │      control: C1,    │   │
│  │ ...             │      │      order: 1,       │   │
│  └─────────────────┘      │      tab: "Haupt",   │   │
│                            │      instance_key    │   │
│                            │    },               │   │
│  ┌─────────────────┐      │    {...}            │   │
│  │ Neues Abdatum   │      │  ]                   │   │
│  │ (Pdvm_DateTime) │      └──────────────────────┘   │
│  │ aus GCS         │                                  │
│  └─────────────────┘      ┌──────────────────────┐   │
│                            │ Kommandos            │   │
│                            │ - render_all()       │   │
│                            │ - save_all()         │   │
│                            │ - refresh_all()      │   │
│                            └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 KOMPONENTEN

### **1. PdvmInputControlV2** (`pdvm_input_control_v2.py`)

**Verantwortlichkeiten**:
- Wert aus DB-Instanz laden (mit GCS-Stichtag)
- Wert anzeigen (mit Abdatum-Tooltip)
- Änderungen tracken (`is_dirty`)
- Wert speichern (mit GCS Neuem Abdatum)
- UI aktualisieren (refresh)

**Wichtige Eigenschaften**:
```python
self.instance_key      # z.B. "PERSONDATEN_guid1"
self.db_instance       # PdvmCentralDatenbank Instanz (vom Manager!)
self.gruppe            # z.B. "PERSDATEN"
self.feld              # z.B. "FAMILIENNAME"
self.label_text        # z.B. "Familienname"
self.order             # Sortierung
self.tab               # Tab-Zugehörigkeit

# AUTONOME ABDATUM-INSTANZ (nur für Anzeige!)
self.abdatum_dt        # Pdvm_DateTime für Tooltip

# DATEN
self.wert              # Aktueller Wert (aus DB)
self.abdatum_wert      # Abdatum des Wertes (Float aus DB)

# ZUSTAND
self.original_value    # Ursprungswert (für is_dirty)
self.current_value     # Aktueller Wert (editiert)
self.is_dirty          # Geändert?
```

**Kommandos**:
```python
control.render()              # Wert laden + UI erstellen
control.save(neues_abdatum)   # Wert speichern (wenn dirty)
control.refresh()             # Wert neu laden + UI aktualisieren
```

**Interne Methoden**:
```python
control._load_value_from_db()  # Lädt mit gcs.st_inst.PdvmDateTime
control._create_ui()           # Erstellt Widgets
control._update_ui()           # Aktualisiert Anzeige
```

---

### **2. PdvmInputControlsManagerV2** (`pdvm_input_controls_manager_v2.py`)

**Verantwortlichkeiten**:
- Instanzen-Pool aufbauen und verwalten
- Controls-Matrix aufbauen
- Kommandos an alle Controls senden
- Neues Abdatum verwalten (aus GCS)
- Widget mit allen Controls erstellen

**Wichtige Eigenschaften**:
```python
self.instances         # Dict: {instance_key: PdvmCentralDatenbank}
self.controls_matrix   # List: [{control, order, tab, instance_key}, ...]
self.neues_abdatum_dt  # Pdvm_DateTime aus GCS
self.abdatum_picker    # PdvmDateTimePicker Widget
```

**Public API**:
```python
manager.get_widget()   # Erstellt Widget mit allen Controls
manager.save_all()     # Speichert alle Controls
manager.refresh_all()  # Refresht alle Controls
```

**Interne Methoden**:
```python
manager._load_framedaten_and_meta()    # Lädt Metadaten
manager._build_instances_pool()        # Baut Instanzen auf
manager._build_controls_matrix()       # Baut Matrix auf
manager._initialize_neues_abdatum()    # Lädt aus GCS
manager._create_ui()                   # Erstellt UI-Struktur
manager._render_all_controls()         # RENDER-Kommando
manager._show_save_confirmation()      # Bestätigung
```

---

## 🔄 ABLAUF-DIAGRAMME

### **INITIALISIERUNG** (bei `get_widget()`)

```
┌─────────────────────────────────────────────┐
│ 1. Framedaten + Metadaten laden            │
│    - Header-Text                            │
│    - Root-Table                             │
│    - Controls-Metadaten (JSON)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Instanzen-Pool aufbauen                 │
│    - Root-Instanz (historisch)             │
│    - Weitere Instanzen aus Metadaten       │
│    → self.instances = {...}                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. Controls-Matrix aufbauen                │
│    FOR meta IN controls_meta:              │
│      - Control erstellen (NICHT rendern!)  │
│      - In Matrix einfügen mit Metadata     │
│    → Matrix nach Order sortieren           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 4. Neues Abdatum initialisieren            │
│    - Pdvm_DateTime Instanz erstellen       │
│    - GCS lesen: EDIT.NEUES_ABDATUM         │
│    - Falls leer: Fallback + sofort speich. │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 5. UI erstellen                            │
│    - Header mit Neues Abdatum Picker       │
│    - ScrollArea für Controls               │
│    - Buttons (Speichern, etc.)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 6. RENDER-Kommando an alle Controls        │
│    FOR item IN controls_matrix:            │
│      control.render()                      │
│        → _load_value_from_db()             │
│        → _create_ui()                      │
│        → _update_ui()                      │
└─────────────────────────────────────────────┘
```

---

### **SPEICHERN** (bei `save_all()`)

```
┌─────────────────────────────────────────────┐
│ 1. Neues Abdatum aus GCS holen             │
│    - Picker.save() → UI → Pdvm_DateTime    │
│    - neues_abdatum = dt.PdvmDateTime       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Dirty Controls sammeln                  │
│    dirty = [item for item IF is_dirty]     │
│    → Falls leer: Meldung + return          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. Alle dirty Controls durchlaufen         │
│    FOR item IN dirty:                      │
│      control.save(neues_abdatum)           │
│        → IF is_dirty:                      │
│             instance.set_value(            │
│               gruppe, feld, wert,          │
│               neues_abdatum                │
│             )                              │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 4. Alle Instanzen committen                │
│    FOR instance IN instances.values():     │
│      instance.save_all_values()            │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 5. Neues Abdatum in GCS speichern          │
│    gcs._db.set_value(                      │
│      'EDIT', 'NEUES_ABDATUM',              │
│      neues_abdatum                         │
│    )                                       │
│    gcs._db.save_all_values()               │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 6. REFRESH-Kommando (siehe unten)          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 7. Bestätigungsfenster anzeigen            │
│    - Anzahl geänderter Felder              │
│    - Neues Abdatum (formatiert)            │
│    - Liste der Änderungen (max 10)         │
└─────────────────────────────────────────────┘
```

---

### **REFRESH** (bei `refresh_all()`)

```
┌─────────────────────────────────────────────┐
│ 1. Neues Abdatum aus GCS neu laden         │
│    value, _ = gcs._db.get_value(           │
│      'EDIT', 'NEUES_ABDATUM'               │
│    )                                       │
│    dt.PdvmDateTime = value                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Neues Abdatum Picker aktualisieren      │
│    abdatum_picker.load()                   │
│      → Lädt Wert aus dt Instanz            │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. Alle Controls durchlaufen               │
│    FOR item IN controls_matrix:            │
│      control.refresh()                     │
│        → _load_value_from_db()             │
│            stichtag = gcs.st_inst.PdvmDT   │
│            wert, abdatum = get_value(...)  │
│            abdatum_dt.PdvmDT = abdatum     │
│        → _update_ui()                      │
│            value_label.setText(wert)       │
│            tooltip = abdatum_dt.FormTS     │
│        → is_dirty = False                  │
└─────────────────────────────────────────────┘
```

---

## 🔑 WICHTIGE KONZEPTE

### **1. Abdatum-Konzept**

Es gibt **DREI verschiedene Abdatum-Werte**:

#### **a) GCS Stichtag** (`gcs.st_inst.PdvmDateTime`)
- **Systemwert** (für alle Controls gleich)
- Wird bei `get_value()` verwendet
- "Zeige mir den Wert zu diesem Zeitpunkt"

#### **b) GCS Neues Abdatum** (`gcs._db EDIT.NEUES_ABDATUM`)
- **Systemwert** (für alle Controls gleich)
- Wird bei `set_value()` verwendet
- "Speichere mit diesem Abdatum"

#### **c) Control Abdatum-Instanz** (`control.abdatum_dt`)
- **Pro Control** (für Anzeige!)
- Wird bei jedem `get_value()` aktualisiert
- Enthält das **tatsächliche Abdatum des Wertes aus DB**
- Wird im Tooltip angezeigt

**Beispiel-Ablauf**:
```python
# LADEN:
stichtag = gcs.st_inst.PdvmDateTime  # z.B. 2025213.0 (aktueller Stichtag)
wert, abdatum_wert = instance.get_value(gruppe, feld, stichtag)
# wert = "Müller" (der Wert am Stichtag)
# abdatum_wert = 2025059.0 (wann "Müller" gespeichert wurde)

control.abdatum_dt.PdvmDateTime = abdatum_wert  # Für Tooltip-Anzeige

# SPEICHERN:
neues_abdatum = gcs._db.get_value('EDIT', 'NEUES_ABDATUM')  # z.B. 2025294.0
instance.set_value(gruppe, feld, "Müller-Schmidt", neues_abdatum)
# Speichert "Müller-Schmidt" mit Abdatum 2025294.0
```

---

### **2. Matrix-Struktur**

Die **Controls-Matrix** ist eine Liste von Dictionaries:

```python
self.controls_matrix = [
    {
        'control': <PdvmInputControlV2 Instanz>,
        'order': 1,
        'tab': 'Hauptdaten',
        'instance_key': 'PERSONDATEN_guid1'
    },
    {
        'control': <PdvmInputControlV2 Instanz>,
        'order': 2,
        'tab': 'Hauptdaten',
        'instance_key': 'PERSONDATEN_guid1'
    },
    {
        'control': <PdvmInputControlV2 Instanz>,
        'order': 10,
        'tab': 'Finanzen',
        'instance_key': 'FINANZDATEN_guid2'
    },
    # ...
]
```

**Vorteile**:
- ✅ **Sortierbar**: `sorted(matrix, key=lambda x: x['order'])`
- ✅ **Filterbar**: `[x for x in matrix if x['tab'] == 'Hauptdaten']`
- ✅ **Erweiterbar**: Neue Metadata einfach hinzufügen
- ✅ **Multi-Tab**: Einfaches Rendern in verschiedenen Tabs

**Beispiel Multi-Tab**:
```python
for tab_name in ['Hauptdaten', 'Finanzen', 'Sonstiges']:
    tab_controls = [x for x in matrix if x['tab'] == tab_name]
    tab_widget = create_tab(tab_name)
    
    for item in sorted(tab_controls, key=lambda x: x['order']):
        tab_widget.layout().addWidget(item['control'])
```

---

### **3. Command-Pattern**

**Prinzip**: Manager sendet Kommandos, Controls reagieren autonom.

**Vorteile**:
- ✅ **Lose Kopplung**: Manager kennt nur Interface (render/save/refresh)
- ✅ **Testbar**: Controls können einzeln getestet werden
- ✅ **Erweiterbar**: Neue Kommandos einfach hinzufügen
- ✅ **Linear**: Keine verschachtelten IFs, nur Schleifen

**Beispiel**:
```python
# Manager sendet RENDER-Kommando
for item in self.controls_matrix:
    item['control'].render()  # ← Control entscheidet, was passiert

# Manager sendet SAVE-Kommando
for item in self.controls_matrix:
    item['control'].save(neues_abdatum)  # ← Control prüft is_dirty selbst
```

---

## 🚀 VERWENDUNG

### **Im Dialog integrieren**:

```python
# In pdvm_genereller_dialog.py

# Manager registrieren
self.edit_modules = {
    'input_controls': PdvmInputControlsManagerV2
}

# Bei Datensatz-Auswahl:
def _on_datensatz_ausgewaehlt(self, selected_guid):
    # Manager initialisieren
    manager = PdvmInputControlsManagerV2(
        framedaten_db=self.framedaten_db,
        selected_guid=selected_guid
    )
    
    # Widget erstellen
    edit_widget = manager.get_widget()
    
    # In Edit-Tab einfügen
    self.edit_container.layout().addWidget(edit_widget)
    
    # Referenz speichern (für späteren Zugriff)
    self.current_edit_manager = manager
```

### **Refresh nach Stichtag-Änderung**:

```python
# In pdvm_genereller_dialog.py

def on_stichtag_changed(self):
    # Nur Controls refreshen, nicht Dialog neu laden!
    if hasattr(self, 'current_edit_manager'):
        self.current_edit_manager.refresh_all()
```

---

## ✅ VORTEILE V2 vs. V1

| Aspekt | V1 | V2 |
|--------|----|----|
| **Komplexität** | Verschachtelte IFs, viele Zustände | Linear, klare Kommandos |
| **GCS-Zugriff** | Zwischenspeicherung | Direkt |
| **Refresh** | Komplettes Widget neu | Nur Controls aktualisieren |
| **Erweiterbarkeit** | Schwierig | Einfach (Matrix) |
| **Testbarkeit** | Schwierig | Einfach (Controls isoliert) |
| **Performance** | Widget neu bauen | Nur UI aktualisieren |
| **Code-Zeilen** | ~1500 | ~800 |

---

## 📝 NÄCHSTE SCHRITTE

1. **Tests**: `test_input_controls_v2.py` ausführen
2. **Integration**: In `pdvm_genereller_dialog.py` integrieren
3. **Edit-Funktionalität**: `QLineEdit` statt nur Anzeige
4. **Validierung**: Plausibilitätsprüfungen hinzufügen
5. **Multi-Tab**: Tab-Struktur aus Matrix generieren
6. **Verschachtelte Instanzen**: Source-Path auswerten

---

## 📚 DATEIEN

- `pdvm_input_control_v2.py` - Control-Klasse
- `pdvm_input_controls_manager_v2.py` - Manager-Klasse
- `test_input_controls_v2.py` - Test-Skript
- `PDVM_INPUT_CONTROLS_V2_ARCHITEKTUR.md` - Diese Dokumentation

---

**ENDE DER DOKUMENTATION**
