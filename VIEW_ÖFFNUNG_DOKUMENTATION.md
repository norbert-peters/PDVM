# 📋 View-Öffnung direkt aus Datenbank - Dokumentation

## 🎯 Übersicht

**Problem gelöst**: View-Manager benötigt `call_daten` mit der kompletten View-Konfiguration (controls, view_table, etc.) aus der Datenbank.

**Lösung**: `open_view_from_db.py` - Holt alle Daten direkt aus DB und startet View-Manager in neuem Fenster.

---

## 📂 Datenbank-Struktur (viewdaten-Tabelle)

### View-GUID: `0d10a0d0-b1a5-4544-b284-e8a09ca979b5` (Persondaten)

```json
{
  "ROOT": {
    "STICHTAG": 3000001.0,
    "VIEW_TABLE": "persondaten"
  },
  "METADATEN": {
    "PERSONDATEN": {
      "controls": {
        "uid": {
          "gruppe": "SYSTEM",
          "feld": "UID",
          "name": "Identifikation",
          "type": "string",
          "show": false,
          ...
        },
        "familienname": {
          "gruppe": "PERSDATEN",
          "feld": "FAMILIENNAME",
          "name": "Familienname",
          "type": "string",
          "show": true,
          ...
        },
        ...
      }
    }
  }
}
```

### View-GUID: `54073c2c-0efa-4979-8900-2bd1c53d5014` (Finanzdaten)

```json
{
  "ROOT": {
    "STICHTAG": 3000001.0,
    "VIEW_TABLE": "finanzdaten"
  },
  "METADATEN": {
    "FINANZDATEN": {
      "controls": {
        "kontonummer": {
          "gruppe": "FINANZDATEN",
          "feld": "KONTONUMMER",
          ...
        },
        ...
      }
    }
  }
}
```

---

## 🔧 Funktionsweise

### 1. `create_call_daten_from_db(view_guid)` - Daten aus DB holen

```python
def create_call_daten_from_db(view_guid: str) -> dict:
    """
    Erstellt call_daten Dictionary direkt aus Datenbank
    
    Ablauf:
    1. View-Datenbank öffnen (viewdaten-Tabelle)
    2. ROOT.VIEW_TABLE holen (z.B. "persondaten")
    3. METADATEN.{VIEW_TABLE}.controls holen
    4. call_daten Dictionary zusammenbauen
    """
    gcs = get_gcs()
    stichtag = gcs.stichtag
    
    # View-DB öffnen
    view_db = PdvmCentralDatenbank(table_name='viewdaten')
    view_db.set_guid(view_guid)
    
    # VIEW_TABLE holen
    view_table, _ = view_db.get_value('ROOT', 'VIEW_TABLE', stichtag)
    # → "persondaten" oder "finanzdaten"
    
    # METADATEN holen
    table_upper = view_table.upper()  # PERSONDATEN
    metadaten, _ = view_db.get_value('METADATEN', table_upper, stichtag)
    
    # Controls extrahieren
    controls = metadaten.get('controls', {})
    
    # call_daten zusammenbauen
    return {
        'view_guid': view_guid,
        'user_guid': gcs.user_guid,
        'stichtag': stichtag,
        'view_table': view_table,
        'controls': controls,
        'first_call': True
    }
```

### 2. `open_view_in_window(view_guid, window_title)` - View öffnen

```python
def open_view_in_window(view_guid: str, window_title: str = "PDVM View"):
    """
    Öffnet View in neuem Fenster
    
    Ablauf:
    1. call_daten aus DB erstellen
    2. Neues QMainWindow erstellen
    3. Container-Widget mit Layout
    4. PdvmViewDatenManager mit call_daten erstellen
    5. Kontrolliertes Widget erstellen
    6. Fenster anzeigen
    """
    # call_daten holen
    call_daten = create_call_daten_from_db(view_guid)
    
    # Fenster erstellen
    window = QMainWindow()
    window.setWindowTitle(window_title)
    
    # View-Manager erstellen
    view_manager = PdvmViewDatenManager(
        call_daten=call_daten,
        widget=None,
        parent_app=None
    )
    
    # Widget erstellen und einfügen
    view_widget = view_manager.create_controlled_widget(parent=container)
    layout.addWidget(view_widget)
    
    # Fenster anzeigen
    window.show()
    return window
```

---

## 🚀 Verwendung

### Standalone ausführen (nach Login)

