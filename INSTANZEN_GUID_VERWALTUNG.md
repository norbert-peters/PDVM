# Instanzen & GUID-Verwaltung im PDVM-System

## 📋 Übersicht

Das PDVM-System verwendet ein **dynamisches Instanzen-Pool-System** für verschachtelte Datenstrukturen mit **stichtaggenauer** Auflösung von GUID-Referenzen.

---

## 🏗️ Architektur-Konzept

### Zentrale Prinzipien

1. **GUID-Feld als Referenz**: Ein dediziertes Feld enthält die GUID der zugeordneten Tabelle
2. **Source-Path für Auflösung**: Andere Controls nutzen `source_path` um die aktuelle GUID zu ermitteln
3. **Stichtaggenauigkeit**: GUID kann sich über Zeit ändern → `get_value()` mit Stichtag
4. **Lazy Instance Creation**: Instanzen werden nur bei Bedarf erstellt (nicht vorab)

---

## 🔄 Datenfluss

```
┌─────────────────────────────────────────────────────────────┐
│                    PERSONDATEN (ROOT)                        │
│  selected_guid: "abc-123"                                    │
├─────────────────────────────────────────────────────────────┤
│  PERSDATEN / FINANZDATEN-FINANZDATEN = "xyz-789"  ← GUID!  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ source_path: "root_PERSDATEN"
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              FINANZDATEN (verschachtelt)                     │
│  guid: "xyz-789" (ermittelt aus ROOT)                       │
├─────────────────────────────────────────────────────────────┤
│  FINANZDATEN / KONTOINHABER = "Max Mustermann"              │
│  FINANZDATEN / IBAN = "DE89..."                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Metadaten-Format

### Beispiel: Verschachteltes Control

```json
{
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {
    "source_path": "root_PERSDATEN",
    "label": "Kontoinhaber",
    "tooltip": "Name des Kontoinhabers",
    "tab": 1,
    "order": 10,
    "read_only": false,
    "historical": true
  }
}
```

**Field-Key Struktur**: `TABELLE_GRUPPE_FELD`
- `FINANZDATEN`: Ziel-Tabelle
- `FINANZDATEN`: Ziel-Gruppe
- `KONTOINHABER`: Ziel-Feld

**Source-Path**: `root_PERSDATEN`
- `root`: Startet bei ROOT-Instanz
- `PERSDATEN`: Gruppe in ROOT, die die GUID enthält

---

## 🔧 Instanzen-Pool Aufbau

### 1. ROOT-Instanz initialisieren

```python
# Manager erhält selected_guid (z.B. aus View-Selection)
root_instance = PdvmCentralDatenbank('persondaten', selected_guid)
instances['ROOT'] = root_instance
instances['PERSONDATEN_abc-123'] = root_instance
```

### 2. GUID-Auflösung für verschachtelte Instanz

```python
# Metadaten eines Controls:
field_key = "FINANZDATEN_FINANZDATEN_KONTOINHABER"
source_path = "root_PERSDATEN"

# Parse:
target_table = "FINANZDATEN"      # Aus field_key (Teil 1)
target_gruppe = "FINANZDATEN"     # Aus field_key (Teil 2)
lookup_gruppe = "PERSDATEN"       # Aus source_path (nach 'root_')

# Lookup-Feld bauen:
lookup_feld = "FINANZDATEN-FINANZDATEN"  # TABELLE-GRUPPE

# GUID stichtaggenau auflösen (WICHTIG: Stichtag, nicht neues Abdatum!)
stichtag = gcs.st_inst.PdvmDateTime  # ← Bestimmt WELCHE GUID geladen wird
result = root_instance.get_value(lookup_gruppe, lookup_feld, stichtag)
guid, abdatum = result  # z.B. ("xyz-789", 2025294.123)

# DEBUG-Log (neu hinzugefügt):
logger.debug(f"🔍 Suche GUID: {lookup_gruppe}.{lookup_feld} (Stichtag: {stichtag})")
logger.debug(f"   → GUID gefunden: {guid} (Abdatum: {abdatum})")

