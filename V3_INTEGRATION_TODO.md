# 🚀 V3 Filter-System: Integration TODO

## ✅ FERTIG: Komponenten erstellt

- [x] `schnellsuche_manager.py` - GLOBAL:contains:wert Format
- [x] `einfach_filter_manager.py` - feld:operator:wert Format  
- [x] `komplex_filter_manager.py` - feld:pos1|pos2|pos3|pos4 Format
- [x] `search_string_parser.py` - Einheitlicher Parser für alle Formate
- [x] `V3_FILTER_SYSTEM_KOMPLETT.md` - Vollständige Dokumentation

---

## 📋 TODO: Integration in bestehende Dateien

### 1. Matrix Manager Integration

**Datei**: `pdvm_view_matrix_manager.py`

**Änderungen**:
```python
# IMPORT hinzufügen (Zeile ~20)
from search_string_parser import get_search_string_parser

# In apply_filter() Methode (Zeile ~353):
def apply_filter(self, search_string: str = None):
    """SCHRITT 2: FilterMatrix aus BasisMatrix erstellen"""
    
    if not search_string or search_string.strip() == "":
        # Kein Filter
        self.filter_matrix = deepcopy(self.basis_matrix)
        return
    
    # NEU: Parser verwenden
    parser = get_search_string_parser()
    filter_func = parser.parse(search_string)
    
    if not filter_func:
        logger.error("❌ Parser konnte search_string nicht verarbeiten")
        self.filter_matrix = deepcopy(self.basis_matrix)
        return
    
    # Filter anwenden
    self.filter_matrix = [
        row for row in self.basis_matrix
        if filter_func(row)
    ]
    
    logger.info(f"✅ Filter: {len(self.filter_matrix)} von {len(self.basis_matrix)} Zeilen")

# ALT ENTFERNEN (Zeile ~730+):
# - _apply_unified_search_filter()
# - _apply_multi_field_filter()
# - _apply_complex_filter_with_groups()
# - _check_group()
# - _check_single_condition()
# - _apply_single_field_filter()
# - _apply_global_search_filter()
# → Alle diese Methoden werden durch Parser ersetzt!
```

**Status**: ⏳ TODO

---

### 2. View Controller Integration (Schnellsuche)

**Datei**: `pdvm_view_controller.py`

**Änderungen**:
```python
# IMPORT hinzufügen (Zeile ~20)
from schnellsuche_manager import SchnellsucheManager

# In __init__() Methode:
def __init__(self, view_guid, gcs, column_control, temp_instance):
    # ... existing code ...
    
    # NEU: Manager initialisieren
    self.schnellsuche_manager = SchnellsucheManager(
        view_guid=self.view_guid,
        matrix_manager=self.matrix_manager
    )

# In execute_search() Methode (komplett ersetzen):
def execute_search(self):
    """Schnellsuche ausführen"""
    search_text = getattr(self, 'pending_search_text', '')
    
    # NEU: Manager verwenden
    success = self.schnellsuche_manager.execute_schnellsuche(search_text)
    
    if success:
        logger.info(f"✅ Schnellsuche erfolgreich: '{search_text}'")
    else:
        logger.error(f"❌ Schnellsuche fehlgeschlagen")

# ALT ENTFERNEN:
# Alle alten save_all_values() Aufrufe in execute_search()
# Alte s_string/s_source Logik
```

**Status**: ⏳ TODO

---

### 3. View Dialog Integration (UI-Load)

**Datei**: `pdvm_view_dialog.py`

**Änderungen**:
```python
# IMPORT hinzufügen
from schnellsuche_manager import SchnellsucheManager

# In _load_and_apply_persistent_filters() Methode:
def _load_and_apply_persistent_filters(self):
    """Lädt persistente Filter beim Start"""
    
    if hasattr(self, 'search_input'):
        # NEU: Manager für UI-Load verwenden
        manager = SchnellsucheManager(
            view_guid=self.view_guid,
            matrix_manager=self.matrix_manager
        )
        
        search_text = manager.load_schnellsuche_ui()
        
        if search_text:
            self.search_input.setText(search_text)
            logger.info(f"🔄 Schnellsuche UI geladen: '{search_text}'")
        else:
            self.search_input.clear()
            logger.info(f"ℹ️ Schnellsuche-Feld leer (anderer Filter aktiv)")

# ALT ENTFERNEN:
# Alte s_source Check-Logik
# Alte schnell Parameter-Load
```

