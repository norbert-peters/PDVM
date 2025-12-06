# 🔧 KORREKTUR: ROOT_CONTROLS statt ROOT_PROPERTIES

**DATUM**: 06.12.2025  
**ÄNDERUNG**: Template-Struktur korrigiert  
**STATUS**: ✅ IMPLEMENTIERT

---

## ❌ VORHER (FALSCH)

```python
template_data = {
    "ROOT": {
        "name": "Templates",
        "TABLE": table_name,
        "view_templates": False,
        "view_system": False
    },
    "ROOT_PROPERTIES": {  # ❌ FALSCH
        "name": {...},
        "guid": {...}
    },
    "CONTROL_PROPERTIES": {...}
}
```

**PROBLEM**: 
- Gruppe hieß `ROOT_PROPERTIES` statt `ROOT_CONTROLS`
- Felder waren `name`, `guid` statt `TABLE`, `SELF_GUID`, `NAME`, `VIEW_TEMPLATES`, `VIEW_SYSTEM`
- `view_templates` und `view_system` waren in `ROOT` statt in `ROOT_CONTROLS`

---

## ✅ NACHHER (KORREKT)

```python
template_data = {
    "ROOT": {
        "name": "Templates",
        "TABLE": table_name
    },
    "ROOT_CONTROLS": {  # ✅ RICHTIG
        "TABLE": {
            "type": "string",
            "label": "Tabelle",
            "display_order": 1,
            "read_only": True,
            "tab": 1
        },
        "SELF_GUID": {
            "type": "string",
            "label": "GUID",
            "display_order": 2,
            "read_only": True,
            "tab": 1
        },
        "NAME": {
            "type": "string",
            "label": "Name",
            "display_order": 3,
            "read_only": False,
            "tab": 1
        },
        "VIEW_TEMPLATES": {
            "type": "bool",
            "label": "Templates in View anzeigen",
            "display_order": 4,
            "read_only": False,
            "tab": 1
        },
        "VIEW_SYSTEM": {
            "type": "bool",
            "label": "System-Satz in View anzeigen",
            "display_order": 5,
            "read_only": False,
            "tab": 1
        }
    },
    "CONTROL_PROPERTIES": {...}
}
```

---

## 📋 ROOT_CONTROLS Felder

| Feld | Typ | Label | Read-Only | Zweck |
|------|-----|-------|-----------|-------|
| `TABLE` | string | Tabelle | ✅ Ja | Referenz zur Datenbank-Tabelle |
| `SELF_GUID` | string | GUID | ✅ Ja | Eindeutige Identifikation |
| `NAME` | string | Name | ❌ Nein | Benutzer-lesbarer Name |
| `VIEW_TEMPLATES` | bool | Templates in View anzeigen | ❌ Nein | Steuert Sichtbarkeit von Template-Satz |
| `VIEW_SYSTEM` | bool | System-Satz in View anzeigen | ❌ Nein | Steuert Sichtbarkeit von System-Satz |

---

## 🔧 Geänderte Dateien

### 1. `handlers/handler_create_datatable.py`
**Zeile ~195-220**: Template-Struktur korrigiert
- `ROOT_PROPERTIES` → `ROOT_CONTROLS`
- Felder angepasst: `TABLE`, `SELF_GUID`, `NAME`, `VIEW_TEMPLATES`, `VIEW_SYSTEM`

**Zeile ~308**: Frame-Konfiguration korrigiert
- `CONTROL_GROUPS = ['ROOT_PROPERTIES', ...]` → `['ROOT_CONTROLS', ...]`

### 2. `HANDLER_CREATE_DATATABLE_COMPLETE.md`
Dokumentation aktualisiert mit korrekter Struktur

### 3. `test_template_structure.py` (NEU)
Test-Skript zum Prüfen der Template-Struktur nach Tabellen-Erstellung

---

## 🧪 Testen

```powershell
# 1. Neue Tabelle erstellen (via Menü oder Handler direkt)
# Anwendung starten → Menü → "Neue Tabelle anlegen"
python pdvm_main.py

# 2. Template-Struktur prüfen
python test_template_structure.py
# → Tabellenname eingeben (z.B. "testtabelle")
```

**Erwartete Ausgabe**:
```
✅ ROOT_CONTROLS:
   TABLE: {...}
   SELF_GUID: {...}
   NAME: {...}
   VIEW_TEMPLATES: {...}
   VIEW_SYSTEM: {...}

✅ Frame CONTROL_GROUPS: ['ROOT_CONTROLS', 'CONTROL_PROPERTIES']
```

---

## 💡 Warum diese Struktur?

### ROOT_CONTROLS vs ROOT_PROPERTIES
- **ROOT_CONTROLS**: Definiert die Controls/Felder die in der ROOT-Ebene eines Datensatzes verfügbar sind
- **ROOT_PROPERTIES**: War falscher Name, verwechselt mit CONTROL_PROPERTIES

### Die 5 Standard-Felder
1. **TABLE**: Jeder Satz weiß zu welcher Tabelle er gehört
2. **SELF_GUID**: Jeder Satz kennt seine eigene GUID
3. **NAME**: Benutzer-lesbarer Name für Datensatz
4. **VIEW_TEMPLATES**: Steuert ob Template-Satz (5555...) in Views angezeigt wird
5. **VIEW_SYSTEM**: Steuert ob System-Satz (0000...) in Views angezeigt wird

### Warum beide CONTROL_GROUPS?
```python
CONTROL_GROUPS = ['ROOT_CONTROLS', 'CONTROL_PROPERTIES']
```

- **ROOT_CONTROLS**: Für Felder in ROOT-Ebene (TABLE, NAME, etc.)
- **CONTROL_PROPERTIES**: Für dynamische Felder in Unter-Gruppen

→ Frame-Editor zeigt beide Gruppen für vollständige Template-Pflege

---

## 📝 Auswirkung auf neue Sätze

**JETZT MÖGLICH**:
Nach Tabellen-Erstellung kann man über Template-Editor neue Sätze anlegen mit:
- ✅ `ROOT.TABLE` wird automatisch gesetzt
- ✅ `ROOT.SELF_GUID` wird automatisch generiert
- ✅ `ROOT.NAME` kann vom User eingegeben werden
- ✅ `ROOT.VIEW_TEMPLATES` kann gesteuert werden
- ✅ `ROOT.VIEW_SYSTEM` kann gesteuert werden

**VORHER NICHT MÖGLICH**:
- ❌ Fehlende oder falsche Felder in ROOT_CONTROLS
- ❌ Neue Sätze konnten nicht korrekt angelegt werden

---

**STATUS**: ✅ Korrektur implementiert und dokumentiert
