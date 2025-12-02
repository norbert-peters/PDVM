# Property Input Control Layout-Fix

**Datum**: 15.10.2025  
**Problem**: Property Input Controls wurden nicht angezeigt trotz korrekter Implementierung  
**Root Cause**: QFormLayout.addRow(widget) nicht kompatibel mit Property Input Control's HBoxLayout

## Problem-Analyse

### Symptome
- Properties sahen aus wie vorher
- Labels aus Template nicht sichtbar
- read_only nicht aktiv
- Keine Fehler in Logs

### Root Cause
```python
# FALSCH: Property Input Control hat intern HBoxLayout (Label + Input)
self.property_layout = QFormLayout(self.property_container)  # Form-Layout
self.property_layout.addRow(property_ic)  # Versucht single widget in 2-Spalten-Layout

# Property Input Control Struktur:
# [Label (150px, right-aligned)] [Input Widget] [Stretch]
```

**QFormLayout.addRow(single_widget)**: Versucht Widget über beide Spalten zu spannen - funktioniert nicht mit HBoxLayout-Widgets.

## Lösung Implementiert

### 1. Property Layout auf QVBoxLayout geändert
```python
# ALT:
self.property_layout = QFormLayout(self.property_container)

# NEU:
self.property_layout = QVBoxLayout(self.property_container)
```

**Grund**: QVBoxLayout fügt Widgets vertikal hinzu - jedes Property Input Control ist eine vollständige Zeile mit eigenem internen Layout.

### 2. addRow() auf addWidget() geändert
```python
# ALT:
self.property_layout.addRow(property_ic)

# NEU:
self.property_layout.addWidget(property_ic)
```

### 3. Legacy-Fallback angepasst
```python
# ALT:
label = QLabel(f"{prop_name}:")
self.property_layout.addRow(label, editor)

# NEU:
row_widget = QWidget()
row_layout = QHBoxLayout(row_widget)
label = QLabel(f"{prop_name}:")
label.setMinimumWidth(150)
label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
row_layout.addWidget(label)
row_layout.addWidget(editor)
row_layout.addStretch()
self.property_layout.addWidget(row_widget)
```

**Grund**: Legacy-Mode muss auch mit QVBoxLayout arbeiten → Wrapper-Widget mit HBoxLayout.

### 4. Fallback bei Fehler angepasst
```python
# ALT:
self.property_layout.addRow(QLabel(f"{prop_name}:"), QLabel(str(prop_value)))

# NEU:
fallback = QWidget()
fallback_layout = QHBoxLayout(fallback)
fallback_layout.addWidget(QLabel(f"{prop_name}:"))
fallback_layout.addWidget(QLabel(str(prop_value)))
self.property_layout.addWidget(fallback)
```

### 5. Debug-Logging hinzugefügt
```python
logger.info(f"🔍 DEBUG: Gruppe='{gruppe_name}', Template Controls geladen: {bool(template_controls)}")
if template_controls:
    logger.info(f"🔍 DEBUG: Anzahl Controls: {len(template_controls)}")
    logger.info(f"🔍 DEBUG: Control Keys: {list(template_controls.keys())[:5]}")
```

## Layout-Struktur Vergleich

### QFormLayout (ALT)
```
┌─────────────────────────────────────┐
│ Label:          │ Input Widget      │
│ Label:          │ Input Widget      │
│ Label:          │ Input Widget      │
└─────────────────────────────────────┘
```
**Problem**: Property Input Control hat **eigenes Label intern** → Konflikt

### QVBoxLayout (NEU)
```
┌───────────────────────────────────────────────┐
│ [Label (150px)] [Input Widget] [Stretch]     │
│ [Label (150px)] [Input Widget] [Stretch]     │
│ [Label (150px)] [Input Widget] [Stretch]     │
└───────────────────────────────────────────────┘
```
**Lösung**: Jede Zeile ist ein vollständiges Property Input Control Widget

## Config-Sektion (unverändert)
Config-Layout bleibt QFormLayout - macht Sinn für GroupBoxen:
```python
self.config_layout = QFormLayout(self.config_container)  # Bleibt Form-Layout
config_group = QGroupBox(config_name.upper())
config_form = QFormLayout()  # Intern auch Form-Layout
self.config_layout.addRow(config_group)  # Funktioniert mit GroupBox
```

## Erwartetes Verhalten (nach Fix)

### Property Input Controls anzeigen
- ✅ Properties sortiert nach display_order (0, 1, 2, ...)
- ✅ Labels aus control_def.label (nicht Property-Namen)
- ✅ read_only Properties mit grauem Hintergrund + disabled
- ✅ Dropdown aus configs.dropdown
- ✅ Type-basierte Widgets (string, int, float, bool, dropdown, multiline)

### Template-basierte Steuerung
- ✅ Template-Controls aus ROOT_CONTROLS laden
- ✅ Fallback auf Legacy-Mode wenn keine Template-Controls
- ✅ Debug-Logging für Diagnose

### Signal-Verbindung
- ✅ value_changed Signal → _on_property_changed Handler
- ✅ Dirty-Flag setzen bei Änderung
- ✅ Backup für Undo-Funktion

## Dateien Geändert
- `pdvm_system_editor.py`:
  - Line 404: QVBoxLayout statt QFormLayout
  - Line 668: addWidget() statt addRow()
  - Lines 612-619: Debug-Logging hinzugefügt
  - Lines 710-725: Legacy-Fallback mit Wrapper-Widgets
  - Lines 675-680: Fehler-Fallback mit Wrapper-Widget

## Testing
```powershell
# Syntax-Validierung
python -m py_compile pdvm_system_editor.py  # ✅ OK

# Runtime-Test
python main.py
# 1. Login
# 2. sys_beschreibungen öffnen
# 3. Datensatz auswählen
# 4. Properties ansehen

# Erwartete Logs:
# 🔍 DEBUG: Gruppe='ROOT_CONTROLS', Template Controls geladen: True
# 🔍 DEBUG: Anzahl Controls: 8
# ✅ 8 Property Input Controls erstellt (sortiert)
```

## Wichtige Erkenntnisse

### QFormLayout vs. QVBoxLayout
- **QFormLayout**: Für 2-Spalten-Layout (Label | Widget)
- **QVBoxLayout**: Für vertikale Widget-Stapelung
- **Property Input Control**: Hat eigenes internes Layout → braucht QVBoxLayout als Parent

### Widget-Hierarchie
```
QScrollArea
  └─ property_container (QWidget)
       └─ property_layout (QVBoxLayout)  ← GEÄNDERT
            ├─ PdvmPropertyInputControl (Widget mit HBoxLayout)
            │    └─ [Label] [Input] [Stretch]
            ├─ PdvmPropertyInputControl
            │    └─ [Label] [Input] [Stretch]
            └─ ...
```

### Legacy-Mode Kompatibilität
Legacy-Mode muss auch QVBoxLayout verwenden → manuelle Wrapper-Widgets mit HBoxLayout erstellen.

## Nächste Schritte
1. ✅ Syntax-Validierung (erfolgreich)
2. ⏸️ Runtime-Test (User testet)
3. ⏸️ Log-Analyse (Template Controls geladen?)
4. ⏸️ Visuelle Validierung (Labels, read_only, Sortierung)

---

**STATUS**: Layout-Fix implementiert und validiert. Bereit für Runtime-Test.
