"""
SYSTEM-EDITOR V3 - ULTRA VEREINFACHT
=====================================

✅ IMPLEMENTIERT: 18.12.2025

## 🎯 Änderungen

### Problem VORHER:
- pdvm_system_editor.py: 2291 Zeilen, sehr kompliziert
- 3 verschiedene Property-Editor Methoden:
  * _refresh_properties_editor_root() (für ROOT Strings)
  * _refresh_properties_editor() (für Felder mit Templates)
  * _refresh_properties_editor_legacy() (Fallback ohne Template)
- Template-abhängig (55555...)
- Viele Sonderfälle und Verzweigungen

### Lösung JETZT:
- pdvm_system_editor_simple.py: 356 Zeilen, ultra einfach
- EINE lineare Darstellung für ALLES
- Tree-View (links) + JSON-Editor (rechts)
- Keine Template-Abhängigkeit
- Administrator kann ALLES sehen und bearbeiten

## 📦 Neue Dateien

### pdvm_system_editor_simple.py
```python
class PdvmSystemEditorSimple(QWidget):
    \"\"\"
    Ultra-vereinfachter System-Editor für Administrator.
    
    PRINZIP: LINEAR & EINFACH
    - ROOT → Zeigt TABLE, NAME, DESCRIPTION
    - Gruppen → Zeigt alle Gruppen (außer ROOT)
    - Felder → Zeigt alle Felder mit name, label, type, display_order
    \"\"\"
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        # Nur 2 Parameter!
        pass
```

**Features:**
- 🌳 Tree-View: Hierarchische Struktur (ROOT → Gruppen → Felder → Properties)
- 📝 JSON-Editor: Direktes Bearbeiten des kompletten JSON
- 💾 Speichern: Schreibt JSON direkt in Datenbank
- 🔄 Neu laden: Holt Daten frisch aus DB
- ✅ Validieren: Prüft JSON-Syntax
- 🎨 Farbcodierung: ROOT (blau), Gruppen (grün)

**Verwendung:**

Als Widget (embedded):
```python
from pdvm_system_editor_simple import PdvmSystemEditorSimple

editor = PdvmSystemEditorSimple("sys_mandanten", "66666666-6666-6666-6666-666666666666")
layout.addWidget(editor)
```

Als Dialog (standalone):
```python
from pdvm_system_editor_simple import PdvmSystemEditorDialog

dialog = PdvmSystemEditorDialog("persondaten", "66666...")
dialog.exec_()
```

## 🔧 Integration ins System

### pdvm_genereller_dialog.py
**Zeile 110:**
```python
'system_editor': 'pdvm_system_editor_simple.PdvmSystemEditorSimple',
```

**Zeile 797-808:**
```python
if self.edit_type == 'system_editor':
    self.current_edit_module = ModuleClass(
        table_name=self.root_table,  # ✅ TABLE aus framedaten
        record_uid=selected_guid,    # ✅ Ausgewählter Datensatz
        parent=self
    )
```

## 🧪 Test-Frame erstellt

**Frame-GUID:** `fd5f2198-854d-456e-957a-15a877bf2973`

**Test-Ablauf:**
```python
# 1. System starten
python pdvm_main.py

# 2. Dialog öffnen (in Python Console)
start_dialog('fd5f2198-854d-456e-957a-15a877bf2973')

# 3. Datensatz auswählen
# - sys_mandanten Table wird angezeigt
# - 66666... Dictionary auswählen
# - Tab 2 öffnet sich mit System-Editor

# 4. Dictionary bearbeiten
# - Tree-View zeigt Struktur
# - JSON-Editor zeigt kompletten Inhalt
# - Änderungen direkt speichern
```

## 🎯 Anwendungsfälle

### 1. Dictionary 66666... bearbeiten
```
sys_mandanten (66666...)
├── ROOT
│   ├── TABLE: sys_mandanten
│   ├── NAME: sys_mandanten-Dictionary
│   └── DESCRIPTION: Control-Definitionen...
├── STAMMDATEN
│   └── <guid-1>
│       ├── name: DB_NAME
│       ├── label: Datenbank-Name
│       ├── type: string
│       └── display_order: 1
└── METADATEN
    └── <guid-2>
        ├── name: MANDANT_ID
        └── ...
```

### 2. Template 55555... anpassen
Gleicher Editor, andere UID:
```python
editor = PdvmSystemEditorSimple("sys_framedaten", "55555555-5555-5555-5555-555555555555")
```

### 3. Normale Datensätze prüfen
```python
editor = PdvmSystemEditorSimple("persondaten", "<irgendeine-person-guid>")
```

## 📊 Vergleich Alt vs Neu

| Feature | ALT (pdvm_system_editor.py) | NEU (pdvm_system_editor_simple.py) |
|---------|----------------------------|-----------------------------------|
| Zeilen Code | 2291 | 356 |
| Methoden | 3x _refresh_properties_editor | 1x _refresh_tree |
| Template-Abhängig | Ja (55555...) | Nein |
| Sonderfälle | ROOT vs Normal vs Legacy | Keine |
| Darstellung | Property Input Controls | Tree + JSON |
| Komplexität | Hoch | Niedrig |
| Administrator-freundlich | Eingeschränkt | Vollständig |

## ✅ Vorteile der neuen Lösung

1. **Ultra einfach:** Nur 2 Parameter, keine komplexe Konfiguration
2. **Universal:** Funktioniert mit ALLEN Tabellen und ALLEN UIDs
3. **Transparent:** Administrator sieht ALLES (keine versteckten Logiken)
4. **Direkt:** JSON-Editor ermöglicht direktes Bearbeiten
5. **Wartbar:** Weniger Code, weniger Bugs, einfacher zu erweitern
6. **Linear:** Keine Verzweigungen, keine Sonderfälle

## 🚀 Nächste Schritte

1. ✅ Integration getestet → Im System testen
2. View-GUID für sys_mandanten konfigurieren (für Tab 1)
3. Weitere Test-Frames für andere Tabellen:
   - sys_framedaten (Frames bearbeiten)
   - sys_viewdaten (Views bearbeiten)
   - persondaten (66666... Dictionary)

## 📝 Hinweise

**Alte Datei NICHT löschen:**
- `pdvm_system_editor.py` → Kann als Referenz dienen
- Bei Bedarf später entfernen wenn neuer Editor sich bewährt hat

**Template-System:**
- 55555... Templates können weiterhin verwendet werden
- Aber: System-Editor ist NICHT mehr abhängig davon
- Administrator kann direkt im JSON alles anpassen

**66666... Dictionaries:**
- Perfekt geeignet für Bearbeitung mit neuem Editor
- Tree-View zeigt klare Struktur
- JSON-Editor ermöglicht Copy & Paste zwischen Dictionaries

---

**Erstellt:** 18.12.2025
**Status:** ✅ Vollständig implementiert und integriert
**Test:** Bereit für System-Test