**Status**: ⏳ TODO

---

### 4. Parameter Dialog Integration (Einfach Filter)

**Datei**: `search_parameter_dialog.py`

**Änderungen**:
```python
# IMPORT hinzufügen
from einfach_filter_manager import EinfachFilterManager

# In __init__() Methode:
def __init__(self, view_guid, column_control, gcs, matrix_manager, parent=None):
    # ... existing code ...
    
    # NEU: Manager initialisieren
    self.einfach_manager = EinfachFilterManager(
        view_guid=self.view_guid,
        matrix_manager=self.matrix_manager
    )

# In accept_changes() Methode (für EINFACHE Filter):
def accept_changes(self):
    """Accept-Button wurde geklickt"""
    
    # Sammle neue Filter
    new_filters = {}
    for field_key, widgets in self.field_widgets.items():
        search_value = widgets['search_input'].text()
        if search_value and search_value.strip():
            new_filters[field_key] = search_value.strip()
    
    # Prüfe ob Extended Filter gesetzt
    extended_summary = {}
    for field_key, widgets in self.field_widgets.items():
        conditions = self._get_field_conditions(field_key)
        if conditions:
            # KOMPLEX Filter - siehe nächsten Punkt
            pass
    
    # Wenn KEINE Extended Filter:
    if not extended_summary and new_filters:
        # NEU: Einfach-Manager verwenden
        success = self.einfach_manager.execute_einfach_filter(new_filters)
        
        if success:
            logger.info(f"✅ Einfach-Filter gesetzt: {new_filters}")
        else:
            logger.error(f"❌ Einfach-Filter fehlgeschlagen")
    
    self.accept()

# ALT ENTFERNEN:
# Alte s_string/s_source Save-Logik für einfache Filter
# Alte save_persistent_filters() für einfache Filter
```

**Status**: ⏳ TODO

---

### 5. Parameter Dialog Integration (Komplex Filter)

**Datei**: `search_parameter_dialog.py`

**Änderungen**:
```python
# IMPORT hinzufügen
from komplex_filter_manager import KomplexFilterManager

# In __init__() Methode:
def __init__(self, view_guid, column_control, gcs, matrix_manager, parent=None):
    # ... existing code ...
    
    # NEU: Manager initialisieren
    self.komplex_manager = KomplexFilterManager(
        view_guid=self.view_guid,
        matrix_manager=self.matrix_manager
    )

# In accept_changes() Methode (für KOMPLEXE Filter):
def accept_changes(self):
    """Accept-Button wurde geklickt"""
    
    # Sammle Extended Filter
    field_conditions = {}
    for field_key, widgets in self.field_widgets.items():
        conditions = self._get_field_conditions(field_key)
        if conditions:
            field_conditions[field_key] = conditions
    
    # Wenn Extended Filter vorhanden:
    if field_conditions:
        # NEU: Komplex-Manager verwenden
        success = self.komplex_manager.execute_komplex_filter(field_conditions)
        
        if success:
            logger.info(f"✅ Komplex-Filter gesetzt: {len(field_conditions)} Felder")
        else:
            logger.error(f"❌ Komplex-Filter fehlgeschlagen")
    
    self.accept()

# ALT ENTFERNEN:
# Alte s_string/s_source Save-Logik für komplexe Filter
# Alte _build_search_string_from_conditions()
```

**Status**: ⏳ TODO

---

### 6. Extended Filter Engine Integration

**Datei**: `extended_filter_engine.py`

**Änderungen**:
```python
# IMPORT hinzufügen
from komplex_filter_manager import KomplexFilterManager

# In save_field_conditions() Methode:
def save_field_conditions(self, field_key: str, conditions: List):
    """Speichert Bedingungen für ein Feld"""
    
    # NEU: Komplex-Manager verwenden
    manager = KomplexFilterManager(
        view_guid=self.view_guid,
        matrix_manager=None  # Hier kein Matrix Manager nötig
    )
    
    # Nur für dieses eine Feld speichern
    field_conditions = {field_key: conditions}
    
    success = manager.execute_komplex_filter(field_conditions)
    
    if success:
        logger.info(f"✅ Extended Filter gespeichert: {field_key}")
    else:
        logger.error(f"❌ Extended Filter fehlgeschlagen: {field_key}")

# ALT ENTFERNEN:
# Alte s_string/s_source Save-Logik
# Alte _build_search_string_from_conditions()
```

