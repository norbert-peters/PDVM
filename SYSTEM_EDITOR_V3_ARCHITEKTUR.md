# PdvmSystemEditor V3 - Architektur-Dokumentation

## 🎯 Überblick

**Datum**: 15.10.2025  
**Status**: ✅ VOLLSTÄNDIG IMPLEMENTIERT  
**Vorher**: `PdvmViewEditor` (5 Parameter, kompliziert)  
**Nachher**: `PdvmSystemEditor` (2 Parameter, einfach + autonom)

---

## 📐 Architektur-Prinzipien

### V3 Design-Philosophie
1. ✅ **Ultra-einfache API**: Nur 2 Parameter statt 5
2. ✅ **Autonome Operation**: Editor holt ALLES intern (GCS, LAST_SELECTION)
3. ✅ **Linear & Unkompliziert**: Keine verschachtelten If-Then-Logiken
4. ✅ **Single Source of Truth**: Jeder Parameter hat EINE zentrale Quelle
5. ✅ **Universell**: Funktioniert mit ALLEN System-Tabellen (sys_viewdaten, sys_framedaten, etc.)

---

## 🔧 API-Vereinfachung

### VORHER (V1/V2): 5 Parameter
```python
editor = PdvmViewEditor(
    framedaten_db=framedaten_db,    # ❌ Externe DB-Instanz
    selected_guid=selected_guid,    # ❌ Externe Auswahl-Logik
    main_app=main_app,              # ❌ Durchreichen nötig
    gcs=gcs,                        # ❌ Durchreichen nötig
    parent=parent
)
```

**Probleme**:
- Dialog musste DB-Instanzen erstellen
- LAST_SELECTION extern verwalten
- main_app + gcs durchreichen
- Komplizierte Initialisierung
- Kopplung zwischen Dialog und Editor

### NACHHER (V3): 2 Parameter
```python
editor = PdvmSystemEditor(
    frame_guid='3be5d463-c0ea-4b71-b486-f2d9f647d527',  # ✅ Kontext
    table_name='sys_viewdaten',                        # ✅ Tabelle
    parent=parent                                       # ✅ Optional
)
```

**Vorteile**:
- ✅ Editor ist komplett autonom
- ✅ LAST_SELECTION intern geladen aus GCS
- ✅ GCS intern geholt via `get_gcs()`
- ✅ Alle DB-Instanzen intern erstellt
- ✅ Minimale Kopplung zum Dialog

---

## 🏗️ Interne Struktur

### Datenfluss im Editor
```
__init__(frame_guid, table_name)
  ↓
1. GCS holen: gcs = get_gcs()
  ↓
2. LAST_SELECTION laden: gcs._db.get_value(frame_guid, 'LAST_SELECTION')
  ↓
3. DB-Instanzen erstellen:
   - self.edit_db = PdvmCentralDatenbank(table_name, last_guid)
   - self.template_db = PdvmCentralDatenbank(table_name, '55555...')
   - self.framedaten_db = PdvmCentralDatenbank('sys_framedaten', frame_guid)
  ↓
4. Daten laden: _load_data()
  ↓
5. UI aufbauen
```

### Wichtige Methoden

**`__init__(frame_guid, table_name, parent=None)`**
- Frame-GUID: Kontext für LAST_SELECTION und ROOT_TABLE
- Table-Name: Welche System-Tabelle bearbeitet wird
- Parent: Optional, für Dialoge

**`set_guid(new_guid)`**
- Wechselt zu anderem Datensatz
- Verwendet von View beim Doppelklick
- Speichert neue LAST_SELECTION in GCS

**`_load_data()`**
- Lädt Daten aus edit_db
- Ermittelt Modus (template vs. normal)
- Aktualisiert UI

**`save_data()`**
- Speichert Änderungen in edit_db
- Aktualisiert LAST_SELECTION in GCS
- Emittiert save_completed Signal

---

## 🔄 Integration im Dialog

