"""
PDVM Stichtag-Bar - Autonomes UI-Modul

ARCHITEKTUR:
- Vollständig autonom - holt GCS selbst
- render(container) fügt Widget zu Container hinzu
- Keine Rückgabewerte nötig
- Container wird vom Aufrufer bereitgestellt

VERWENDUNG:
    from pdvm_stichtag_bar import PdvmStichtagBar
    
    # Container bereitstellen
    stichtag_container = QWidget()
    
    # Autonomes Rendering
    PdvmStichtagBar.render(stichtag_container)
"""

import logging
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QFrame, QDateTimeEdit
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class PdvmStichtagBar:
    """
    Autonomer Stichtag-Balken für historische Datenansicht.
    
    Layout: 'Stichtag:' (PdvmDateTimePicker) → verwendeter Stichtag: (Display) [Refresh]
    """
    
    @staticmethod
    def render(container):
        """
        Rendert Stichtag-Bar autonom in Container.
        
        Args:
            container: QWidget Container für Stichtag-Bar
            
        Returns:
            None (Widget wird direkt zu Container hinzugefügt)
        """
        logger.info("🔧 PdvmStichtagBar.render() gestartet...")
        
        # GCS holen (autonom!)
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar - kann Stichtag-Bar nicht rendern")
            # Fehlermeldung in Container
            error_label = QLabel("❌ GCS nicht verfügbar")
            error_label.setStyleSheet("color: red; padding: 10px;")
            layout = QHBoxLayout(container)
            layout.addWidget(error_label)
            return
        
        logger.info("✅ GCS verfügbar")
        
        # Hauptcontainer-Style
        container.setFrameStyle(QFrame.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # Layout erstellen
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # "Stichtag:" Label
        stichtag_label = QLabel("Stichtag:")
        font = QFont()
        font.setBold(True)
        stichtag_label.setFont(font)
        layout.addWidget(stichtag_label)
        
        # PdvmDateTimePicker erstellen
        try:
            from pdvm_date_time_picker import PdvmDateTimePicker
            stichtag_picker = PdvmDateTimePicker(
                parent=container,
                pdvm_datetime=gcs.st_inst,  # GCS Stichtag-Instanz
                display="all",
                display_time_short=False
            )
            logger.info(f"✅ PdvmDateTimePicker erstellt")
            
            # Kalender-Widget größer machen
            if hasattr(stichtag_picker, '_date_edit'):
                calendar = stichtag_picker._date_edit.calendarWidget()
                if calendar:
                    calendar.setMinimumSize(350, 220)
            
            layout.addWidget(stichtag_picker)
            
        except ImportError:
            # Fallback: Standard QDateTimeEdit
            logger.warning("⚠️ PdvmDateTimePicker nicht verfügbar - verwende QDateTimeEdit")
            stichtag_picker = QDateTimeEdit()
            stichtag_picker.setDisplayFormat("dd.MM.yyyy - hh:mm:ss")
            stichtag_picker.setCalendarPopup(True)
            layout.addWidget(stichtag_picker)
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des DateTimePicker: {e}")
            error_label = QLabel(f"❌ DateTimePicker-Fehler: {e}")
            layout.addWidget(error_label)
            return
        
        # Pfeil "→"
        arrow_label = QLabel(" → ")
        arrow_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(arrow_label)
        
        # "verwendeter Stichtag:" Label
        verwendeter_label = QLabel("verwendeter Stichtag:")
        layout.addWidget(verwendeter_label)
        
        # Stichtag-Display (schreibgeschützt)
        stichtag_display = QLabel()
        stichtag_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 3px 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
            }
        """)
        
        # Stichtag-Wert anzeigen
        try:
            stichtag_value = gcs.st_inst
            if hasattr(stichtag_value, 'FormTimeStamp'):
                display_text = str(stichtag_value.FormTimeStamp)
            else:
                display_text = str(stichtag_value)
            stichtag_display.setText(display_text)
            logger.info(f"✅ Stichtag-Display: {display_text}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen des Stichtags: {e}")
            stichtag_display.setText("Fehler beim Laden")
        
        layout.addWidget(stichtag_display)
        
        # Refresh Button
        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        # Refresh-Callback (lambda mit GCS)
        def on_refresh():
            try:
                logger.info("🔄 Stichtag Refresh triggered")
                # Aktuellen Wert aus Picker holen
                if hasattr(stichtag_picker, 'get_pdvm_datetime'):
                    new_stichtag = stichtag_picker.get_pdvm_datetime()
                    gcs.st_inst.PdvmDateTime = new_stichtag.PdvmDateTime
                    logger.info(f"✅ Stichtag aktualisiert: {new_stichtag.FormTimeStamp}")
                    
                    # Display aktualisieren
                    stichtag_display.setText(new_stichtag.FormTimeStamp)
                    
                    # TODO: Trigger View-Refresh (Event-System?)
                    logger.info("📢 Stichtag-Refresh abgeschlossen - Views sollten aktualisiert werden")
                else:
                    logger.warning("⚠️ Picker hat keine get_pdvm_datetime() Methode")
            except Exception as e:
                logger.error(f"❌ Fehler beim Refresh: {e}")
        
        refresh_button.clicked.connect(on_refresh)
        layout.addWidget(refresh_button)
        
        # Stretch am Ende
        layout.addStretch(1)
        
        logger.info("✅ PdvmStichtagBar gerendert")
