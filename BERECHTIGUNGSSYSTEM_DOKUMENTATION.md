# Berechtigungssystem für App-Menüs

## Konzept

**Jeder Mandant ist autonom** mit eigenen Menüs. Der Zugriff auf App-Menüs wird über die User-Daten gesteuert:

```json
"ANWENDUNGEN": {
  "PERSONALWESEN": {
    "MENU": null          // ❌ Keine Berechtigung
  },
  "BENUTZERDATEN": {
    "MENU": "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"  // ✅ Zugriff erlaubt
  }
}
```

## Verhalten

### ✅ Mit Menü-GUID
- Handler `open_app_menu` lädt das entsprechende Menü aus der Mandanten-DB
- Menü wird im Grund-Bereich angezeigt
- User kann mit der App arbeiten

### ❌ Ohne Menü-GUID (NULL)
- Handler zeigt Dialog-Meldung:
  ```
  Zugriff auf '[App-Name]' nicht möglich
  
  Sie haben keine Berechtigung für diese Anwendung.
  
  Bitte setzen Sie sich mit Ihrem Administrator in Verbindung.
  ```
- Menü wird NICHT geladen
- Content-Bereich bleibt leer

## Implementation

**Datei:** `handlers/handler_open_app_menu.py`

```python
menu_guid = app_data.get('MENU')

if not menu_guid:
    # QMessageBox mit Berechtigungs-Meldung
    msg.setText("<b>Zugriff auf '{app_name}' nicht möglich</b>")
    msg.setInformativeText(
        "Sie haben keine Berechtigung für diese Anwendung.\n\n"
        "Bitte setzen Sie sich mit Ihrem Administrator in Verbindung."
    )
    return False
```

## Aktueller Status (User: 4886ad26-061b-4662-a762-c8c83f36692d)

| App | Menü-GUID | Status |
|-----|-----------|--------|
| PERSONALWESEN | `null` | ❌ Keine Berechtigung |
| FINANZWESEN | `null` | ❌ Keine Berechtigung |
| BENUTZERDATEN | `e1e77039-d1b5-46ff-b12b-cced0ae0da7c` | ✅ Zugriff erlaubt |
| ADMINISTRATION | `4cfbf1ac-c7db-4a3a-ab37-c5b457b89440` | ✅ Zugriff erlaubt |
| TESTBEREICH | `113c6a2c-af9a-4022-929b-6544799e8954` | ✅ Zugriff erlaubt |

## Verwaltung

### Berechtigung erteilen
1. Menü in Mandanten-DB erstellen (via Menü-Editor)
2. Menü-GUID in User-Daten (`auth.db`) eintragen:
   ```python
   user_data['ANWENDUNGEN']['APP_NAME']['MENU'] = 'menu-guid-here'
   ```

### Berechtigung entziehen
1. Menü-GUID in User-Daten auf `null` setzen:
   ```python
   user_data['ANWENDUNGEN']['APP_NAME']['MENU'] = None
   ```
2. ODER: App komplett aus ANWENDUNGEN entfernen

## Vorteile

- ✅ **Mandanten-autonom**: Jeder Mandant hat eigene Menüs
- ✅ **User-spezifisch**: Feinkörnige Berechtigungen pro User
- ✅ **Sicherheit**: Keine Berechtigung = kein Zugriff
- ✅ **Benutzerfreundlich**: Klare Fehlermeldung statt leerer Bereich
- ✅ **Einfache Verwaltung**: Nur GUID in User-Daten ändern

## Logs

### Erfolgreicher Zugriff
```
INFO - 🔵 Handler: open_app_menu
INFO -    App-Name: Benutzerdaten
INFO -    Menu-GUID: e1e77039-d1b5-46ff-b12b-cced0ae0da7c
INFO - ✅ App-Menü geladen: Benutzerdaten
```

### Keine Berechtigung
```
INFO - 🔵 Handler: open_app_menu
INFO -    App-Name: Personalwesen
ERROR - ❌ Keine Berechtigung für Anwendung 'Personalwesen'
WARNING - ⚠️ Command fehlgeschlagen: Personalwesen
```

---

**Datum:** 01.11.2025  
**Version:** V2.0  
**Status:** ✅ Implementiert und getestet