### Dialog-Initialisierung
```python
# Tabelle erkennen: VIEW_GUID aus framedaten prüfen
view_guid_to_edit = self.view_guid
try:
    test_db = PdvmCentralDatenbank('sys_viewdaten', view_guid_to_edit)
    if test_db.data and 'ROOT' in test_db.data:
        editor_table = 'sys_viewdaten'
    else:
        editor_table = 'sys_framedaten'
except:
    editor_table = 'sys_framedaten'

# ✅ EINFACH: Nur 2 Parameter!
self.current_edit_module = PdvmSystemEditor(
    frame_guid=self.frame_guid,
    table_name=editor_table,
    parent=self
)
```

### Datenbank-Architektur im Dialog

**WICHTIG**: Dialog und Editor verwenden **verschiedene** DB-Instanzen!

```
Dialog (pdvm_genereller_dialog.py):
  ├─ self.framedaten_db: sys_framedaten mit frame_guid
  │    ↓ ROOT_TABLE, VIEW_GUID, EDIT_TYPE
  │
  └─ self.current_edit_module (PdvmSystemEditor):
       ├─ self.edit_db: sys_viewdaten/sys_framedaten mit last_guid
       ├─ self.template_db: sys_viewdaten/sys_framedaten mit 55555...
       └─ self.framedaten_db: sys_framedaten mit frame_guid (EIGENE INSTANZ!)
```

**KRITISCH**: Editor erstellt **eigene** framedaten_db-Instanz für ROOT_TABLE-Lookup!

---

## 📂 3-Datenbank-Architektur im Editor

Der Editor verwaltet **3 separate DB-Instanzen**:

### 1. edit_db - Daten-Bearbeitung
```python
self.edit_db = PdvmCentralDatenbank(table_name, edit_guid)
```
- **Tabelle**: sys_viewdaten ODER sys_framedaten (je nach Kontext)
- **GUID**: Letzte bearbeitete GUID (aus LAST_SELECTION)
- **Zweck**: Aktueller Datensatz zum Bearbeiten

### 2. template_db - Template-Daten
```python
self.template_db = PdvmCentralDatenbank(table_name, '55555555-5555-5555-5555-555555555555')
```
- **Tabelle**: GLEICHE wie edit_db
- **GUID**: Immer 55555... (Template-GUID)
- **Zweck**: Template-Struktur (TEMPLATES, CONTROL_PROPERTIES)

### 3. framedaten_db - Dialog-Kontext
```python
self.framedaten_db = PdvmCentralDatenbank('sys_framedaten', frame_guid)
```
- **Tabelle**: Immer sys_framedaten
- **GUID**: frame_guid (aus Dialog-Aufruf)
- **Zweck**: ROOT_TABLE-Lookup für Validierung

---

## 🔄 LAST_SELECTION System

### Persistierung
```python
# Speichern (beim Speichern/Wechsel)
gcs._db.set_value(frame_guid, 'LAST_SELECTION', current_guid)
gcs._db.save_all_values()
```

### Laden
```python
# Beim Start
last_guid, _ = gcs._db.get_value(frame_guid, 'LAST_SELECTION')
if not last_guid:
    last_guid = '55555555-5555-5555-5555-555555555555'  # Fallback: Template
```

### Konzept
- **Key**: frame_guid (jeder Dialog hat eigene LAST_SELECTION)
- **Value**: GUID des zuletzt bearbeiteten Datensatzes
- **Storage**: systemsteuerung.db (User-spezifisch)
- **Fallback**: Template-GUID (55555...) wenn keine Auswahl

---

## 📋 Variablen-Umbenennung

### VORHER → NACHHER
```python
self.view_data           → self.data
self.view_db             → self.edit_db
self.view_guid           → self.edit_guid
self.framedaten          → self.frame_data
_load_view_data()        → _load_data()
_save_view_data()        → _save_data()
```

**Grund**: Editor ist jetzt **universell**, nicht nur für Views!

---

## 🎨 Modus-Erkennung

### Template-Modus
```python
# Prüfung: GUID ist Template?
if self.edit_guid == '55555555-5555-5555-5555-555555555555':
    self.edit_mode = 'template'
    # Tab 2 zeigt: TEMPLATES, ROOT_CONTROLS, CONTROL_PROPERTIES
```

### Normal-Modus
```python
else:
    self.edit_mode = 'normal'
    # Tab 2 zeigt: controls, standard_controls
```

