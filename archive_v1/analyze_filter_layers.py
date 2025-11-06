#!/usr/bin/env python3
"""
FILTER-EBENEN ANALYSE
=====================

Analysiert alle verschiedenen Filter-Ebenen die parallel existieren können:
1. Search Parameter Dialog Filter (current_filters, original_filters)
2. Extended Filter Engine Conditions (extended_conditions)
3. Persistente Filter in anwendungsdaten
4. Gesamtfilter (Ausnahme - bleibt bestehen)
5. UI-Element Filter-States
6. Cache-Filter
"""

import logging
import sys
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path setup für Imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_filter_layers():
    """Analysiere alle Filter-Ebenen"""
    print("🔍 ANALYSE: Verschiedene Filter-Ebenen")
    print("=" * 50)
    
    try:
        # Import Search Parameter Dialog
        from search_parameter_dialog import SearchParameterDialog
        from extended_filter_engine import ExtendedFilterEngine
        from pdvm_central_systemsteuerung import initialize_gcs, get_gcs
        
        # Initialize GCS
        test_user_guid = "test-user-12345"
        test_user_data = {"name": "Test User", "role": "admin"}
        initialize_gcs(test_user_guid, test_user_data)
        gcs = get_gcs()
        
        if not gcs:
            print("❌ GCS nicht verfügbar")
            return False
        
        test_view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        
        print(f"📂 Test View-GUID: {test_view_guid}")
        
        # 1. EBENE: Search Parameter Dialog
        print("\\n1️⃣ EBENE: Search Parameter Dialog Filter")
        dialog = SearchParameterDialog(None, view_guid=test_view_guid)
        
        # Simuliere einige Filter
        dialog.current_filters = {
            "vorname_show": "TestDialog",
            "familienname_show": "DialogFilter"
        }
        dialog.original_filters = {
            "vorname_show": "OriginalDialog"  
        }
        
        print(f"   current_filters: {dialog.current_filters}")
        print(f"   original_filters: {dialog.original_filters}")
        
        # 2. EBENE: Extended Filter Engine
        print("\\n2️⃣ EBENE: Extended Filter Engine Conditions")
        
        # Import SearchCondition
        try:
            from field_search_detail_dialog import SearchCondition
        except ImportError:
            # Fallback für 4-Positionen Struktur  
            class SearchCondition:
                def __init__(self, value="", operator_type="=", logic_operator="FIRST", negation="IS"):
                    self.value = value
                    self.operator_type = operator_type
                    self.logic_operator = logic_operator
                    self.negation = negation
                
                def to_dict(self):
                    return {
                        'value': self.value,
                        'operator_type': self.operator_type,
                        'logic_operator': self.logic_operator,
                        'negation': self.negation
                    }
                
                @classmethod
                def from_dict(cls, data):
                    return cls(
                        value=data.get('value', ''),
                        operator_type=data.get('operator_type', '='),
                        logic_operator=data.get('logic_operator', 'FIRST'),
                        negation=data.get('negation', 'IS')
                    )
        
        engine = ExtendedFilterEngine()
        engine.view_guid = test_view_guid
        
        # Simuliere erweiterte Bedingungen
        test_conditions = [
            SearchCondition(value="EngineTest", operator_type="contains", logic_operator="AND", negation="IS")
        ]
        
        engine.extended_conditions = {
            "vorname_show": test_conditions,
            "familienname_show": [SearchCondition(value="EngineFamily", operator_type="=")]
        }
        
        print(f"   extended_conditions keys: {list(engine.extended_conditions.keys())}")
        for key, conditions in engine.extended_conditions.items():
            print(f"     {key}: {len(conditions)} conditions")
        
        # 3. EBENE: Persistente Filter in anwendungsdaten
        print("\\n3️⃣ EBENE: Persistente anwendungsdaten Filter")
        
        # Schaue nach vorhandenen persistenten Filtern
        view_data, _ = gcs._app_db.get_value(test_view_guid, "vorname_show") or (None, None)
        if view_data:
            print(f"   vorname_show persistent: {view_data}")
        
        # Weitere Spalten prüfen
        for col in ["familienname_show", "geburtsdatum_show", "anrede_show"]:
            col_data, _ = gcs._app_db.get_value(test_view_guid, col) or (None, None) 
            if col_data:
                print(f"   {col} persistent: {col_data}")
        
        # 4. EBENE: Gesamtfilter (Ausnahme - bleibt)
        print("\\n4️⃣ EBENE: Gesamtfilter (AUSNAHME - bleibt bestehen)")
        
        # Prüfe ob es ein Gesamtfilter-Pattern gibt
        gesamtfilter_data, _ = gcs._app_db.get_value(test_view_guid, "gesamtfilter") or (None, None)
        if gesamtfilter_data:
            print(f"   Gesamtfilter: {gesamtfilter_data}")
        else:
            print("   Kein Gesamtfilter gefunden")
        
        # 5. ZUSAMMENFASSUNG: Potentielle Konflikte
        print("\\n🚨 POTENTIELLE KONFLIKTE:")
        print("   - Dialog current_filters vs. original_filters")
        print("   - Dialog Filter vs. Extended Conditions")  
        print("   - Memory Filter vs. Persistente Filter")
        print("   - Alte Filter bleiben in Persistenz stehen")
        print("   - Cache-Ebenen werden nicht synchronisiert")
        
        return True
        
    except Exception as e:
        print(f"❌ Analyse fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = analyze_filter_layers()
    sys.exit(0 if success else 1)