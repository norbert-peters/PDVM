# ✅ EINFACHER FILTER-DIALOG - V2 PERSISTIERUNG IMPLEMENTIERT

## Was wurde geändert

### 1. search_parameter_dialog.py

#### A) Neue Methode: `_save_search_string_to_gcs()`
**Zeile ~458** (nach `save_persistent_filters()`)

```python
def _save_search_string_to_gcs(self, new_filters, extended_summary):
    """
    🆕 V2: Speichert search_string in GCS für autonome Pipeline
    
    Konvertiert Filter-Parameter zu search_string und speichert beides:
    - Parameter unter 'einfach' (für Dialog-Anzeige)
    - search_string unter 'search_string' (für Pipeline)
    """
    # Erstelle search_string aus Filtern
    search_parts = []
    
    if extended_summary and len(extended_summary) > 0:
        # KOMPLEX-Filter
        for field_key, summary in extended_summary.items():
            search_parts.append(f"EXTENDED:{field_key}:{summary}")
    else:
        # EINFACH-Filter
        for field_key, value in new_filters.items():
            if not field_key.startswith('EXTENDED:'):
                search_parts.append(f"{field_key}:{value}")
    
    search_string = "||".join(search_parts) if search_parts else None
    
    # Speichere search_string
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()  # 💾 CRITICAL!
```

#### B) Integration in `accept_changes()`
**Zeile ~982** (in der Accept-Methode)

```python
# SCHRITT 5: Persistent speichern (ALT - behalten für Kompatibilität)
self.save_persistent_filters(new_filters)

# SCHRITT 5.5: NEU - Speichere auch search_string in GCS
self._save_search_string_to_gcs(new_filters, extended_summary)

# SCHRITT 6: DIREKTE FILTER-AUSFÜHRUNG...
```

### 2. central_filter_reset.py

#### Erweiterung: `_reset_persistent_filters()`
**Zeile ~130** (in Reset-Methode)

```python
# Lösche Filter-Spalten...

# 🆕 V2: Lösche auch search_string (wenn nicht Gesamtfilter bewahrt)
if not preserve_gesamtfilter:
    gcs._app_db.set_value(self.view_guid, 'search_string', None)
    logger.info(f"🗑️ search_string gelöscht")
    reset_count += 1

# Speichere Änderungen
gcs._app_db.save_all_values()
```

## Workflow

### Filter setzen (Einfach)
```
1. User gibt "Lau" in Familienname ein
2. Klickt "Übernehmen"

3. Dialog:
   ├─ save_persistent_filters() → Speichert Parameter unter 'einfach'
   ├─ _save_search_string_to_gcs() → Erstellt "familienname_show:Lau"
   │   ├─ gcs._app_db.set_value(view_guid, 'search_string', "familienname_show:Lau")
   │   └─ gcs._app_db.save_all_values()
   └─ apply_filters_LINEAR() → Filter ausführen

4. Pipeline (bei rebuild_pipeline):
   ├─ _load_search_string_from_gcs() → Lädt "familienname_show:Lau"
   └─ apply_filter("familienname_show:Lau") → Direkt anwenden!
```

### Filter setzen (Komplex)
```
1. User setzt mehrere Bedingungen
2. Klickt "Übernehmen"

3. Dialog:
   ├─ save_persistent_filters() → Speichert Parameter unter 'komplex'
   ├─ _save_search_string_to_gcs() → Erstellt "EXTENDED:familienname_show:..."
   │   ├─ gcs._app_db.set_value(view_guid, 'search_string', "EXTENDED:...")
   │   └─ gcs._app_db.save_all_values()
   └─ apply_filters_LINEAR() → Filter ausführen

4. Pipeline: Lädt und wendet search_string an
```

### Filter zurücksetzen
```
1. User klickt "Alle Filter zurücksetzen"

2. central_filter_reset.reset_all_filters_for_view():
   ├─ Lösche Filter-Spalten
   ├─ Lösche search_string (wenn nicht preserve_gesamtfilter)
   │   ├─ gcs._app_db.set_value(view_guid, 'search_string', None)
   │   └─ gcs._app_db.save_all_values()
   └─ Pipeline neu (ohne Filter)
```

### App-Neustart
```
1. App startet → Login → View öffnen

2. Pipeline (rebuild_pipeline):
   ├─ _load_search_string_from_gcs()
   │   └─ gcs._app_db.get_value(view_guid, 'search_string')
   │       → "familienname_show:Lau"
   ├─ apply_filter("familienname_show:Lau")
   └─ ✅ Filter ist AUTOMATISCH aktiv!

3. Dialog öffnen:
   ├─ load_persistent_filters()
   │   └─ gcs._app_db.get_value(view_guid, 'einfach')
   │       → {'field_name': 'familienname_show', 'search_value': 'Lau', ...}
   └─ ✅ Parameter werden ANGEZEIGT!
```

## Datenbank-Struktur

```sql
-- Nach Einfach-Filter "Lau" auf "Familienname":

-- Parameter für Dialog-Anzeige (ALT - behalten)
gruppe: "0d10a0d0-..."
feld: "familienname_show"
wert: '{"simple_search": "Lau", "conditions": []}'

-- search_string für Pipeline (NEU!)
gruppe: "0d10a0d0-..."
feld: "search_string"
wert: "familienname_show:Lau"
```

## Status

✅ **Einfacher Filter-Dialog**: DONE
- ✅ Speichert Parameter unter Spalten-Keys
- ✅ Speichert search_string unter 'search_string'
- ✅ Reset löscht search_string
- ✅ Pipeline lädt search_string autonom

⏳ **Komplexer Filter-Dialog**: TODO
- extended_filter_engine.py anpassen

⏳ **View Controller - Gesamt-Suche**: TODO
- pdvm_view_controller.py anpassen
- Speichert unter 'gesamt' + 'search_string'

⏳ **Linear Filter Manager**: TODO
- Bereinigen (Persistierung raus)

## Nächste Schritte

1. ✅ Einfacher Filter-Dialog fertig
2. ⏳ Komplexer Filter-Dialog (extended_filter_engine.py)
3. ⏳ Gesamt-Suche (pdvm_view_controller.py)
4. ⏳ Linear Filter Manager bereinigen
5. ⏳ Testen mit allen 3 Filterarten

**Ready für:** Komplexer Filter-Dialog! 🚀
