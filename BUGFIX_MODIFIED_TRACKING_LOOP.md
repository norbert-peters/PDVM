# 🔧 BUGFIX: Modified Tracking Loop behoben

**DATUM**: 06.12.2025  
**PROBLEM**: Modified Tracking Loop vor Login  
**STATUS**: ✅ BEHOBEN

---

## 🐛 Problem

Modified Tracking lief in einen Loop beim Anwendungsstart:

```
save_all_values() 
  → update_modified_tracking()
    → PdvmCentralDatenbank('sys_systemsteuerung')
      → save_all_values()
        → update_modified_tracking()
          → [LOOP] ♾️
```

**URSACHE**: 
- Modified Tracking wurde für ALLE Tabellen aufgerufen
- `sys_systemsteuerung` speichert selbst Modified Tracking Daten
- → Rekursiver Loop beim Speichern

---

## ✅ Lösung

**REGEL**: Modified Tracking NUR für Geschäftsdaten-Tabellen, NICHT für System-Tabellen

### System-Tabellen Whitelist
```python
system_tables = [
    'sys_systemsteuerung',  # Tracking-Daten selbst
    'sys_viewdaten',        # View-Metadaten
    'sys_framedaten',       # Frame-Metadaten
    'sys_dialogdaten',      # Dialog-Metadaten
    'sys_menudaten',        # Menü-Metadaten
    'benutzerstamm'         # User-Datenbank
]
```

### Implementierung

#### 1. `pdvm_central_datenbank.py` - save_all_values()
```python
# ✅ Modified Tracking: Aktualisiere MODIFIED_AT für diese Tabelle
# WICHTIG: Nur für Geschäftsdaten, nicht für System-Tabellen (verhindert Loop)
if self.table_name not in ['sys_systemsteuerung', 'sys_viewdaten', 'sys_framedaten', 'sys_dialogdaten', 'sys_menudaten']:
    try:
        from pdvm_modified_tracking import update_modified_tracking
        update_modified_tracking(self.table_name)
    except Exception as e:
        logger.debug(f"Modified Tracking Update übersprungen: {e}")
```

#### 2. `pdvm_datenbank.py` - speichern()
```python
# ✅ Modified Tracking: Aktualisiere MODIFIED_AT für diese Tabelle
# WICHTIG: Nur für Geschäftsdaten, nicht für System-Tabellen (verhindert Loop)
if self.table_name not in ['sys_systemsteuerung', 'sys_viewdaten', 'sys_framedaten', 'sys_dialogdaten', 'sys_menudaten', 'benutzerstamm']:
    try:
        from pdvm_modified_tracking import update_modified_tracking
        update_modified_tracking(self.table_name)
    except Exception as e:
        logger.debug(f"Modified Tracking Update übersprungen: {e}")
```

#### 3. `pdvm_view_controller.py` - _load_viewdata()
```python
# ✅ Modified Tracking: Prüfe ob Tabelle neu geladen werden muss
# NUR für Geschäftsdaten-Tabellen, nicht für System-Tabellen
system_tables = ['sys_systemsteuerung', 'sys_viewdaten', 'sys_framedaten', 'sys_dialogdaten', 'sys_menudaten', 'benutzerstamm']
if self.table_name not in system_tables and self.gcs:
    try:
        from pdvm_modified_tracking import check_modified_and_should_refresh
        should_refresh = check_modified_and_should_refresh(self.table_name)
        if should_refresh:
            logger.info(f"🔄 Tabelle '{self.table_name}' wurde geändert - lade View neu")
        else:
            logger.info(f"✅ Tabelle '{self.table_name}' unverändert - nutze Cache")
    except Exception as e:
        logger.debug(f"Modified Tracking Check übersprungen: {e}")
```

---

## 🧪 Ergebnis

**VORHER**:
```
❌ Anwendung startet nicht (Loop)
❌ Fehler vor Login
```

**NACHHER**:
```
✅ Anwendung startet normal
✅ Login funktioniert
✅ Modified Tracking aktiv für Geschäftsdaten
✅ System-Tabellen werden übersprungen
```

---

## 📝 Weitere Erkenntnisse

### Warum nur Geschäftsdaten?
- **System-Tabellen** enthalten Konfiguration und Metadaten
- Ändern sich selten und nicht durch normale Geschäftsvorgänge
- Werden beim App-Start geladen (kein Caching nötig)

### Warum Geschäftsdaten?
- **Geschäftsdaten** (z.B. persondaten, finanzdaten) ändern sich häufig
- Werden von mehreren Usern gleichzeitig bearbeitet
- Profitieren stark von Modified Tracking Caching

### System-Tabellen Liste
Alle Tabellen die mit `sys_` beginnen oder Basis-Funktionalität enthalten:
- `sys_systemsteuerung` - GCS Daten
- `sys_viewdaten` - View-Konfiguration
- `sys_framedaten` - Frame-Konfiguration
- `sys_dialogdaten` - Dialog-Konfiguration
- `sys_menudaten` - Menü-Struktur
- `benutzerstamm` - User-Verwaltung

---

**STATUS**: ✅ Loop behoben - Anwendung startet normal
