# Projektion-System Korrektur

**Datum:** 7. Oktober 2025  
**Probleme identifiziert und gelöst:**

## 1. Problem: Spalten-Reihenfolge nach "Spalten übernehmen" nicht angepasst

**Ursache:**
- Column Management Dialog hat zwar `display_order` gespeichert, aber Projektions-Tabellen wurden nicht neu aufgebaut
- Projektionen verwendeten alte cached Werte

**Lösung:**
```python
# column_management_dialog.py - accept_changes()
gcs.rebuild_projection_tables(self.view_guid)  # NEU: Projektionen neu aufbauen
logger.info(f"🔄 Projektions-Tabellen neu aufgebaut für View {self.view_guid}")
```

## 2. Problem: Neue Spalten (show=true) nicht sichtbar

**Ursache:**
- Projektions-Tabellen wurden nicht automatisch neu aufgebaut nach Control-Änderungen
- View verwendete alte Projektions-Listen

**Lösung:**
- `rebuild_projection_tables()` wird jetzt IMMER nach Control-Speicherung aufgerufen
- Projektionen werden aus aktuellen Controls neu berechnet

## 3. Problem: Projektions-Architektur inkonsistent

### 3.1 Ursprüngliches Design (FALSCH)
```
❌ Controls → Projektion → Matrix → View
   - Projektionen wurden VOR Matrix-Verarbeitung angewendet
   - Filter/Sort arbeiteten auf bereits reduzierten Daten
```

### 3.2 Korrigiertes Design (KORREKT)
```
✅ Controls → BASIS_MATRIX → FILTER_MATRIX → SORT_MATRIX → Projektion → VIEW
   - Alle 62 Spalten in BASIS/FILTER/SORT Matrizen
   - Projektionen werden nur auf finale VIEW angewendet
   - Filter/Sort arbeiten mit allen Spalten
```

## 4. Projektions-Tabellen System

### 4.1 Struktur
8 Projektions-Tabellen pro View (4 Bereiche × 2 Modi):

```python
{
    # VIEW-Bereich: Tabellen-Darstellung
    'table_standard': [spalten_mit_show_true],      # nur sichtbare
    'table_expert': [alle_spalten_außer_dummy],     # alle
    
    # SEARCH-Bereich: Such-Dialoge
    'search_standard': [spalten_mit_show_true],     # nur sichtbare
    'search_expert': [alle_spalten_außer_dummy],    # alle
    
    # CHANGE-Bereich: Spalten-Verwaltung
    'change_standard': [spalten_mit_expert_mode_false],  # nur non-expert
    'change_expert': [alle_spalten_außer_dummy],         # alle
    
    # SORT-Bereich: Sortier-Dialog
    'sort_standard': [spalten_mit_show_true],       # nur sichtbare
    'sort_expert': [alle_spalten_außer_dummy]       # alle
}
```

### 4.2 Sortierung
**WICHTIG:** Alle Projektionen verwenden `display_order` (nicht `expert_order`!)

```python
# VORHER (FALSCH):
all_controls_expert = sorted(all_controls, key=lambda x: (x['expert_order'], x['display_order']))

# NACHHER (KORREKT):
all_controls_sorted = sorted(all_controls, key=lambda x: x['display_order'])
```

**Begründung:** 
- `expert_order` wurde nie konsistent verwendet
- `display_order` ist die einzige Quelle der Wahrheit
- Vereinfacht Logik und vermeidet Inkonsistenzen

## 5. ExpertMode Zugriffskontrolle

### 5.1 Problem: mode Attribut nicht gefunden
**Ursache:** mode kam nicht aus Benutzerstamm

**Lösung:**
```python
# pdvm_central_systemsteuerung.py
@property
def mode(self):
    """Mode aus Benutzerdaten (Parameter Gruppe) - 'user' oder 'admin'"""
    try:
        parameter_data = self._user_data.get('Parameter', {})
        mode_value = parameter_data.get('mode', 'user')
        
        # Validierung: nur 'user' oder 'admin' erlaubt
        if mode_value not in ['user', 'admin']:
            logger.warning(f"⚠️ Ungültiger mode Wert '{mode_value}', verwende 'user' als Fallback")
            return 'user'
        
        return mode_value
    except (KeyError, AttributeError, TypeError):
        logger.warning("⚠️ mode nicht gefunden in Benutzerdaten, verwende 'user' als Fallback")
        return 'user'
```

### 5.2 ExpertMode Menü nur für Admins

```python
# pdvm_view_dialog.py - _show_settings_menu()
if gcs:
    user_mode = gcs.mode  # 'user' oder 'admin'
    if user_mode == 'admin':
        expert_action = QAction("🔧 Expert Mode", self)
        expert_action.setCheckable(True)
        expert_action.setChecked(gcs.expert_mode)
        expert_action.triggered.connect(self._toggle_expert_mode)
        menu.addAction(expert_action)
        logger.debug(f"✅ Expert Mode Menüpunkt für Admin angezeigt (mode={user_mode})")
    else:
        logger.debug(f"ℹ️ Expert Mode Menüpunkt ausgeblendet für mode={user_mode}")
```

### 5.3 ExpertMode Toggle Validierung

