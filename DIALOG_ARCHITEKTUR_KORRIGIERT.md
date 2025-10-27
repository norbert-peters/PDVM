# 🎯 PDVM GENERELLER DIALOG - KORREKTE ARCHITEKTUR

## ❌ VORHERIGES MISSVERSTÄNDNIS

Ich habe fälschlicherweise angenommen:
- Input-Controls laden ihre Daten aus ViewDaten-Controls
- Input-Controls brauchen die View-GUID für Controls-Definition

## ✅ TATSÄCHLICHE ARCHITEKTUR (vom Benutzer beschrieben)

### 1. DIALOG-START

```
Dialog gestartet mit frame_guid
```

### 2. FRAMEDATEN LADEN (aus `framedaten.db` mit `frame_guid`)

**Gruppe: ROOT**

```json
{
  "ROOT_TABLE": "persondaten",
  "VIEW_GUID": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
  "DIALOG_GUID": "65d48641-250e-440c-8c70-0b6d0703df30",
  "HEADER_TEXT": "Persönliche Daten - Test",
  "EDIT_TYPE": "input_controls"
}
```

**WICHTIG**: `VIEW_GUID` wird **NUR für Tab 1 (View)** verwendet!

### 3. DIALOGDATEN LADEN (aus `dialogdaten.db` mit `DIALOG_GUID`)

**Aktueller Stand** (FEHLERHAFT!):
```json
{
  "ROOT": {
    "active_tab": 1,
    "tab_count": 2
  },
  "Tab01": {
    "tab_type": "view",
    "tab_title": "Übersicht",
    "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"  // ❌ REDUNDANT!
  },
  "Tab02": {
    "tab_type": "edit",
    "tab_title": "Bearbeiten",
    "selected_guid": "58c0acaa-fd40-4444-b516-c162f17a39b8"  // ❌ GEHÖRT HIER NICHT HIN!
  }
}
```

**KORRIGIERT**:
```json
{
  "ROOT": {
    "active_tab": 1,
    "tab_count": 2
  },
  "Tab01": {
    "tab_type": "view",
    "tab_title": "Übersicht"
    // view_guid kommt aus FRAMEDATEN, nicht hier!
  },
  "Tab02": {
    "tab_type": "edit",
    "tab_title": "Bearbeiten"
    // selected_guid kommt aus SYSTEMSTEUERUNG (GCS), nicht hier!
  }
}
```

### 4. TAB 1: VIEW (AUTONOM)

```
View(view_guid=FRAMEDATEN.ROOT.VIEW_GUID)
  ↓
Zeigt alle Datensätze aus root_table
  ↓
Bei Doppelklick → Signal mit GUID
```

**View ist vollständig autonom!**
- Kennt Dialog nicht
- Kennt Edit nicht
- Liefert nur GUID via Signal

### 5. TAB 2: EDIT (AUTONOM, aber GUID-abhängig)

```
Edit-Manager initialisiert mit:
  - framedaten_db (für EDIT_TYPE, ROOT_TABLE, etc.)
  - selected_guid (kommt aus Systemsteuerung oder View-Signal)

get_widget() aufgerufen:
  ↓
Edit-Widget erstellt für selected_guid
```

**Edit ist autonom von View!**
- Braucht KEINE View-GUID
- Braucht KEINE ViewDaten-Controls
- Braucht nur:
  - `framedaten_db` (für ROOT_TABLE, ggf. eigene Metadaten)
  - `selected_guid` (für welchen Datensatz editieren?)

### 6. GUID-PERSISTIERUNG (SYSTEMSTEUERUNG via GCS)

**Schlüssel**: `{frame_guid}_LAST_SELECTION`

```python
# Beim Auswählen in View:
gcs._db.set_value('DIALOG', f'{frame_guid}_LAST_SELECTION', selected_guid)
gcs._db.save_all_values()

# Beim Dialog-Start:
last_guid, _ = gcs._db.get_value('DIALOG', f'{frame_guid}_LAST_SELECTION')
if last_guid:
    # Edit direkt öffnen mit dieser GUID
```

**NICHT** in dialogdaten.db speichern!
**NUR** in systemsteuerung.db (User-spezifisch!)

