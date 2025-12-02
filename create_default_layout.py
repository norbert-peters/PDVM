"""
Default Layout Template erstellen

Erstellt den Template-Datensatz für das Layout-System in sys_layout.
GUID: 55555555-5555-5555-5555-555555555555

AUTOR: Norbert Peters
DATUM: 28.11.2025
VERSION: 1.0
"""

import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_default_layout():
    """Erstellt Default-Layout und Template in sys_layout"""
    
    # Template-GUID (5555...)
    template_guid = '55555555-5555-5555-5555-555555555555'
    
    # Default-GUID (wird verwendet wenn User keine eigene Layout-GUID hat)
    default_guid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    
    # Layout-Daten-Struktur (gemeinsame Konfiguration)
    common_layout_config = {
            # ROOT Gruppe - Layout-Metadaten
            'ROOT': {
                'LAYOUT_NAME': 'PDVM Default Theme',
                'LAYOUT_TYPE': 'LIGHT',
                'ACTIVE': True,
                'VERSION': '1.0',
                'AUTHOR': 'Norbert Peters',
                'DESCRIPTION': 'Standard-Layout für PDVM-System mit hellen Farben'
            },
            
            # COLORS Gruppe - Farbdefinitionen
            'COLORS': {
                'BACKGROUND': '#ffffff',
                'TEXT': '#000000',
                'MENU_HOVER_BG': '#0078d4',
                'MENU_HOVER_TEXT': '#ffffff',
                'BORDER': '#cccccc',
                'DISABLED_TEXT': '#999999',
                'DISABLED_BG': '#f0f0f0',
                'BUTTON_BG': '#e1e1e1',
                'BUTTON_TEXT': '#000000',
                'BUTTON_HOVER_BG': '#d0d0d0',
                'INPUT_BG': '#ffffff',
                'INPUT_BORDER': '#a0a0a0',
                'INPUT_FOCUS_BORDER': '#0078d4',
                'HEADER_BG': '#f5f5f5',
                'HEADER_TEXT': '#333333',
                'ERROR': '#d32f2f',
                'WARNING': '#f57c00',
                'SUCCESS': '#388e3c',
                'INFO': '#1976d2'
            },
            
            # FONTS Gruppe - Schriftarten
            'FONTS': {
                'FAMILY': 'Arial',
                'SIZE_DEFAULT': 9,
                'SIZE_HEADER': 11,
                'SIZE_SMALL': 8,
                'WEIGHT_NORMAL': 400,
                'WEIGHT_BOLD': 700
            },
            
            # STYLES Gruppe - Widget-Stylesheets mit Template-Variablen
            'STYLES': {
                'QMenu': '''
                    QMenu {
                        background-color: {COLORS.BACKGROUND};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.BORDER};
                        padding: 4px;
                    }
                    QMenu::item {
                        padding: 4px 20px 4px 20px;
                    }
                    QMenu::item:selected {
                        background-color: {COLORS.MENU_HOVER_BG};
                        color: {COLORS.MENU_HOVER_TEXT};
                    }
                    QMenu::item:disabled {
                        color: {COLORS.DISABLED_TEXT};
                    }
                ''',
                
                'QComboBox': '''
                    QComboBox {
                        background-color: {COLORS.INPUT_BG};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.INPUT_BORDER};
                        padding: 2px 5px;
                    }
                    QComboBox:hover {
                        border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                    }
                    QComboBox:disabled {
                        background-color: {COLORS.DISABLED_BG};
                        color: {COLORS.DISABLED_TEXT};
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 20px;
                    }
                    QComboBox QAbstractItemView {
                        background-color: {COLORS.BACKGROUND};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.BORDER};
                        selection-background-color: {COLORS.MENU_HOVER_BG};
                        selection-color: {COLORS.MENU_HOVER_TEXT};
                    }
                ''',
                
                'QPushButton': '''
                    QPushButton {
                        background-color: {COLORS.BUTTON_BG};
                        color: {COLORS.BUTTON_TEXT};
                        border: 1px solid {COLORS.BORDER};
                        padding: 5px 15px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: {COLORS.BUTTON_HOVER_BG};
                    }
                    QPushButton:pressed {
                        background-color: {COLORS.BORDER};
                    }
                    QPushButton:disabled {
                        background-color: {COLORS.DISABLED_BG};
                        color: {COLORS.DISABLED_TEXT};
                    }
                ''',
                
                'QLineEdit': '''
                    QLineEdit {
                        background-color: {COLORS.INPUT_BG};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.INPUT_BORDER};
                        padding: 3px;
                    }
                    QLineEdit:focus {
                        border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                    }
                    QLineEdit:disabled {
                        background-color: {COLORS.DISABLED_BG};
                        color: {COLORS.DISABLED_TEXT};
                    }
                ''',
                
                'QTextEdit': '''
                    QTextEdit {
                        background-color: {COLORS.INPUT_BG};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.INPUT_BORDER};
                        padding: 3px;
                    }
                    QTextEdit:focus {
                        border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                    }
                    QTextEdit:disabled {
                        background-color: {COLORS.DISABLED_BG};
                        color: {COLORS.DISABLED_TEXT};
                    }
                ''',
                
                'QSpinBox': '''
                    QSpinBox {
                        background-color: {COLORS.INPUT_BG};
                        color: {COLORS.TEXT};
                        border: 1px solid {COLORS.INPUT_BORDER};
                        padding: 2px;
                    }
                    QSpinBox:focus {
                        border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                    }
                    QSpinBox:disabled {
                        background-color: {COLORS.DISABLED_BG};
                        color: {COLORS.DISABLED_TEXT};
                    }
                '''
            }
    }
    
    # Layout-Daten-Struktur: Template + Default
    layout_data = {
        template_guid: common_layout_config,
        default_guid: common_layout_config
    }
    
    # sys_layout.json Pfad in pdvm_system.db
    db_path = Path(__file__).parent / "pdvm_system.db" / "sys_layout.json"
    
    # Verzeichnis erstellen falls nicht vorhanden
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # JSON speichern
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Layout-System erstellt: {db_path}")
        logger.info(f"   Template-GUID: {template_guid}")
        logger.info(f"   Default-GUID: {default_guid}")
        logger.info(f"   Name: {common_layout_config['ROOT']['LAYOUT_NAME']}")
        logger.info(f"   Farben: {len(common_layout_config['COLORS'])} definiert")
        logger.info(f"   Widgets: {len(common_layout_config['STYLES'])} Styles")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des Layouts: {e}")
        return False


if __name__ == '__main__':
    logger.info("🎨 Default-Layout Template wird erstellt...")
    success = create_default_layout()
    
    if success:
        logger.info("✅ Default-Layout erfolgreich erstellt!")
        logger.info("   Verwende: gcs.layout.get_color('BACKGROUND')")
        logger.info("   Verwende: gcs.layout.get_stylesheet('QMenu')")
    else:
        logger.error("❌ Fehler beim Erstellen des Layouts")
