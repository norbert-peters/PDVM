"""
PDVM Input-Control V2 - Autonom & Command-basiert

ARCHITEKTUR:
- Autonom: Jedes Control ist eigenständig
- Command-Pattern: Reagiert auf Kommandos (RENDER/SAVE/REFRESH)
- GCS-Integration: Verwendet direkt gcs.st_inst (Stichtag) und gcs Neues Abdatum

DESIGN-PRINZIPIEN:
1. Control kennt nur seine DB-Instanz (Referenz vom Manager)
2. GCS-Werte werden DIREKT verwendet (keine Zwischenspeicherung)
3. Abdatum-Instanz nur für ANZEIGE (wird mit jedem get_value neu gesetzt)
4. Keine Verschachtelungen, nur lineare Abläufe

READ-ONLY LOGIK (STRIKTE PRIORITÄT):
1. Keine DB-Instanz (db_instance=None) → IMMER Read-Only (HÖCHSTE PRIORITÄT!)
2. Explizites read_only=True aus Metadaten → Read-Only
3. Sonst → Editierbar

WICHTIG: Ohne gültige Instanz KANN nichts editierbar sein!

KOMMANDOS:
- render()   → Erstmaliges Laden + UI erstellen
- save()     → Speichern (wenn dirty) mit neuem Abdatum
- refresh()  → Neu laden + UI aktualisieren

AUTOR: Norbert Peters
DATUM: 22.10.2025
VERSION: 2.0 (Neu-Bau + Read-Only Logik)
"""

import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt

from global_gcs import gcs
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)


