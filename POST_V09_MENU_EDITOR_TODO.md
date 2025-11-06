# 📝 POST-V0.9 TODO: Menü-Editor Implementierung

**Status**: ⚠️ DEAKTIVIERT (Post-0.9 Feature)  
**Priorität**: HOCH  
**Datum**: 06.11.2025

---

## 🎯 Ziel

Der Menü-Editor ermöglicht das visuelle Bearbeiten von Menü-Strukturen direkt in der Anwendung.

---

## ❌ Aktuelle Situation (V0.9)

### Problem 1: Import-Fehler
```python
# pdvm_systemstart.py (Zeile 1002, 1439)
from pdvm_menu_editor import PdvmMenuEditor
# ❌ Pylance: Import "pdvm_menu_editor" could not be resolved
```

### Problem 2: Modul nicht fertig
- `pdvm_menu_editor.py` existiert im Archiv als alte Version
- Noch nicht an V3.2 Pipeline angepasst
- Noch nicht an neue Menü-Struktur angepasst

### Temporäre Lösung (V0.9)
```python
# ⚠️ DEAKTIVIERT - Menü-Editor noch nicht fertig (Post-0.9 Feature)
# from pdvm_menu_editor import PdvmMenuEditor
logger.warning("⚠️ Menü-Editor noch nicht implementiert (Post-0.9 Feature)")
```

**Betroffene Dateien**:
- ✅ `pdvm_systemstart.py` (Zeile 1002, 1439) - Imports deaktiviert
- ✅ Keine Pylance-Fehler mehr

---

## 📋 Aufgaben für Post-V0.9

### Phase 1: Analyse & Design
- [ ] Alte `pdvm_menu_editor.py` aus Archiv analysieren
- [ ] Anforderungen definieren (User-Story)
- [ ] UI-Design entwerfen (Mockup)
- [ ] Datenmodell definieren (Menü-Struktur)

### Phase 2: Implementierung
- [ ] `pdvm_menu_editor.py` neu schreiben
- [ ] V3.2 Pipeline-Integration
- [ ] Neue Menü-Struktur-Kompatibilität
- [ ] CRUD-Operationen (Create, Read, Update, Delete)
- [ ] Drag & Drop für Menü-Sortierung

### Phase 3: Integration
- [ ] Import-Statements in `pdvm_systemstart.py` aktivieren
- [ ] Handler-Metadaten definieren (SKIP_CLEAR, etc.)
- [ ] GCS-Integration (Persistierung)
- [ ] Menu-Handler-Integration

### Phase 4: Testing
- [ ] Unit-Tests schreiben
- [ ] Integration-Tests
- [ ] UI-Tests (Benutzer-Workflow)
- [ ] Edge-Cases testen (leere Menüs, Verschachtelungen, etc.)

---

## 🔧 Technische Details

### Erwartete Funktionen
1. **Menü anzeigen**: Aktuelle Menü-Struktur visualisieren
2. **Menü bearbeiten**: 
   - Namen ändern
   - Icons ändern
   - Reihenfolge ändern (Drag & Drop)
   - Verschachtelung anpassen
3. **Menü-Items hinzufügen**:
   - Neue Untermenüs
   - Neue Commands
   - Neue Views
4. **Menü-Items löschen**: Mit Bestätigung
5. **Speichern**: In GCS-Datenbank persistieren

### Integration in V3.2 Pipeline
```python
# Handler: handler_open_menu_editor.py
SKIP_CLEAR = False  # Workspace wird geleert
HANDLER_METADATA = {
    'description': 'Öffnet Menü-Editor',
    'category': 'system',
    'requires_gcs': True
}

def execute(params: dict, context: dict, gcs) -> bool:
    menu_handler = context.get('menu_handler')
    main_app = context.get('main_app')
    
    # Menü-Editor als Widget erstellen
    from pdvm_menu_editor import PdvmMenuEditor
    editor = PdvmMenuEditor(menu_handler.menu, gcs)
    
    # In Context speichern für Pipeline
    context['widget'] = editor
    return True
```

### Datenmodell
```python
# Menü-Struktur (bereits vorhanden in GCS)
{
    "guid": "menu-item-guid",
    "name": "Menü-Item Name",
    "icon": "icon-path.png",
    "type": "submenu|command|view",
    "children": [...],  # Nur bei type=submenu
    "handler": "handler_name",  # Nur bei type=command
    "view_guid": "view-guid",  # Nur bei type=view
    "order": 0  # Sortierung
}
```

---

## 📚 Referenzen

### Bestehende Dateien
- `archive_v1/pdvm_menu_editor.py` - Alte Version (Referenz)
- `pdvm_menu_handler.py` - Menü-Handler
- `pdvm_menu_builder.py` - Menü-Builder
- `pdvm_menu_storage.py` - Menü-Persistierung
- `v3_menu_handler.py` - V3-Menu-Handler

### Dokumentation
- `V3.2_LINEARE_PIPELINE_DOKUMENTATION.md` - Pipeline-Integration
- `V3_MENU_TRACE_PROBLEME_BEHOBEN.md` - Menü-System-Dokumentation
- `.github/copilot-instructions.md` - Entwickler-Richtlinien

---

## ⚠️ Wichtige Hinweise

### Was NICHT gemacht werden sollte
- ❌ Imports in V0.9 aktivieren (System muss stabil bleiben)
- ❌ Alte Version aus Archiv einfach zurückkopieren (nicht kompatibel)
- ❌ Menü-Struktur ändern ohne Dokumentation

### Was gemacht werden sollte
- ✅ User-Story definieren (Was soll der Editor können?)
- ✅ Neues Design (V3.2-kompatibel)
- ✅ Schrittweise Implementierung (Phase für Phase)
- ✅ Tests vor Integration

---

## 🚀 Nächste Schritte

**Nach V0.9 Release**:
1. User-Story für Menü-Editor definieren (Du beschreibst die Anforderungen)
2. Alte Version analysieren (Was war gut? Was muss neu?)
3. Design-Entwurf (Mockup der UI)
4. Implementierung starten (Phase 1)

**Geschätzte Dauer**: 2-3 Wochen (je nach Komplexität)

---

**Status**: DOKUMENTIERT ✅  
**Verantwortlich**: Norbert Peters  
**Priorität nach V0.9**: HOCH
