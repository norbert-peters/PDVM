# Frame-Daten für Menu-Editor View
# ===================================
# 
# View-GUID: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
# Table: sys_menudaten
# Zweck: Menü-Auswahl für Menu-Editor
#
# Bitte kopieren Sie diese JSON in die Tabelle frame_data:
# - Gruppe: 0d10a0d0-b1a5-4544-b284-e8a09ca979b5
# - Feld: json_data
#
# Alternativ: SQL-Insert am Ende dieser Datei verwenden

```json
{
  "ROOT": {
    "STICHTAG": 3000001.0,
    "VIEW_TABLE": "sys_menudaten",
    "NO_DATA": true
  },
  "METADATEN": {
    "standard_control": {
      "guid": {
        "gruppe": "SYSTEM",
        "feld": "GUID",
        "name": "GUID",
        "type": "string",
        "default": "",
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 1,
        "expert_order": 0,
        "searchable": true,
        "sortable": true,
        "sortDirection": "asc",
        "sortByOriginal": false,
        "filterType": "contains"
      },
      "menu_name": {
        "gruppe": "SYSTEM",
        "feld": "MENU_NAME",
        "name": "Menü-Name",
        "type": "string",
        "default": "",
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 2,
        "expert_order": 0,
        "searchable": true,
        "sortable": true,
        "sortDirection": "asc",
        "sortByOriginal": false,
        "filterType": "contains"
      },
      "is_startmenu": {
        "gruppe": "SYSTEM",
        "feld": "IS_STARTMENU",
        "name": "Startmenü",
        "type": "boolean",
        "default": false,
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 3,
        "expert_order": 0,
        "searchable": false,
        "sortable": true,
        "sortDirection": "desc",
        "sortByOriginal": false,
        "filterType": "exact"
      },
      "description": {
        "gruppe": "SYSTEM",
        "feld": "DESCRIPTION",
        "name": "Beschreibung",
        "type": "string",
        "default": "",
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 4,
        "expert_order": 0,
        "searchable": true,
        "sortable": false,
        "sortDirection": "asc",
        "sortByOriginal": false,
        "filterType": "contains"
      },
      "vertikal_count": {
        "gruppe": "SYSTEM",
        "feld": "VERTIKAL_COUNT",
        "name": "Vertikal Items",
        "type": "number",
        "default": 0,
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 5,
        "expert_order": 0,
        "searchable": false,
        "sortable": true,
        "sortDirection": "desc",
        "sortByOriginal": false,
        "filterType": "exact"
      },
      "grund_count": {
        "gruppe": "SYSTEM",
        "feld": "GRUND_COUNT",
        "name": "Grund Items",
        "type": "number",
        "default": 0,
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 6,
        "expert_order": 0,
        "searchable": false,
        "sortable": true,
        "sortDirection": "desc",
        "sortByOriginal": false,
        "filterType": "exact"
      },
      "abdatum": {
        "gruppe": "SYSTEM",
        "feld": "ABDATUM",
        "name": "AB-Datum",
        "type": "datetime",
        "default": null,
        "dropdown": null,
        "control_type": "base",
        "expert_mode": true,
        "show": false,
        "display_order": 7,
        "expert_order": 1,
        "searchable": false,
        "sortable": true,
        "sortDirection": "desc",
        "sortByOriginal": false,
        "filterType": "exact"
      },
      "formatiertes_abdatum": {
        "gruppe": "SYSTEM",
        "feld": "FORMATIERTES_ABDATUM",
        "name": "Zuletzt geändert",
        "type": "string",
        "default": "",
        "dropdown": null,
        "control_type": "base",
        "expert_mode": false,
        "show": true,
        "display_order": 8,
        "expert_order": 0,
        "searchable": false,
        "sortable": true,
        "sortDirection": "desc",
        "sortByOriginal": true,
        "filterType": "contains"
      }
    }
  }
}
```

## SQL-Insert Statement (Alternative)

Falls Sie SQL bevorzugen:

