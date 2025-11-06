"""
PDVM Input-Control V4 - TYPE-BASIERTE ARCHITEKTUR

ARCHITEKTUR-PRINZIP:
- Control ist nur noch RAHMEN (Label, Historie-Button, Hilfe-Button)
- Eigentliche Input-Logik in autonomen Type-Klassen:
  * PdvmInputTypeText
  * PdvmInputTypeDatetime
  * PdvmInputTypeDropdown
  * ... weitere Types

CONTROL VERANTWORTLICHKEITEN:
- Instanz beschaffen (autonom)
- Type-Klasse instanziieren
- Layout mit Label + Type-Widget + Buttons
- Historie-Dialog öffnen
- Hilfe-Dialog öffnen

TYPE VERANTWORTLICHKEITEN:
- Widget erstellen
- Wert laden
- Wert anzeigen
- Dirty-Tracking
- Wert zurückgeben für save()

AUTOR: Norbert Peters
DATUM: 24.10.2025
VERSION: 4.0 (Type-basierte Architektur - EINFACH & LINEAR!)
"""

import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QDialog
from PyQt5.QtCore import Qt

from pdvm_central_systemsteuerung import get_gcs  # ✅ V2-Version!
from pdvm_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank  # ✅ V2-Version!

# Type-Klassen importieren (✅ V2-Versionen!)
from pdvm_input_type_text import PdvmInputTypeText
from pdvm_input_type_datetime import PdvmInputTypeDatetime
from pdvm_input_type_dropdown import PdvmInputTypeDropdown
from pdvm_input_type_viewtable import PdvmInputTypeViewtable

logger = logging.getLogger(__name__)


