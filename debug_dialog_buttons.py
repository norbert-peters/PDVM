"""
DEBUG: Test ob Dialog OK-Button korrekt verbunden ist
"""
import logging
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dialog_button_connections():
    """Testet die Dialog-Button-Verbindungen"""
    
    try:
        # Simuliere minimale Umgebung
        from pdvm_spalten_parameter_dialog import PdvmSpaltenParameterDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Mock-Objekte erstellen
        class MockProvider:
            def save_column_configuration(self, columns, mode):
                logger.info(f"💾 MockProvider: save_column_configuration aufgerufen - {len(columns)} Spalten, Mode: {mode}")
                return True
        
        class MockManager:
            def get_current_controls(self, for_dialog=False):
                logger.info(f"📥 MockManager: get_current_controls aufgerufen - for_dialog: {for_dialog}")
                return MockControls()
            
            def save_column_configuration(self, columns, mode):
                logger.info(f"💾 MockManager: save_column_configuration aufgerufen - {len(columns)} Spalten, Mode: {mode}")
                return True
        
        class MockControls:
            def __init__(self):
                self.columns = [
                    {
                        'name': 'test_spalte_1',
                        'anzeige': 'Test Spalte 1',
                        'display_show': True,
                        'display_order': 1,
                        'expert': False,
                        'show_show': True,
                        'show': True,
                        'show_order': 1,
                        'order': 1,
                        'type': 'string'
                    },
                    {
                        'name': 'test_spalte_2',
                        'anzeige': 'Test Spalte 2',
                        'display_show': True,
                        'display_order': 2,
                        'expert': False,
                        'show_show': True,
                        'show': True,
                        'show_order': 2,
                        'order': 2,
                        'type': 'string'
                    }
                ]
        
        # Test-Dialog erstellen
        dialog = PdvmSpaltenParameterDialog(
            parent=None,
            mode="normal",
            controls=MockControls(),
            provider=MockProvider(),
            daten_manager=MockManager(),
            user_guid="test-user-guid",
            view_config={'view_guid': 'test-view', 'stichtag': '2025216'}
        )
        
        logger.info("🔨 Dialog erstellt, teste Button-Verbindungen...")
        
        # Test: OK-Button Verbindung prüfen
        ok_button = dialog.btn_ok
        logger.info(f"🔨 OK-Button gefunden: {ok_button}")
        logger.info(f"🔨 OK-Button verbunden mit: {ok_button.receivers(ok_button.clicked)}")
        
        # Test: Cancel-Button Verbindung prüfen  
        cancel_button = dialog.btn_cancel
        logger.info(f"🔨 Cancel-Button gefunden: {cancel_button}")
        logger.info(f"🔨 Cancel-Button verbunden mit: {cancel_button.receivers(cancel_button.clicked)}")
        
        # Test: _apply_changes Methode prüfen
        if hasattr(dialog, '_apply_changes'):
            logger.info("✅ _apply_changes Methode vorhanden")
            
            # Direkt testen
            logger.info("🔨 Teste _apply_changes direkt...")
            try:
                dialog._apply_changes()
                logger.info("✅ _apply_changes lief ohne Fehler")
            except Exception as e:
                logger.error(f"❌ _apply_changes Fehler: {e}")
        else:
            logger.error("❌ _apply_changes Methode fehlt!")
        
        dialog.show()
        
        # Timer für automatisches Schließen
        QTimer.singleShot(5000, app.quit)
        
        logger.info("🔨 Starte Dialog-Test... (schließt automatisch nach 5 Sekunden)")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Dialog-Test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dialog_button_connections()
