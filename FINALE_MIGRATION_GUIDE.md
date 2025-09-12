
# MIGRATIONSLEITFADEN: Bestehende Systemsteuerung → Finale Architektur

## 1. ÄNDERUNGEN in pdvm_linear_start_new.py

```python
# ALT:
initialize_gcs(self.current_user_guid)

# NEU:
user_data = {
    'username': self.username,  # Aus Login
    'country': 'DEU',
    'role': 'admin',
    'language': 'de-de'
}
initialize_finale_gcs(self.current_user_guid, user_data)
```

## 2. ÄNDERUNGEN in PDVM-Systemstart-with-new-gcs.py

```python
# ALT:
gcs = get_gcs()
stichtag_value = gcs.stichtag

# NEU:
gcs = get_finale_gcs()
stichtag_value = gcs.stichtag  # Gleich
stichtag_inst = gcs.st_inst   # Für DateTimePicker

# ALT: Spezielle Stichtag-Behandlung
# NEU: Einfacher Setter
gcs.field_value('stichtag', new_value)  # Automatisches Speichern
```

## 3. NEUE FEATURES nutzen

```python
# Parametrisierte Properties
country = gcs.field_value('country')
gcs.field_value('country', 'AUT')

# Flexible Erweiterung
new_setting = gcs.field_value('new_setting')  # Funktioniert automatisch
gcs.field_value('new_setting', 'new_value')

# Gruppen-Handling
other_data = gcs.group_value('some-guid')
```

## 4. VORTEILE der finalen Architektur

✅ Robuste Initialisierung - keine Überraschungen
✅ Parametrisierte Properties - einfache Erweiterung
✅ Automatisches Speichern - kein Datenverlust
✅ Spezielle Stichtag-Behandlung - bewährtes Pattern
✅ Flexible Gruppen-Verwaltung - skalierbar
✅ Saubere Trennung - klare Verantwortlichkeiten

## 5. SCHRITTWEISE MIGRATION

1. Neue finale Systemsteuerung integrieren
2. Login-Prozess anpassen (user_data sammeln)
3. Stichtag-Bar auf neue API umstellen
4. Bestehende Properties migrieren
5. Tests und Validierung