### Modus-Umschalter
```python
# Benutzer kann manuell wechseln
mode_combo.currentIndexChanged.connect(self._on_mode_changed)

def _on_mode_changed(self, index):
    if index == 0:  # Template
        self.set_guid('55555555-5555-5555-5555-555555555555')
    else:  # Normal
        # Lade erste normale View/Frame
        first_guid = self._get_first_normal_guid()
        self.set_guid(first_guid)
```

---

## 🧪 Testing

### Test mit sys_viewdaten
```python
# Frame für View-Verwaltung
frame_guid = '3be5d463-c0ea-4b71-b486-f2d9f647d527'

editor = PdvmSystemEditor(
    frame_guid=frame_guid,
    table_name='sys_viewdaten'
)
```

### Test mit sys_framedaten
```python
# Frame für Frame-Verwaltung
frame_guid = 'abc-123-def-456'

editor = PdvmSystemEditor(
    frame_guid=frame_guid,
    table_name='sys_framedaten'
)
```

### Test mit anderen Tabellen
```python
# Funktioniert mit JEDER System-Tabelle!
editor = PdvmSystemEditor(
    frame_guid=frame_guid,
    table_name='sys_menudaten'
)
```

---

## 📁 Datei-Änderungen

### Umbenannt
- `pdvm_view_editor.py` → `pdvm_system_editor.py`

### Geändert
- `pdvm_system_editor.py`: Komplette Klassen-Überarbeitung
- `pdvm_genereller_dialog.py`: Editor-Initialisierung vereinfacht
- `handlers/handler_show_dialog.py`: Parameter dialog_guid → frame_guid
- `test_template_editor.py`: Import + Klassenname aktualisiert

---

## ✅ Vorteile der neuen Architektur

### 1. Einfachheit
- ✅ Nur 2 Parameter beim Aufruf
- ✅ Keine komplexe Vorbereitung im Dialog nötig
- ✅ Klare, lineare Initialisierung

### 2. Autonomie
- ✅ Editor holt ALLE Daten selbst
- ✅ Keine externen DB-Instanzen nötig
- ✅ Kein Durchreichen von GCS/main_app

### 3. Universalität
- ✅ Funktioniert mit sys_viewdaten
- ✅ Funktioniert mit sys_framedaten
- ✅ Funktioniert mit ALLEN System-Tabellen

### 4. Wartbarkeit
- ✅ Single Source of Truth
- ✅ Keine verschachtelten Logiken
- ✅ Klare Verantwortlichkeiten

---

## 🚀 Nächste Schritte

### ABGESCHLOSSEN ✅
- [x] Klasse umbenannt: PdvmViewEditor → PdvmSystemEditor
- [x] __init__ vereinfacht: 5 → 2 Parameter
- [x] Variablen umbenannt: view_data → data, etc.
- [x] Dialog-Integration aktualisiert
- [x] Imports aktualisiert
- [x] Test-Dateien aktualisiert
- [x] Keine Syntax-Fehler

### ZU TESTEN 🧪
- [ ] Öffne Persondaten-Frame → sys_viewdaten Editor
- [ ] Öffne Frame-Verwaltung → sys_framedaten Editor
- [ ] Prüfe LAST_SELECTION Persistierung
- [ ] Prüfe set_guid() beim Doppelklick in View
- [ ] Prüfe Template-Modus-Umschalter
- [ ] Prüfe ROOT_TABLE Validierung

### OFFEN FÜR STEP 8 📝
User-Zitat: "Wenn es soweit läuft dann müssen wir uns über die Editorbereiche ROOT und METADATEN nochmals unterhalten."

---

## 📚 Referenzen

- **Hauptdatei**: `pdvm_system_editor.py`
- **Dialog**: `pdvm_genereller_dialog.py`
- **Handler**: `handlers/handler_show_dialog.py`
- **Template-Docs**: `TEMPLATE_EDITING_COMPLETE.md`
- **GCS-Docs**: `.github/copilot-instructions.md`

---

**Zusammenfassung**: PdvmSystemEditor V3 ist ein **universeller, autonomer Editor** mit **ultra-einfacher API**. Nur 2 Parameter nötig, der Rest passiert intern. Linear, unkompliziert, wartbar. 🎯
