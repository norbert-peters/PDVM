# Vier-Ebenen-Spalten-Architektur für Expert-Mode - VEREINFACHT

## Übersicht

Die **Vier-Ebenen-Architektur** erweitert das ursprüngliche Drei-Ebenen-System um eine **Reihenfolge-Ebene**. **Besonderheit**: Die Reihenfolge wird **direkt in der Tabelle** per Drag & Drop verwaltet, nicht über einen separaten Dialog.

## Die vier Ebenen

### Ebene 1: Standard-Spalten (Basis)
- **Definition**: Spalten mit `show = true` in den viewdaten
- **Zweck**: Grundlegende Spalten, die immer verfügbar sind
- **Verhalten**: Unveränderlich, definiert die Basis-Funktionalität

### Ebene 2: Benutzer-Auswahl (Sichtbarkeit)
- **Definition**: Individuelle Aktivierung/Deaktivierung von Spalten
- **Zweck**: Benutzer kann entscheiden, welche verfügbaren Spalten angezeigt werden
- **Verhalten**: Persistent gespeichert pro Benutzer und View
- **UI**: **Dialog mit Checkboxen**
- **Speicherort**: `systemsteuerung` Tabelle → `ColumnSelection`

### Ebene 3: Expert-Spalten (Erweiterte Funktionen)
- **Definition**: Spalten mit `expert = true` in den viewdaten
- **Zweck**: Zusätzliche Spalten nur für Expert-Mode sichtbar
- **Verhalten**: Werden automatisch hinten angefügt wenn Expert-Mode aktiv
- **UI**: **Orange markierte Checkboxen im Dialog**

### Ebene 4: Benutzer-Reihenfolge (Anordnung) - **DIREKT IN TABELLE!**
- **Definition**: Individuelle Spalten-Reihenfolge per Drag & Drop
- **Zweck**: Benutzer kann die Reihenfolge der angezeigten Spalten bestimmen
- **Verhalten**: Persistent gespeichert pro Benutzer und View
- **UI**: **Direkte Verschiebung in der Tabellen-Header per Maus** 🖱️
- **Speicherort**: `systemsteuerung` Tabelle → `ColumnOrder`

## Revolutionärer Ansatz: Zwei-UI-System

### 1. Dialog für Auswahl (Sichtbarkeit)
```
✅ Spalten-Auswahl: Dialog mit Checkboxen
   ├─ Standard-Spalten (schwarz)
   └─ Expert-Spalten (🔧 orange)

💡 Hinweis im Dialog: "Spalten-Reihenfolge können Sie direkt 
   in der Tabelle per Drag & Drop ändern"
```

### 2. Tabelle für Reihenfolge (Drag & Drop)
```
✅ Spalten-Verschiebung: Direkt im Tabellen-Header
   ├─ Header.setSectionsMovable(True)
   ├─ Drag & Drop zwischen Spalten
   └─ Automatische Speicherung bei Verschiebung
```

## Benutzer-Workflow - VEREINFACHT

### Spalten auswählen:
1. **Spalten-Button** klicken
2. **Checkboxen** aktivieren/deaktivieren
3. **OK** → Auswahl wird gespeichert

### Reihenfolge ändern:
1. **Spalten-Header** in der Tabelle anklicken
2. **Drag & Drop** zur gewünschten Position
3. **Automatische Speicherung** - keine weitere Aktion nötig!

## Technische Implementierung

### Dialog-Vereinfachung
```python
class ColumnSelectionDialog(QDialog):
    """Nur für Spalten-Auswahl - KEINE Reihenfolge"""
    
    def __init__(self, available_columns, selected_columns, parent=None):
        # Einfaches einspaltige Layout
        # Standard/Expert-Spalten getrennt dargestellt
        # Hinweis auf Drag & Drop in Tabelle
```

### Tabellen-Drag & Drop
```python
def _create_table(self):
    header = self.table.horizontalHeader()
    header.setSectionsMovable(True)  # Drag & Drop aktivieren
    header.sectionMoved.connect(self._on_column_moved)  # Auto-Speicherung

def _on_column_moved(self, logical_index, old_visual_index, new_visual_index):
    # Neue Reihenfolge ermitteln und automatisch speichern
    new_order = self._get_current_column_order()
    self._save_user_column_order(new_order)
    # Fertig! Keine Bestätigung nötig
```

### Persistierung - Unverändert
```json
{
  "user_guid": {
    "ColumnSelection": {
      "view_guid": ["spalte1", "spalte2", "spalte3"]
    },
    "ColumnOrder": {
      "view_guid": ["spalte2", "spalte1", "expert_spalte1", "spalte3"]
    }
  }
}
```

## Vorteile der vereinfachten Lösung

1. **Intuitive Bedienung**: Reihenfolge direkt da ändern wo sie sichtbar ist
2. **Keine Bestätigung nötig**: Drag & Drop = sofort gespeichert
3. **Weniger Klicks**: Ein Dialog weniger
4. **Bessere UX**: Direkte Manipulation statt abstrakte Liste
5. **Standard-Verhalten**: Wie in Excel/andere Tabellen-Programme
6. **Expert-Integration**: Expert-Spalten nahtlos verschiebbar

## Problem gelöst: "Bestätigung fehlte"

❌ **Vorher**: Komplexer Dialog mit separater Drag & Drop Liste
- Reihenfolge in Dialog ändern
- OK klicken für Bestätigung  
- Unintuitiv und mehrere Schritte

✅ **Jetzt**: Direkte Manipulation in der Tabelle
- Spalte anklicken und ziehen
- Automatische Speicherung
- Ein Vorgang = eine Aktion

## Expert-Spalten-Verhalten

- Expert-Spalten werden **standardmäßig hinten** angefügt
- Können aber **sofort per Drag & Drop** an jede Position verschoben werden
- Reihenfolge wird **persistent gespeichert**
- **Orange Markierung** im Auswahl-Dialog für bessere Erkennung

## Fazit

Diese Lösung kombiniert das Beste aus beiden Welten:
- **Dialog**: Für strukturierte Auswahl (sichtbar/unsichtbar)
- **Tabelle**: Für intuitive Reihenfolge-Änderung

**Ergebnis**: Weniger komplex, intuitiver, standard-konform! 🎯
