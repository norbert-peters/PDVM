# Enhanced Multi-Tab System Dokumentation v2.0
===============================

## Übersicht

Das Enhanced Multi-Tab System für PDVM bietet erweiterte Funktionalität für die parallele Anzeige von Tabs mit intelligenter Tab-Auswahl, Frame-basierter Konfiguration, persistenten Benutzer-Einstellungen und **direkter Tab-Navigation im Multi-Tab-Modus**.

## ✨ Neue Features v2.0

### 🔄 Tab-Navigation im Multi-Tab-Modus
- **Button-Navigation**: Alle verfügbaren Tabs als klickbare Buttons angezeigt
- **Dropdown-Wechsel**: Schneller Tab-Wechsel über Dropdown-Menü
- **Keyboard-Shortcuts**: Ctrl+←/→ für Tab-Navigation, Alt+1-9 für direkten Zugriff
- **Dynamische Updates**: Tab-Anzeige passt sich automatisch dem aktiven Tab an
- **Kein Modus-Wechsel nötig**: Navigation direkt im Multi-Tab-Modus ohne Deaktivierung

### 1. Smart Tab-Anzeige
- **Aktiver Tab + rechte Nachbarn**: Zeigt immer den aktiven Tab und die nächsten 1-2 Tabs rechts davon
- **Wraparound-Logik**: Wenn nicht genügend Tabs rechts vorhanden, beginnt wieder von vorne
- **Dynamische Anpassung**: Tab-Auswahl passt sich automatisch der gewählten Anzahl an
- **Live-Update**: Bei Tab-Wechsel wird Multi-Tab-Anzeige automatisch neu berechnet

### 2. Frame-basierte Konfiguration
- **Framedaten-Integration**: Multi-Tab-Einstellungen werden in der `framedaten`-Tabelle gespeichert
- **Tab-Eigenschaften**: Jeder Tab hat `multi_tab_eligible` und `preferred_position` Attribute
- **Presets**: Vordefinierte Multi-Tab-Layouts (2er, 3er, vertikal)
- **Gruppenorganisation**: Tabs können verschiedene Feldgruppen enthalten

### 3. Benutzer-Einstellungen
- **Systemsteuerung-Integration**: Einstellungen werden unter der Frame-GUID in `systemsteuerung` gespeichert
- **Persistente Präferenzen**: Layout, Tab-Anzahl, Auto-Aktivierung werden gespeichert
- **Benutzerspezifisch**: Jeder User kann eigene Einstellungen pro Frame haben

### 4. Erweiterte UI-Komponenten
- **Navigation-Leiste**: Zeigt alle Tabs mit Status-Anzeige (aktiv/verfügbar)
- **Konfigurations-Panel**: F5 öffnet dediziertes Einstellungs-Panel
- **Echte Daten**: Alle Split-Views zeigen echte Formulardaten
- **Status-Integration**: View-Bereich zeigt Multi-Tab-Status in Echtzeit
- **Scroll-Support**: Jeder Tab-Container hat eigene Scrollbars

## 🎛️ Bedienung v2.0

### Keyboard-Shortcuts
- **F1**: View-Lupe (versteckt Input-Bereich)
- **F2**: Input-Lupe (versteckt View-Bereich) 
- **F3**: Position zurücksetzen (alle Modi deaktivieren)
- **F4**: Multi-Tab-Modus umschalten
- **F5**: Konfigurations-Panel öffnen/schließen
- **Ctrl+←**: Vorheriger Tab (mit Wraparound)
- **Ctrl+→**: Nächster Tab (mit Wraparound)
- **Alt+1-9**: Direkter Sprung zu Tab 1, 2, 3, ..., 9

### Tab-Navigation Workflow
1. **F4 drücken** → Multi-Tab-Modus aktivieren
2. **Navigation-Leiste erscheint** oben mit:
   - Tab-Buttons (grün=aktiv, grau=verfügbar)
   - Dropdown für Tab-Wechsel
   - ◀▶ Buttons für sequenzielle Navigation
3. **Tab wechseln** per:
   - **Button-Klick**: Direkt auf gewünschten Tab klicken
   - **Dropdown**: Tab auswählen → automatischer Wechsel
   - **Keyboard**: Ctrl+←/→ oder Alt+Nummer
4. **Multi-Tab-Anzeige aktualisiert sich automatisch**
5. **Kein Modus-Verlassen nötig** - Navigation bleibt aktiv

