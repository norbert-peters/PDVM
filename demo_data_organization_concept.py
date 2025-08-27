#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KONZEPT: Erweiterte Datenorganisation mit Column Control System
=============================================================

Zeigt wie wir:
1. Spaltenwerte als dict mit GUID als Schlüssel organisieren
2. Mehrebenen-Sortierung linear implementieren 
3. Column Control System für Sortierungslogik nutzen
"""

class EnhancedColumnControl:
    """
    Erweiterte Column Control für Datenorganisation und Sortierung
    """
    def __init__(self):
        self.columns = []  
        self.column_map = {}
        
        # NEU: Datenorganisation
        self.column_data = {}  # {column_name: {guid1: value1, guid2: value2, ...}}
        self.row_guids = []    # Sortierte Liste der GUIDs (bestimmt Zeilenreihenfolge)
        
        # NEU: Sortierungsstack für Mehrebenen-Sortierung
        self.sort_stack = []   # [('anrede_show', 'asc'), ('familienname_show', 'asc'), ...]
        
    def add_column_data(self, column_name: str, guid: str, value):
        """Fügt Daten für eine Spalte hinzu"""
        if column_name not in self.column_data:
            self.column_data[column_name] = {}
        self.column_data[column_name][guid] = value
        
        # GUID zur Liste hinzufügen wenn neu
        if guid not in self.row_guids:
            self.row_guids.append(guid)
    
    def get_column_data(self, column_name: str, guid: str):
        """Holt Daten für eine bestimmte Spalte und GUID"""
        return self.column_data.get(column_name, {}).get(guid, "")
    
    def add_sort_level(self, column_name: str, direction: str = 'asc'):
        """
        Fügt eine Sortierebene hinzu
        Beispiel: add_sort_level('anrede_show', 'asc')
        """
        # Entferne existing level für diese Spalte
        self.sort_stack = [(col, dir) for col, dir in self.sort_stack if col != column_name]
        # Füge als neue oberste Ebene hinzu
        self.sort_stack.insert(0, (column_name, direction))
    
    def remove_sort_level(self, column_name: str):
        """Entfernt eine Sortierebene"""
        self.sort_stack = [(col, dir) for col, dir in self.sort_stack if col != column_name]
    
    def apply_multi_level_sort(self):
        """
        Wendet Mehrebenen-Sortierung an
        Sortiert self.row_guids basierend auf sort_stack
        """
        if not self.sort_stack:
            return
            
        # Sortierungsschlüssel-Funktion
        def sort_key(guid):
            key_values = []
            for column_name, direction in reversed(self.sort_stack):  # Reverse für korrekte Priorität
                value = self.get_column_data(column_name, guid)
                
                # Wert für Sortierung aufbereiten
                if isinstance(value, str):
                    sort_value = value.lower()  # Case-insensitive
                elif isinstance(value, (int, float)):
                    sort_value = value
                else:
                    sort_value = str(value).lower()
                
                # Bei DESC-Sortierung negieren (für numerische Werte) oder umkehren
                if direction == 'desc':
                    if isinstance(sort_value, (int, float)):
                        sort_value = -sort_value
                    else:
                        # Für Strings: Zeichen umkehren (primitiv aber funktional)
                        sort_value = ''.join(reversed(str(sort_value)))
                
                key_values.append(sort_value)
            
            return tuple(key_values)
        
        # Sortierung anwenden
        self.row_guids.sort(key=sort_key)
        
        print(f"✅ Mehrebenen-Sortierung angewendet: {len(self.sort_stack)} Ebenen")
        for i, (col, direction) in enumerate(self.sort_stack):
            print(f"   {i+1}. {col} ({direction})")
    
    def get_sorted_rows_as_dicts(self):
        """
        Gibt alle Zeilen als Liste von Dictionaries zurück
        In der durch Sortierung bestimmten Reihenfolge
        """
        rows = []
        for guid in self.row_guids:
            row_dict = {'uid_original': guid}  # GUID immer dabei
            for column_name in self.column_data.keys():
                row_dict[column_name] = self.get_column_data(column_name, guid)
            rows.append(row_dict)
        return rows
    
    def get_display_table_data(self, show_columns_only=True):
        """
        Bereitet Daten für Tabellenanzeige vor
        """
        # Zeilen in sortierter Reihenfolge
        rows = self.get_sorted_rows_as_dicts()
        
        # Spalten filtern wenn gewünscht (nur _show Spalten)
        if show_columns_only:
            display_columns = [col['name'] for col in self.columns if col['name'].endswith('_show') or col['name'] == 'uid_original']
        else:
            display_columns = [col['name'] for col in self.columns]
        
        # Gefilterte Daten
        display_data = []
        for row in rows:
            display_row = {col: row.get(col, "") for col in display_columns}
            display_data.append(display_row)
        
        return display_data, display_columns


# DEMO: Praktische Anwendung
if __name__ == "__main__":
    
    print("🚀 DEMO: Erweiterte Datenorganisation mit Column Control")
    
    # Column Control erstellen
    ctrl = EnhancedColumnControl()
    
    # Beispiel-Spalten hinzufügen (vereinfacht)
    spalten = ['anrede_original', 'anrede_show', 'familienname_original', 'familienname_show', 
              'vorname_original', 'vorname_show', 'alter_original', 'alter_show']
    
    for i, name in enumerate(spalten):
        ctrl.columns.append({'name': name, 'order': i})
        ctrl.column_map[name] = {'name': name, 'order': i}
    
    # DEMO-Daten hinzufügen
    demo_personen = [
        {'guid': 'guid-1', 'anrede': 'Herr', 'familienname': 'Müller', 'vorname': 'Anton', 'alter': 45},
        {'guid': 'guid-2', 'anrede': 'Frau', 'familienname': 'Schmidt', 'vorname': 'Beate', 'alter': 32},
        {'guid': 'guid-3', 'anrede': 'Herr', 'familienname': 'Müller', 'vorname': 'Bernd', 'alter': 28},
        {'guid': 'guid-4', 'anrede': 'Frau', 'familienname': 'Müller', 'vorname': 'Anna', 'alter': 55},
        {'guid': 'guid-5', 'anrede': 'Herr', 'familienname': 'Weber', 'vorname': 'Anton', 'alter': 41}
    ]
    
    # Daten in Column Control laden
    for person in demo_personen:
        guid = person['guid']
        ctrl.add_column_data('anrede_original', guid, person['anrede'])
        ctrl.add_column_data('anrede_show', guid, person['anrede'])
        ctrl.add_column_data('familienname_original', guid, person['familienname'])
        ctrl.add_column_data('familienname_show', guid, person['familienname'])
        ctrl.add_column_data('vorname_original', guid, person['vorname'])
        ctrl.add_column_data('vorname_show', guid, person['vorname'])
        ctrl.add_column_data('alter_original', guid, person['alter'])
        ctrl.add_column_data('alter_show', guid, str(person['alter']))
    
    print(f"✅ {len(demo_personen)} Personen in Column Control geladen")
    
    # UNSORTIERTE Ausgabe
    print("\n📋 UNSORTIERTE Daten:")
    unsorted_data, columns = ctrl.get_display_table_data()
    for i, row in enumerate(unsorted_data):
        print(f"   {i+1}. {row['anrede_show']} {row['familienname_show']}, {row['vorname_show']} ({row['alter_show']})")
    
    # MEHREBENEN-SORTIERUNG anwenden
    print("\n🔧 Mehrebenen-Sortierung konfigurieren:")
    print("   1. Anrede (aufsteigend)")  
    print("   2. Familienname (aufsteigend)")
    print("   3. Vorname (aufsteigend)")
    
    ctrl.add_sort_level('anrede_show', 'asc')      # Oberste Ebene
    ctrl.add_sort_level('familienname_show', 'asc') # Zweite Ebene 
    ctrl.add_sort_level('vorname_show', 'asc')     # Dritte Ebene
    
    # Sortierung anwenden
    ctrl.apply_multi_level_sort()
    
    # SORTIERTE Ausgabe
    print("\n📋 SORTIERTE Daten (Anrede → Familienname → Vorname):")
    sorted_data, columns = ctrl.get_display_table_data()
    for i, row in enumerate(sorted_data):
        print(f"   {i+1}. {row['anrede_show']} {row['familienname_show']}, {row['vorname_show']} ({row['alter_show']})")
    
    # SORTIERUNG ÄNDERN
    print("\n🔧 Sortierung ändern: Nach Alter absteigend, dann Familienname")
    ctrl.sort_stack = []  # Reset
    ctrl.add_sort_level('alter_show', 'desc')       # Primär: Alter absteigend
    ctrl.add_sort_level('familienname_show', 'asc') # Sekundär: Familienname aufsteigend
    
    ctrl.apply_multi_level_sort()
    
    print("\n📋 NEU SORTIERTE Daten (Alter ↓ → Familienname ↑):")
    new_sorted_data, columns = ctrl.get_display_table_data()
    for i, row in enumerate(new_sorted_data):
        print(f"   {i+1}. {row['anrede_show']} {row['familienname_show']}, {row['vorname_show']} ({row['alter_show']})")
    
    print("\n✅ DEMO abgeschlossen - Konzept funktioniert!")
