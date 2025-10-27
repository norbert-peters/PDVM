# ✅ READ-ONLY LOGIK FÜR INPUT-CONTROLS IMPLEMENTIERT

**Datum**: 22.10.2025  
**Status**: ✅ Vollständig implementiert

---

## 🎯 IMPLEMENTIERTE FEATURES

### 1. ✅ Automatisches Read-Only bei fehlender GUID
- Controls ohne DB-Instanz (`db_instance=None`) sind automatisch schreibgeschützt
- Verhindert Fehler bei verschachtelten Controls ohne gefundene GUID
- Tooltip zeigt: "🔒 SCHREIBGESCHÜTZT (keine Instanz - GUID nicht gefunden)"

### 2. ✅ Explizites `read_only` Attribut aus Metadaten
- Neuer Parameter `read_only: bool` in Metadaten `field_config`
- Überschreibt ALLES (auch wenn Instanz vorhanden!)
- Ermöglicht bewusstes Schreibschützen von Feldern
- Tooltip zeigt: "🔒 SCHREIBGESCHÜTZT (read_only=True in Metadaten)"

### 3. ✅ Prioritäts-Logik
```
Read-Only = read_only=True ODER db_instance=None
```

**Tabelle**:
| `read_only` | `db_instance` | Ergebnis | Grund |
|-------------|---------------|----------|-------|
| `True` | vorhanden | ❌ Read-Only | Explizit in Metadaten |
| `True` | `None` | ❌ Read-Only | Explizit in Metadaten |
| `False` | `None` | ❌ Read-Only | Keine Instanz |
| `False` | vorhanden | ✅ Editierbar | Alles OK |

---

## 📋 CODE-ÄNDERUNGEN

### 1. Neuer Parameter in `__init__()`

```python
def __init__(self, 
             instance_key: str,
             db_instance,
             gruppe: str,
             feld: str,
             label: str,
             order: int = 0,
             tab: str = "default",
             tooltip: str = None,
             read_only: bool = False,  # NEU!
             parent=None):
    
    self.read_only = read_only  # Read-Only Flag speichern
```

### 2. Erweiterte `_create_ui()` Logik

```python
def _create_ui(self):
    """
    Read-Only wenn:
    1. Explizites read_only=True aus Metadaten (HÖCHSTE PRIORITÄT!)
    2. Keine DB-Instanz vorhanden (db_instance ist None)
    3. Instanz ist schreibgeschützt
    """
    
    # Read-Only Logik (PRIORITÄT: read_only Flag > keine Instanz)
    is_readonly = self.read_only or (not self.db_instance)
    
    if is_readonly:
        self.edit_widget.setReadOnly(True)
        self.edit_widget.setStyleSheet("""
            QLineEdit {
                background-color: #ecf0f1;  /* Grau */
                border: 1px solid #bdc3c7;
                color: #7f8c8d;
            }
        """)
        logger.debug(f"    🔒 {self.label_text}: Read-Only (read_only={self.read_only}, db_instance={'None' if not self.db_instance else 'OK'})")
    else:
        self.edit_widget.setReadOnly(False)
        self.edit_widget.setStyleSheet("""
            QLineEdit {
                background-color: white;  /* Weiß */
                border: 1px solid #3498db;
                color: #2c3e50;
            }
        """)
        logger.debug(f"    ✏️ {self.label_text}: Editierbar")
```

### 3. Erweiterte Tooltip-Logik

```python
def _update_ui(self):
    """Tooltip zeigt Grund für Read-Only"""
    
    tooltip_parts = []
    
    # [1] Read-Only Status (ERWEITERT)
    if self.read_only:
        tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (read_only=True in Metadaten)")
    elif not self.db_instance:
        tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (keine Instanz - GUID nicht gefunden)")
    
    # [2] Abdatum
    if self.abdatum_wert:
        tooltip_parts.append(f"💾 Abdatum: {self.abdatum_dt.FormTimeStamp}")
    
    # [3] Metadaten-Tooltip
    if self.meta_tooltip:
        tooltip_parts.append("─" * 40)
        tooltip_parts.append(self.meta_tooltip)
        tooltip_parts.append("─" * 40)
    
    # [4] Instanz-Info
    tooltip_parts.append(f"📂 Instanz: {self.instance_key}")
    
    self.edit_widget.setToolTip("\n".join(tooltip_parts))
```

### 4. Erweiterte Factory-Funktion

