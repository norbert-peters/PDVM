"""
ERWEITERTE SUCHFUNKTIONALITÄT - KONZEPT
========================================

Hierarchische Suchstruktur:
┌─────────────────────────────────────┐
│ Hauptdialog (SearchParameterDialog) │
├─────────────────────────────────────┤
│ ┌─ Familienname [Details...] ───┐   │
│ │ └─ "M*"                       │   │
│ ├─ Vorname [Details...]  ──────┐   │
│ │ └─ "UND *au* UND NICHT Laure*"│   │
│ └─ Weitere Felder...            │   │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ Detail-Dialog (FieldSearchDialog)   │
├─────────────────────────────────────┤
│ Feld: Familienname                  │
│                                     │
│ ┌─ UND ─┐ [Text____] [☐ Von links] │
│ ├─ UND ─┤ [Text____] [☑ Von links] │
│ ├─ ODER─┤ [Text____] [☐ Wildcard]  │
│ ├─ NICHT┤ [Text____] [☑ Regex]     │
│                                     │
│ [+ Bedingung hinzufügen]            │
│ [OK] [Abbrechen]                    │
└─────────────────────────────────────┘

DATENSTRUKTUR für komplexe Filter:
{
    "familienname": {
        "conditions": [
            {"operator": "AND", "value": "M*", "type": "startswith"},
            {"operator": "AND", "value": "Mül*", "type": "wildcard"}
        ]
    },
    "vorname": {
        "conditions": [
            {"operator": "AND", "value": "*au*", "type": "contains"},
            {"operator": "NOT", "value": "Laure*", "type": "startswith"}
        ]
    }
}
"""

# BEISPIEL: Erweiterte Such-Condition Klasse
class SearchCondition:
    def __init__(self, field_name, operator="AND", value="", search_type="contains"):
        self.field_name = field_name
        self.operator = operator  # AND, OR, NOT
        self.value = value
        self.search_type = search_type  # contains, startswith, endswith, exact, regex
        
    def matches(self, data_value):
        """Prüfe ob Datenwert der Bedingung entspricht"""
        if not data_value:
            return False
            
        data_str = str(data_value).lower()
        search_str = str(self.value).lower()
        
        if self.search_type == "startswith":
            return data_str.startswith(search_str.replace('*', ''))
        elif self.search_type == "endswith":
            return data_str.endswith(search_str.replace('*', ''))
        elif self.search_type == "contains":
            return search_str.replace('*', '') in data_str
        elif self.search_type == "exact":
            return data_str == search_str
        elif self.search_type == "regex":
            import re
            try:
                return bool(re.search(search_str, data_str, re.IGNORECASE))
            except:
                return False
        elif self.search_type == "wildcard":
            import fnmatch
            return fnmatch.fnmatch(data_str, search_str)
        
        return False

class FieldSearchGroup:
    def __init__(self, field_name):
        self.field_name = field_name
        self.conditions = []
        
    def add_condition(self, operator, value, search_type):
        condition = SearchCondition(self.field_name, operator, value, search_type)
        self.conditions.append(condition)
        return condition
        
    def matches(self, data_value):
        """Prüfe alle Bedingungen für dieses Feld"""
        if not self.conditions:
            return True  # Keine Bedingungen = alle Werte passen
            
        results = []
        
        for condition in self.conditions:
            match = condition.matches(data_value)
            
            if condition.operator == "NOT":
                results.append(not match)
            else:
                results.append(match)
        
        # Kombiniere Ergebnisse
        final_result = True
        or_group = []
        
        for i, condition in enumerate(self.conditions):
            if condition.operator == "OR":
                or_group.append(results[i])
            elif condition.operator == "AND":
                if or_group:
                    # Schließe OR-Gruppe ab
                    final_result = final_result and any(or_group)
                    or_group = []
                final_result = final_result and results[i]
            elif condition.operator == "NOT":
                if or_group:
                    final_result = final_result and any(or_group)
                    or_group = []
                final_result = final_result and results[i]
        
        # Finale OR-Gruppe verarbeiten
        if or_group:
            final_result = final_result and any(or_group)
            
        return final_result

# BEISPIEL USAGE:
"""
# Familienname mit M beginnt
familienname_group = FieldSearchGroup("familienname")
familienname_group.add_condition("AND", "M*", "startswith")

# Vorname mit "au" aber nicht "Laure"
vorname_group = FieldSearchGroup("vorname")
vorname_group.add_condition("AND", "*au*", "contains")
vorname_group.add_condition("NOT", "Laure*", "startswith")

# Test
print(familienname_group.matches("Müller"))    # True
print(familienname_group.matches("Schmidt"))   # False

print(vorname_group.matches("Paul"))          # True  (hat "au")
print(vorname_group.matches("Laurence"))      # False (beginnt mit "Laure")
print(vorname_group.matches("Klaus"))         # True  (hat "au")
"""