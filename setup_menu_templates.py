# setup_menu_templates.py
"""
Skript zum Einrichten der Standard-Menü-Templates
"""
import logging
from pdvm_menu_template_handler import PdvmMenuTemplateHandler

# Logger-Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_standard_templates():
    """Richtet die Standard-Templates ein"""
    print("🔧 Richte Standard-Menü-Templates ein...")
    
    try:
        template_handler = PdvmMenuTemplateHandler()
        
        # Standard-Templates erstellen
        template_handler.create_standard_templates()
        
        print("✅ Standard-Templates erfolgreich eingerichtet!")
        print("\n📋 Verfügbare Template-GUIDs:")
        print("- template-basis-standard (Standard Basis-Menü)")
        print("- template-basis-admin (Admin Basis-Menü)")  
        print("- template-startmenu-basis (Startmenü Basis)")
        
        print("\n💡 Verwendung in Menüdaten:")
        print('   "PD_grund": {')
        print('     "!guid!": "template-basis-standard",')
        print('     "Eigene Einträge": "meine_funktion()"')
        print('   }')
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Einrichten der Templates: {e}")
        return False

if __name__ == "__main__":
    success = setup_standard_templates()
    if success:
        print("\n🎉 Setup abgeschlossen!")
    else:
        print("\n💥 Setup fehlgeschlagen!")
