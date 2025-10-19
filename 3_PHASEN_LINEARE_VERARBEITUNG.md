# 3-Phasen Lineare Verarbeitung - Input-Controls System

## 🎯 Übersicht

Das Input-Controls System verwendet eine **ultra-lineare 3-Phasen-Verarbeitung** für maximale Klarheit und Erweiterbarkeit.

**Prinzipien**:
- ✅ Jede Phase ist isoliert und testbar
- ✅ Keine Verschachtelungen oder komplexe Abhängigkeiten
- ✅ Klare Trennung: Vorbereitung → Instanzen → Rendering
- ✅ Vorbereitet für Expert Mode (manuelle Sortierung)

---

## 📋 PHASE 1: Controls mit Order aufbauen

**Methode**: `_prepare_controls()`

**Zweck**: Baut interne Control-Liste mit Order-Informationen auf

### Workflow

```python
def _prepare_controls(self):
    """
    PHASE 1: Baut Control-Metadaten mit Order auf
    """
    for field_key, field_config in self.metadaten.items():
        # Source-Path aus Config (Default: 'root')
        source_path = field_config.get('source_path', 'root')
        
        # Order berechnen
        if source_path == 'root':
            order = 1000 + index  # ROOT-Controls
        else:
            order = 2000 + index  # Andere Controls
        
        # Control-Metadaten speichern
        self.controls_meta.append({
            'field_key': field_key,
            'field_config': field_config,
            'source_path': source_path,
            'order': order
        })
    
    # Nach Order sortieren
    self.controls_meta.sort(key=lambda x: x['order'])
```

### Order-System

| Source-Path | Order | Beschreibung |
|------------|-------|--------------|
| `root` | 1000-1999 | ROOT-Tabelle Controls |
| `root_GRUPPE1` | 2000-2999 | Verknüpfte Tabelle 1 |
| `root_GRUPPE2` | 3000-3999 | Verknüpfte Tabelle 2 |
| ... | ... | ... |

**Hinweis**: Später kann der User/Expert Mode die Order manuell ändern!

### Beispiel

```python
# Metadaten Input
{
    'PERSONDATEN_PERSDATEN_FAMILIENNAME': {
        'source_path': 'root',
        'label': 'Familienname'
    },
    'FINANZWESEN_FINANZWESEN_KONTONUMMER': {
        'source_path': 'root_PERSDATEN',
        'label': 'Kontonummer'
    }
}

# Controls-Meta Output (sortiert!)
[
    {
        'field_key': 'PERSONDATEN_PERSDATEN_FAMILIENNAME',
        'source_path': 'root',
        'order': 1000
    },
    {
        'field_key': 'FINANZWESEN_FINANZWESEN_KONTONUMMER',
        'source_path': 'root_PERSDATEN',
        'order': 2000
    }
]
```

---

## 🔧 PHASE 2: DB-Instanzen aufbauen

**Methode**: `_prepare_instances()`

**Zweck**: Erstellt ALLE benötigten DB-Instanzen BEVOR das Rendering startet

### Instance-Key Format

**WICHTIG**: Key-Format ist `{TABELLE}_{GUID}` für eindeutige Zuordnung!

```python
# Beispiel
"PERSONDATEN_abc-123-def"  # ROOT-Instanz
"FINANZWESEN_xyz-789-ghi"  # Verknüpfte Tabelle
```

**Warum?** Gleiche Tabelle kann mit verschiedenen GUIDs mehrfach vorkommen!

### Source-Path Logik

#### 1. `source_path = 'root'`
→ ROOT-Instanz verwenden (bereits vorhanden mit `selected_guid`)

```python
if source_path == 'root':
    instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
    # Bereits in self.db_instances vorhanden!
```

#### 2. `source_path = 'root_GRUPPE'`
→ GUID aus ROOT-Tabelle holen und neue Instanz erstellen

```python
if source_path.startswith('root_'):
    # 1. Gruppe extrahieren
    source_gruppe = source_path[5:]  # Nach "root_"
    
    # 2. Feldschlüssel bauen: {GRUPPE}-{TABELLE} (uppercase!)
    feld_schluessel = f"{gruppe}-{table_name}".upper()
    # Beispiel: "FINANZWESEN-FINANZWESEN"
    
    # 3. GUID aus ROOT holen
    guid = root_instance.get_value(source_gruppe, feld_schluessel)[0]
    
    # 4. Neue Instanz erstellen
    instance_key = f"{table_name.upper()}_{guid}"
    instance = PdvmCentralDatenbank(table_name.lower(), guid)
    self.db_instances[instance_key] = instance
```

### Beispiel

**Framedaten-Konfiguration**:
```python
# METADATEN
{
    'FINANZWESEN_FINANZWESEN_KONTONUMMER': {
        'source_path': 'root_PERSDATEN',
        'label': 'Kontonummer'
    }
}
```

