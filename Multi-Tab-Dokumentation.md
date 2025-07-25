# Multi-Tab-Layout Dokumentation
# ===============================

## Übersicht

Die Multi-Tab-Layout-Funktionalität ermöglicht es, 2-3 Tabs parallel in einem geteilten Layout anzuzeigen. Dies ist besonders nützlich für:

- Große Bildschirme mit viel verfügbarem Platz
- Arbeit mit zusammenhängenden Daten in verschiedenen Tabs
- Kombinationen mit der Lupe-Funktion (ausgeschaltetes Menü)
- Effiziente Datenbearbeitung ohne ständiges Tab-Wechseln

## Funktionen

### Steuerung über UI-Elemente
- **📱 Multi-Tab Button**: Aktiviert/deaktiviert den Multi-Tab-Modus
- **Layout-Auswahl**: 
  - 2 Tabs horizontal
  - 2 Tabs vertikal  
  - 3 Tabs horizontal
  - 3 Tabs vertikal
- **Tab-Auswahl**: Checkboxen für jeden verfügbaren Tab

### Keyboard-Shortcuts
- **F4**: Multi-Tab-Modus umschalten
- **F1**: View-Lupe (blendet Input-Bereich aus)
- **F2**: Input-Lupe (blendet View-Bereich aus)
- **F3**: Position wiederherstellen

## Anwendungsszenarien

### Szenario 1: Parallele Dateneingabe
```
[Stammdaten]  |  [Details]
Person-Info   |  Adresse/Kontakt
Grunddaten    |  Erweiterte Felder
```

### Szenario 2: Vergleich und Prüfung
```
[Stammdaten]
Hauptdaten
-----------
[Details]     |  [Zusatz]  
Finanzen      |  Notizen
```

### Szenario 3: Mit Lupe-Funktion
```
Menü ausgeschaltet (mehr Platz)
+ Input-Lupe (View ausgeblendet)
+ Multi-Tab (2-3 Tabs parallel)
= Maximaler Arbeitsbereich
```

## Technische Details

### Architektur
- `MultiTabLayoutManager`: Kernlogik für Tab-Verwaltung
- `QSplitter`: Geteilte Layouts (horizontal/vertikal)
- Dynamische Tab-Container mit eigenständigen Scrollbars
- Persistente Einstellungen (geplant)

### Integration
- Vollständig in `UnifiedPdvmDialogWidget V3` integriert
- Kompatibel mit bestehender Lupe-Funktionalität
- Automatische Layout-Anpassung bei Fenstergrößenänderungen

### Verwendung im Code
```python
# Multi-Tab-Unterstützung hinzufügen
from pdvm_multi_tab_layout import add_multi_tab_support

# In Widget-Initialisierung:
self.multi_tab_manager = add_multi_tab_support(container, tab_widget)

# Multi-Tab-Status abfragen:
status = widget.get_multi_tab_status()
```

## Vorteile

1. **Effizienz**: Weniger Tab-Wechsel, mehr parallele Sicht
2. **Flexibilität**: Verschiedene Layout-Optionen je nach Bedarf
3. **Benutzerfreundlichkeit**: Einfache Aktivierung über F4
4. **Skalierbarkeit**: Funktioniert gut auf verschiedenen Bildschirmgrößen
5. **Integration**: Nahtlose Einbindung in bestehende UI

## Zukünftige Erweiterungen

- Persistente Speicherung der Multi-Tab-Einstellungen
- Drag & Drop für Tab-Anordnung
- Benutzerdefinierte Splitter-Positionen speichern
- Integration mit Frame-spezifischen Layouts
- Touch-Gesten für Tablet-Unterstützung

## Demo und Test

Verwende `test_multi_tab_demo.py` für eine vollständige Demonstration der Funktionalität:

```bash
python test_multi_tab_demo.py
```

Die Demo zeigt alle verfügbaren Features und Keyboard-Shortcuts in einer eigenständigen Anwendung.