### Multi-Tab-Konfiguration
1. **F5 drücken** → Konfigurations-Panel öffnet sich
2. **Tab-Anzahl wählen**: 2-4 parallel angezeigte Tabs
3. **Layout wählen**: Horizontal oder Vertikal
4. **Auto-Aktivierung**: Beim Laden automatisch aktivieren
5. **Einstellungen werden automatisch gespeichert**

### Smart Tab-Auswahl mit Navigation
- **Beispiel mit 5 Tabs (A, B, C, D, E) und 2er-Anzeige:**
  - Tab A aktiv → Anzeige: A, B → Navigation zu C
  - Tab C aktiv → Anzeige: C, D → Navigation zu E  
  - Tab E aktiv → Anzeige: E, A (Wraparound) → Navigation zu B
  - Tab B aktiv → Anzeige: B, C → etc.

## 🏗️ Technische Architektur v2.0

### Klassenstruktur

```python
# Hauptkomponenten
EnhancedMultiTabManager          # Kern-Logik für Multi-Tab-Verwaltung
├── Smart Tab-Auswahl           # get_smart_tab_selection()
├── Tab-Navigation              # navigate_to_tab(), navigate_previous_tab(), navigate_next_tab()
├── Navigation-UI               # create_tab_navigation_widget(), update_navigation_widget()
├── Konfiguration laden/speichern  # load_multi_tab_config(), save_user_settings()
├── Layout-Management           # activate_multi_tab(), deactivate_multi_tab()
├── Display-Updates            # refresh_multi_tab_display()
└── Container-Erstellung        # create_enhanced_tab_container()

MultiTabConfigWidget            # UI für Konfiguration
├── Tab-Anzahl-Spinner         # QSpinBox für 2-4 Tabs
├── Layout-Radio-Buttons       # Horizontal/Vertikal
├── Auto-Aktivierung-Checkbox  # QCheckBox
└── Status-Anzeige            # Live-Status des Systems

EnhancedUnifiedPdvmDialogWidget # Hauptwidget mit Navigation
├── View-Container             # Erweiterte Daten-Anzeige
├── Input-Container           # Multi-Tab-fähige Eingabe mit Navigation
├── Config-Container          # Einstellungs-Panel
├── Navigation-Shortcuts      # Erweiterte Keyboard-Controls
└── Enhanced Multi-Tab-Manager # Integration mit Navigation
```

### Datenbank-Strukturen

#### framedaten-Tabelle
```json
{
  "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
  "multi_tab_config": {
    "multi_tab_enabled": true,
    "max_tabs_display": 3,
    "layout_orientation": "horizontal",
    "tab_selection_mode": "smart",
    "allow_user_override": true,
    "default_active": false
  },
  "tabs": [
    {
      "tab_id": "stammdaten",
      "tab_name": "Stammdaten", 
      "tab_icon": "👤",
      "multi_tab_eligible": true,
      "preferred_position": "left",
      "groups": ["person_basic", "address_data"]
    }
  ],
  "multi_tab_presets": {
    "default_2_tabs": {
      "name": "Standard (2 Tabs)",
      "layout": "horizontal",
      "tabs": ["stammdaten", "geschaeftsdaten"],
      "sizes": [50, 50]
    }
  }
}
```

#### systemsteuerung-Tabelle  
```json
{
  "user-guid": {
    "MultiTabSettings": {
      "frame-guid": {
        "preferred_layout": "horizontal",
        "max_tabs_display": 2,
        "auto_activate": false,
        "remember_state": true,
        "last_used_preset": "default_2_tabs",
        "custom_tab_order": ["stammdaten", "geschaeftsdaten"],
        "splitter_sizes": [400, 400]
      }
    }
  }
}
```

## 🔧 Integration ins Hauptsystem

### In PDVM-Systemstart.py hinzufügen:

```python
def pdvm_enhanced_test(self):
    """Test für Enhanced Multi-Tab-Widget"""
    call_daten = {
        "app": self,
        "user_guid": self.user_guid,
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "language": "de",
        "stichtag": "2025185"
    }
    
    self.clear_content_layout()
    
    from pdvm_enhanced_multi_tab_widget import EnhancedUnifiedPdvmDialogWidget
    self.enhanced_widget = EnhancedUnifiedPdvmDialogWidget(call_daten)
    self.content_layout.addWidget(self.enhanced_widget, 1)
    self.current_dialog_widget = self.enhanced_widget
```

### Setup ausführen:
```bash
python setup_multi_tab_framedaten.py
```

## 📊 Konfiguration anpassen