class PdvmInputControlV4(QWidget):
    """
    TYPE-BASIERTES Input-Control
    
    EINFACH & LINEAR:
    - Control = Rahmen (Label + Type-Widget + Buttons)
    - Type = Logik (laden/anzeigen/ändern/speichern)
    """
    
    # KLASSEN-CACHE für Instanzen
    _instance_cache = {}
    
    # TYPE-MAPPING
    TYPE_CLASSES = {
        'text': PdvmInputTypeText,
        'datetime': PdvmInputTypeDatetime,
        'dropdown': PdvmInputTypeDropdown,
        'viewtable': PdvmInputTypeViewtable,
    }
    
    def __init__(self, root_instance, meta: dict, manager=None, parent=None, gcs=None):
        super().__init__(parent)
        
        self.root_instance = root_instance
        self.manager = manager
        
        # ✅ V2: GCS holen (entweder als Parameter oder via get_gcs)
        self.gcs = gcs if gcs is not None else get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS nicht initialisiert!")
        
        # METADATEN
        self.field_key = meta.get('field_key', '')
        self.source_path = meta.get('source_path', 'root')
        self.label_text = meta.get('label', '')
        self.order = meta.get('order', 0)
        self.tab = meta.get('tab', 'default')
        
        # FIELD_CONFIG
        field_config = meta.get('field_config', {})
        if isinstance(field_config, dict):
            self.meta_tooltip = field_config.get('tooltip', None)
            self.read_only_meta = field_config.get('read_only', False)
            self.historical = field_config.get('historical', False)
            self.help_config = field_config.get('help_config', None)
            self.control_type = field_config.get('type', 'text')  # DEFAULT: text
            self.show_abdatum = field_config.get('abdatum', True)
            self.field_config = field_config
        else:
            self.meta_tooltip = None
            self.read_only_meta = False
            self.historical = False
            self.help_config = None
            self.control_type = 'text'
            self.show_abdatum = True
            self.field_config = {}
        
        # FIELD_KEY parsen
        field_parts = self.field_key.split('_')
        if len(field_parts) >= 3:
            self.tabelle = field_parts[0].upper()
            self.gruppe = field_parts[1].upper()
            self.feld = '_'.join(field_parts[2:]).upper()
        else:
            logger.error(f"❌ Ungültiger field_key: {self.field_key}")
            self.tabelle = ""
            self.gruppe = ""
            self.feld = ""
        
        # INSTANZ & READ-ONLY
        self.zugeordnete_instanz = None
        self.zugeordnete_guid = None
        self.read_only = False
        
        # ABDATUM für Tooltip
        self.abdatum_dt = Pdvm_DateTime(self.gcs.field_value('country'))
        self.abdatum_wert = None
        
        # TYPE-INSTANZ (wird in render() erstellt)
        self.input_type = None
        
        # HILFE-INSTANZ
        self.help_instance = None
        
        # UI-WIDGETS
        self.label_widget = None
        self.history_button = None
        self.help_button = None
        
        logger.debug(f"  📦 Control V4 erstellt: {self.label_text} (type: {self.control_type})")
    
    # =========================================================================
    # KOMMANDO: RENDER
    # =========================================================================
    
    def render(self):
        """
        KOMMANDO: Erstmaliges Laden + UI erstellen
        
        ABLAUF (LINEAR!):
        1. Instanz beschaffen
        2. Type-Klasse instanziieren
        3. Type: Wert laden
        4. UI erstellen (Label + Type-Widget + Buttons)
        5. Type: Display aktualisieren
        """
        logger.debug(f"  🎨 RENDER V4: {self.label_text}")
        
        # [1] INSTANZ BESCHAFFEN
        self._resolve_instance()
        
        # [2] TYPE-KLASSE INSTANZIIEREN
        self._create_input_type()
        
        # [3] TYPE: WERT LADEN
        if self.input_type:
            stichtag = self.gcs.st_inst.PdvmDateTime
            wert, self.abdatum_wert = self.input_type.load_value(stichtag)
            
            if self.abdatum_wert:
                self.abdatum_dt.PdvmDateTime = float(self.abdatum_wert)
        
        # [4] UI ERSTELLEN
        self._create_ui()
        
        # [5] TYPE: DISPLAY AKTUALISIEREN
        if self.input_type:
            self.input_type.update_display()
    
    # =========================================================================
    # KOMMANDO: REFRESH
    # =========================================================================
    
    def refresh(self):
        """
        KOMMANDO: Refresh nach Stichtag-Wechsel
        
        ABLAUF:
        1. Instanz NEU auflösen (GUID könnte sich geändert haben)
        2. Type: Wert NEU laden (mit aktuellem Stichtag)
        3. Type: Display aktualisieren
        
        WICHTIG: UI wird NICHT neu erstellt, nur Werte aktualisiert!
        WICHTIG: is_dirty wird NICHT zurückgesetzt (nur bei reset_dirty()!)
        """
        logger.info(f"  🔄 REFRESH V4: {self.label_text}")
        
        # DEBUG: Dirty-State VOR refresh
        if self.input_type:
            dirty_before = self.input_type.is_dirty()
            logger.info(f"    🔍 DEBUG VOR refresh: is_dirty={dirty_before}, type={type(self.input_type).__name__}")
        
        # [1] INSTANZ NEU BESCHAFFEN (GUID könnte sich geändert haben!)
        self._resolve_instance()
        
        # [2] TYPE: WERT NEU LADEN
        if self.input_type:
            stichtag = self.gcs.st_inst.PdvmDateTime
            wert, self.abdatum_wert = self.input_type.load_value(stichtag)
            
            if self.abdatum_wert:
                self.abdatum_dt.PdvmDateTime = float(self.abdatum_wert)
            
            # [3] TYPE: DISPLAY AKTUALISIEREN
            self.input_type.update_display()
            
            # DEBUG: Dirty-State NACH refresh
            dirty_after = self.input_type.is_dirty()
            logger.info(f"    🔍 DEBUG NACH refresh: is_dirty={dirty_after}")
            
            # [4] TOOLTIP AKTUALISIEREN
            if self.input_type.widget:
                self._set_widget_tooltip(self.input_type.widget)
    
    # =========================================================================
    # KOMMANDO: SAVE
    # =========================================================================
    
    def save(self, neues_abdatum: float) -> bool:
        """
        KOMMANDO: Wert speichern (wenn dirty)
        
        EINFACH: Type fragen ob dirty, dann Wert holen und speichern!
        """
        if not self.input_type:
            return False
        
        # [1] Type prüfen ob dirty
        if not self.input_type.is_dirty():
            logger.debug(f"  ⏭️  SAVE (skipped): {self.label_text} - nicht dirty")
            return False
        
        # [2] Keine Instanz? Fehler!
        if not self.zugeordnete_instanz:
            logger.warning(f"  ⚠️ SAVE (failed): {self.label_text} - keine Instanz")
            return False
        
        try:
            # [3] Wert vom Type holen
            current_value = self.input_type.get_current_value()
            
            # [4] Abdatum bestimmen
            if not self.show_abdatum and self.abdatum_wert:
                save_abdatum = self.abdatum_wert  # Altes Abdatum
                logger.info(f"  💾 SAVE (ohne neue Historie): {self.label_text}")
            else:
                save_abdatum = neues_abdatum  # Neues Abdatum
                logger.info(f"  💾 SAVE (mit Historie): {self.label_text}")
            
            logger.info(f"      Wert: {str(current_value)[:50]}")
            
            # [5] In DB speichern
            self.zugeordnete_instanz.set_value(
                self.gruppe,
                self.feld,
                current_value,
                save_abdatum
            )
            
            logger.info(f"  ✅ SAVE erfolgreich: {self.label_text}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ SAVE-Fehler: {self.label_text} - {e}")
            return False
    
    # =========================================================================
    # INSTANZ-BESCHAFFUNG (wie V3 - unverändert)
    # =========================================================================
    
    def _resolve_instance(self):
        """Beschafft zugeordnete Instanz (autonom)"""
        if self.source_path == 'root':
            self.zugeordnete_instanz = self.root_instance
            self.zugeordnete_guid = self.root_instance.guid
            self.read_only = self.read_only_meta
            return
        
        # Verschachtelt
        if '_' in self.source_path:
            source_gruppe = self.source_path.split('_')[1].upper()
        else:
            logger.error(f"    ❌ Ungültiger source_path: {self.source_path}")
            self.zugeordnete_instanz = None
            self.read_only = True
            return
        
        zuordnungsfeld = f"{self.tabelle}-{self.gruppe}"
        stichtag = self.gcs.st_inst.PdvmDateTime
        
        try:
            result = self.root_instance.get_value(source_gruppe, zuordnungsfeld, stichtag)
            guid = result[0] if isinstance(result, tuple) else result
        except Exception as e:
            logger.error(f"    ❌ GUID-Abruf-Fehler: {e}")
            guid = None
        
        if not guid or guid == "":
            self.zugeordnete_instanz = None
            self.zugeordnete_guid = None
            self.read_only = True
            return
        
        self.zugeordnete_guid = guid
        self.zugeordnete_instanz = self._get_or_create_instance(self.tabelle, guid)
        self.read_only = self.read_only_meta
    
    def _get_or_create_instance(self, tabelle: str, guid: str):
        """Holt Instanz aus Cache oder erstellt neue"""
        cache_key = (tabelle.upper(), guid)
        
        if cache_key in self._instance_cache:
            return self._instance_cache[cache_key]
        
        instance = PdvmCentralDatenbank(tabelle, guid)
        self._instance_cache[cache_key] = instance
        return instance
    
    @classmethod
    def clear_instance_cache(cls):
        """Leert Instanz-Cache"""
        cls._instance_cache.clear()
        logger.info("🗑️ Instanz-Cache geleert")
    
    # =========================================================================
    # TYPE-ERSTELLUNG
    # =========================================================================
    
    def _create_input_type(self):
        """
        Erstellt Type-Instanz basierend auf control_type
        
        EINFACH: Type aus TYPE_CLASSES holen und instanziieren!
        """
        type_class = self.TYPE_CLASSES.get(self.control_type, PdvmInputTypeText)
        
        control_config = {
            'db_instance': self.zugeordnete_instanz,
            'gruppe': self.gruppe,
            'feld': self.feld,
            'read_only': self.read_only,
            'field_config': self.field_config
        }
        
        try:
            self.input_type = type_class(self, control_config)
            logger.debug(f"    ✨ Type erstellt: {type_class.__name__}")
        except Exception as e:
            logger.error(f"    ❌ Type-Erstellungs-Fehler: {e}")
            # Fallback auf Text
            self.input_type = PdvmInputTypeText(self, control_config)
    
    # =========================================================================
    # UI ERSTELLEN
    # =========================================================================
    
    def _create_ui(self):
        """
        Erstellt UI-Layout
        
        Layout: [Label 150px] [Widget var] [Spacer inkl. 10px] [Buttons] [Stretch]
        
        WICHTIG: Spacer beinhaltet Abstand zu Buttons!
        Buttons stehen bei fester Position (150 + 10 + 400 + 10 = 570px)
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(0)  # KEIN automatisches Spacing! Wir steuern alles manuell!
        
        # DEBUG: Logging der Layout-Berechnung
        logger.debug(f"🎨 Layout-Aufbau für: {self.label_text}")
        
        # [1] LABEL (fixe Breite 150px)
        self.label_widget = QLabel(self.label_text)
        self.label_widget.setFixedWidth(150)
        self.label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        layout.addWidget(self.label_widget)
        logger.debug(f"    📍 Label: 150px")
        
        # Manueller Abstand nach Label (10px)
        layout.addSpacing(10)
        logger.debug(f"    📍 Spacing nach Label: 10px")
        
        # [2] TYPE-WIDGET (variable Breite, max 400px)
        widget_target_width = 400  # Default
        if self.input_type:
            type_widget = self.input_type.create_widget()
            if type_widget:
                layout.addWidget(type_widget)
                self._set_widget_tooltip(type_widget)
                
                # Ziel-Breite vom Type holen
                widget_target_width = self.input_type.get_target_width()
                logger.debug(f"    📍 Widget: {widget_target_width}px (Type: {type(self.input_type).__name__})")
        
        # [3] SPACER - Gleicht Widget auf 400px aus + 10px Abstand zu Buttons
        # Damit Buttons IMMER bei gleicher Position (150 + 10 + 400 + 10 = 570px)
        spacer_width = (400 - widget_target_width) + 10
        logger.debug(f"    📍 Spacer: {spacer_width}px (gleicht {widget_target_width}px auf 400px aus + 10px Abstand)")
        
        if spacer_width > 0:
            layout.addSpacing(spacer_width)
        
        logger.debug(f"    📍 Buttons-Position: {150 + 10 + 400 + 10}px")
        
        # [4] HILFE-BUTTON (kommt ZUERST - ist immer da)
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(30, 30)
        self.help_button.setToolTip("Hilfe anzeigen (noch nicht implementiert)")
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        # Aktivieren wenn help_config vorhanden
        if self.help_config:
            self.help_button.clicked.connect(self._open_help_dialog)
        else:
            self.help_button.setEnabled(False)
        layout.addWidget(self.help_button)
        
        # [5] HISTORIE-BUTTON (kommt DANACH - nur bei Bedarf)
        if self.historical and self.show_abdatum:
            layout.addSpacing(5)  # 5px zwischen Buttons
            self.history_button = QPushButton("📜")
            self.history_button.setFixedSize(30, 30)
            self.history_button.setToolTip("Historie anzeigen")
            self.history_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 14pt;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            self.history_button.setEnabled(self.zugeordnete_instanz is not None)
            self.history_button.clicked.connect(self._open_history_dialog)
            layout.addWidget(self.history_button)
        
        # [6] FLEXIBLER STRETCH - Rest nach rechts
        layout.addStretch(1)
        
        self.setLayout(layout)
    
    def _set_widget_tooltip(self, widget):
        """Setzt Tooltip auf Type-Widget"""
        tooltip_parts = []
        
        if not self.zugeordnete_instanz:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (keine Instanz)")
        elif self.read_only:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (read_only=True)")
        
        if self.abdatum_wert and self.show_abdatum:
            tooltip_parts.append(f"💾 Abdatum: {self.abdatum_dt.FormTimeStamp}")
        
        if self.meta_tooltip:
            tooltip_parts.append("─" * 40)
            tooltip_parts.append(self.meta_tooltip)
        
        if tooltip_parts:
            widget.setToolTip("\n".join(tooltip_parts))
    
    # =========================================================================
    # DIALOGE
    # =========================================================================
    
    def _open_history_dialog(self):
        """Öffnet Historie-Dialog"""
        if not self.zugeordnete_instanz:
            logger.warning("  ⚠️ Historie-Dialog: Keine Instanz vorhanden")
            return
        
        try:
            # Historie-Dialog V2 (finale Version für alle Types)
            from pdvm_input_control_history_dialog import PdvmInputControlHistoryDialog
            dialog_class = PdvmInputControlHistoryDialog
            logger.info(f"  📜 Verwende Historie-Dialog für Type: {self.control_type}")
            
            # display_val aus field_config extrahieren (für DateTime)
            display_val = self.field_config.get('display_val', 'all') if self.field_config else 'all'
            
            dialog = dialog_class(
                label=self.label_text,
                gruppe=self.gruppe,
                feld=self.feld,
                db_instance=self.zugeordnete_instanz,
                control_type=self.control_type,
                display_val=display_val,
                field_config=self.field_config,
                parent=self
            )
            
            result = dialog.exec_()
            
            # Refresh nach Dialog-Schließen (wenn geändert wurde)
            if result == QDialog.Accepted:
                logger.info("  ✅ Historie-Dialog geschlossen mit Änderungen")
                
                # EINFACH: Dialog-Refresh aufrufen (wenn in Dialog-Kontext)
                # Das ist der gleiche Mechanismus wie beim Speichern im Dialog!
                if hasattr(self, 'parent') and self.parent():
                    parent = self.parent()
                    # Prüfe ob Parent ein Dialog mit refresh() ist
                    while parent:
                        if hasattr(parent, 'refresh') and callable(parent.refresh):
                            logger.info("  🔄 Trigger Dialog-Refresh (wie nach Speichern)")
                            parent.refresh()
                            break
                        parent = parent.parent() if hasattr(parent, 'parent') else None
                else:
                    logger.info("  ℹ️ Kein Parent-Dialog gefunden - kein Refresh")
            
        except Exception as e:
            logger.error(f"  ❌ Historie-Dialog-Fehler: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _open_help_dialog(self):
        """Öffnet Hilfe-Dialog mit Instanz-basierten Hilfedaten"""
        if not self.help_config:
            logger.warning(f"  ⚠️ Keine Hilfe-Konfiguration für: {self.label_text}")
            return
        
        logger.info(f"  ❓ Öffne Hilfe: {self.label_text}")
        
        try:
            # [1] Hilfe-Instanz lazy erstellen
            if not self.help_instance:
                table = self.help_config.get('table')
                guid = self.help_config.get('key')
                
                if not table or not guid:
                    logger.error(f"  ❌ Ungültige help_config: {self.help_config}")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self, 
                        "Fehler", 
                        "Hilfe-Konfiguration ungültig."
                    )
                    return
                
                # Instance-Key für Cache
                cache_key = (table.upper(), guid)
                
                # Aus Cache holen oder neu erstellen
                if cache_key in self._instance_cache:
                    self.help_instance = self._instance_cache[cache_key]
                    logger.info(f"  📂 Hilfe-Instanz aus Cache: {table}.{guid[:8]}...")
                else:
                    logger.info(f"  🔧 Erstelle Hilfe-Instanz: {table}.{guid[:8]}...")
                    self.help_instance = PdvmCentralDatenbank(table, guid)
                    self._instance_cache[cache_key] = self.help_instance
            
            # [2] Hilfe-Daten laden
            field_name = self.help_config.get('value')
            if not field_name:
                logger.error(f"  ❌ Kein Feldname in help_config: {self.help_config}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, 
                    "Fehler", 
                    "Hilfe-Feldname fehlt in Konfiguration."
                )
                return
            
            # Hilfe-Daten aus ROOT-Gruppe laden (value = kompletter Feldname)
            logger.info(f"  📖 Lade Hilfedaten: ROOT.{field_name}")
            help_data = self.help_instance.get_static_value('ROOT', field_name)
            
            if not help_data:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "Keine Hilfe", 
                    f"Keine Hilfedaten für '{self.label_text}' verfügbar."
                )
                logger.warning(f"  ⚠️ Keine Hilfedaten gefunden")
                return
            
            # [3] Header und Text extrahieren
            header = help_data.get('header', 'Hilfe')
            text = help_data.get('text', 'Keine Hilfeinformationen verfügbar.')
            
            logger.info(f"  ✅ Hilfedaten geladen: {header}")
            
            # [4] Hilfe-Dialog anzeigen
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(header)
            msg_box.setText(text)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Styling für bessere Lesbarkeit
            msg_box.setStyleSheet("""
                QMessageBox {
                    min-width: 400px;
                }
                QMessageBox QLabel {
                    min-height: 100px;
                    font-size: 11pt;
                }
            """)
            
            msg_box.exec_()
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Öffnen des Hilfe-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Fehler beim Laden der Hilfe:\n{str(e)}"
            )
    
    def _init_help_instance(self):
        """Initialisiert Hilfe-Instanz (DEPRECATED - wird jetzt lazy in _open_help_dialog erstellt)"""
        pass

