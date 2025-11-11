# METADATEN für Framedaten (Menu-Editor)
# =========================================
#
# Frame-GUID: 794cbfc3-ccb6-4681-b432-efa9f44682c8
# Zweck: Template für neuen Menüpunkt im Menu-Editor
#
# Diese Metadaten in sys_framedaten.json_data unter "METADATEN" einfügen

```json
{
  "METADATEN": {
    "menu_item_template": {
      "guid": {
        "name": "GUID",
        "type": "string",
        "control_type": "text",
        "readonly": true,
        "auto_generate": true,
        "visible": false,
        "display_order": 0,
        "required": false,
        "default": ""
      },
      "label": {
        "name": "Beschriftung",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 1,
        "required": true,
        "default": "Neuer Menüpunkt",
        "placeholder": "z.B. Personen",
        "max_length": 50,
        "validation": "not_empty"
      },
      "type": {
        "name": "Typ",
        "type": "string",
        "control_type": "dropdown",
        "readonly": false,
        "visible": true,
        "display_order": 2,
        "required": true,
        "default": "BUTTON",
        "dropdown": {
          "BUTTON": "Button (Aktion)",
          "SUBMENU": "Untermenü",
          "SEPARATOR": "Trennlinie",
          "SPACER": "Abstand"
        }
      },
      "icon": {
        "name": "Icon",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 3,
        "required": false,
        "default": "",
        "placeholder": "Icon-Name oder Pfad"
      },
      "command_guid": {
        "name": "Command",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 4,
        "required": false,
        "default": "",
        "condition": "type == 'BUTTON'",
        "placeholder": "Command-GUID"
      },
      "zusatz_guid": {
        "name": "Zusatzmenü",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 5,
        "required": false,
        "default": "",
        "condition": "type == 'SUBMENU'",
        "placeholder": "Zusatzmenü-GUID"
      },
      "sort_order": {
        "name": "Reihenfolge",
        "type": "number",
        "control_type": "number",
        "readonly": false,
        "visible": true,
        "display_order": 6,
        "required": true,
        "default": 0,
        "auto_calculate": true,
        "min": 0,
        "max": 9999
      },
      "visible": {
        "name": "Sichtbar",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": false,
        "visible": true,
        "display_order": 7,
        "required": false,
        "default": true
      },
      "enabled": {
        "name": "Aktiviert",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": false,
        "visible": true,
        "display_order": 8,
        "required": false,
        "default": true
      },
      "tooltip": {
        "name": "Tooltip",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 9,
        "required": false,
        "default": "",
        "placeholder": "Hilfetext beim Hover...",
        "max_length": 200
      }
    }
  }
}
```

## Komplett für sys_framedaten (794cbfc3-ccb6-4681-b432-efa9f44682c8)

```json
{
  "ROOT": {
    "ROOT_TABLE": "sys_menudaten",
    "VIEW_GUID": "8746d0cc-6acb-4f14-a7cb-3d48f97b0751",
    "DIALOG_GUID": "079ebf6e-fc9c-498f-8a94-1726a5c23cb1",
    "HEADER_TEXT": "Menüs pflegen",
    "EDIT_TYPE": "menu_editor",
    "EDIT_TABS": 1,
    "EDIT_TAB_LABEL_01": "Menü",
    "DISPLAY_ST": "only_date",
    "DISPLAY_TIME_SHORT": true
  },
  "METADATEN": {
    "menu_item_template": {
      "guid": {
        "name": "GUID",
        "type": "string",
        "control_type": "text",
        "readonly": true,
        "auto_generate": true,
        "visible": false,
        "display_order": 0,
        "required": false,
        "default": ""
      },
      "label": {
        "name": "Beschriftung",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 1,
        "required": true,
        "default": "Neuer Menüpunkt",
        "placeholder": "z.B. Personen",
        "max_length": 50,
        "validation": "not_empty"
      },
      "type": {
        "name": "Typ",
        "type": "string",
        "control_type": "dropdown",
        "readonly": false,
        "visible": true,
        "display_order": 2,
        "required": true,
        "default": "BUTTON",
        "dropdown": {
          "BUTTON": "Button (Aktion)",
          "SUBMENU": "Untermenü",
          "SEPARATOR": "Trennlinie",
          "SPACER": "Abstand"
        }
      },
      "icon": {
        "name": "Icon",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 3,
        "required": false,
        "default": "",
        "placeholder": "Icon-Name oder Pfad"
      },
      "command_guid": {
        "name": "Command",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 4,
        "required": false,
        "default": "",
        "condition": "type == 'BUTTON'",
        "placeholder": "Command-GUID"
      },
      "zusatz_guid": {
        "name": "Zusatzmenü",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 5,
        "required": false,
        "default": "",
        "condition": "type == 'SUBMENU'",
        "placeholder": "Zusatzmenü-GUID"
      },
      "sort_order": {
        "name": "Reihenfolge",
        "type": "number",
        "control_type": "number",
        "readonly": false,
        "visible": true,
        "display_order": 6,
        "required": true,
        "default": 0,
        "auto_calculate": true,
        "min": 0,
        "max": 9999
      },
      "visible": {
        "name": "Sichtbar",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": false,
        "visible": true,
        "display_order": 7,
        "required": false,
        "default": true
      },
      "enabled": {
        "name": "Aktiviert",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": false,
        "visible": true,
        "display_order": 8,
        "required": false,
        "default": true
      },
      "tooltip": {
        "name": "Tooltip",
        "type": "string",
        "control_type": "text",
        "readonly": false,
        "visible": true,
        "display_order": 9,
        "required": false,
        "default": "",
        "placeholder": "Hilfetext beim Hover...",
        "max_length": 200
      }
    }
  }
}
```

## Erklärung

### Template-Felder (menu_item_template)

**Basis-Felder**:
- `guid` - Auto-generiert, versteckt
- `label` - Beschriftung (PFLICHT)
- `type` - Dropdown: BUTTON/SUBMENU/SEPARATOR/SPACER
- `icon` - Icon-Name (optional)

**Conditional Fields**:
- `command_guid` - Nur wenn type == 'BUTTON'
- `zusatz_guid` - Nur wenn type == 'SUBMENU'

**Ordnung & Status**:
- `sort_order` - Reihenfolge (auto-berechnet beim Drag&Drop)
- `visible` - Sichtbar-Checkbox
- `enabled` - Aktiviert-Checkbox
- `tooltip` - Hilfetext

### Verwendung im Menu-Editor

1. **Neues Item**: Template-Defaults verwenden
2. **Bearbeitung**: Template für Validierung
3. **Speichern**: Template-Struktur zu MenuItem konvertieren

---

**Status**: Metadaten fertig - Bitte in sys_framedaten einfügen!