### Neue Frame-GUID konfigurieren:
1. In `setup_multi_tab_framedaten.py` die gewünschte Frame-GUID setzen
2. Tab-Strukturen in `tabs`-Array definieren
3. Multi-Tab-Presets anpassen
4. Setup-Skript ausführen

### Benutzer-spezifische Anpassungen:
- User-GUID in `create_demo_user_settings()` ändern
- Standard-Einstellungen in `MultiTabSettings` anpassen
- Custom Tab-Order definieren

## 🎯 Anwendungsszenarien

### 1. Datenpflege mit 2 Tabs horizontal
- **Links**: Stammdaten (Person, Adresse)
- **Rechts**: Geschäftsdaten (Firma, Kontakt)
- **Vorteil**: Alle wichtigen Daten gleichzeitig sichtbar

### 2. Vollständige Ansicht mit 3 Tabs
- **Tab 1**: Stammdaten
- **Tab 2**: Geschäftsdaten  
- **Tab 3**: Zusatzdaten (Notizen, Dokumente)
- **Vorteil**: Kompletter Überblick ohne Tab-Wechsel

### 3. Arbeitsbereich vertikal
- **Oben**: Stammdaten (70% Höhe)
- **Unten**: Dokumente (30% Höhe)
- **Vorteil**: Effizienter Dokumenten-Workflow

### 4. Mit Lupe-Funktionen kombiniert
- **F2 + F4**: Input-Lupe mit Multi-Tab = maximaler Eingabe-Bereich
- **F4 + Menü ausblenden**: Vollbild Multi-Tab-Modus
- **Vorteil**: Optimale Bildschirmnutzung

## 🚀 Vorteile des Enhanced Systems

### 1. Intelligente Tab-Auswahl
- ✅ Immer relevante Tabs sichtbar
- ✅ Automatisches Wraparound
- ✅ Keine manuellen Tab-Auswahl nötig

### 2. Frame-basierte Konfiguration
- ✅ Pro Dialog individuell konfigurierbar
- ✅ Zentrale Verwaltung in framedaten
- ✅ Wiederverwendbare Presets

### 3. Benutzer-Präferenzen
- ✅ Persönliche Einstellungen pro Frame
- ✅ Persistente Speicherung
- ✅ Automatische Wiederherstellung

### 4. Professionelle UI
- ✅ Echte Datenstrukturen in allen Tabs
- ✅ Scroll-Support pro Container
- ✅ Live-Konfigurations-Panel
- ✅ Status-Integration

## 🔮 Zukünftige Erweiterungen

### Geplante Features:
- **Drag & Drop**: Tab-Reihenfolge per Drag & Drop ändern
- **Custom Splitter-Positionen**: Individuelle Größenverhältnisse speichern
- **Tab-Gruppen**: Thematische Gruppierung von Tabs
- **Touch-Gesten**: Tablet-optimierte Bedienung
- **Multi-Monitor-Support**: Tabs auf verschiedene Bildschirme verteilen

### Erweiterte Konfiguration:
- **Conditional Tabs**: Tabs abhängig von Daten ein-/ausblenden
- **Dynamic Loading**: Tabs erst bei Bedarf laden
- **Integration APIs**: REST-APIs für externe Konfiguration
- **Themeing**: Verschiedene Farb-Schemata für Multi-Tab-Container

## 📋 Checkliste für Implementierung

- [x] Enhanced Multi-Tab-Manager erstellt
- [x] Smart Tab-Auswahl implementiert
- [x] Frame-basierte Konfiguration integriert
- [x] Benutzer-Einstellungen in systemsteuerung
- [x] Konfigurations-Panel mit Live-Updates
- [x] Echte Datenstrukturen in allen Tabs
- [x] Scroll-Support für jeden Container
- [x] Keyboard-Shortcuts F1-F5
- [x] Setup-Skript für Konfiguration
- [x] Integration in Hauptsystem
- [x] Umfassende Dokumentation

## 🎉 Fazit

Das Enhanced Multi-Tab System bietet eine professionelle, benutzerfreundliche Lösung für die parallele Anzeige von Tabs im PDVM-System. Die intelligente Tab-Auswahl, Frame-basierte Konfiguration und persistenten Benutzer-Einstellungen machen es zu einer wertvollen Erweiterung für effizientes Arbeiten.

**Besonders geeignet für:**
- Datenpflege mit vielen Eingabefeldern
- Kombination mit Lupe-Funktionen für maximale Bildschirmnutzung
- Workflows mit häufigem Tab-Wechsel
- Benutzer mit großen Bildschirmen (>= 1920px Breite)