**Status**: ⏳ TODO

---

### 7. Filter Reset Integration

**Datei**: `central_filter_reset.py`

**Änderungen**:
```python
# Sollte bereits korrekt sein (aus V2):
# - s_string → None
# - s_source → None
# - schnell → None
# - Alle Feld-Parameter → None

# Keine Änderung nötig, nur Überprüfung
```

**Status**: ✅ OK (bereits V2 korrekt)

---

## 🧪 Test-Plan

### Test 1: Schnellsuche persistent
```
1. Gib "lau" in Schnellsuche ein
2. Klick Suchen (3 Treffer erwartet)
3. App schließen & neu starten
4. Erwartung:
   - Matrix Manager lädt s_string="GLOBAL:contains:lau"
   - Parser gibt Filter-Funktion zurück
   - Filter aktiv, 3 Treffer
   - Suchfeld zeigt "lau"
```

### Test 2: Einfacher Filter persistent
```
1. Parameter Dialog öffnen
2. Familienname = "Müller" setzen
3. OK klicken (2 Treffer erwartet)
4. App schließen & neu starten
5. Erwartung:
   - Matrix Manager lädt s_string="familienname_show:contains:Müller"
   - Parser gibt Filter-Funktion zurück
   - Filter aktiv, 2 Treffer
   - Schnellsuche-Feld LEER (s_source='einfach')
```

### Test 3: Komplexer Filter persistent
```
1. Parameter Dialog öffnen
2. Familienname: Extended Filter setzen
   - Position 1: AND
   - Position 2: IS
   - Position 3: enthält
   - Position 4: Müller
3. OK klicken
4. App schließen & neu starten
5. Erwartung:
   - Matrix Manager lädt s_string="familienname_show:AND|IS|enthält|Müller"
   - Parser gibt Filter-Funktion zurück
   - Filter aktiv
   - Schnellsuche-Feld LEER (s_source='komplex')
```

### Test 4: Filter-Wechsel
```
1. Schnellsuche "lau" → 3 Treffer
2. Parameter Dialog "Müller" → 2 Treffer
3. Schnellsuche-Feld sollte LEER sein (s_source='einfach')
4. App Restart
5. Erwartung: 2 Treffer (Einfach-Filter aktiv)
```

### Test 5: Filter Reset
```
1. Beliebigen Filter setzen
2. Filter-Reset klicken
3. Erwartung: Alle Zeilen sichtbar
4. App Restart
5. Erwartung: Alle Zeilen sichtbar (kein Filter persistent)
```

---

## 📝 Checkliste

- [ ] Matrix Manager: Parser integriert, alte Methoden entfernt
- [ ] View Controller: SchnellsucheManager verwendet
- [ ] View Dialog: SchnellsucheManager für UI-Load
- [ ] Parameter Dialog: EinfachFilterManager verwendet
- [ ] Parameter Dialog: KomplexFilterManager verwendet
- [ ] Extended Filter Engine: KomplexFilterManager verwendet
- [ ] Filter Reset: Überprüft (sollte OK sein)
- [ ] Test 1: Schnellsuche ✅
- [ ] Test 2: Einfach Filter ✅
- [ ] Test 3: Komplex Filter ✅
- [ ] Test 4: Filter-Wechsel ✅
- [ ] Test 5: Filter Reset ✅

---

## 🎯 Erwartetes Ergebnis

Nach Integration:
- ✅ ALLE 3 Filter-Typen speichern Parameter + s_string + s_source
- ✅ Matrix Manager kann JEDEN search_string ausführen
- ✅ Einheitliche Struktur - linear auswertbar
- ✅ Filter persistent über Restart
- ✅ UI zeigt korrekten aktiven Filter (via s_source)

---

**Nächster Schritt**: Matrix Manager Integration starten
