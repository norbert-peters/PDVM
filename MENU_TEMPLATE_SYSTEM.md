# MENU_TEMPLATE_SYSTEM.md

# Menü-Template-System für PDVM

## Überblick
Das Template-System ermöglicht es, häufig verwendete Menüteile zentral zu definieren und in verschiedenen Menüs wiederzuverwenden. Dies reduziert Redundanz und vereinfacht die Wartung.

## Template-Syntax

### Basis-Syntax
```json
{
  "PD_grund": {
    "!guid!": "template-basis-standard",
    "Lokale Einträge": "lokale_funktion()"
  }
}
```

### Erweiterte Syntax mit Merge-Modi

#### 1. Template am Ende anhängen (Standard)
```json
"PD_grund": {
  "Meine Einträge": "meine_funktion()",
  "!guid!": "template-basis-standard"
}
```

#### 2. Template am Anfang einfügen
```json
"PD_grund": {
  "!guid!prepend": "template-basis-standard", 
  "Lokale Einträge": "lokale_funktion()"
}
```

#### 3. Template ersetzt alles
```json
"PD_grund": {
  "!guid!replace": "template-basis-standard"
}
```

## Standard-Templates

### template-basis-standard
Standard Basis-Menü für normale Anwendungen:
- Zurück zu Apps
- Menü ein/aus  
- Logout

### template-basis-admin
Erweiterte Basis-Menü für Admin-Bereiche:
- Zurück zu Apps
- Menü ein/aus
- Menü Editor
- Logout

### template-startmenu-basis
Basis-Menü für Startmenü (ohne "Zurück zu Apps"):
- Menü ein/aus
- Logout

## Beispiele

### Personalwesen-Menü mit Standard-Basis
```json
{
  "PD_commands": { /* Kommandos */ },
  "PD_grund": {
    "!guid!": "template-basis-standard"
  },
  "PD_zusatz": { /* Zusatz-Menüs */ },
  "PD_menu": { /* Hauptmenü-Einträge */ }
}
```

### Admin-Menü mit erweiterte Basis
```json
{
  "PD_commands": { /* Kommandos */ },
  "PD_grund": {
    "!guid!": "template-basis-admin",
    "Spezielle Admin-Funktion": "admin_funktion()"
  },
  "PD_zusatz": { /* Zusatz-Menüs */ },
  "PD_menu": { /* Hauptmenü-Einträge */ }
}
```

### Startmenü mit Basis-Template
```json
{
  "PD_commands": { /* Kommandos */ },
  "PD_grund": {
    "!guid!prepend": "template-startmenu-basis",
    "System-Info": "system_info()"
  },
  "PD_zusatz": { /* Zusatz-Menüs */ },
  "PD_menu": { 
    "Personalwesen": "pdvm_start('Personalwesen')",
    "Finanzwesen": "pdvm_start('Finanzwesen')",
    "Testbereich": "pdvm_start('Testbereich')"
  }
}
```

## Eigene Templates erstellen

### 1. Template in menudaten-Tabelle speichern
```python
from pdvm_central_datenbank import PdvmCentralDatenbank

# Template-Daten
template_data = {
    "Mein Standard-Eintrag": "standard_funktion()",
    "---": "---",
    "Hilfe": "hilfe_anzeigen()"
}

# In Datenbank speichern
db = PdvmCentralDatenbank(
    db_name="PdvmManager.db", 
    table_name="menudaten",
    guid="mein-custom-template-guid"
)

db.speichern("mein-custom-template-guid", {
    "mein-custom-template-guid": {
        "uid": "mein-custom-template-guid",
        "bezeichnung": "Mein Custom Template",
        "daten": template_data,
        "template": True
    }
})
```

### 2. Template in Menü verwenden
```json
"PD_grund": {
  "!guid!": "mein-custom-template-guid",
  "Weitere Einträge": "weitere_funktion()"
}
```

## Vorteile

✅ **Zentrale Wartung**: Änderungen an Templates wirken sich auf alle Menüs aus
✅ **Konsistenz**: Gleiche Basis-Funktionen in allen Menüs
✅ **Weniger Redundanz**: Keine doppelten Menü-Einträge
✅ **Flexibilität**: Templates können mit lokalen Einträgen kombiniert werden
✅ **Skalierbarkeit**: Neue Templates können einfach hinzugefügt werden

## Technische Details

- Templates werden beim Laden eines Menüs aufgelöst
- Template-Cache für bessere Performance  
- Fehlerbehandlung: Bei Template-Fehlern wird mit Original-Struktur weitergearbeitet
- Unterstützung für alle Menü-Gruppen (PD_grund, PD_menu, PD_zusatz, PD_commands)