**Ablauf**:
1. Field-Key: `FINANZWESEN_FINANZWESEN_KONTONUMMER`
2. Parsing: `table='FINANZWESEN'`, `gruppe='FINANZWESEN'`
3. Source-Path: `root_PERSDATEN` → `source_gruppe='PERSDATEN'`
4. Feldschlüssel: `FINANZWESEN-FINANZWESEN`
5. GUID holen: `ROOT.get_value('PERSDATEN', 'FINANZWESEN-FINANZWESEN')`
6. Instanz erstellen: `PdvmCentralDatenbank('finanzwesen', guid)`
7. Speichern: `self.db_instances[f"FINANZWESEN_{guid}"] = instance`

### Lazy Loading

**WICHTIG**: Instanzen werden nur erstellt, wenn sie noch nicht existieren!

```python
instance_key = f"{table_name}_{guid}"
if instance_key in self.db_instances:
    continue  # Bereits vorhanden
```

---

## 🎨 PHASE 3: Rendering

**Methode**: `get_widget()`

**Zweck**: Rendert Controls in sortierter Reihenfolge

### Workflow

```python
def get_widget(self):
    # ... Header + GUID ...
    
    # Controls BEREITS SORTIERT (nach Order)!
    for control_meta in self.controls_meta:
        # Passende Instanz holen
        db_instance = self._get_instance_for_control(control_meta)
        
        # Control erstellen
        control = PdvmInputControl(
            field_key=control_meta['field_key'],
            field_config=control_meta['field_config'],
            db_instance=db_instance
        )
        
        # Zu Layout hinzufügen
        content_layout.addWidget(control)
```

### `_get_instance_for_control()` Helper

Diese Methode holt die passende Instanz für ein Control:

```python
def _get_instance_for_control(self, control_meta):
    field_key = control_meta['field_key']
    source_path = control_meta['source_path']
    
    # Tabelle aus Field-Key
    table_name = field_key.split('_')[0]
    gruppe = field_key.split('_')[1].upper()
    
    if source_path == 'root':
        # ROOT-Instanz
        instance_key = f"{self.root_table.upper()}_{self.selected_guid}"
        return self.db_instances.get(instance_key)
    
    # Andere Instanz: GUID aus ROOT holen
    source_gruppe = source_path[5:]
    feld_schluessel = f"{gruppe}-{table_name}".upper()
    
    guid = root_instance.get_value(source_gruppe, feld_schluessel)[0]
    instance_key = f"{table_name.upper()}_{guid}"
    
    return self.db_instances.get(instance_key)
```

---

## 🔄 Kompletter Ablauf (Beispiel)

### Input (Framedaten)

```python
# ROOT-Tabelle: PERSONDATEN
# Selected GUID: "abc-123-def"

# METADATEN
{
    'PERSONDATEN_PERSDATEN_FAMILIENNAME': {
        'source_path': 'root',
        'label': 'Familienname'
    },
    'PERSONDATEN_PERSDATEN_VORNAME': {
        'source_path': 'root',
        'label': 'Vorname'
    },
    'FINANZWESEN_FINANZWESEN_KONTONUMMER': {
        'source_path': 'root_PERSDATEN',
        'label': 'Kontonummer'
    },
    'FINANZWESEN_FINANZWESEN_BLZAHL': {
        'source_path': 'root_PERSDATEN',
        'label': 'BLZ'
    }
}

# ROOT-Daten
# PERSONDATEN[abc-123-def].PERSDATEN.FINANZWESEN-FINANZWESEN = "xyz-789-ghi"
```

### PHASE 1: Controls aufbauen

```python
controls_meta = [
    {
        'field_key': 'PERSONDATEN_PERSDATEN_FAMILIENNAME',
        'source_path': 'root',
        'order': 1000
    },
    {
        'field_key': 'PERSONDATEN_PERSDATEN_VORNAME',
        'source_path': 'root',
        'order': 1001
    },
    {
        'field_key': 'FINANZWESEN_FINANZWESEN_KONTONUMMER',
        'source_path': 'root_PERSDATEN',
        'order': 2000
    },
    {
        'field_key': 'FINANZWESEN_FINANZWESEN_BLZAHL',
        'source_path': 'root_PERSDATEN',
        'order': 2001
    }
]
```

### PHASE 2: Instanzen erstellen

```python
db_instances = {
    # ROOT-Instanz (bereits vorhanden)
    "PERSONDATEN_abc-123-def": <PdvmCentralDatenbank('persondaten', 'abc-123-def')>,
    
    # Neue Instanz (GUID aus ROOT geholt)
    "FINANZWESEN_xyz-789-ghi": <PdvmCentralDatenbank('finanzwesen', 'xyz-789-ghi')>
}
```

**Ablauf für FINANZWESEN**:
1. source_path: `root_PERSDATEN` → `source_gruppe='PERSDATEN'`
2. Feldschlüssel: `FINANZWESEN-FINANZWESEN`
3. GUID holen: `ROOT.get_value('PERSDATEN', 'FINANZWESEN-FINANZWESEN')` → `"xyz-789-ghi"`
4. Instanz erstellen: `PdvmCentralDatenbank('finanzwesen', 'xyz-789-ghi')`