class PdvmInputControlV2(QWidget):
    """
    Autonomes Input-Control mit Command-Pattern
    
    VERANTWORTLICHKEITEN:
    - Wert aus DB-Instanz laden (mit GCS-Stichtag)
    - Wert anzeigen (mit Abdatum-Tooltip)
    - Änderungen tracken (is_dirty)
    - Wert speichern (mit GCS Neuem Abdatum)
    - UI aktualisieren (refresh)
    
    ABHÄNGIGKEITEN:
    - DB-Instanz (vom Manager übergeben)
    - GCS (für Stichtag + Neues Abdatum)
    """
    
    def __init__(self, 
                 instance_key: str,
                 db_instance,
                 gruppe: str,
                 feld: str,
                 label: str,
                 order: int = 0,
                 tab: str = "default",
                 tooltip: str = None,
                 read_only: bool = False,
                 historical: bool = False,  # NEU: Historical Flag
                 parent=None):
        """
        Args:
            instance_key: Schlüssel der DB-Instanz (z.B. "persondaten.guid1")
            db_instance: PdvmCentralDatenbank Instanz (vom Manager!)
            gruppe: DB-Gruppe (z.B. "PERSDATEN")
            feld: DB-Feld (z.B. "FAMILIENNAME")
            label: Anzeige-Label (z.B. "Familienname")
            order: Reihenfolge (für Sortierung)
            tab: Tab-Name (für Multi-Tab)
            tooltip: Tooltip-Text aus Metadaten (optional)
            read_only: Explizites Read-Only Flag aus Metadaten (überschreibt alles!)
            historical: Historical Flag aus Metadaten (für Historie-Button)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        # KONFIGURATION
        self.instance_key = instance_key
        self.db_instance = db_instance
        self.gruppe = gruppe.upper()
        self.feld = feld.upper()
        self.label_text = label
        self.order = order
        self.tab = tab
        self.meta_tooltip = tooltip
        self.read_only = read_only
        self.historical = historical  # NEU: Historical Flag speichern
        
        # AUTONOME ABDATUM-INSTANZ (nur für Anzeige!)
        self.abdatum_dt = Pdvm_DateTime(gcs.field_value('country'))
        
        # DATEN (aus DB)
        self.wert = None
        self.abdatum_wert = None  # Float aus get_value()
        
        # ZUSTAND
        self.original_value = None
        self.current_value = None
        self.is_dirty = False
        
        # UI-WIDGETS (werden bei render() erstellt)
        self.label_widget = None
        self.value_label = None
        self.edit_widget = None
        self.history_button = None  # NEU: Historie-Button
        
        logger.debug(f"  📦 Control erstellt: {self.label_text} (Order: {self.order}, Historical: {self.historical})")
    
    # =========================================================================
    # KOMMANDO: RENDER (Erstmaliges Laden + UI erstellen)
    # =========================================================================
    
    def render(self):
        """
        KOMMANDO: Wert laden + UI erstellen
        
        Wird vom Manager einmalig beim Initialisieren aufgerufen.
        
        ABLAUF:
        1. Wert aus DB laden (mit GCS-Stichtag)
        2. UI erstellen
        3. Wert anzeigen
        """
        logger.debug(f"  🎨 RENDER: {self.label_text}")
        
        # [1] Wert laden
        self._load_value_from_db()
        
        # [2] UI erstellen
        self._create_ui()
        
        # [3] Wert anzeigen
        self._update_ui()
    
    # =========================================================================
    # KOMMANDO: SAVE (Speichern wenn dirty)
    # =========================================================================
    
    def save(self, neues_abdatum: float) -> bool:
        """
        KOMMANDO: Wert speichern (wenn dirty)
        
        Args:
            neues_abdatum: Neues Abdatum (Float aus GCS!)
        
        Returns:
            True wenn gespeichert, False wenn nichts zu speichern
        """
        if not self.is_dirty:
            logger.debug(f"  ⏭️  SAVE (skipped): {self.label_text} - nicht dirty")
            return False
        
        if not self.db_instance:
            logger.warning(f"  ⚠️ SAVE (failed): {self.label_text} - keine DB-Instanz")
            return False
        
        try:
            logger.debug(f"  💾 SAVE: {self.label_text} = {self.current_value} (Abdatum: {neues_abdatum})")
            
            # Wert speichern (mit neuem Abdatum!)
            self.db_instance.set_value(
                self.gruppe,
                self.feld,
                self.current_value,
                neues_abdatum  # ← GCS-Wert!
            )
            
            # Original-Wert aktualisieren
            self.original_value = self.current_value
            self.is_dirty = False
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ SAVE (error): {self.label_text} - {e}")
            return False
    
    # =========================================================================
    # KOMMANDO: REFRESH (Neu laden + UI aktualisieren)
    # =========================================================================
    
    def refresh(self):
        """
        KOMMANDO: Wert neu laden + UI aktualisieren
        
        Wird vom Manager nach save_all_values() aufgerufen.
        
        ABLAUF:
        1. Wert aus DB neu laden (mit GCS-Stichtag)
        2. UI aktualisieren
        3. is_dirty zurücksetzen
        4. Styling zurücksetzen
        """
        logger.debug(f"  🔄 REFRESH: {self.label_text}")
        
        # [1] Wert neu laden
        self._load_value_from_db()
        
        # [2] UI aktualisieren
        self._update_ui()
        
        # [3] Zustand zurücksetzen
        self.is_dirty = False
        
        # [4] Styling zurücksetzen (wenn editierbar)
        if self.edit_widget and not self.edit_widget.isReadOnly():
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
    
    # =========================================================================
    # INTERNE METHODEN (Private)
    # =========================================================================
    
    def _open_history_dialog(self):
        """Öffnet Historie-Dialog (nur wenn historical=True und Instanz vorhanden)"""
        if not self.db_instance:
            logger.warning(f"  ⚠️ Historie-Dialog: Keine Instanz vorhanden für {self.label_text}")
            return
        
        logger.info(f"  📜 Öffne Historie-Dialog: {self.label_text}")
        
        try:
            from pdvm_input_control_history_dialog import PdvmInputControlHistoryDialog
            
            dialog = PdvmInputControlHistoryDialog(
                label=self.label_text,
                gruppe=self.gruppe,
                feld=self.feld,
                db_instance=self.db_instance,
                parent=self
            )
            
            dialog.exec_()  # Modal - blockiert bis geschlossen
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Öffnen des Historie-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _load_value_from_db(self):
        """
        Lädt Wert aus DB-Instanz mit GCS-Stichtag
        
        WICHTIG:
        - Verwendet DIREKT gcs.st_inst.PdvmDateTime (Stichtag)
        - get_value() gibt (wert, abdatum) zurück
        - abdatum ist das TATSÄCHLICHE Abdatum des Wertes aus DB
        - Abdatum-Instanz (self.abdatum_dt) wird für ANZEIGE aktualisiert
        """
        if not self.db_instance:
            logger.warning(f"  ⚠️ Keine DB-Instanz für {self.label_text}")
            self.wert = None
            self.abdatum_wert = None
            self.original_value = None
            self.current_value = None
            return
        
        try:
            # Stichtag DIREKT von GCS holen (SYSTEMWERT!)
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Wert laden (stichtagsgenau!)
            self.wert, self.abdatum_wert = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # Original-Werte speichern
            self.original_value = self.wert
            self.current_value = self.wert
            
            # Abdatum-Instanz für Anzeige aktualisieren
            if self.abdatum_wert:
                self.abdatum_dt.PdvmDateTime = float(self.abdatum_wert)
            
            logger.debug(f"    📊 Geladen: wert={str(self.wert)[:30]}, abdatum={self.abdatum_dt.FormTimeStamp if self.abdatum_wert else 'None'}")
            
        except Exception as e:
            logger.error(f"  ❌ Fehler beim Laden von {self.label_text}: {e}")
            self.wert = None
            self.abdatum_wert = None
            self.original_value = None
            self.current_value = None
    
    def _create_ui(self):
        """
        Erstellt UI-Widgets (einmalig bei render())
        
        Layout:
        [Label: Familienname] [QLineEdit (editierbar oder read-only)]
        
        Read-Only wenn (STRIKTE PRIORITÄT):
        1. Keine DB-Instanz vorhanden (db_instance ist None) → IMMER Read-Only!
        2. Explizites read_only=True aus Metadaten → Read-Only
        3. Sonst → Editierbar
        
        WICHTIG: Ohne Instanz KANN nichts editierbar sein!
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # === LABEL ===
        self.label_widget = QLabel(self.label_text + ":")
        self.label_widget.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                min-width: 150px;
                max-width: 150px;
            }
        """)
        layout.addWidget(self.label_widget)
        
        # === EDIT-WIDGET (QLineEdit) ===
        self.edit_widget = QLineEdit()
        
        # Read-Only Logik (STRIKTE PRIORITÄT: Instanz ZUERST!)
        if not self.db_instance:
            # KEINE INSTANZ → IMMER Read-Only (egal was in Metadaten steht!)
            is_readonly = True
            readonly_reason = "keine Instanz - GUID nicht gefunden"
        elif self.read_only:
            # Instanz vorhanden, aber explizit read_only
            is_readonly = True
            readonly_reason = "read_only=True in Metadaten"
        else:
            # Instanz vorhanden UND nicht explizit read_only → Editierbar
            is_readonly = False
            readonly_reason = None
        
        if is_readonly:
            self.edit_widget.setReadOnly(True)
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px;
                    color: #7f8c8d;
                }
            """)
            logger.debug(f"    🔒 {self.label_text}: Read-Only ({readonly_reason})")
        else:
            self.edit_widget.setReadOnly(False)
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
                QLineEdit:focus {
                    border: 2px solid #2980b9;
                }
            """)
            logger.debug(f"    ✏️ {self.label_text}: Editierbar")
        
        # Signal für Änderungen verbinden
        self.edit_widget.textChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.edit_widget, 1)  # Stretch
        
        # === HISTORIE-BUTTON (nur wenn historical=True) ===
        if self.historical:
            from PyQt5.QtWidgets import QPushButton
            self.history_button = QPushButton("📜")
            self.history_button.setToolTip("Historie anzeigen")
            self.history_button.setFixedSize(30, 30)
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
                QPushButton:disabled {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
            
            # Aktivierung: Nur wenn Instanz vorhanden
            self.history_button.setEnabled(self.db_instance is not None)
            
            # Signal verbinden
            self.history_button.clicked.connect(self._open_history_dialog)
            
            layout.addWidget(self.history_button)
            
            logger.debug(f"    📜 Historie-Button hinzugefügt (aktiv: {self.db_instance is not None})")
    
    def _on_value_changed(self, text):
        """Callback: Wert wurde geändert"""
        self.current_value = text
        self.is_dirty = (self.current_value != self.original_value)
        
        # Visuelles Feedback bei Änderung
        if self.is_dirty and not self.edit_widget.isReadOnly():
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
        elif not self.edit_widget.isReadOnly():
            self.edit_widget.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px;
                    color: #2c3e50;
                }
            """)
    
    def _update_ui(self):
        """
        Aktualisiert UI mit aktuellem Wert + Abdatum + Metadaten-Tooltip
        
        - Wert im QLineEdit
        - Tooltip mit:
          1. Abdatum
          2. Trennlinie
          3. Metadaten-Tooltip (falls vorhanden)
          4. Trennlinie
          5. Instanz-Info
        """
        if not self.edit_widget:
            return
        
        # Wert formatieren
        display_value = str(self.wert) if self.wert is not None else ""
        
        # QLineEdit aktualisieren (ohne Signal auszulösen)
        self.edit_widget.blockSignals(True)
        self.edit_widget.setText(display_value)
        self.edit_widget.blockSignals(False)
        
        # Tooltip zusammenbauen
        tooltip_parts = []
        
        # [1] Read-Only Status (STRIKTE PRIORITÄT: Instanz ZUERST!)
        if not self.db_instance:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (keine Instanz - GUID nicht gefunden)")
        elif self.read_only:
            tooltip_parts.append("🔒 SCHREIBGESCHÜTZT (read_only=True in Metadaten)")
        
        # [2] Abdatum
        if self.abdatum_wert:
            tooltip_parts.append(f"💾 Abdatum: {self.abdatum_dt.FormTimeStamp}")
        
        # [3] Metadaten-Tooltip (mit Trennlinien)
        if self.meta_tooltip:
            tooltip_parts.append("─" * 40)  # Trennlinie
            tooltip_parts.append(self.meta_tooltip)
            tooltip_parts.append("─" * 40)  # Trennlinie
        
        # [4] Instanz-Info
        tooltip_parts.append(f"📂 Instanz: {self.instance_key}")
        
        tooltip = "\n".join(tooltip_parts)
        self.edit_widget.setToolTip(tooltip)


