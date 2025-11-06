"""
🎯 PDVM VIEW PIPELINE - VOLLSTÄNDIG GEKAPSELTE VIEW-VERWALTUNG
==============================================================

BENUTZER-ANFORDERUNG (15.10.2025):
"Projektierung in die View kapseln. Mit dem Setzen des Schnellsuche-Wertes auch kapseln.
Von außen nur Parent für View und Parent für Schnellsuche-Parameter.
Einfach machen und fixe Bereiche kapseln."

ARCHITEKTUR:
    View-Pipeline verwaltet ALLES:
    - Matrix-Pipeline (Daten)
    - View-Widget (UI)
    - Schnellsuche-Widget (UI)
    - Projektion (GCS)
    - Filter-Status (app_db)

AUFRUFE VON AUSSEN:
    # Initialisierung
    view_pipeline = get_view_pipeline(view_guid, matrix_manager)
    view_pipeline.initialize_view(parent_widget, schnellsuche_parent)
    
    # Schnellsuche aktivieren
    view_pipeline.set_schnellsuche('lau')
    
    # Filter zurücksetzen
    view_pipeline.reset_filters()
    
    # View refresh
    view_pipeline.refresh()

INTERN (AUTOMATISCH):
    1. Matrix-Pipeline läuft
    2. Projektion wird aus GCS geholt (Standard/Expert Mode)
    3. View wird mit projizierten Daten befüllt
    4. Schnellsuche-Feld wird aktualisiert
"""

import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QWidget, QLineEdit

# ========================================
# GLOBALER GCS-ZUGRIFF (ULTRA-EINFACH)
# ========================================
from pdvm_central_systemsteuerung import get_gcs as gcs
from pdvm_pipeline import get_pipeline

logger = logging.getLogger(__name__)


