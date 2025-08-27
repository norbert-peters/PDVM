# Zentrale Systemsteuerung - Architektur-Dokumentation

## Problem
- Multiple Instanzen von PdvmCentralDatenbank für die systemsteuerung führten zu Inkonsistenzen
- MenuStatus (Felder) wurden nicht mehr geschrieben  
- View-Einstellungen funktionierten nicht korrekt

## Lösung: Zentrale Systemsteuerung-Instanz

### 1. Hauptanwendung (PDVM-Systemstart.py)

#### Initialisierung
```python
def _initialize_central_systemsteuerung(self):
    """Initialisiert die zentrale Systemsteuerung-Instanz für die gesamte Anwendung."""
    self.central_systemsteuerung = PdvmCentralDatenbank(
        db_name="PdvmManager.db",
        table_name="systemsteuerung",
        guid=PdvmCentralDatenbank.SYSTEM_USER_ID
    )
    
    # Stichtag und Sprache aus Benutzer-Gruppe laden oder setzen
    # self.stichtag und self.language als Eigenschaften verfügbar
```

#### Menü-Status-Verwaltung
```python
def _save_menu_visibility_status(self):
    """Speichert Menü-Status mit zentraler Instanz"""
    self.central_systemsteuerung.set_value(
        gruppe=self.user_guid,
        feld=f"menu_{current_menu_id}",
        wert=menu_visible,
        ab_zeit=1001.0
    )
    self.central_systemsteuerung.save_values()
```

### 2. Modern View Widget (pdvm_modern_view_widget.py)

#### Konstruktor-Update
```python
def __init__(self, view_guid, user_guid=None, parent=None, central_systemsteuerung=None):
    self.central_systemsteuerung = central_systemsteuerung  # Zentrale Instanz
```

#### View-Einstellungen-Speicherung
```python
def _save_view_settings(self):
    """Verwendet zentrale Systemsteuerung-Instanz"""
    if not self.central_systemsteuerung:
        logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar")
        return
    
    self.central_systemsteuerung.set_value(
        gruppe=self.view_guid,
        feld="expert_mode",
        wert=self.expert_mode,
        ab_zeit=1001.0
    )
    # ... weitere Felder
    self.central_systemsteuerung.save_values()
```

### 3. Widget-Übergabe

```python
# In pdvm_modern_view()
self.modern_view_widget = PdvmModernViewWidget(
    view_guid=view_guid,
    user_guid=self.user_guid,
    parent=self,
    central_systemsteuerung=self.central_systemsteuerung  # Zentrale Instanz übergeben
)
```

## Datenstruktur

### Benutzer-Gruppe (user_guid)
```json
{
  "5f97b7da-42d4-4b03-815a-34775fbb6138": {
    "stichtag": "2025216",
    "language": "DE", 
    "menu_startmenu_id": true,
    "menu_application_id": false
  }
}
```

### View-Gruppe (view_guid)
```json
{
  "0d10a0d0-b1a5-4544-b284-e8a09ca979b5": {
    "expert_mode": true,
    "custom_columns": ["VORNAME", "FAMILIENNAME", "GEBURTSDATUM"],
    "last_updated": "2025-08-04T15:18:35.511070"
  }
}
```

## Vorteile

✅ **Eine einzige Instanz** für die gesamte Anwendung  
✅ **Konsistente Datenhaltung** - keine Synchronisationsprobleme  
✅ **Zentrale Konfiguration** - Stichtag und Sprache am Anfang geladen  
✅ **Gruppen-basierte Isolation** - User- und View-Daten getrennt  
✅ **Persistente Einstellungen** - MenuStatus und View-Einstellungen bleiben erhalten  
✅ **Einfache Übergabe** - Zentrale Instanz wird an Widgets weitergegeben  

## Tests

- ✅ Zentrale Systemsteuerung schreibt und liest korrekt
- ✅ Menü-Status wird persistent gespeichert  
- ✅ View-Einstellungen funktionieren mit zentraler Instanz
- ✅ Gruppen-Isolation verhindert Datenüberschreibung
- ✅ Mehrfache Operationen funktionieren zuverlässig

## Verwendung

1. **Hauptanwendung starten** → Zentrale Systemsteuerung wird initialisiert
2. **Stichtag/Sprache** → Als Eigenschaften in MainApp verfügbar
3. **Widgets erstellen** → Zentrale Instanz wird übergeben  
4. **Speicheroperationen** → Verwenden automatisch die zentrale Instanz
5. **Konsistente Daten** → Alle Widgets arbeiten mit derselben Datenbasis
