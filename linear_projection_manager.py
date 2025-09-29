#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINEARER PROJECTION MANAGER

Einfache, lineare Lösung für alle Projektionsanforderungen:
1. Drei separate Tabellen: Table, Search, Management
2. Automatische Updates bei Mode-Wechsel
3. Direkte Persistierung in GCS
4. Keine komplexen Fallbacks

Architektur:
- Controls aus GCS laden
- Drei Projektions-Listen berechnen
- Bei Änderungen: Alle drei Listen neu berechnen und persistent speichern
- Direkte Instanz-Updates ohne Refresh
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LinearProjectionManager:
    """
    LINEARER PROJECTION MANAGER
    
    Verwaltet drei separate Projektions-Listen:
    - table_projection: Für View-Tabelle (nur sichtbare Spalten)
    - search_projection: Für Search-Panel (nur sichtbare Spalten)  
    - management_projection: Für Spalten-Verwaltung (alle Spalten)
    """
    
    def __init__(self, view_guid: str, gcs_instance):
        self.view_guid = view_guid
        self.gcs = gcs_instance
        
        # Drei separate Projektions-Listen
        self.table_projection: List[str] = []
        self.search_projection: List[str] = []
        self.management_projection: List[str] = []
        
        # Cache für Controls
        self._controls_cache: Dict[str, Dict] = {}
        
        logger.info(f"📊 LinearProjectionManager für View {view_guid} erstellt")
    
    def initialize(self, controls: Dict[str, Dict]):
        """
        INITIALISIERUNG MIT CONTROLS
        
        Args:
            controls: Controls-Dictionary aus GCS
        """
        logger.info(f"🔧 Initialisiere ProjectionManager mit {len(controls)} Controls")
        
        # WICHTIG: Debug-Ausgabe für alle Controls
        logger.info("🔍 DEBUG: Analysiere alle Controls...")
        show_true_count = 0
        expert_mode_false_count = 0
        both_conditions_count = 0
        
        # Erstmal die ersten 10 Controls im Detail analysieren
        control_list = list(controls.items())
        logger.info(f"🔍 DEBUG: Detailanalyse der ersten 10 von {len(control_list)} Controls:")
        
        for i, (control_name, control_data) in enumerate(control_list[:10]):
            show = control_data.get('show', False)
            expert_mode = control_data.get('expert_mode', None)  # None um zu sehen ob es fehlt
            expert_order = control_data.get('expertOrder', 999)
            display_order = control_data.get('displayOrder', 999)
            
            logger.info(f"  Control {i+1}: {control_name}")
            logger.info(f"    show: {show} (type: {type(show)})")
            logger.info(f"    expert_mode: {expert_mode} (type: {type(expert_mode)}, exists: {'expert_mode' in control_data})")
            logger.info(f"    expertOrder: {expert_order}")
            logger.info(f"    displayOrder: {display_order}")
        
        for control_name, control_data in controls.items():
            show = control_data.get('show', False)
            expert_mode = control_data.get('expert_mode', False)  # Default False!
            expert_order = control_data.get('expertOrder', 999)
            display_order = control_data.get('displayOrder', 999)
            
            if show:
                show_true_count += 1
            if not expert_mode:
                expert_mode_false_count += 1
            if show and not expert_mode:
                both_conditions_count += 1
                
            # Debug erste 10 Controls
            if len([c for c in controls.keys()]) <= 10:
                logger.info(f"  '{control_name}': show={show}, expert_mode={expert_mode}, expertOrder={expert_order}, displayOrder={display_order}")
        
        logger.info(f"📊 Controls-Analyse:")
        logger.info(f"  - Gesamt: {len(controls)}")
        logger.info(f"  - show=True: {show_true_count}")
        logger.info(f"  - expert_mode=False (oder nicht gesetzt): {expert_mode_false_count}")
        logger.info(f"  - show=True AND expert_mode=False: {both_conditions_count}")
        
        # Falls alle expert_mode=True sind oder expert_mode fehlt überall:
        if expert_mode_false_count == 0:
            logger.warning("⚠️ ALLE Spalten haben expert_mode=True oder expert_mode fehlt komplett!")
            logger.warning("⚠️ Setze alle Spalten auf expert_mode=False für Kompatibilität")
            
            # Kompatibilitäts-Fix: Alle auf expert_mode=False setzen
            for control_name, control_data in controls.items():
                if 'expert_mode' not in control_data:
                    control_data['expert_mode'] = False
                    logger.info(f"  Fix: '{control_name}' → expert_mode=False")
        
        # Controls cachen
        self._controls_cache = controls.copy()
        
        # Alle drei Projektionen berechnen und persistent speichern
        self._rebuild_all_projections()
        
        # ZUSÄTZLICHES DEBUG: Projektion-Ergebnisse
        logger.info(f"🎯 PROJEKTION-ERGEBNISSE:")
        logger.info(f"  📊 Table-Projection: {len(self._table_projection)} Spalten")
        logger.info(f"  🔍 Search-Projection: {len(self._search_projection)} Spalten")
        logger.info(f"  ⚙️ Management-Projection: {len(self._management_projection)} Spalten")
        
        if len(self._table_projection) > 0:
            logger.info(f"  📊 Table-Spalten: {[col['name'] for col in self._table_projection[:5]]}")
        else:
            logger.warning("⚠️ PROBLEM: Table-Projection ist leer!")
            
        if len(self._search_projection) > 0:
            logger.info(f"  🔍 Search-Spalten: {[col['name'] for col in self._search_projection[:5]]}")
        else:
            logger.warning("⚠️ PROBLEM: Search-Projection ist leer!")

        logger.info("✅ ProjectionManager initialisiert")
    
    def _rebuild_all_projections(self):
        """
        ALLE DREI PROJEKTIONEN NEU BERECHNEN
        
        Exakte Spezifikation mit Debug-Ausgaben:
        1. TABLE + SEARCH PROJECTION:
           - ExpertMode: Alle Spalten, sortiert nach expertOrder
           - StandardMode: Nur Spalten mit show=True UND expert_mode=False (oder expert_mode nicht gesetzt), sortiert nach displayOrder
        
        2. MANAGEMENT PROJECTION:
           - ExpertMode: Alle Spalten, sortiert nach expertOrder (zum Bearbeiten)
           - StandardMode: Nur Spalten mit expert_mode=False (oder expert_mode nicht gesetzt), sortiert nach displayOrder (zum Bearbeiten)
        """
        try:
            expert_mode = self.gcs.global_expert_mode
            logger.info(f"🔄 Baue alle Projektionen neu - ExpertMode: {expert_mode}")
            
            # Basis-Spalten aus Controls extrahieren mit Debug-Info
            basis_columns = []
            for control_name, control_data in self._controls_cache.items():
                column = {
                    'name': control_name,
                    'show': control_data.get('show', False),
                    'expert_mode': control_data.get('expert_mode', False),  # Default False für Kompatibilität
                    'expertOrder': control_data.get('expertOrder', 999),
                    'displayOrder': control_data.get('displayOrder', 999),
                    'spaltenueberschrift': control_data.get('spaltenueberschrift', control_name)
                }
                basis_columns.append(column)
                
                # Debug-Ausgabe für erste 3 Spalten
                if len(basis_columns) <= 3:
                    logger.info(f"  Debug Spalte '{control_name}': show={column['show']}, expert_mode={column['expert_mode']}, expertOrder={column['expertOrder']}, displayOrder={column['displayOrder']}")
            
            logger.info(f"📊 Gesamt {len(basis_columns)} Basis-Spalten geladen")
            
            # 1. TABLE PROJECTION
            if expert_mode:
                # ExpertMode: Alle Spalten nach expertOrder
                table_columns = sorted(basis_columns, key=lambda c: c['expertOrder'])
                logger.info(f"  TABLE (ExpertMode): Alle {len(table_columns)} Spalten nach expertOrder")
            else:
                # StandardMode: Nur show=True UND expert_mode=False (oder nicht gesetzt)
                filtered_columns = [col for col in basis_columns 
                                  if col['show'] and not col['expert_mode']]
                table_columns = sorted(filtered_columns, key=lambda c: c['displayOrder'])
                logger.info(f"  TABLE (StandardMode): {len(filtered_columns)} von {len(basis_columns)} Spalten (show=True AND expert_mode=False)")
                
                # Debug: Zeige gefilterte Spalten
                if len(filtered_columns) <= 5:
                    for col in filtered_columns:
                        logger.info(f"    → '{col['name']}': show={col['show']}, expert_mode={col['expert_mode']}")
            
            self.table_projection = [col['name'] for col in table_columns]
            
            # 2. SEARCH PROJECTION: Identisch mit Table
            self.search_projection = self.table_projection.copy()
            
            # 3. MANAGEMENT PROJECTION
            if expert_mode:
                # ExpertMode: Alle Spalten nach expertOrder (zum Bearbeiten aller)
                management_columns = sorted(basis_columns, key=lambda c: c['expertOrder'])
                logger.info(f"  MANAGEMENT (ExpertMode): Alle {len(management_columns)} Spalten nach expertOrder")
            else:
                # StandardMode: Nur expert_mode=False (oder nicht gesetzt) nach displayOrder
                filtered_columns = [col for col in basis_columns 
                                  if not col['expert_mode']]
                management_columns = sorted(filtered_columns, key=lambda c: c['displayOrder'])
                logger.info(f"  MANAGEMENT (StandardMode): {len(filtered_columns)} von {len(basis_columns)} Spalten (expert_mode=False)")
            
            self.management_projection = [col['name'] for col in management_columns]
            
            # Persistent speichern
            self._persist_projections()
            
            logger.info(f"✅ FINAL: Table={len(self.table_projection)}, Search={len(self.search_projection)}, Management={len(self.management_projection)}")
            if len(self.table_projection) <= 5:
                logger.info(f"   Table-Spalten: {self.table_projection}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuaufbau der Projektionen: {e}")
            raise
    
    def _persist_projections(self):
        """
        ALLE PROJEKTIONEN PERSISTENT SPEICHERN
        """
        try:
            # Drei separate Keys in GCS speichern
            self.gcs.db.set_value(self.view_guid, f"{self.view_guid}_table_projection", self.table_projection, ab_zeit=999999.0)
            self.gcs.db.set_value(self.view_guid, f"{self.view_guid}_search_projection", self.search_projection, ab_zeit=999999.0)
            self.gcs.db.set_value(self.view_guid, f"{self.view_guid}_management_projection", self.management_projection, ab_zeit=999999.0)
            
            logger.info("💾 Alle Projektionen persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Persistieren der Projektionen: {e}")
    
    def _load_projections(self):
        """
        PROJEKTIONEN AUS GCS LADEN
        
        Returns:
            bool: True wenn erfolgreich geladen
        """
        try:
            table_proj = self.gcs.db.get_value(self.view_guid, f"{self.view_guid}_table_projection")
            search_proj = self.gcs.db.get_value(self.view_guid, f"{self.view_guid}_search_projection")
            management_proj = self.gcs.db.get_value(self.view_guid, f"{self.view_guid}_management_projection")
            
            if table_proj and search_proj and management_proj:
                self.table_projection = table_proj
                self.search_projection = search_proj
                self.management_projection = management_proj
                
                logger.info("📂 Projektionen aus GCS geladen")
                return True
            else:
                logger.info("ℹ️ Keine gespeicherten Projektionen gefunden")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Projektionen: {e}")
            return False
    
    def update_controls(self, updated_controls: Dict[str, Dict]):
        """
        CONTROLS AKTUALISIEREN UND ALLE PROJEKTIONEN NEU BERECHNEN
        
        Args:
            updated_controls: Neue Controls (z.B. aus Spalten-Verwaltung)
        """
        logger.info(f"🔄 Aktualisiere Controls und alle Projektionen")
        
        # Controls-Cache aktualisieren
        self._controls_cache = updated_controls.copy()
        
        # Alle Projektionen neu berechnen
        self._rebuild_all_projections()
        
        logger.info("✅ Controls und Projektionen aktualisiert")
    
    def handle_expert_mode_change(self):
        """
        EXPERTMODE-WECHSEL BEHANDELN
        
        Berechnet alle Projektionen neu basierend auf neuem Modus
        """
        logger.info("🔄 ExpertMode-Wechsel - berechne alle Projektionen neu")
        
        # Alle Projektionen neu berechnen (verwendet aktuellen expert_mode aus GCS)
        self._rebuild_all_projections()
        
        logger.info("✅ Projektionen nach ExpertMode-Wechsel aktualisiert")
    
    # PUBLIC API: Einfacher Zugriff auf die drei Projektionen
    
    def get_table_projection(self) -> List[str]:
        """TABLE PROJECTION: Spaltennamen für View-Tabelle"""
        return self.table_projection.copy()
    
    def get_search_projection(self) -> List[str]:
        """SEARCH PROJECTION: Spaltennamen für Search-Panel"""
        return self.search_projection.copy()
    
    def get_management_projection(self) -> List[str]:
        """MANAGEMENT PROJECTION: Spaltennamen für Spalten-Verwaltung"""
        return self.management_projection.copy()
    
    def get_projection_summary(self) -> Dict[str, Any]:
        """DEBUGGING: Detaillierte Zusammenfassung aller Projektionen"""
        return {
            'expert_mode': self.gcs.global_expert_mode,
            'table': {
                'count': len(self.table_projection),
                'columns': self.table_projection[:5]  # Erste 5 für Debug
            },
            'search': {
                'count': len(self.search_projection),
                'columns': self.search_projection[:5]  # Erste 5 für Debug
            },
            'management': {
                'count': len(self.management_projection),
                'columns': self.management_projection[:5]  # Erste 5 für Debug
            },
            'logic': {
                'table_search': 'ExpertMode: alle nach expertOrder | StandardMode: show=True AND expert_mode=False nach displayOrder',
                'management': 'ExpertMode: alle nach expertOrder | StandardMode: expert_mode=False nach displayOrder'
            }
        }