```python
def create_control_from_config(instance_key: str,
                                db_instance,
                                config: dict,
                                parent=None) -> PdvmInputControlV2:
    """Factory-Funktion mit read_only Support"""
    
    # Tooltip + read_only aus field_config extrahieren
    field_config = config.get('field_config', {})
    if isinstance(field_config, dict):
        tooltip = field_config.get('tooltip', None)
        read_only = field_config.get('read_only', False)  # NEU!
    else:
        tooltip = None
        read_only = False
    
    return PdvmInputControlV2(
        instance_key=instance_key,
        db_instance=db_instance,
        gruppe=config.get('gruppe', ''),
        feld=config.get('feld', ''),
        label=config.get('label', config.get('feld', 'Unbekannt')),
        order=config.get('order', 0),
        tab=config.get('tab', 'default'),
        tooltip=tooltip,
        read_only=read_only,  # NEU!
        parent=parent
    )
```

---

## 📊 METADATEN-FORMAT (ERWEITERT)

```json
{
  "PERSONDATEN_PERSDATEN_ANREDE": {
    "source_path": "root",
    "label": "Anrede",
    "tooltip": "Anrede bitte auswählen",
    "type": "dropdown",
    "tab": 1,
    "order": 1,
    "read_only": false
  },
  "PERSONDATEN_PERSDATEN_ID": {
    "source_path": "root",
    "label": "ID (automatisch)",
    "tooltip": "Automatisch generierte ID - nicht editierbar",
    "tab": 1,
    "order": 2,
    "read_only": true  // ← EXPLIZIT READ-ONLY!
  },
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {
    "source_path": "root_PERSDATEN",
    "label": "Kontoinhaber",
    "tooltip": "Name des Kontoinhabers",
    "tab": 2,
    "order": 1,
    "read_only": false
    // Wenn GUID nicht gefunden → Automatisch Read-Only!
  }
}
```

---

## 🧪 BEISPIEL-SZENARIEN

### Szenario 1: Explizites Read-Only

**Metadaten**:
```json
{
  "PERSONDATEN_PERSDATEN_ID": {
    "label": "ID",
    "read_only": true
  }
}
```

**Ergebnis**:
- Control ist **immer** schreibgeschützt (auch wenn Instanz vorhanden)
- Tooltip: "🔒 SCHREIBGESCHÜTZT (read_only=True in Metadaten)"
- Grauer Hintergrund

---

### Szenario 2: Verschachtelte Instanz ohne GUID

**Metadaten**:
```json
{
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {
    "source_path": "root_PERSDATEN",
    "label": "Kontoinhaber",
    "read_only": false
  }
}
```

**Wenn GUID nicht gefunden**:
- Manager findet keine FINANZDATEN-GUID in ROOT.PERSDATEN
- Control wird mit `db_instance=None` erstellt
- Ergebnis: **Automatisch Read-Only**
- Tooltip: "🔒 SCHREIBGESCHÜTZT (keine Instanz - GUID nicht gefunden)"
- Grauer Hintergrund

---

### Szenario 3: Normal editierbar

**Metadaten**:
```json
{
  "PERSONDATEN_PERSDATEN_FAMILIENNAME": {
    "source_path": "root",
    "label": "Familienname",
    "read_only": false
  }
}
```

**Ergebnis**:
- Control ist **editierbar**
- Weißer Hintergrund, blauer Rand
- Bei Änderung: Gelber Hintergrund
- Logger: "✏️ Familienname: Editierbar"

---

## ✅ VORTEILE

1. **Sichere Daten**: Fehlende GUIDs führen nicht zu Fehlern beim Speichern
2. **Explizite Kontrolle**: `read_only` Flag ermöglicht bewusstes Schreibschützen
3. **Klare Kommunikation**: Tooltip zeigt GRUND für Read-Only
4. **Flexibilität**: Metadaten können Read-Only pro Feld steuern
5. **Konsistente Logik**: Priorität: Explizit > Keine Instanz > Editierbar

---

## 🔍 LOGGING

### Read-Only wegen `read_only=True`:
```
DEBUG: 🔒 ID (automatisch): Read-Only (read_only=True, db_instance=OK)
```

### Read-Only wegen fehlender GUID:
```
DEBUG: 🔒 Kontoinhaber: Read-Only (read_only=False, db_instance=None)
```

### Editierbar:
```
DEBUG: ✏️ Familienname: Editierbar
```

---

**STATUS**: ✅ **READ-ONLY LOGIK VOLLSTÄNDIG IMPLEMENTIERT!**
