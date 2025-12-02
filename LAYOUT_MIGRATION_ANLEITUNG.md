# 🎨 Layout-System Migrations-Anleitung

## Problem: "Funktioniert nicht überall"

Das Layout-System ist **nicht automatisch** aktiv - du musst jedes Widget **explizit migrieren**.

---

## ✅ Wie Stylesheets in JSON gespeichert werden

### JSON-Format (mit `\n` = Zeilenumbrüche):
```json
{
  "STYLES": {
    "QMenu": "\n    QMenu {\n        background-color: {COLORS.BACKGROUND};\n    }\n"
  }
}
```

### Nach Python-Parsing (echte Zeilenumbrüche):
```python
"""
    QMenu {
        background-color: {COLORS.BACKGROUND};
    }
"""
```

### Nach Template-Ersetzung durch Layout-Manager:
```css
    QMenu {
        background-color: #ffffff;
    }
```

**➡️ Die Leerzeichen und `\n` sind KORREKT!**

---

## 📋 Verfügbare Stylesheets

In `sys_layout.STYLES` sind definiert:

1. **QMenu** - Kontextmenüs ✅ BEREITS MIGRIERT (pdvm_system_editor.py)
2. **QComboBox** - Dropdowns
3. **QPushButton** - Buttons
4. **QLineEdit** - Einzeilige Eingabefelder
5. **QTextEdit** - Mehrzeilige Eingabefelder
6. **QSpinBox** - Zahlen-Eingabe
7. **QDateEdit** - Datums-Picker
8. **QTimeEdit** - Zeit-Picker
9. **QCalendarWidget** - Kalender-Dropdown ✅ BEREITS MIGRIERT (pdvm_date_time_picker.py)

---

## 🔧 Migration: Schritt-für-Schritt

### ❌ VORHER (Hardcoded):
```python
# pdvm_input_controls_manager.py - Zeile 456
button = QPushButton("Speichern")
button.setStyleSheet("""
    QPushButton {
        background-color: #f0f0f0;
        color: #000000;
    }
""")
```

### ✅ NACHHER (Layout-System):
```python
# pdvm_input_controls_manager.py - Zeile 456
from pdvm_central_systemsteuerung import get_gcs

button = QPushButton("Speichern")
gcs = get_gcs()
if gcs and hasattr(gcs, 'layout'):
    button_style = gcs.layout.get_stylesheet('QPushButton')
    if button_style:
        button.setStyleSheet(button_style)
```

---

## 🎯 Migrations-Prioritäten

### HOCH (Sichtbarkeitsprobleme):
- ✅ **QMenu** - Context-Menüs (FERTIG)
- ✅ **QCalendarWidget** - Datum-Picker Dropdown (FERTIG)
- ⚠️ **QComboBox** - Dropdowns in Formularen (noch hardcoded?)

### MITTEL (Konsistenz):
- ⚠️ **QLineEdit** - Text-Eingabefelder
- ⚠️ **QPushButton** - Alle Buttons
- ⚠️ **QDateEdit** - Datums-Felder

### NIEDRIG (Nice-to-have):
- **QTextEdit** - Mehrzeilige Felder
- **QSpinBox** - Zahlen-Felder
- **QTimeEdit** - Zeit-Felder

---

## 🔍 Wo muss migriert werden?

### Suche nach hardcoded Styles:

```powershell
# In MyApplication Verzeichnis:
Select-String -Path *.py -Pattern "setStyleSheet" | Select-Object -First 20
```

**Typische Kandidaten:**
1. `pdvm_input_controls_manager.py` - Input-Felder
2. `pdvm_view_widget_with_tooltips.py` - Tabellen
3. `pdvm_dialog_generator.py` - Dialoge
4. `pdvm_menu_handler.py` - Menüs (bereits migriert?)

---

## 🧪 Test: Funktioniert Layout-System?

### Test 1: Context-Menü (SOLLTE funktionieren)
```python
# Im System-Editor → Rechtsklick auf Feld
# ✅ Sollte weiße Hintergrundfarbe haben
# ✅ Hover sollte blau (#0078d4) sein
```

### Test 2: DateTimePicker Kalender (SOLLTE funktionieren)
```python
# Im Input Controls → Datum-Feld öffnen
# ✅ Kalender-Dropdown sollte sichtbar sein
# ✅ Monat-Dropdown sollte sichtbar sein
```

### Test 3: Buttons (FUNKTIONIERT NOCH NICHT)
```python
# Beliebiger Button in Anwendung
# ❌ Hat wahrscheinlich noch keinen Layout-Style
# ❌ Nutzt OS-Default oder hardcoded Style
```

---

## 🛠️ Beispiel-Migration: QPushButton

