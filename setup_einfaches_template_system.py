# setup_einfaches_template_system.py
"""
Vereinfachtes Template-System: Templates sind normale Menüs
"""
import logging
from pdvm_menu_template_handler import PdvmMenuTemplateHandler

# Logger-Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_basis_template():
    """Richtet das Basis-Template genau wie in Ihrem Beispiel ein"""
    print("🔧 Richte vereinfachtes Basis-Template ein...")
    
    try:
        template_handler = PdvmMenuTemplateHandler()
        
        # Ihr Basis-Template erstellen
        template_handler.create_standard_templates()
        
        print("✅ Basis-Template erfolgreich eingerichtet!")
        print("\n📋 Template-GUID: 1a653694-3132-48d9-bc3e-a512962ae8e6")
        
        print("\n💡 Verwendung in Ihrem Menü:")
        print('   "PD_grund": {')
        print('     "!guid!": "1a653694-3132-48d9-bc3e-a512962ae8e6"')
        print('   }')
        
        print("\n🔧 Das Template enthält:")
        print("   - PD_commands mit allen Basis-Kommandos")
        print("   - PD_grund mit Basis-Menüstruktur")
        print("   - Diese werden automatisch mit Ihrem Menü zusammengeführt")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Einrichten des Templates: {e}")
        return False

def test_template_merge():
    """Testet das Template-Merging mit Ihrem Beispiel"""
    print("\n🧪 Teste Template-Merging...")
    
    # Ihr Original-Menü (simuliert)
    original_menu = {
        "PD_commands": {
            "Benutzer_Profil bearbeiten": None,
            "Benutzer_Einstellungen": None,
            "Benutzer_---": None,
            "Testbereich_Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
            "Testbereich_Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
            "Testbereich_Current Frame Enhanced": "self.reload_current_frame_enhanced()",
            "Testbereich_---": None
        },
        "PD_grund": {
            "!guid!": "1a653694-3132-48d9-bc3e-a512962ae8e6"
        },
        "PD_zusatz": {"PD_z_Grund": {}, "PD_z_Menu": {}},
        "PD_menu": {}
    }
    
    try:
        template_handler = PdvmMenuTemplateHandler()
        processed_menu = template_handler.process_menu_templates(original_menu)
        
        print("✅ Template-Merging erfolgreich!")
        print("\n📋 Resultat:")
        print(f"   - PD_commands: {len(processed_menu.get('PD_commands', {}))} Einträge")
        
        if "PD_grund" in processed_menu:
            grund_entries = processed_menu["PD_grund"]
            print(f"   - PD_grund: {len(grund_entries)} Haupteinträge")
            
            if "Basis" in grund_entries:
                basis_entries = grund_entries["Basis"]
                print(f"   - Basis-Untermenü: {len(basis_entries)} Einträge")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Template-Test: {e}")
        return False

if __name__ == "__main__":
    # Template einrichten
    setup_success = setup_basis_template()
    
    if setup_success:
        # Template testen
        test_success = test_template_merge()
        
        if test_success:
            print("\n🎉 Vereinfachtes Template-System bereit!")
            print("💡 Jetzt können Sie '!guid!' in Ihren Menüs verwenden")
        else:
            print("\n💥 Template-Test fehlgeschlagen!")
    else:
        print("\n💥 Template-Setup fehlgeschlagen!")