```python
# pdvm_view_dialog.py - _toggle_expert_mode()
def _toggle_expert_mode(self):
    """Toggle Expert Mode über Menü - NUR für mode='admin'"""
    gcs = get_gcs()
    
    # Prüfe ob Benutzer Admin ist
    user_mode = gcs.mode
    if user_mode != 'admin':
        logger.warning(f"⚠️ Expert Mode Toggle verweigert - Benutzer ist kein Admin (mode={user_mode})")
        QMessageBox.warning(
            self,
            "Zugriff verweigert",
            "Expert Mode kann nur von Administratoren aktiviert werden."
        )
        return
    
    # Toggle Expert Mode (nur für Admin)
    old_mode = gcs.expert_mode
    gcs.expert_mode = not old_mode
    logger.info(f"🎓 Expert Mode: {old_mode} → {gcs.expert_mode} (Admin-Benutzer)")
```

## 6. Änderungen im Detail

### 6.1 pdvm_central_systemsteuerung.py
1. `mode` Property mit 'user' Fallback und Validierung
2. Projektions-Sortierung vereinfacht (nur `display_order`)
3. Log-Nachrichten verbessert

### 6.2 pdvm_view_dialog.py
1. ExpertMode Menüpunkt nur für `mode='admin'`
2. `_toggle_expert_mode()` mit Admin-Validierung
3. Kommentare zur Projektion aus SORT_MATRIX

### 6.3 column_management_dialog.py
1. `accept_changes()` ruft `rebuild_projection_tables()` auf
2. Verbesserte Log-Nachrichten

## 7. Testing Checkliste

### 7.1 Spalten-Reihenfolge
- [ ] Spalten verwalten öffnen
- [ ] Reihenfolge mit Drag & Drop ändern
- [ ] "Spalten übernehmen" klicken
- [ ] Prüfen: Tabelle zeigt neue Reihenfolge

### 7.2 Show/Hide Spalten
- [ ] Spalte mit show=false aktivieren (Checkbox)
- [ ] "Spalten übernehmen" klicken
- [ ] Prüfen: Spalte ist jetzt sichtbar in Tabelle

### 7.3 ExpertMode Zugriff
- [ ] Als User (mode='user') anmelden
- [ ] Prüfen: ExpertMode Menüpunkt NICHT sichtbar
- [ ] Als Admin (mode='admin') anmelden
- [ ] Prüfen: ExpertMode Menüpunkt SICHTBAR
- [ ] ExpertMode aktivieren
- [ ] Prüfen: Alle Spalten (außer dummy) angezeigt

### 7.4 Projektionen
- [ ] Filter anwenden → filtert über alle 62 Spalten
- [ ] Sortierung anwenden → sortiert über alle 62 Spalten
- [ ] View zeigt nur projizierte Spalten (je nach ExpertMode)

## 8. Architektur-Fluss (Final)

```
┌─────────────────────────────────────────────────────────────┐
│ PDVM Matrix Pipeline - LINEARES PROJEKTIONS-SYSTEM          │
└─────────────────────────────────────────────────────────────┘

1. CONTROLS (GCS - Persistent)
   ├─ 62 Spalten-Definitionen
   ├─ Properties: show, expert_mode, display_order
   └─ Dummy-Spalten markiert

2. PROJEKTIONS-TABELLEN (GCS - Cached)
   ├─ 8 Listen pro View (4 Bereiche × 2 Modi)
   ├─ Neu aufgebaut bei Control-Änderungen
   └─ Alle sortiert nach display_order

3. BASIS_MATRIX (PdvmMatrixManager)
   ├─ Alle 62 Spalten
   ├─ Alle Datensätze
   └─ Original-Daten unverändert

4. FILTER_MATRIX (PdvmMatrixManager)
   ├─ Alle 62 Spalten (wichtig!)
   ├─ Gefilterte Datensätze
   └─ Filter arbeitet auf allen Spalten

5. SORT_MATRIX (PdvmMatrixManager)
   ├─ Alle 62 Spalten (wichtig!)
   ├─ Gefiltert + Sortiert
   └─ Sort arbeitet auf allen Spalten

6. VIEW (PdvmViewDialog)
   ├─ Projektion aus SORT_MATRIX
   ├─ Nur projizierte Spalten sichtbar
   └─ table_standard (7-20) oder table_expert (alle)

┌─────────────────────────────────────────────────────────────┐
│ KRITISCH: Filter/Sort arbeiten IMMER mit allen 62 Spalten!  │
│ Projektionen werden NUR auf finale VIEW angewendet!          │
└─────────────────────────────────────────────────────────────┘
```

## 9. Mode Attribute

### 9.1 Benutzer-Typen
```python
mode = 'user'   # Standard-Benutzer (kein ExpertMode Zugriff)
mode = 'admin'  # Administrator (voller Zugriff inkl. ExpertMode)
```

### 9.2 Fallback-Verhalten
```python
# Wenn mode nicht gefunden oder ungültig:
return 'user'  # Sicherster Default (eingeschränkte Rechte)
```

### 9.3 Speicherort
```
Benutzerstamm → Parameter → mode: 'user' | 'admin'
```

## 10. Zusammenfassung

**Gelöst:**
✅ Spalten-Reihenfolge wird nach Änderung korrekt angewendet  
✅ Neue Spalten (show=true) werden sofort sichtbar  
✅ Projektions-Architektur linear und konsistent  
✅ ExpertMode nur für Admins zugänglich  
✅ mode Attribut mit sicherem Fallback  

**Architektur:**
✅ Filter/Sort arbeiten mit allen 62 Spalten  
✅ Projektion nur auf finale VIEW  
✅ 8 Projektions-Tabellen pro View  
✅ Nur display_order für Sortierung  
✅ Projektionen werden aus SORT_MATRIX erstellt  

**Sicherheit:**
✅ ExpertMode Menü nur für mode='admin'  
✅ ExpertMode Toggle validiert Admin-Rechte  
✅ Default mode='user' bei fehlenden Daten  
