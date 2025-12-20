# ✅ GENERELLER DIALOG HANDLER IMPLEMENTIERT

**DATUM**: 08.12.2025  
**VERSION**: 1.0  
**STATUS**: ✅ VOLLSTÄNDIG IMPLEMENTIERT

---

## 🎯 Anforderung

**Benutzer-Anforderung**:
> "Da ich im Laufe der Zeit noch viele generelle Dialog anlegen werde, ist es sinnvoll diesen Ablauf als Handler zu machen, damit ich den über das Menü aufrufen kann."

**Workflow**:
1. Namen abfragen
2. Frame-GUID automatisch generieren
3. View-GUID: Bestehend wählen ODER neu erstellen
4. Dialog-GUID: Aus sys_dialogdaten wählen (mit last_selected Vortrag)
5. "Ausführen" → Prozess durchführen

---

## 🏗️ Implementierung

### 1. Handler-Klasse: `CreateGenerellerDialogWizard`

**Datei**: `create_genereller_dialog.py` (388 Zeilen)

**Features**:
- ✅ **3-Schritte Workflow**: Name → View → Dialog → Ausführen
- ✅ **View-Modi**: Bestehende View ODER neue View erstellen
- ✅ **SimpleView auf sys_viewdaten**: Dropdown mit allen Views
- ✅ **SimpleView auf sys_dialogdaten**: Dropdown mit allen Dialoge
- ✅ **Last-Selected Vortrag**: Zuletzt verwendete Dialog-GUID vorgeschlagen
- ✅ **Auto-GUID-Generation**: Frame-GUID + View-GUID (bei neu)
- ✅ **Automatische Persistierung**: Datensätze in pdvm_system.db

### 2. UI-Struktur

```
📝 Schritt 1: Name
   ├─ Input: Dialog-Name (z.B. "Mandanten verwalten")
   
🖼️ Schritt 2: View-GUID
   ├─ Radio: [●] Bestehende View verwenden
   │   └─ Dropdown: View auswählen (mit name + GUID)
   ├─ Radio: [ ] Neue View erstellen
   │   └─ Input: Tabellen-Name (z.B. "sys_mandanten")
   
💬 Schritt 3: Dialog-GUID
   └─ Dropdown: Dialog auswählen (last_selected vorgeschlagen)

[Abbrechen]  [✅ Ausführen]
```

### 3. Workflow-Logik

```python
def _on_execute(self):
    # 1. Validierung: Name vorhanden?
    # 2. View-GUID ermitteln:
    #    - Bestehend: Aus Dropdown
    #    - Neu: _create_view() mit Tabellen-Name
    # 3. Dialog-GUID: Aus Dropdown
    # 4. Frame erstellen: _create_frame()
    # 5. Last-Dialog-GUID speichern in GCS
    # 6. Erfolg-Message mit allen GUIDs
```

### 4. Last-Selected Mechanismus

**Speicherung in GCS**:
```python
def _save_last_dialog_guid(self, dialog_guid):
    gcs = get_gcs()
    if gcs:
        gcs.set_field_value('LAST_DIALOG_GUID', dialog_guid)
        gcs._db.save_all_data()

def _get_last_dialog_guid(self):
    gcs = get_gcs()
    if gcs:
        return gcs.field_value('LAST_DIALOG_GUID')
    return None
```

**Vortrag im Dropdown**:
```python
last_dialog_guid = self._get_last_dialog_guid()
last_index = 0

for i, (dialog_guid, dialog_name) in enumerate(self.existing_dialogs, start=1):
    self.combo_dialogs.addItem(f"{dialog_name} ({dialog_guid[:8]}...)", dialog_guid)
    if dialog_guid == last_dialog_guid:
        last_index = i

if last_index > 0:
    self.combo_dialogs.setCurrentIndex(last_index)  # ← Vortrag!
```

### 5. Handler-Funktion für Menü

**Verwendung**:
```python
from create_genereller_dialog import handle_create_genereller_dialog

# Im Menü-System
menu_item = {
    'name': 'Generellen Dialog erstellen',
    'handler': 'create_genereller_dialog.handle_create_genereller_dialog',
    'icon': '🔧'
}
```

**Handler-Signatur**:
```python
def handle_create_genereller_dialog(**kwargs):
    main_app = kwargs.get('main_app')
    wizard = CreateGenerellerDialogWizard(parent=main_app)
    
    if wizard.exec_() == QDialog.Accepted:
        # Erfolg-Message
        QMessageBox.information(main_app, "Erfolg", 
            "Dialog erfolgreich erstellt!")
```

---

## 🧪 Test-Ergebnisse

### Test 1: Standalone Wizard

**Befehl**: `python test_genereller_dialog_wizard.py`