### 1. Finde alle Buttons:
```python
# grep für "QPushButton" in allen .py Dateien
```

### 2. Ersetze hardcoded Styles:

**VORHER:**
```python
save_button = QPushButton("Speichern", self)
save_button.setStyleSheet("QPushButton { background-color: #e0e0e0; }")
```

**NACHHER:**
```python
save_button = QPushButton("Speichern", self)
if hasattr(self, 'gcs') and hasattr(self.gcs, 'layout'):
    style = self.gcs.layout.get_stylesheet('QPushButton')
    if style:
        save_button.setStyleSheet(style)
```

### 3. Test im laufenden System:
- Starte Anwendung
- Button sollte jetzt Layout-Style haben
- Farben aus `sys_layout.COLORS` verwenden

---

## 🎨 Farben anpassen

### Im System-Editor (sys_layout Tabelle öffnen):

1. Öffne GUID: `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` (Default-Layout)
2. Gehe zu Gruppe **COLORS**
3. Ändere z.B.:
   ```
   BUTTON_BG: #f0f0f0  → #e3f2fd  (hellblau)
   BUTTON_HOVER_BG: #d0d0d0 → #bbdefb  (dunkleres blau)
   ```
4. **Speichern**
5. **Anwendung neu starten** (kein Hot-Reload implementiert)

---

## ⚡ Hot-Reload aktivieren (Optional)

Aktuell ist **kein Hot-Reload** implementiert. Du musst die Anwendung neu starten nach Layout-Änderungen.

**Zukünftige Implementierung:**
```python
# In pdvm_system_editor.py - nach save_all_values():
if table_name == 'sys_layout':
    gcs = get_gcs()
    if gcs and hasattr(gcs, 'layout'):
        gcs.layout.reload_layout()  # Cache leeren
        # TODO: Alle Widgets neu stylen
```

---

## 📊 Status-Check: Was ist bereits migriert?

### ✅ FERTIG:
- `pdvm_system_editor.py` → Zeilen 1170-1173 (Context-Menü)
- `pdvm_date_time_picker.py` → Zeilen 80-91 (DateEdit + Calendar)

### ❌ TODO:
- **QComboBox** überall finden und migrieren
- **QPushButton** in allen Dialogen/Views
- **QLineEdit** in Input-Controls
- **QTextEdit** in Edit-Bereichen

---

## 🚀 Nächste Schritte

### Schnell-Migration (empfohlen):

1. **Finde alle QComboBox** (höchste Priorität):
   ```powershell
   Select-String -Path *.py -Pattern "QComboBox" | Select-Object Path, LineNumber
   ```

2. **Migriere pro Datei:**
   - Import GCS: `from pdvm_central_systemsteuerung import get_gcs`
   - Nach Widget-Erstellung: `widget.setStyleSheet(gcs.layout.get_stylesheet('QComboBox'))`

3. **Test nach jeder Migration:**
   - Anwendung starten
   - Betroffene Widgets prüfen
   - Farben/Sichtbarkeit validieren

### Langzeit-Migration (vollständig):

1. Erstelle `migrate_to_layout_system.py` Script
2. Parse alle `.py` Dateien
3. Finde alle `setStyleSheet()` Aufrufe
4. Ersetze automatisch durch Layout-System
5. Manuelle Nachprüfung

---

## ❓ FAQ

### Q: Warum sehe ich `\n` in der Datenbank?
**A:** Das sind Zeilenumbrüche im JSON-String. Python ersetzt sie automatisch durch echte Zeilenumbrüche.

### Q: Kann ich die Leerzeichen entfernen?
**A:** Ja, aber NICHT empfohlen! Die Formatierung macht Stylesheets im System-Editor lesbar.

### Q: Werden Widgets automatisch gestylt?
**A:** NEIN! Du musst `widget.setStyleSheet(gcs.layout.get_stylesheet(...))` explizit aufrufen.

### Q: Kann ich mehrere Layouts haben?
**A:** JA! Kopiere Template-GUID (`55555555...`) zu neuer GUID, ändere Farben, setze in `sys_systemsteuerung.ACTIVE_LAYOUT`.

### Q: Funktioniert Dark Theme?
**A:** Noch nicht implementiert, aber vorbereitet! Ändere einfach alle `COLORS` in Template-Kopie.

---

## 📝 Zusammenfassung

**Problem:** "Funktioniert nicht überall"  
**Ursache:** Widgets müssen manuell migriert werden  
**Lösung:** `widget.setStyleSheet(gcs.layout.get_stylesheet('WidgetType'))`

**JSON-Format:** `\n` und Leerzeichen sind **korrekt und gewollt**!

**Nächster Schritt:** Finde alle `QComboBox` und migriere sie zum Layout-System.