# Instanz-Key:
instance_key = "FINANZDATEN_xyz-789"
```

**KRITISCH**: 
- Verwendet **Stichtag** (nicht neues Abdatum)
- Bestimmt WELCHE GUID zum Stichtag gültig ist
- Person kann zu verschiedenen Zeiten verschiedene GUIDs haben

### 3. Instanz erstellen oder wiederverwenden

```python
if instance_key not in instances:
    # Neue Instanz erstellen
    new_instance = PdvmCentralDatenbank('finanzdaten', guid)
    instances[instance_key] = new_instance
    logger.info(f"✅ Neue Instanz: {instance_key}")
else:
    logger.debug(f"♻️ Instanz bereits vorhanden: {instance_key}")
```

---

## 📊 Control-Zuordnung

### Matching-Logik

```python
def get_instance_for_control(field_key: str, instances: dict):
    """
    Findet passende Instanz für Control
    
    1. Ermittle Ziel-Tabelle aus field_key
    2. Suche Instanz mit Tabellen-Präfix im Pool
    3. Falls mehrere: Nimm erste (oder spezifische Logik)
    4. Falls keine: Control ohne Instanz (read-only)
    """
    field_parts = field_key.split('_')
    target_table = field_parts[0].upper()
    
    # Suche Instanz mit passendem Tabellen-Präfix
    for instance_key, instance in instances.items():
        if instance_key.startswith(f"{target_table}_"):
            return instance_key, instance
    
    # Keine Instanz gefunden
    return None, None
```

### Control-Erstellung

```python
# Instanz holen
instance_key, db_instance = get_instance_for_control(field_key, instances)

if not db_instance:
    logger.warning(f"⚠️ Keine Instanz für {field_key} → Read-Only")

# Control erstellen
control = create_control_from_config(
    instance_key=instance_key or 'NO_INSTANCE',
    db_instance=db_instance,  # Kann None sein!
    config=meta
)

# Read-Only Logik (in Control):
if not self.db_instance:
    # KEINE INSTANZ → IMMER Read-Only
    self.edit_widget.setReadOnly(True)
```

---

## ⏱️ Stichtag-Wechsel

### Problem

Bei Stichtag-Wechsel können sich GUIDs ändern:
- 01.01.2024: `FINANZDATEN-FINANZDATEN = "guid-alt"`
- 01.06.2024: `FINANZDATEN-FINANZDATEN = "guid-neu"`

### Lösung

```python
def rebuild_instances_on_stichtag_change(selected_guid: str, stichtag: float):
    """
    Baut Instanzen-Pool nach Stichtag-Wechsel neu auf
    
    WICHTIG: 
    - Alte Instanzen verwerfen
    - GUIDs NEU auflösen (mit neuem Stichtag)
    - Controls neu laden
    """
    logger.info(f"🔄 Stichtag-Wechsel: Instanzen neu aufbauen...")
    
    # GCS Stichtag aktualisieren
    gcs.st_inst.PdvmDateTime = stichtag
    
    # Instanzen-Pool leeren
    instances.clear()
    
    # ROOT neu laden
    root_instance = PdvmCentralDatenbank('persondaten', selected_guid)
    instances['ROOT'] = root_instance
    
    # Verschachtelte Instanzen NEU auflösen
    for meta in controls_meta:
        # ... GUID-Auflösung mit NEUEM Stichtag ...
        result = root_instance.get_value(gruppe, feld, stichtag)  # ← NEUE GUID!
        guid, _ = result
        
        # Neue Instanz erstellen
        new_instance = PdvmCentralDatenbank(tabelle, guid)
        instances[f"{tabelle}_{guid}"] = new_instance
    
    logger.info(f"✅ Instanzen-Pool aktualisiert")
```

---

## 🛡️ Fehlerbehandlung

### GUID nicht gefunden

```python
result = root_instance.get_value(gruppe, feld, stichtag)

