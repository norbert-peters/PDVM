"""
Befüllt sys_layout Tabelle direkt via SQL

OHNE GCS-Abhängigkeit - kann standalone ausgeführt werden.

AUTOR: Norbert Peters
DATUM: 28.11.2025
"""

import sqlite3
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fill_sys_layout():
    """Befüllt sys_layout Tabelle direkt via SQL"""
    
    # DB-Pfad
    db_path = Path(__file__).parent / "Daten" / "pdvm_system.db"
    
    if not db_path.exists():
        logger.error(f"❌ Datenbank nicht gefunden: {db_path}")
        return False
    
    logger.info(f"📂 Verwende Datenbank: {db_path}")
    
    # Template-GUID
    template_guid = '55555555-5555-5555-5555-555555555555'
    
    # Default-GUID
    default_guid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    
    # Layout-Konfiguration
    layout_config = {
        'ROOT': {
            'LAYOUT_NAME': 'PDVM Default Theme',
            'LAYOUT_TYPE': 'LIGHT',
            'ACTIVE': True,
            'VERSION': '1.0',
            'AUTHOR': 'Norbert Peters',
            'DESCRIPTION': 'Standard-Layout für PDVM-System mit hellen Farben'
        },
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
        'FONTS': {
            'FAMILY': 'Arial',
            'SIZE_DEFAULT': 9,
            'SIZE_HEADER': 11,
            'SIZE_SMALL': 8,
            'WEIGHT_NORMAL': 400,
            'WEIGHT_BOLD': 700
        },
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
            ''',
            'QDateEdit': '''
                QDateEdit {
                    background-color: {COLORS.INPUT_BG};
                    color: {COLORS.TEXT};
                    border: 1px solid {COLORS.INPUT_BORDER};
                    padding: 2px 5px;
                }
                QDateEdit:focus {
                    border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                }
                QDateEdit:disabled {
                    background-color: {COLORS.DISABLED_BG};
                    color: {COLORS.DISABLED_TEXT};
                }
                QDateEdit::drop-down {
                    border: none;
                    width: 20px;
                }
            ''',
            'QTimeEdit': '''
                QTimeEdit {
                    background-color: {COLORS.INPUT_BG};
                    color: {COLORS.TEXT};
                    border: 1px solid {COLORS.INPUT_BORDER};
                    padding: 2px 5px;
                }
                QTimeEdit:focus {
                    border: 1px solid {COLORS.INPUT_FOCUS_BORDER};
                }
                QTimeEdit:disabled {
                    background-color: {COLORS.DISABLED_BG};
                    color: {COLORS.DISABLED_TEXT};
                }
            ''',
            'QCalendarWidget': '''
                QCalendarWidget {
                    background-color: {COLORS.BACKGROUND};
                }
                QCalendarWidget QToolButton {
                    background-color: {COLORS.BUTTON_BG};
                    color: {COLORS.TEXT};
                    border: 1px solid {COLORS.BORDER};
                    border-radius: 3px;
                    padding: 3px;
                }
                QCalendarWidget QToolButton:hover {
                    background-color: {COLORS.BUTTON_HOVER_BG};
                }
                QCalendarWidget QMenu {
                    background-color: {COLORS.BACKGROUND};
                    color: {COLORS.TEXT};
                    border: 1px solid {COLORS.BORDER};
                }
                QCalendarWidget QMenu::item:selected {
                    background-color: {COLORS.MENU_HOVER_BG};
                    color: {COLORS.MENU_HOVER_TEXT};
                }
                QCalendarWidget QSpinBox {
                    background-color: {COLORS.INPUT_BG};
                    color: {COLORS.TEXT};
                    border: 1px solid {COLORS.INPUT_BORDER};
                }
                QCalendarWidget QAbstractItemView {
                    background-color: {COLORS.BACKGROUND};
                    color: {COLORS.TEXT};
                    selection-background-color: {COLORS.MENU_HOVER_BG};
                    selection-color: {COLORS.MENU_HOVER_TEXT};
                }
            '''
        }
    }
    
    # JSON serialisieren
    layout_json = json.dumps(layout_config, ensure_ascii=False)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Template-Satz einfügen/aktualisieren
        cursor.execute('''
            INSERT OR REPLACE INTO sys_layout (uid, daten, name, historisch)
            VALUES (?, ?, ?, 0)
        ''', (template_guid, layout_json, 'PDVM Default Theme (Template)'))
        
        logger.info(f"✅ Template-Satz gespeichert: {template_guid}")
        
        # Default-Satz einfügen/aktualisieren
        cursor.execute('''
            INSERT OR REPLACE INTO sys_layout (uid, daten, name, historisch)
            VALUES (?, ?, ?, 0)
        ''', (default_guid, layout_json, 'PDVM Default Theme (Default)'))
        
        logger.info(f"✅ Default-Satz gespeichert: {default_guid}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Layout-Statistik:")
        logger.info(f"   Farben: {len(layout_config['COLORS'])} definiert")
        logger.info(f"   Widgets: {len(layout_config['STYLES'])} Styles")
        logger.info(f"   Fonts: {len(layout_config['FONTS'])} Eigenschaften")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    logger.info("🎨 Befülle sys_layout Tabelle...")
    
    success = fill_sys_layout()
    
    if success:
        logger.info("✅ sys_layout erfolgreich befüllt!")
        logger.info("   Template-GUID: 55555555-5555-5555-5555-555555555555")
        logger.info("   Default-GUID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    else:
        logger.error("❌ Fehler beim Befüllen")
