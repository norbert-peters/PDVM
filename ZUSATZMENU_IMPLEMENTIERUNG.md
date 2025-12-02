# Zusatzmenü-System Implementierung

## 📋 Übersicht

**Datum**: 13.11.2025  
**Status**: ✅ Kern-Implementierung abgeschlossen  
**Version**: V2.0

## 🎯 Konzept

Zusatzmenüs sind kontextsensitive horizontale Menüs die:
- An einzelne BUTTON oder SUBMENU Items gebunden werden
- Sich mit Vererbungslogik durch die Menühierarchie ziehen
- Gemeinsam mit GRUND-Menü horizontal gerendert werden
- Gleiche Button-Breiten haben (kein Springen beim Wechsel)

## 🏗️ Architektur

### Datenstruktur
```
sys_menudaten (SQLite):
├── VERTIKAL/{menu_guid}     # Vertikales Hauptmenü
├── GRUND/{menu_guid}         # Horizontales Hauptmenü
└── ZUSATZ/{item_guid}        # Zusatzmenü unter Item-GUID gespeichert
    └── [Menu-Items...]       # Gleiche Struktur wie Hauptmenüs
```

**Schlüssel-Konzept**: 
- Zusatzmenü wird unter `ZUSATZ/{item_guid}` gespeichert
- `item_guid` = GUID des Menüpunkts aus VERTIKAL/GRUND
- Keine doppelte Speicherung nötig!

### Vererbungslogik
```
SUBMENU "Personen" (hat Zusatzmenü: person-actions-guid)
├── BUTTON "Person anlegen" (erbt: person-actions-guid)
├── BUTTON "Person bearbeiten" (erbt: person-actions-guid)
└── SUBMENU "Erweitert" (eigenes Zusatzmenü: advanced-guid)
    ├── BUTTON "Import" (erbt: advanced-guid)
    └── BUTTON "Export" (erbt: advanced-guid)
```

**Regel**: Eigenes Zusatzmenü überschreibt geerbtes!

## 📂 Implementierte Dateien

### 1. `pdvm_central_systemsteuerung.py`

#### Neue Methoden:

**`build_zusatzmenu_mapping(menu_matrix)`**
- Baut Zusatzmenü-Zuordnung mit Vererbungslogik auf
- Temporäre Instanz bei jedem Menü-Wechsel
- Returns: `{item_guid: zusatz_guid}` Mapping

```python
# Beispiel-Aufruf:
mapping = gcs.build_zusatzmenu_mapping(menu_matrix)
# Result: {
#   'person-anlegen-guid': 'person-actions-guid',
#   'person-bearbeiten-guid': 'person-actions-guid',
#   ...
# }
```

**`get_zusatzmenu_for_item(item_guid, zusatz_mapping)`**
- Ermittelt Zusatzmenü-GUID für Item aus Mapping
- Schneller Lookup ohne Rekursion

**`load_zusatzmenu_data(zusatzmenu_guid)`**
- Lädt Zusatzmenü-Matrix aus ZUSATZ-Gruppe
- Returns: Menu-Matrix oder `[]`

### 2. `pdvm_menu_system_autonomous.py`

#### Neue Methode:

**`render_horizontal_combined(grund_matrix, zusatz_matrix, container, menu_handler, gcs)`**