---

## 🔧 INPUT-CONTROLS V2 - KORREKTE IMPLEMENTATION

### Was Input-Controls WIRKLICH braucht:

1. **`framedaten_db`** - Für:
   - `ROOT_TABLE` (aus `ROOT.ROOT_TABLE`)
   - Eigene Metadaten (z.B. Gruppe `INPUTCONTROLS_META` oder ähnlich)

2. **`selected_guid`** - Für:
   - Welcher Datensatz soll bearbeitet werden?

### Was Input-Controls NICHT braucht:

- ❌ `view_guid` (hat nichts mit View zu tun!)
- ❌ ViewDaten-Controls (View ist autonom!)
- ❌ Projektions-Tabellen (View-intern!)

### Wo sind die Input-Controls-Definitionen?

**OPTION 1**: In `framedaten.db` unter eigener Gruppe:
```
Gruppe: INPUTCONTROLS
  feld1: {label: "Familienname", gruppe: "PERSDATEN", feld: "FAMILIENNAME", ...}
  feld2: {label: "Vorname", gruppe: "PERSDATEN", feld: "VORNAME", ...}
  ...
```

**OPTION 2**: In `framedaten.db` als JSON-Feld:
```
Gruppe: ROOT
  INPUTCONTROLS_META: "[{...}, {...}, ...]"
```

**OPTION 3** (wie V1): Separate Metadaten-Gruppe:
```
Gruppe: METADATEN
  PERSONDATEN_PERSDATEN_FAMILIENNAME: {...}
  PERSONDATEN_PERSDATEN_VORNAME: {...}
  ...
```

---

## 📋 DIALOG V2 - ERFORDERLICHE ÄNDERUNGEN

### 1. Dialogdaten bereinigen

**ENTFERNEN**:
- `Tab01.view_guid` (kommt aus FRAMEDATEN!)
- `Tab02.selected_guid` (kommt aus SYSTEMSTEUERUNG!)

### 2. GUID-Persistierung korrigieren

**Schlüssel ändern**:
```python
# ❌ FALSCH (View-GUID):
last_guid_key = f"{self.view_guid}_last_selected_guid"

# ✅ RICHTIG (Frame-GUID):
last_guid_key = f"{self.frame_guid}_LAST_SELECTION"
```

**Gruppe ändern** (falls nötig):
```python
# Aktuell: gcs._db.get_value('DIALOG', ...)
# Das ist korrekt - systemsteuerung.db, Gruppe DIALOG
```

### 3. Edit-Typ aus Framedaten laden

**NEU in Framedaten hinzufügen**:
```python
self.edit_type, _ = self.framedaten_db.get_value('ROOT', 'EDIT_TYPE')
```

**Beim Edit-Tab-Erstellen verwenden**:
```python
ModuleClass = self.edit_modules.get(self.edit_type)
```

---

## ✅ ZUSAMMENFASSUNG

**Dialog-Ablauf (LINEAR)**:

1. `frame_guid` → **Framedaten laden**
   - `ROOT_TABLE`, `VIEW_GUID`, `DIALOG_GUID`, `HEADER_TEXT`, `EDIT_TYPE`

2. `DIALOG_GUID` → **Dialogdaten laden**
   - Tab-Konfiguration (KEINE GUIDs!)

3. **Tab 1**: View(view_guid=`VIEW_GUID` aus Framedaten)
   - Vollständig autonom
   - Signal bei Doppelklick → GUID

4. **Tab 2**: Edit-Manager(framedaten_db, selected_guid)
   - `selected_guid` aus:
     - Systemsteuerung (beim Start) ODER
     - View-Signal (bei Doppelklick)
   - Vollständig autonom von View

5. **GUID speichern**: GCS → `systemsteuerung.db`
   - Schlüssel: `{frame_guid}_LAST_SELECTION`
   - Gruppe: `DIALOG`

**Klare Trennung**:
- **framedaten.db**: Frame-Konfiguration (für ALLE User gleich)
- **dialogdaten.db**: Dialog-UI-Status (Tab-Titel, etc.)
- **systemsteuerung.db** (via GCS): User-spezifisch (LAST_SELECTION, etc.)