```sql
-- Frame-Daten für Menu-Editor View einfügen/aktualisieren
INSERT OR REPLACE INTO frame_data (gruppe, feld, value, abdatum)
VALUES (
    '0d10a0d0-b1a5-4544-b284-e8a09ca979b5',
    'json_data',
    '{
      "ROOT": {
        "STICHTAG": 3000001.0,
        "VIEW_TABLE": "sys_menudaten",
        "NO_DATA": true
      },
      "METADATEN": {
        "standard_control": {
          "guid": {
            "gruppe": "SYSTEM",
            "feld": "GUID",
            "name": "GUID",
            "type": "string",
            "default": "",
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 1,
            "expert_order": 0,
            "searchable": true,
            "sortable": true,
            "sortDirection": "asc",
            "sortByOriginal": false,
            "filterType": "contains"
          },
          "menu_name": {
            "gruppe": "SYSTEM",
            "feld": "MENU_NAME",
            "name": "Menü-Name",
            "type": "string",
            "default": "",
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 2,
            "expert_order": 0,
            "searchable": true,
            "sortable": true,
            "sortDirection": "asc",
            "sortByOriginal": false,
            "filterType": "contains"
          },
          "is_startmenu": {
            "gruppe": "SYSTEM",
            "feld": "IS_STARTMENU",
            "name": "Startmenü",
            "type": "boolean",
            "default": false,
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 3,
            "expert_order": 0,
            "searchable": false,
            "sortable": true,
            "sortDirection": "desc",
            "sortByOriginal": false,
            "filterType": "exact"
          },
          "description": {
            "gruppe": "SYSTEM",
            "feld": "DESCRIPTION",
            "name": "Beschreibung",
            "type": "string",
            "default": "",
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 4,
            "expert_order": 0,
            "searchable": true,
            "sortable": false,
            "sortDirection": "asc",
            "sortByOriginal": false,
            "filterType": "contains"
          },
          "vertikal_count": {
            "gruppe": "SYSTEM",
            "feld": "VERTIKAL_COUNT",
            "name": "Vertikal Items",
            "type": "number",
            "default": 0,
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 5,
            "expert_order": 0,
            "searchable": false,
            "sortable": true,
            "sortDirection": "desc",
            "sortByOriginal": false,
            "filterType": "exact"
          },
          "grund_count": {
            "gruppe": "SYSTEM",
            "feld": "GRUND_COUNT",
            "name": "Grund Items",
            "type": "number",
            "default": 0,
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 6,
            "expert_order": 0,
            "searchable": false,
            "sortable": true,
            "sortDirection": "desc",
            "sortByOriginal": false,
            "filterType": "exact"
          },
          "abdatum": {
            "gruppe": "SYSTEM",
            "feld": "ABDATUM",
            "name": "AB-Datum",
            "type": "datetime",
            "default": null,
            "dropdown": null,
            "control_type": "base",
            "expert_mode": true,
            "show": false,
            "display_order": 7,
            "expert_order": 1,
            "searchable": false,
            "sortable": true,
            "sortDirection": "desc",
            "sortByOriginal": false,
            "filterType": "exact"
          },
          "formatiertes_abdatum": {
            "gruppe": "SYSTEM",
            "feld": "FORMATIERTES_ABDATUM",
            "name": "Zuletzt geändert",
            "type": "string",
            "default": "",
            "dropdown": null,
            "control_type": "base",
            "expert_mode": false,
            "show": true,
            "display_order": 8,
            "expert_order": 0,
            "searchable": false,
            "sortable": true,
            "sortDirection": "desc",
            "sortByOriginal": true,
            "filterType": "contains"
          }
        }
      }
    }',
    2025311.0
);
```

## Erklärung der Spalten

**Sichtbare Spalten** (show: true):
1. **GUID** - Menü-GUID (für Editor-Öffnung)
2. **MENU_NAME** - Name des Menüs (z.B. "Hauptmenü")
3. **IS_STARTMENU** - Checkbox: Ist Startmenü?
4. **DESCRIPTION** - Beschreibung des Menüs
5. **VERTIKAL_COUNT** - Anzahl Vertikal-Items (berechnet)
6. **GRUND_COUNT** - Anzahl Grund-Items (berechnet)
7. **FORMATIERTES_ABDATUM** - Letzte Änderung (formatiert)

**Versteckte Spalten** (expert_mode: true):
- **ABDATUM** - Rohes AB-Datum (nur Expert-Modus)

## View-Tabelle in DB

Die Tabelle `sys_menudaten` sollte bereits existieren (aus MenuContainer).
Falls nicht, hier das CREATE Statement:

```sql
CREATE TABLE IF NOT EXISTS sys_menudaten (
    GUID TEXT PRIMARY KEY,
    MENU_NAME TEXT NOT NULL,
    IS_STARTMENU INTEGER DEFAULT 0,
    DESCRIPTION TEXT,
    VERTIKAL TEXT,  -- JSON Array
    GRUND TEXT,     -- JSON Array
    ZUSATZ TEXT,    -- JSON Array
    COMMANDS TEXT,  -- JSON Array
    ABDATUM REAL,
    FORMATIERTES_ABDATUM TEXT
);

-- View für Editor mit berechneten Counts
CREATE VIEW IF NOT EXISTS sys_menudaten_view AS
SELECT 
    GUID,
    MENU_NAME,
    IS_STARTMENU,
    DESCRIPTION,
    (SELECT COUNT(*) FROM json_each(VERTIKAL)) AS VERTIKAL_COUNT,
    (SELECT COUNT(*) FROM json_each(GRUND)) AS GRUND_COUNT,
    ABDATUM,
    FORMATIERTES_ABDATUM
FROM sys_menudaten;
```

---

**Status**: Frame-Daten fertig - Bitte in DB kopieren!