class PdvmViewPipeline:
    """
    Vollständig gekapselte View-Verwaltung
    
    Verwaltet:
    - Matrix-Pipeline (Datenverarbeitung)
    - View-Widget (Tabellenansicht)
    - Schnellsuche-Widget (Suchfeld)
    - Projektion (aus GCS)
    - Filter-Status (aus app_db)
    """
    
    def __init__(self, view_guid: str, matrix_manager):
        """
        Args:
            view_guid: Eindeutige View-GUID
            matrix_manager: Matrix Manager mit BasisMatrix
        """
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        self.gcs = gcs()
        
        # Matrix-Pipeline (Datenverarbeitung)
        self.matrix_pipeline = get_pipeline(view_guid, matrix_manager)
        
        # UI-Widgets (werden bei initialize_view gesetzt)
        self.view_widget = None  # Tabellenansicht
        self.schnellsuche_widget = None  # Suchfeld
        
        # Projektion (wird aus GCS geladen)
        self.projection_columns = []  # Sichtbare Spalten in Reihenfolge
        
        logger.info(f"🎯 ViewPipeline erstellt für View: {view_guid[:20]}...")
    
    # ============================================================
    # INITIALISIERUNG
    # ============================================================
    
    def initialize_view(self, view_parent: QWidget, schnellsuche_parent: QWidget = None):
        """
        View und Schnellsuche initialisieren
        
        Args:
            view_parent: Parent-Widget für Tabellenansicht
            schnellsuche_parent: Parent-Widget für Suchfeld (optional)
        """
        logger.info("🏗️ === VIEW INITIALISIERUNG ===")
        
        # 1. View-Widget erstellen (TODO: Implementierung)
        # self.view_widget = PdvmTableWidget(view_parent)
        logger.info("📊 View-Widget erstellt (TODO)")
        
        # 2. Schnellsuche-Widget erstellen (falls Parent vorhanden)
        if schnellsuche_parent:
            self.schnellsuche_widget = QLineEdit(schnellsuche_parent)
            self.schnellsuche_widget.setPlaceholderText("Schnellsuche...")
            # Signal verbinden
            self.schnellsuche_widget.textChanged.connect(self._on_schnellsuche_changed)
            logger.info("🔍 Schnellsuche-Widget erstellt")
        
        # 3. Projektion aus GCS laden
        self._load_projection()
        
        # 4. Matrix-Pipeline durchlaufen (kompletter Start)
        self.matrix_pipeline.run('BASIS')
        
        # 5. View aktualisieren
        self._refresh_view()
        
        logger.info("✅ View initialisiert")
    
    # ============================================================
    # PROJEKTION (AUS GCS)
    # ============================================================
    
    def _load_projection(self):
        """
        ✅ PROJEKTIONS-BASIERT: Projektion aus GCS-Array laden
        
        ARRAY-STRUKTUR in GCS._projection_tables[view_guid]:
        - Position [0]: View Standard (show=true, display_order)
        - Position [5]: View Expert (alle außer dummy+row_type, expert_order)
        
        DIREKTER ARRAY-ZUGRIFF über expert_mode aus GCS!
        """
        logger.info("📊 === PROJEKTION AUS GCS LADEN ===")
        
        try:
            # ✅ DIREKTER ARRAY-ZUGRIFF: Index 0 (Standard) oder 5 (Expert)
            expert_mode = self.gcs.expert_mode
            projection_index = 5 if expert_mode else 0
            
            logger.info(f"📋 Mode: {'ExpertMode' if expert_mode else 'StandardMode'} → Index [{projection_index}]")
            
            # Projektionstabelle aus GCS-Array holen
            projection = self.gcs.get_projection_table(self.view_guid, projection_index)
            
            if projection and isinstance(projection, list):
                self.projection_columns = projection
                logger.info(f"✅ Projektion [{projection_index}] geladen: {len(self.projection_columns)} Spalten")
            else:
                logger.warning(f"⚠️ Keine Projektion an Index [{projection_index}] - erstelle neu")
                self.gcs.rebuild_projection_tables(self.view_guid)
                projection = self.gcs.get_projection_table(self.view_guid, projection_index)
                self.projection_columns = projection if projection else []
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Projektion: {e}")
            self.projection_columns = []
    
    # ============================================================
    # SCHNELLSUCHE
    # ============================================================
    
    def set_schnellsuche(self, search_text: str):
        """
        Schnellsuche aktivieren - EINFACH!
        
        Args:
            search_text: Suchtext (z.B. "lau")
        """
        logger.info(f"🔍 === SCHNELLSUCHE: '{search_text}' ===")
        
        try:
            # 1. Parameter in app_db speichern
            self.gcs._app_db.set_value(self.view_guid, 's_string', search_text.strip())
            self.gcs._app_db.set_value(self.view_guid, 's_source', 'schnell')
            self.gcs._app_db.save_all_values()
            
            # 2. Matrix-Pipeline durchlaufen (ab FILTER)
            self.matrix_pipeline.run('FILTER')
            
            # 3. View aktualisieren
            self._refresh_view()
            
            logger.info("✅ Schnellsuche abgeschlossen")
        
        except Exception as e:
            logger.error(f"❌ Schnellsuche fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _on_schnellsuche_changed(self, text: str):
        """
        Event-Handler für Schnellsuche-Feld
        
        Args:
            text: Aktueller Text im Suchfeld
        """
        # Nur ausführen wenn Text nicht leer
        if text.strip():
            self.set_schnellsuche(text)
        else:
            self.reset_filters()
    
    # ============================================================
    # FILTER-VERWALTUNG
    # ============================================================
    
    def reset_filters(self):
        """
        Alle Filter zurücksetzen - EINFACH!
        """
        logger.info("🔄 === FILTER RESET ===")
        
        try:
            # 1. Parameter in app_db löschen
            self.gcs._app_db.set_value(self.view_guid, 's_string', None)
            self.gcs._app_db.set_value(self.view_guid, 's_source', None)
            self.gcs._app_db.save_all_values()
            
            # 2. Matrix-Pipeline durchlaufen (ab FILTER)
            self.matrix_pipeline.run('FILTER')
            
            # 3. View aktualisieren
            self._refresh_view()
            
            logger.info("✅ Filter zurückgesetzt")
        
        except Exception as e:
            logger.error(f"❌ Filter-Reset fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # ============================================================
    # VIEW-UPDATE (INTERN)
    # ============================================================
    
    def _refresh_view(self):
        """
        View mit Daten aus Matrix-Pipeline aktualisieren
        
        VOLLSTÄNDIG GEKAPSELT:
        - Holt projizierte Daten aus Matrix-Pipeline
        - Holt Suchtext für Schnellsuche-Feld
        - Verwendet Projektion aus GCS
        - Aktualisiert View-Widget
        - Aktualisiert Schnellsuche-Widget
        """
        logger.info("🎨 === VIEW UPDATE ===")
        
        try:
            # 1. Daten aus Matrix-Pipeline holen
            matrix_project, pipeline_columns = self.matrix_pipeline.get_projected_data()
            search_text = self.matrix_pipeline.get_search_text()
            
            logger.info(f"📊 Matrix: {len(matrix_project)} Zeilen")
            logger.info(f"📋 Pipeline-Spalten: {len(pipeline_columns)}")
            logger.info(f"📋 Projektions-Spalten: {len(self.projection_columns)}")
            logger.info(f"🔍 Suchtext: '{search_text}'" if search_text else "📋 Kein Suchtext")
            
            # 2. Spalten verwenden: Projektion aus GCS oder Fallback aus Pipeline
            visible_columns = self.projection_columns if self.projection_columns else pipeline_columns
            
            # 3. Schnellsuche-Feld aktualisieren
            if self.schnellsuche_widget:
                if search_text:
                    # Blockiere Signal während Aktualisierung
                    self.schnellsuche_widget.blockSignals(True)
                    self.schnellsuche_widget.setText(search_text)
                    self.schnellsuche_widget.blockSignals(False)
                else:
                    self.schnellsuche_widget.blockSignals(True)
                    self.schnellsuche_widget.clear()
                    self.schnellsuche_widget.blockSignals(False)
            
            # 4. View-Widget aktualisieren (TODO: Implementierung)
            # self.view_widget.set_data(matrix_project, visible_columns)
            logger.info(f"✅ View-Update: {len(matrix_project)} Zeilen, {len(visible_columns)} Spalten")
        
        except Exception as e:
            logger.error(f"❌ View-Update fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh(self):
        """
        Public Refresh-Methode (für externe Aufrufe)
        """
        self._refresh_view()


# ============================================================
# FACTORY FUNCTION
# ============================================================

_view_pipelines: Dict[str, PdvmViewPipeline] = {}


def get_view_pipeline(view_guid: str, matrix_manager) -> PdvmViewPipeline:
    """
    Factory-Funktion für View-Pipeline (Singleton pro View)
    
    Args:
        view_guid: Eindeutige View-GUID
        matrix_manager: Matrix Manager mit BasisMatrix
        
    Returns:
        PdvmViewPipeline-Instanz
    """
    if view_guid not in _view_pipelines:
        _view_pipelines[view_guid] = PdvmViewPipeline(view_guid, matrix_manager)
        logger.info(f"✅ View-Pipeline erstellt für View: {view_guid[:20]}...")
    
    return _view_pipelines[view_guid]


def reset_view_pipeline(view_guid: str):
    """
    View-Pipeline zurücksetzen (z.B. bei Stichtag-Wechsel)
    
    Args:
        view_guid: View-GUID
    """
    if view_guid in _view_pipelines:
        del _view_pipelines[view_guid]
        logger.info(f"♻️ View-Pipeline zurückgesetzt: {view_guid[:20]}...")
