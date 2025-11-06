#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM AUTONOME VIEW - Ultra-Einfach

EINZIGE ANFORDERUNG:
- view_guid → Alles andere kommt aus viewdaten-Tabelle in GCS
- parent → Wo die View angezeigt wird

KONZEPT:
Die View holt sich ALLES SELBST aus der Datenbank:
- ROOT.VIEW_TABLE → Welche Tabelle
- ROOT.STICHTAG → Zeitpunkt
- METADATEN.{TABLE}.controls → Spaltendefinitionen

KEINE call_daten, KEINE manuelle Konfiguration!

AUTOR: Norbert Peters  
DATUM: 26.10.2025 - AUTONOME VERSION
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmAutonomeView(QWidget):
    """
    ULTRA-EINFACHE AUTONOME VIEW
    
    Benötigt nur:
    - view_guid: GUID der View-Konfiguration
    - parent: Parent-Widget (optional)
    
    Holt alles andere selbst aus viewdaten-Tabelle!
    
    Signals:
    - row_selected(str): GUID der ausgewählten Zeile
    - row_double_clicked(str): GUID bei Doppelklick
    """
    
    # Signals
    row_selected = pyqtSignal(str)  # GUID der ausgewählten Zeile
    row_double_clicked = pyqtSignal(str)  # GUID bei Doppelklick
    
    def __init__(self, view_guid: str, parent: Optional[QWidget] = None):
        """
        Args:
            view_guid: GUID der View-Konfiguration (aus viewdaten-Tabelle)
            parent: Parent-Widget (optional)
        """
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht verfügbar!")
            QMessageBox.critical(self, "Fehler", "Systemsteuerung nicht verfügbar!")
            return
        
        # View-Konfiguration aus DB laden
        self.view_table = None
        self.controls = {}
        self.stichtag = None
        
        # View-Controller (wird erstellt)
        self.view_controller = None
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # View initialisieren
        self._initialize_view()
    
    def _initialize_view(self):
        """
        Initialisiert View AUTONOM aus viewdaten-Tabelle
        
        Ablauf:
        1. viewdaten-Tabelle öffnen
        2. ROOT.VIEW_TABLE holen
        3. ROOT.STICHTAG holen (oder GCS-Stichtag verwenden)
        4. METADATEN.{TABLE}.controls holen
        5. ViewDatenManager erstellen mit call_daten
        6. Widget vom Manager erstellen lassen
        """
        try:
            logger.info(f"🚀 === AUTONOME VIEW INITIALISIERUNG ===")
            logger.info(f"📋 View-GUID: {self.view_guid}")
            
            # [1] viewdaten-Tabelle öffnen (NEUE SIGNATUR!)
            view_db = PdvmCentralDatenbank(
                table_name='sys_viewdaten',
                guid=self.view_guid
            )
            
            # [2] ROOT.VIEW_TABLE holen
            self.view_table, _ = view_db.get_value('ROOT', 'VIEW_TABLE', self.gcs.stichtag)
            if not self.view_table:
                raise ValueError(f"VIEW_TABLE nicht gefunden für view_guid={self.view_guid}")
            
            logger.info(f"✅ VIEW_TABLE: {self.view_table}")
            
            # [3] STICHTAG holen (oder GCS-Stichtag verwenden)
            view_stichtag, _ = view_db.get_value('ROOT', 'STICHTAG', self.gcs.stichtag)
            self.stichtag = view_stichtag if view_stichtag else self.gcs.stichtag
            
            logger.info(f"📅 Stichtag: {self.stichtag}")
            
            # [4] METADATEN.{TABLE}.controls holen
            table_upper = self.view_table.upper()
            metadaten, _ = view_db.get_value('METADATEN', table_upper, self.stichtag)
            
            if not metadaten or 'controls' not in metadaten:
                raise ValueError(f"METADATEN.{table_upper}.controls nicht gefunden")
            
            self.controls = metadaten['controls']
            logger.info(f"✅ {len(self.controls)} Controls geladen: {list(self.controls.keys())}")
            
            # [5] call_daten für ViewController erstellen
            call_daten = {
                'view_guid': self.view_guid,
                'title': self.view_table.title() if self.view_table else 'View',
                'first_call': True
            }
            
            logger.info(f"✅ call_daten erstellt")
            
            # [6] ViewController erstellen (wie im generellen Dialog!)
            from pdvm_view_controller import V2PdvmViewController
            
            self.view_controller = V2PdvmViewController(
                call_daten=call_daten,
                parent=self
            )
            
            logger.info(f"✅ ViewController erstellt")
            
            # [7] ViewController initialisieren
            init_success = self.view_controller.initialize()
            
            if not init_success:
                raise RuntimeError("ViewController-Initialisierung fehlgeschlagen")
            
            # [8] Widget vom Controller holen
            view_widget = self.view_controller.get_widget()
            
            if not view_widget:
                raise RuntimeError("ViewDatenManager konnte kein Widget erstellen")
            
            # Widget in Layout einfügen
            self.layout().addWidget(view_widget)
            
            # Signals verbinden vom ViewController
            if hasattr(self.view_controller, 'row_double_clicked'):
                self.view_controller.row_double_clicked.connect(self._on_view_row_double_clicked)
                logger.info("  ✅ Signal 'row_double_clicked' verbunden")
            
            logger.info(f"✅ Autonome View initialisiert!")
            logger.info(f"   - Tabelle: {self.view_table}")
            logger.info(f"   - Controls: {len(self.controls)}")
            logger.info(f"   - Stichtag: {self.stichtag}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei View-Initialisierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fehler", 
                f"View konnte nicht initialisiert werden:\n{str(e)}")
    
    def _on_view_row_double_clicked(self, row_data: dict):
        """
        Handler für Doppelklick vom ViewController
        
        Args:
            row_data: Dict mit allen Feldern (3-Ebenen Arrays aus matrix_sort!)
        """
        try:
            # GUID aus row_data extrahieren (uid_original ist Array!)
            from pdvm_matrix_constants import get_wert
            
            guid = None
            
            # 1. PDVM-Standard: uid_original (ist ARRAY!)
            uid_cell = row_data.get('uid_original')
            if uid_cell:
                guid = get_wert(uid_cell) if isinstance(uid_cell, list) else uid_cell
                logger.debug(f"  ✅ uid_original gefunden: {guid[:20] if guid else 'None'}...")
            
            # 2. Fallback: Versuche GUID/UID Varianten (nur _original, NICHT _show!)
            if not guid:
                logger.debug(f"  ⚠️ uid_original nicht gefunden - probiere Fallbacks...")
                for key in ['guid_original', 'GUID_original', 'UID_original', 'id_original', 'ID_original']:
                    value = row_data.get(key)
                    if value:
                        guid = get_wert(value) if isinstance(value, list) else value
                        if guid:
                            logger.debug(f"  ✅ {key} gefunden: {guid[:20]}...")
                            break
            
            if guid:
                logger.info(f"👆 Doppelklick erkannt - GUID: {guid[:20] if len(str(guid)) > 20 else guid}...")
                self.row_double_clicked.emit(str(guid))
            else:
                logger.warning("⚠️ Keine GUID im row_data gefunden!")
                logger.warning(f"  Verfügbare Keys: {list(row_data.keys())[:10]}...")
                # Debug: Zeige uid_original falls vorhanden
                if 'uid_original' in row_data:
                    logger.warning(f"  uid_original Wert: {row_data['uid_original']}")
                if 'uid_show' in row_data:
                    logger.warning(f"  uid_show Wert: {row_data['uid_show']}")
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Doppelklick-Handler: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_selection_changed(self, selected, deselected):
        """Handler für Selection Changed"""
        try:
            if not self.view_controller:
                return
            
            # GUID aus ausgewählter Zeile holen
            # (ViewController managed die Selection intern)
            # Wir emittieren nur das Signal weiter
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Selection Changed: {e}")
    
    def _on_double_clicked(self, index):
        """Handler für Doppelklick"""
        try:
            # Wird über ViewController.row_double_clicked Signal gehandelt
            pass
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Doppelklick: {e}")
    
    def get_selected_guid(self) -> Optional[str]:
        """
        Holt GUID der aktuell ausgewählten Zeile
        
        Returns:
            str: GUID oder None wenn keine Auswahl
        """
        try:
            if not self.view_controller:
                logger.warning("⚠️ ViewController nicht verfügbar")
                return None
            
            # UI vom Controller holen
            if not hasattr(self.view_controller, 'ui') or not self.view_controller.ui:
                logger.warning("⚠️ UI nicht verfügbar")
                return None
            
            ui = self.view_controller.ui
            
            # Table-Widget vom UI holen
            if not hasattr(ui, 'table_widget') or not ui.table_widget:
                logger.warning("⚠️ Table-Widget nicht verfügbar")
                return None
            
            # Aktuell ausgewählte Zeile
            current_row = ui.table_widget.currentRow()
            
            if current_row < 0:
                logger.warning("⚠️ Keine Zeile ausgewählt (currentRow < 0)")
                return None
            
            # GUID aus matrix_sort holen (wie beim Doppelklick!)
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_controller.view_guid, self.view_controller.matrix_manager)
            
            # Finde die entsprechende Zeile in matrix_sort (ohne Gruppen-Header)
            data_row_index = 0
            for matrix_row in pipeline.matrix_sort:
                row_type = matrix_row.get('row_type')
                
                # Überspringe Gruppen-Header
                if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                    continue
                
                # Ist das die gesuchte Zeile?
                if data_row_index == current_row:
                    # GUID aus matrix_row extrahieren
                    from pdvm_matrix_constants import get_wert
                    
                    uid_cell = matrix_row.get('uid_original')
                    if uid_cell:
                        guid = get_wert(uid_cell) if isinstance(uid_cell, list) else uid_cell
                        logger.info(f"✅ Ausgewählte GUID: {guid[:20] if guid and len(str(guid)) > 20 else guid}...")
                        return str(guid) if guid else None
                    else:
                        logger.warning(f"⚠️ uid_original nicht in matrix_row gefunden!")
                        logger.warning(f"   Verfügbare Keys: {list(matrix_row.keys())[:10]}...")
                        return None
                
                data_row_index += 1
            
            logger.warning(f"⚠️ Zeile {current_row} nicht in matrix_sort gefunden!")
            return None
        
        except Exception as e:
            logger.error(f"❌ Fehler bei get_selected_guid: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def refresh(self):
        """View neu laden (z.B. nach Stichtag-Änderung)"""
        try:
            if self.view_controller:
                # ViewController neu laden
                # TODO: Refresh-Methode im ViewController prüfen
                logger.info("✅ View refresh requested")
        except Exception as e:
            logger.error(f"❌ Fehler bei Refresh: {e}")


# ============================================================================
# FACTORY FUNKTION (ULTRA-EINFACH)
# ============================================================================

def create_autonome_view(view_guid: str, parent: Optional[QWidget] = None) -> PdvmAutonomeView:
    """
    Erstellt autonome View - ULTRA-EINFACH!
    
    Args:
        view_guid: GUID der View-Konfiguration
        parent: Parent-Widget (optional)
        
    Returns:
        PdvmAutonomeView: Fertige View mit allen Features
        
    Example:
        >>> # Persondaten-View erstellen
        >>> view = create_autonome_view("0d10a0d0-b1a5-4544-b284-e8a09ca979b5")
        >>> 
        >>> # Signal verbinden
        >>> view.row_double_clicked.connect(lambda guid: print(f"Doppelklick: {guid}"))
        >>> 
        >>> # Ausgewählte GUID holen
        >>> selected = view.get_selected_guid()
    """
    return PdvmAutonomeView(view_guid, parent)
