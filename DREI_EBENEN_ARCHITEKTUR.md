# DREI_EBENEN_ARCHITEKTUR.md
# Drei-Ebenen-Spalten-System für Expert-Mode

## 🎯 PROBLEM-ANALYSE

**Das Problem:** Im Expert-Mode werden nicht die erwarteten zusätzlichen Spalten angezeigt.
- **Erwartet:** 10 show-Spalten + 10 expert-Spalten = 20 Spalten total
- **Tatsächlich:** Nur 10 Spalten angezeigt

## 🏗️ DREI-EBENEN-ARCHITEKTUR

### **Ebene 1: Standard-Spalten (`show=true`)**
- Basis-Spalten die immer verfügbar sind
- Beispiel: FAMILIENNAME, VORNAME, GEBURTSDATUM, etc.
- Anzahl: ~10 Spalten

### **Ebene 2: Benutzer-Auswahl-Ebene**
- Basiert auf Ebene 1, kann aber individuell an-/abgewählt werden
- Wird persistent gespeichert
- Standard: Alle Ebene-1-Spalten aktiviert

### **Ebene 3: Expert-Spalten (`expert=true`)**  
- Zusätzliche Original-Spalten (z.B. _original-Felder)
- Nur im Expert-Mode verfügbar
- Werden temporär zu den verfügbaren Spalten hinzugefügt
- Anzahl: ~10 zusätzliche Spalten

## 🔧 IMPLEMENTIERUNGS-PLAN

### **Datenstruktur:**
```python
columns = [
    # Ebene 1: Standard-Spalten
    {"name": "FAMILIENNAME", "label": "Familienname", "show": True, "expert": False},
    {"name": "VORNAME", "label": "Vorname", "show": True, "expert": False},
    # ... weitere 8 Standard-Spalten
    
    # Ebene 3: Expert-Spalten  
    {"name": "FAMILIENNAME_ORIGINAL", "label": "Familienname (Original)", "show": False, "expert": True},
    {"name": "VORNAME_ORIGINAL", "label": "Vorname (Original)", "show": False, "expert": True},
    # ... weitere 8 Expert-Spalten
]
```

### **Logik:**
```python
def _get_available_columns_for_mode():
    if expert_mode:
        # Ebene 1 + Ebene 3
        return [col for col in columns if col['show'] or col['expert']]
    else:
        # Nur Ebene 1  
        return [col for col in columns if col['show'] and not col['expert']]

def _get_visible_columns():
    available = _get_available_columns_for_mode()
    # Ebene 2: Benutzer-Auswahl anwenden
    return [col for col in available if col['name'] in user_selection]
```

## 🎯 WORKFLOW-SZENARIEN

### **Normal-Mode:**
1. **Verfügbare Spalten:** 10 (nur show=true)
2. **Standard-Auswahl:** Alle 10 aktiviert
3. **Benutzer kann:** Spalten ab-/anwählen
4. **Sichtbar:** Benutzer-Auswahl aus 10 Spalten

### **Expert-Mode aktivieren:**
1. **Verfügbare Spalten:** 20 (10 show=true + 10 expert=true)
2. **Standard-Auswahl:** Alle 20 aktiviert (oder vorherige Auswahl + neue Expert-Spalten)
3. **Benutzer kann:** Alle 20 Spalten ab-/anwählen
4. **Sichtbar:** Benutzer-Auswahl aus 20 Spalten

### **Zurück zu Normal-Mode:**
1. **Verfügbare Spalten:** 10 (nur show=true)
2. **Auswahl:** Expert-Spalten verschwinden aus Auswahl
3. **Sichtbar:** Nur Standard-Spalten-Auswahl bleibt

## ✅ VORTEILE

1. **Linear:** Klare Trennung der Ebenen
2. **Einfach umschaltbar:** Nur verfügbare Spalten ändern sich
3. **Persistent:** Benutzer-Auswahl wird pro Ebene gespeichert
4. **Erweiterbar:** Weitere Ebenen können hinzugefügt werden
5. **Testbar:** Jede Ebene kann separat getestet werden

## 🚀 IMPLEMENTATION

Implementierung der drei Methoden:
1. `_get_standard_columns()` - Ebene 1
2. `_get_expert_columns()` - Ebene 3  
3. `_get_available_columns_for_mode()` - Kombination basierend auf Mode
4. `_apply_user_selection()` - Ebene 2