### PHASE 3: Rendering

```
┌─────────────────────────────────────┐
│ Edit-Bereich                        │
├─────────────────────────────────────┤
│ 📋 Selected GUID: abc-123-def       │
├─────────────────────────────────────┤
│ Familienname: Mustermann            │ ← Order 1000
│ Vorname: Max                        │ ← Order 1001
│ Kontonummer: 123456789              │ ← Order 2000
│ BLZ: 12345678                       │ ← Order 2001
└─────────────────────────────────────┘
```

---

## 📊 Vorteile dieser Architektur

### 1. **Ultra-Linear**
- Keine Verschachtelungen
- Klare Trennung der Phasen
- Jede Phase hat genau eine Aufgabe

### 2. **Effizient**
- Instanzen nur einmal erstellen (Lazy Loading)
- Keine redundanten DB-Zugriffe
- Sortierung nur einmal

### 3. **Erweiterbar**
- Order kann später vom User geändert werden (Expert Mode)
- Neue Source-Path Typen leicht hinzufügbar
- Keine Änderungen an bestehender Logik nötig

### 4. **Testbar**
- Jede Phase kann einzeln getestet werden
- Klare Input/Output-Kontrakte
- Keine versteckten Abhängigkeiten

### 5. **Verständlich**
- Workflow ist linear und nachvollziehbar
- Logging zeigt genau, was passiert
- Code ist selbstdokumentierend

---

## 🔮 Zukünftige Erweiterungen

### Expert Mode: Manuelle Sortierung

```python
# User kann Order ändern
controls_meta[2]['order'] = 1500  # Kontonummer ZWISCHEN Familienname und Vorname

# Neu sortieren
controls_meta.sort(key=lambda x: x['order'])

# Rendering erfolgt in neuer Reihenfolge!
```

### Komplexere Source-Paths

```python
# Aktuell: 'root', 'root_GRUPPE'
# Zukünftig möglich:
'root_GRUPPE1_GRUPPE2'  # Verschachtelte Verknüpfungen
'external_GUID'         # Externe GUID direkt angeben
'calculated'            # Berechnete Verknüpfungen
```

### Conditional Controls

```python
# Control nur anzeigen, wenn Bedingung erfüllt
{
    'field_key': 'FINANZWESEN_...',
    'source_path': 'root_PERSDATEN',
    'order': 2000,
    'visible_if': 'PERSDATEN.IST_GESCHAEFTSKUNDE == True'  # NEU
}
```

---

## 📝 Code-Beispiel: Komplette Integration

```python
# Initialisierung
module = PdvmInputControlsModule(
    framedaten_db=framedaten_db,
    selected_guid="abc-123-def"
)

# 3-Phasen-Verarbeitung (automatisch im __init__)
# PHASE 1: Controls mit Order aufbauen ✅
# PHASE 2: Instanzen erstellen ✅

# Widget holen
widget = module.get_widget()
# PHASE 3: Rendering ✅

# Widget anzeigen
dialog.setWidget(widget)
```

---

## ⚠️ Wichtige Hinweise

### 1. **Instance-Key Format**
Immer `{TABELLE}_{GUID}`, niemals nur `{TABELLE}`!

```python
# ❌ FALSCH
"PERSONDATEN"

# ✅ RICHTIG
"PERSONDATEN_abc-123-def"
```

### 2. **Feldschlüssel Format**
Immer `{GRUPPE}-{TABELLE}` in GROSSBUCHSTABEN!

```python
# ❌ FALSCH
"finanzwesen_finanzwesen"
"Finanzwesen-Finanzwesen"

# ✅ RICHTIG
"FINANZWESEN-FINANZWESEN"
```

### 3. **Source-Path Format**
- `root` → ROOT-Tabelle
- `root_GRUPPE` → Verknüpfte Tabelle über GRUPPE
- Mehrere `root_XXX` möglich (nicht nur eine!)

### 4. **Order-Bereiche**
- 1000-1999: ROOT-Controls
- 2000+: Andere Controls
- Lücken lassen für spätere Einfügungen!

---

## 🎯 Zusammenfassung

Die **3-Phasen Lineare Verarbeitung** bietet:

1. ✅ **Klarheit**: Jede Phase hat genau eine Aufgabe
2. ✅ **Effizienz**: Lazy Loading, keine Redundanzen
3. ✅ **Erweiterbarkeit**: Expert Mode, neue Source-Paths
4. ✅ **Testbarkeit**: Isolierte Phasen
5. ✅ **Verständlichkeit**: Linear, keine Verschachtelungen

**Workflow**: Vorbereiten → Instanzen → Rendern

**Prinzip**: "Everything in its right place" - Jede Operation zur richtigen Zeit am richtigen Ort.

---

**Version**: 1.0.0  
**Datum**: 19.10.2025  
**Status**: ✅ Vollständig implementiert