# =============================================================================
# HELPER-FUNKTIONEN
# =============================================================================

def create_control_from_config(instance_key: str,
                                db_instance,
                                config: dict,
                                parent=None) -> PdvmInputControlV2:
    """
    Factory-Funktion: Erstellt Control aus Konfiguration
    
    Args:
        instance_key: Schlüssel der DB-Instanz
        db_instance: DB-Instanz (vom Manager)
        config: Konfiguration (aus Metadaten)
            {
                "gruppe": "PERSDATEN",
                "feld": "FAMILIENNAME",
                "label": "Familienname",
                "order": 1,
                "tab": "Hauptdaten",
                "field_config": {
                    "tooltip": "Bitte Familiennamen eingeben",
                    "read_only": false,
                    "historical": true,
                    ...
                }
            }
        parent: Parent-Widget
    
    Returns:
        PdvmInputControlV2 Instanz
    """
    # Tooltip + read_only + historical aus field_config extrahieren (falls vorhanden)
    field_config = config.get('field_config', {})
    if isinstance(field_config, dict):
        tooltip = field_config.get('tooltip', None)
        read_only = field_config.get('read_only', False)
        historical = field_config.get('historical', False)  # NEU!
    else:
        tooltip = None
        read_only = False
        historical = False
    
    return PdvmInputControlV2(
        instance_key=instance_key,
        db_instance=db_instance,
        gruppe=config.get('gruppe', ''),
        feld=config.get('feld', ''),
        label=config.get('label', config.get('feld', 'Unbekannt')),
        order=config.get('order', 0),
        tab=config.get('tab', 'default'),
        tooltip=tooltip,
        read_only=read_only,
        historical=historical,  # NEU!
        parent=parent
    )