if not result or result[0] is None:
    logger.warning(f"⚠️ Keine GUID gefunden: {gruppe}.{feld}")
    logger.warning(f"   → Control '{field_key}' wird ohne Instanz erstellt")
    # Control wird read-only sein (keine Instanz)
    continue
```

### Instanz-Erstellung fehlgeschlagen

```python
try:
    new_instance = PdvmCentralDatenbank(tabelle, guid)
except Exception as e:
    logger.error(f"❌ Fehler beim Erstellen von Instanz: {e}")
    # Control ohne Instanz → read-only
    db_instance = None
```

### Mehrstufige Pfade (noch nicht implementiert)

```python
# Format: "root_PERSDATEN_WEITERE_DATEN"
# → Benötigt rekursive Auflösung

if len(path_parts) > 2:
    logger.warning(f"⚠️ Mehrstufige Pfade noch nicht unterstützt: {source_path}")
    continue
```

---

## 🎯 Wichtige Regeln

### ✅ DO

1. **IMMER `source_path` für GUID-Auflösung verwenden**
   - Nicht direkt GUID aus Feld lesen (kann veraltet sein)
   
2. **Stichtag bei `get_value()` übergeben**
   - Garantiert zeitpunktgenaue Daten
   
3. **Instanzen wiederverwenden**
   - Prüfe Pool vor Erstellung
   
4. **Read-Only bei fehlender Instanz**
   - Verhindert ungültige Schreiboperationen

### ❌ DON'T

1. **NIEMALS GUID cachen ohne Stichtag**
   - GUIDs können sich ändern
   
2. **NIEMALS Instanz vorab für alle Controls erstellen**
   - Lazy Loading → nur bei Bedarf
   
3. **NIEMALS direkt auf DB zugreifen ohne Instanz-Pool**
   - Zentrale Verwaltung garantiert Konsistenz

---

## 📚 Code-Referenzen

### Dateien

- **`pdvm_input_controls_manager_v2.py`**
  - `_build_instances_pool()`: Instanzen-Pool Aufbau
  - `_build_controls_matrix()`: Control-Instanz-Zuordnung
  
- **`pdvm_central_datenbank.py`**
  - `get_value(gruppe, feld, stichtag)`: Stichtaggenaue Datenabfrage
  - `get_field(gruppe, feld)`: Historische Werte (für Historie-Dialog)
  
- **`pdvm_input_control_v2.py`**
  - `__init__(db_instance=None)`: Control mit optionaler Instanz
  - Read-Only Logik: Instanz-Prüfung ZUERST!

### Wichtige Variablen

```python
# Manager:
self.instances: Dict[str, PdvmCentralDatenbank]
  # {"ROOT": instance1, "FINANZDATEN_xyz-789": instance2, ...}

self.controls_matrix: List[Dict]
  # [{"control": PdvmInputControl, "instance_key": "FINANZDATEN_xyz-789", ...}]

# Control:
self.db_instance: Optional[PdvmCentralDatenbank]
  # None → Read-Only, sonst editierbar
```

---

## 🚀 Erweiterungen (TODO)

### Mehrstufige Pfade

```python
# source_path: "root_PERSDATEN_FINANZDATEN_VERTRÄGE"
# → Rekursive Auflösung:
#    1. ROOT → PERSDATEN → guid1
#    2. Instanz mit guid1 → FINANZDATEN → guid2
#    3. Instanz mit guid2 → VERTRÄGE → guid3
#    4. Finale Instanz mit guid3
```

### Automatische Instanz-Aktualisierung

```python
# Signal-System bei Änderung:
# GUID in ROOT ändert sich → Observer benachrichtigen
# → Instanz neu laden → Controls aktualisieren
```

### Instanz-Caching mit Stichtag

```python
# Cache-Key: (tabelle, guid, stichtag)
# Vermeidet redundante DB-Zugriffe
cache[(tabelle, guid, stichtag)] = instance
```

---

**Stand**: 22.10.2025 - Historie-Funktion implementiert  
**Version**: V2 mit autonomer Pipeline