# GLOBALER CACHE FÜR PROJECTION MANAGER
_projection_managers: Dict[str, LinearProjectionManager] = {}


def get_projection_manager(view_guid: str, gcs_instance) -> LinearProjectionManager:
    """
    GLOBALER ZUGRIFF AUF PROJECTION MANAGER
    
    Args:
        view_guid: GUID der View
        gcs_instance: GCS-Instanz
        
    Returns:
        LinearProjectionManager: Manager für die View
    """
    if view_guid not in _projection_managers:
        _projection_managers[view_guid] = LinearProjectionManager(view_guid, gcs_instance)
        logger.info(f"📝 Neuer ProjectionManager für View {view_guid} erstellt")
        
        # WICHTIG: Automatische Initialisierung mit Controls
        try:
            controls_config = gcs_instance.get_value(view_guid, "controls")
            if controls_config:
                logger.info(f"🔧 Initialisiere ProjectionManager automatisch mit {len(controls_config)} Controls")
                _projection_managers[view_guid].initialize(controls_config)
            else:
                logger.warning(f"⚠️ Keine Controls-Config für View {view_guid} gefunden!")
        except Exception as e:
            logger.error(f"❌ Fehler bei automatischer Initialisierung: {e}")
    
    return _projection_managers[view_guid]


def clear_projection_managers():
    """ALLE PROJECTION MANAGER LÖSCHEN (für Tests/Neustarts)"""
    global _projection_managers
    _projection_managers.clear()
    logger.info("🗑️ Alle ProjectionManager gelöscht")