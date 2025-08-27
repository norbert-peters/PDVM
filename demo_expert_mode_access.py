"""
Demo: Expert-Mode nur bei Admin-Modus

Zeigt den Unterschied zwischen mode='admin' und mode='user'
"""

import sys
sys.path.append('.')

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QPushButton
from pdvm_view_widget import PdvmViewWidget

def demo_admin_mode():
    """Demo mit Admin-Modus - Expert-Mode verfügbar"""
    call_daten_admin = {
        "view_guid": "test_view_guid",
        "user_guid": "test_user_guid", 
        "stichtag": 1001.0,
        "view_header": "Admin Demo - Expert-Mode verfügbar",
        "mode": "admin"  # Expert-Mode wird angezeigt
    }
    
    widget = PdvmViewWidget(call_daten=call_daten_admin)
    widget.setWindowTitle("Admin-Modus Demo")
    widget.show()
    return widget

def demo_user_mode():
    """Demo mit User-Modus - Expert-Mode nicht verfügbar"""
    call_daten_user = {
        "view_guid": "test_view_guid",
        "user_guid": "test_user_guid",
        "stichtag": 1001.0, 
        "view_header": "User Demo - Expert-Mode versteckt",
        "mode": "user"  # Expert-Mode wird NICHT angezeigt
    }
    
    widget = PdvmViewWidget(call_daten=call_daten_user)
    widget.setWindowTitle("User-Modus Demo")
    widget.show()
    return widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("🎯 Expert-Mode Demo")
    print("-------------------")
    print("🔧 Admin-Modus: Expert-Mode Menüpunkt verfügbar")
    print("👤 User-Modus: Expert-Mode Menüpunkt versteckt")
    
    # Beide Modi starten
    admin_widget = demo_admin_mode()
    user_widget = demo_user_mode()
    
    # Positionierung der Fenster
    admin_widget.setGeometry(100, 100, 600, 400)
    user_widget.setGeometry(750, 100, 600, 400)
    
    print("\n✅ Demo gestartet - prüfen Sie die Einstellungen-Menüs!")
    sys.exit(app.exec_())