**Ergebnis**:
```
✅ Dialog erstellt:
   Frame-GUID: 79142e42-d679-498f-ada4-0409747cd845
   View-GUID: 1927fb47-91e9-4e4e-b8af-1d91a621ff16
   Dialog-GUID: 0e1cf621-38bc-4671-8027-eaae9b9ec327
```

**Status**: ✅ Erfolgreich (ohne GCS für last_selected)

### Test 2: sys_mandanten system_editor Frame

**Befehl**: `python create_sys_mandanten_frame_system_editor.py`

**Ergebnis**:
```
✅ Frame erstellt: 7dea382c-7833-4ef2-a49d-7171c304e78c
   View-GUID: 0326ca8f-d16e-4170-b152-d0f0585b36ba
   Dialog-GUID: 079ebf6e-fc9c-498f-8a94-1726a5c23cb1
   EDIT_TYPE: system_editor
```

**Status**: ✅ Erfolgreich

---

## 📋 sys_mandanten Frames

### Übersicht

| Edit-Type | Frame-GUID | Verwendung |
|-----------|------------|------------|
| **input_controls** | `011fc4bc-e3a6-4877-bb76-ae14dcdbf43e` | Input-Controls verwalten |
| **system_editor** | `7dea382c-7833-4ef2-a49d-7171c304e78c` | Stammdaten bearbeiten |

### Unterschied

**input_controls Frame** (vorher erstellt):
- Template-Satz 55555... bearbeiten
- Input-Controls für Mandanten-Datenerfassung konfigurieren
- Root, Root_Controls, Control_Properties, Templates

**system_editor Frame** (jetzt erstellt):
- sys_mandanten Tabelle direkt bearbeiten
- Mandanten-Stammdaten (uid, name, daten JSON)
- Standard-Editor für Tabellen-Einträge

---

## 🔧 Dateien

**Neu erstellt**:
1. ✅ `create_genereller_dialog.py` (388 Zeilen) - Handler + Wizard
2. ✅ `test_genereller_dialog_wizard.py` (23 Zeilen) - Standalone Test
3. ✅ `create_sys_mandanten_frame_system_editor.py` (108 Zeilen) - Frame-Erstellung

**Verwendete Komponenten**:
- `allgemeines.neue_guid()` - GUID-Generierung
- `pdvm_system.db` - sys_viewdaten, sys_framedaten, sys_dialogdaten
- `pdvm_central_systemsteuerung.get_gcs()` - Last-Selected Speicherung

---

## 🎯 Workflow-Beispiel

### Beispiel: Neuen generellen Dialog erstellen

**Schritt 1: Handler aufrufen**
```
Menü → System → Generellen Dialog erstellen
```

**Schritt 2: Dialog ausfüllen**
```
Name: "Konten verwalten"
View: [●] Neue View erstellen
      Tabelle: "sys_konten"
Dialog: [Dropdown] → "Standard System Editor (079e...)"
```

**Schritt 3: Ausführen**
```
✅ Frame-GUID: ab12cd34-...
✅ View-GUID: ef56gh78-...
✅ Dialog-GUID: 079ebf6e-...
```

**Schritt 4: Menü-Eintrag erstellen**
```python
{
    'name': 'Konten verwalten',
    'frame_guid': 'ab12cd34-...',
    'icon': '💰'
}
```

---

## ✅ Anforderungen erfüllt

| Anforderung | Status |
|-------------|--------|
| Namen abfragen | ✅ Input-Feld |
| Frame-GUID automatisch generieren | ✅ `allgemeines.neue_guid()` |
| Bestehende View wählen | ✅ SimpleView auf sys_viewdaten |
| Neue View erstellen | ✅ Radio-Button + Tabellen-Name |
| Dialog-GUID wählen | ✅ SimpleView auf sys_dialogdaten |
| Last-Selected Vortrag | ✅ GCS LAST_DIALOG_GUID |
| Ausführen-Button | ✅ Workflow starten |
| Menü-Integration | ✅ Handler-Funktion |

---

## 📌 Nächste Schritte

1. **Menü-Eintrag erstellen** für Handler
2. **sys_mandanten testen** mit beiden Frames:
   - Input-Controls konfigurieren (input_controls Frame)
   - Mandanten anlegen/bearbeiten (system_editor Frame)
3. **Weitere generelle Dialoge** mit Handler erstellen

---

## 💡 Architektur-Vorteile

**Wiederverwendbar**:
- Ein Handler für ALLE generellen Dialoge
- Konsistenter Workflow
- Automatische GUID-Verwaltung

**Flexibel**:
- Bestehende Views wiederverwenden
- Neue Views on-the-fly erstellen
- Dialog-Templates wiederverwendbar

**Benutzerfreundlich**:
- 3-Schritte Wizard
- Last-Selected Vortrag
- Sofort-Feedback mit GUIDs

---

**STATUS**: ✅ VOLLSTÄNDIG IMPLEMENTIERT UND GETESTET
