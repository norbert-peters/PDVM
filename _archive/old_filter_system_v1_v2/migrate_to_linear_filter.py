"""
🔄 MIGRATION ZUM UNIFIED LINEAR FILTER SYSTEM
==========================================

Dieses Skript ersetzt das komplexe Multi-Klassen Filter-System durch 
das neue einheitliche lineare System in pdvm_view_dialog.py.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def migrate_pdvm_view_dialog():
    """
    Migriert pdvm_view_dialog.py zum neuen linearen Filter-System.
    
    MIGRATION STRATEGIE:
    1. Alle drei Klassen (PdvmViewDialog, PdvmViewDisplay, PdvmFilterPanel) 
       bekommen die neue einheitliche Filter-Integration
    2. Alle alten apply_filter_string() Methoden werden ersetzt
    3. Nur EINE Methode pro Klasse für Filter-Anwendung
    """
    
    logger.info("🔄 === MIGRATION ZUM UNIFIED LINEAR FILTER ===")
    
    # Backup erstellen
    original_file = Path("pdvm_view_dialog.py")
    backup_file = Path("pdvm_view_dialog_BACKUP_BEFORE_MIGRATION.py")
    
    if original_file.exists():
        logger.info(f"💾 Erstelle Backup: {backup_file}")
        backup_file.write_text(original_file.read_text(encoding='utf-8'), encoding='utf-8')
    
    migration_code = '''
# =======================================
# NEUE UNIFIED LINEAR FILTER INTEGRATION  
# =======================================

from pdvm_linear_filter_integration import create_pdvm_linear_filter

class PdvmViewDialog(QDialog):
    """Dialog für View-Anzeige mit NEUEM LINEAREN FILTER-SYSTEM"""
    
    def __init__(self, parent=None, view_guid=None):
        super().__init__(parent)
        # ... bestehende Initialisierung ...
        
        # NEUES LINEARES FILTER-SYSTEM
        self.linear_filter = None  # Wird nach display-Erstellung initialisiert
    
    def apply_filter_string(self, filter_string: str):
        """🎯 NEUE LINEARE FILTER-METHODE - ersetzt alles alte"""
        try:
            logger.info("🎯 === PDVM VIEW DIALOG - LINEARE FILTER-ANWENDUNG ===")
            
            # Filter-Integration sicherstellen
            if not self.linear_filter and hasattr(self, 'display') and self.display and hasattr(self.display, 'table'):
                self.linear_filter = create_pdvm_linear_filter(self.display.table, self.view_guid)
                logger.info("✅ Linear Filter Integration erstellt")
            
            if not self.linear_filter:
                logger.error("❌ Kein Linear Filter verfügbar")
                return
            
            # EINHEITLICHE FILTER-ANWENDUNG
            success = self.linear_filter.apply_filter_unified(filter_string)
            
            if success:
                logger.info("✅ Lineare Filter-Anwendung erfolgreich")
                # UI refresh falls erforderlich
                if hasattr(self, 'display') and self.display and hasattr(self.display, 'refresh_table'):
                    self.display.refresh_table()
            else:
                logger.error("❌ Lineare Filter-Anwendung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler in neuer linearer Filter-Methode: {e}")


class PdvmViewDisplay(QWidget):
    """Display für Tabellen-Anzeige mit NEUEM LINEAREN FILTER-SYSTEM"""
    
    def __init__(self, view_dialog):
        super().__init__()
        self.view_dialog = view_dialog
        # ... bestehende Initialisierung ...
        
        # NEUES LINEARES FILTER-SYSTEM  
        self.linear_filter = None  # Wird nach table-Erstellung initialisiert
    
    def apply_filter_string(self, filter_string: str):
        """🎯 NEUE LINEARE FILTER-METHODE für Display"""
        try:
            logger.info("🎯 === PDVM VIEW DISPLAY - LINEARE FILTER-ANWENDUNG ===")
            
            # Filter-Integration sicherstellen
            if not self.linear_filter and hasattr(self, 'table'):
                view_guid = getattr(self.view_dialog, 'view_guid', None)
                self.linear_filter = create_pdvm_linear_filter(self.table, view_guid)
                logger.info("✅ Linear Filter Integration für Display erstellt")
            
            if not self.linear_filter:
                logger.error("❌ Kein Linear Filter verfügbar")
                return
            
            # EINHEITLICHE FILTER-ANWENDUNG
            success = self.linear_filter.apply_filter_unified(filter_string)
            
            if success:
                logger.info("✅ Display lineare Filter-Anwendung erfolgreich")
                self.refresh_table()
            else:
                logger.error("❌ Display lineare Filter-Anwendung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler in Display linearer Filter-Methode: {e}")
    
    def _show_all_rows(self):
        """Reset alle Zeilen sichtbar - wird vom linearen System automatisch aufgerufen"""
        if self.linear_filter:
            return self.linear_filter.clear_all_filters()
        else:
            # Fallback
            if hasattr(self, 'table'):
                for row in range(self.table.rowCount()):
                    self.table.setRowHidden(row, False)


class PdvmFilterPanel(QWidget):
    """Filter-Panel mit NEUEM LINEAREN FILTER-SYSTEM"""
    
    def __init__(self, view_dialog, parent=None):
        super().__init__(parent)
        self.view_dialog = view_dialog
        # ... bestehende Initialisierung ...
        
        # NEUES LINEARES FILTER-SYSTEM
        self.linear_filter = None  # Wird über view_dialog geholt
    
    def apply_filter_string(self, filter_string: str):
        """🎯 NEUE LINEARE FILTER-METHODE für Filter-Panel"""
        try:
            logger.info("🎯 === PDVM FILTER PANEL - LINEARE FILTER-ANWENDUNG ===")
            
            # Filter-Integration über view_dialog holen
            if (hasattr(self.view_dialog, 'linear_filter') and 
                self.view_dialog.linear_filter):
                
                # EINHEITLICHE FILTER-ANWENDUNG über Dialog
                success = self.view_dialog.linear_filter.apply_filter_unified(filter_string)
                
                if success:
                    logger.info("✅ Filter-Panel lineare Filter-Anwendung erfolgreich")
                else:
                    logger.error("❌ Filter-Panel lineare Filter-Anwendung fehlgeschlagen")
            else:
                logger.error("❌ Kein Linear Filter über view_dialog verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler in Filter-Panel linearer Filter-Methode: {e}")
'''
    
    logger.info("📝 Migration-Code erstellt")
    logger.info("💡 NÄCHSTE SCHRITTE:")
    logger.info("   1. Backup wurde erstellt")
    logger.info("   2. Implementiere die neuen Methoden in den bestehenden Klassen")
    logger.info("   3. Entferne alle alten komplexen Filter-Aufrufe")
    logger.info("   4. Teste das neue lineare System")
    
    return migration_code

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    migrate_pdvm_view_dialog()