```powershell
# 1. Hauptanwendung starten (für Login und GCS-Initialisierung)
python main.py

# 2. In anderem Terminal: View öffnen
python open_view_from_db.py
```

### In bestehendem Code verwenden

```python
from open_view_from_db import open_view_in_window

# Persondaten öffnen
PERSONDATEN_VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
window = open_view_in_window(PERSONDATEN_VIEW_GUID, "Meine Persondaten")

# Finanzdaten öffnen
FINANZDATEN_VIEW_GUID = "54073c2c-0efa-4979-8900-2bd1c53d5014"
window = open_view_in_window(FINANZDATEN_VIEW_GUID, "Meine Finanzen")
```

### In Menü integrieren

```python
def on_menu_persondaten_clicked(self):
    """Menü-Handler für Persondaten"""
    from open_view_from_db import open_view_in_window
    
    view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    self.persondaten_window = open_view_in_window(
        view_guid, 
        "Persondaten - Übersicht"
    )
```

---

## 📋 call_daten Struktur

```python
call_daten = {
    # Identifikation
    'view_guid': '0d10a0d0-b1a5-4544-b284-e8a09ca979b5',
    'user_guid': 'aktuelle-user-guid-aus-gcs',
    
    # Zeitpunkt
    'stichtag': 3000001.0,  # Aus GCS
    
    # View-Konfiguration
    'view_table': 'persondaten',  # Aus ROOT.VIEW_TABLE
    
    # Controls (Spaltendefinitionen)
    'controls': {
        'uid': {
            'gruppe': 'SYSTEM',
            'feld': 'UID',
            'name': 'Identifikation',
            'type': 'string',
            'show': False,
            'display_order': 0,
            'searchable': True,
            'sortable': True,
            ...
        },
        'familienname': {
            'gruppe': 'PERSDATEN',
            'feld': 'FAMILIENNAME',
            'name': 'Familienname',
            'type': 'string',
            'show': True,
            'display_order': 1,
            ...
        },
        ...
    },
    
    # Initialisierung
    'first_call': True
}
```

---

## ✅ Vorteile

1. **Sauber**: Keine manuellen Konfigurationen - alles aus DB
2. **Konsistent**: Verwendet exakt die gleiche Struktur wie funktionierende Views
3. **Einfach**: Nur View-GUID übergeben → Fenster öffnet sich
4. **Flexibel**: Kann für Persondaten, Finanzdaten, beliebige Views verwendet werden
5. **Wartbar**: Änderungen in DB → sofort in allen Views aktiv

---

## ⚠️ Voraussetzungen

1. **GCS initialisiert**: Login muss erfolgreich sein (`get_gcs()` nicht None)
2. **View-GUID vorhanden**: View muss in viewdaten-Tabelle existieren
3. **Struktur korrekt**: 
   - `ROOT.VIEW_TABLE` muss gesetzt sein
   - `METADATEN.{TABLE}.controls` muss existieren

---

## 🔍 Debugging

### Log-Ausgaben prüfen

```python
logging.basicConfig(level=logging.INFO)
```

**Erfolgreiche Ausführung**:
```
INFO - ✅ VIEW_TABLE geladen: persondaten
INFO - ✅ 6 Controls geladen: ['uid', 'familienname', 'vorname', 'geburtsdatum', 'anrede', 'email']
INFO - ✅ call_daten erstellt: view_table=persondaten, 6 controls
INFO - ✅ View-Fenster geöffnet: Persondaten - Test
```

**Fehler-Szenarien**:
```
ERROR - ❌ GCS nicht verfügbar!
ERROR - ❌ VIEW_TABLE nicht gefunden für view_guid=...
ERROR - ❌ METADATEN nicht gefunden für PERSONDATEN
```

---

## 📦 Dateien

- **`open_view_from_db.py`**: Hauptdatei mit allen Funktionen
- **`VIEW_ÖFFNUNG_DOKUMENTATION.md`**: Diese Dokumentation

---

## 🎯 Nächste Schritte

1. **Testen** mit Persondaten-View
2. **Finanzdaten-GUID** eintragen und testen
3. **In Menü integrieren** für Produktiv-Nutzung
4. **Weitere Views** nach Bedarf hinzufügen

---

**WICHTIG**: GCS MUSS initialisiert sein (Login erfolgreich)! Sonst `get_gcs()` gibt None zurück.