**Features**:
- ✅ GRUND + ZUSATZ in einem Container
- ✅ Gleiche Button-Breiten (längster Text + Padding)
- ✅ Font-Metriken für exakte Berechnung
- ✅ Separator zwischen GRUND und ZUSATZ
- ✅ Unterschiedliche Farben (GRUND: #2c3e50, ZUSATZ: #16a085)
- ✅ `execute_command_with_zusatz()` für Auto-Update

**Layout**:
```
[GRUND Button 1] [GRUND Button 2] [GRUND Button 3] | [ZUSATZ Button 1] [ZUSATZ Button 2] [Spacer]
←────────────── Alle gleich breit ──────────────→
```

### 3. `pdvm_menu_handler.py`

#### Neue Properties:
```python
self._zusatz_mapping = {}           # {item_guid: zusatz_guid}
self._current_menu_matrix = []      # Aktuelle Menu-Matrix
```

#### Neue Methoden:

**`set_menu_matrix(menu_matrix)`**
- Setzt aktuelle Matrix und baut Mapping auf
- Wird bei `load_startmenu()` und `load_menu()` aufgerufen

**`execute_command_with_zusatz(command_data, item_guid)`**
- Führt Command aus + aktualisiert Zusatzmenü
- Workflow:
  1. Command normal ausführen
  2. Zusatzmenü für `item_guid` ermitteln
  3. Horizontales Menü neu rendern

**`_update_zusatzmenu(item_guid)`**
- Private Methode für Zusatzmenü-Aktualisierung
- Lädt Zusatzmenü-Daten
- Ruft `render_horizontal_combined()` auf

## 🔄 Workflow

### Bei Menü-Start/Wechsel:
```
1. load_startmenu(menu_guid) aufgerufen
   ↓
2. Menu-Matrix aus DB laden (VERTIKAL/GRUND)
   ↓
3. menu_handler.set_menu_matrix(matrix)
   → Baut Zusatzmenü-Mapping auf
   ↓
4. VERTIKAL normal rendern (_render_unified_button_menu)
   ↓
5. GRUND als leer rendern (kein Zusatzmenü initial)
```

### Bei Button/Submenu-Klick:
```
1. User klickt "Person anlegen" (item_guid)
   ↓
2. execute_command_with_zusatz(command, item_guid)
   ↓
3. Command ausführen (z.B. Dialog öffnen)
   ↓
4. _update_zusatzmenu(item_guid)
   ↓
5. Zusatzmenü-GUID ermitteln (aus Mapping)
   ↓
6. render_horizontal_combined(GRUND + ZUSATZ)
   → Gleiche Button-Breiten
   → Separator
   → ZUSATZ-Buttons
```

## 🎨 Button-Breiten-Berechnung

```python
# 1. Alle Labels sammeln (GRUND + ZUSATZ)
all_labels = ['▶ Personen', 'Einstellungen', 'Speichern', 'Abbrechen']

# 2. Längsten Text mit Font-Metriken messen
font = QFont("Segoe UI", 13, QFont.Bold)
fm = QFontMetrics(font)
max_width = max(fm.horizontalAdvance(label) for label in all_labels)

# 3. Button-Breite = max_width + Padding
button_width = max_width + 40  # 15px links + 15px rechts + 10px Reserve

# 4. Alle Buttons setzen
btn.setFixedWidth(button_width)
```

**Vorteil**: Buttons springen nicht hin und her beim Zusatzmenü-Wechsel!

## 🚀 Nächste Schritte

### Sofort:
1. ✅ load_startmenu() anpassen → `set_menu_matrix()` aufrufen
2. ⏳ Testen mit Beispiel-Zusatzmenü
3. ⏳ Debugging der Vererbungslogik

### Später:
4. ⏳ MenuEditor: Zusatzmenü-Button hinzufügen
5. ⏳ MenuEditor: Zusatzmenü-Editor (eigenes Fenster)
6. ⏳ Template-System für Zusatzmenüs
7. ⏳ Scroll-Funktion für viele Buttons

## ⚠️ Wichtige Hinweise

### Performance:
- **Mapping-Aufbau**: Nur bei Menü-Wechsel (nicht bei jedem Klick!)
- **Caching**: Zusatzmenü-Daten gecacht in GCS
- **Lookup**: O(1) Zugriff via Dict-Mapping

### Datenbank:
- **ZUSATZ-Gruppe**: Item-GUID als Feld-Name
- **Struktur**: Gleich wie VERTIKAL/GRUND
- **Persistenz**: Automatisch via PdvmCentralDatenbank

### UI:
- **Container**: Bereits in pdvm_systemstart.py vorhanden
- **Layout**: QHBoxLayout für horizontal
- **Farben**: GRUND (#2c3e50), ZUSATZ (#16a085)

## 📝 Code-Beispiel

### Zusatzmenü erstellen:
```python
# In sys_menudaten unter ZUSATZ/{item_guid}:
zusatz_menu = [
    {
        'guid': 'save-btn-guid',
        'type': 'BUTTON',
        'label': 'Speichern',
        'sort_order': 0,
        'parent_guid': None,
        'command': {
            'handler': 'save_data',
            'params': {}
        }
    },
    {
        'guid': 'cancel-btn-guid',
        'type': 'BUTTON',
        'label': 'Abbrechen',
        'sort_order': 1,
        'parent_guid': None,
        'command': {
            'handler': 'cancel_dialog',
            'params': {}
        }
    }
]

# Unter ZUSATZ/person-anlegen-guid speichern
gcs._menu_system_db.set_value('ZUSATZ', 'person-anlegen-guid', zusatz_menu)
```

### Zusatzmenü verwenden:
```python
# Automatisch via execute_command_with_zusatz()
# Kein manueller Code nötig - Rendering erfolgt automatisch!
```

## ✅ Erfolgs-Kriterien

- [x] Zusatzmenü-Verwaltung in GCS
- [x] Vererbungslogik implementiert
- [x] Horizontales kombiniertes Rendering
- [x] Gleiche Button-Breiten
- [x] Auto-Update bei Klick
- [ ] Integration in load_startmenu()
- [ ] Test mit Beispieldaten
- [ ] MenuEditor-Unterstützung

---

**Implementiert von**: GitHub Copilot  
**Review**: Ausstehend  
**Dokumentation**: Vollständig
