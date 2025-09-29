"""
EINFACHER PROJEKTIONS-MANAGER
============================

Grundidee:
- Drei separate, kleine Tabellen mit nur keys
- Keine komplexe Logik - nur Listen verwalten
- Übersichtlich und robust

Tabellen:
1. table_projection: [key1, key2, key3] - Was in der Tabelle angezeigt wird
2. search_projection: [key1, key2] - Was durchsuchbar ist  
3. management_projection: [key1, key2, key3, key4] - Was konfigurierbar ist

Logik:
- StandardMode: Nur Controls mit expert_mode=False oder None
- ExpertMode: Alle Controls
"""

import logging
from global_gcs import gcs
logger = logging.getLogger(__name__)

class SimpleProjectionManager:
    """Verwaltet 6 separate Projektions-Tabellen für Standard/Expert Modi"""
    
    def __init__(self, view_guid):
        self.view_guid = view_guid
        
        # 6 separate Projektions-Tabellen für Standard/Expert Modi
        self.table_projection_standard = []      # Tabellen-Anzeige Standard
        self.table_projection_expert = []        # Tabellen-Anzeige Expert
        self.search_projection_standard = []     # Such-Panel Standard  
        self.search_projection_expert = []       # Such-Panel Expert
        self.management_projection_standard = [] # Spalten-Management Standard
        self.management_projection_expert = []   # Spalten-Management Expert
        
        # Controls-Daten (werden nur zum Filtern verwendet)
        self.controls = {}
        
        logger.info(f"📊 SimpleProjectionManager für View {view_guid} erstellt")
    
    def initialize(self, controls_config):
        """Initialisierung mit Controls-Konfiguration"""
        self.controls = controls_config
        logger.info(f"🔧 Initialisiere mit {len(controls_config)} Controls")
        
        # Lade bestehende Projektionen oder erstelle neue
        self._load_or_create_projections()
        
    def _load_or_create_projections(self):
        """Lädt existierende Projektionen oder erstellt neue."""
        # Lade einzelne Projektionen direkt
        try:
            table_std = gcs.db.get_value(self.view_guid, "table_projection_standard")
            table_exp = gcs.db.get_value(self.view_guid, "table_projection_expert")
            search_std = gcs.db.get_value(self.view_guid, "search_projection_standard")
            search_exp = gcs.db.get_value(self.view_guid, "search_projection_expert")
            mgmt_std = gcs.db.get_value(self.view_guid, "management_projection_standard")
            mgmt_exp = gcs.db.get_value(self.view_guid, "management_projection_expert")
            
            # Wenn alle vorhanden sind, lade sie
            if table_std and table_exp and search_std and search_exp and mgmt_std and mgmt_exp:
                self.table_projection_standard = table_std
                self.search_projection_standard = search_std  
                self.management_projection_standard = mgmt_std
                self.table_projection_expert = table_exp
                self.search_projection_expert = search_exp
                self.management_projection_expert = mgmt_exp
                
                # Prüfe ob ExpertMode-Projektionen korrekt sind (beide original + show Controls)
                if self.table_projection_expert:
                    original_count = sum(1 for key in self.table_projection_expert if key.endswith('_original'))
                    show_count = sum(1 for key in self.table_projection_expert if key.endswith('_show'))
                    
                    # Falls ExpertMode unvollständig ist, neu erstellen
                    if original_count == 0 or show_count == 0:
                        logger.info("🔄 ExpertMode-Projektionen unvollständig, erstelle neu")
                        self._create_default_projections()
                        self._save_projections()
                        return
                        
                logger.info("📋 Bestehende Projektionen geladen")
                return
        except Exception as e:
            logger.info(f"⚠️ Fehler beim Laden der Projektionen: {e}")

        # Keine existierenden Projektionen gefunden, erstelle neue
        logger.info("🎯 Erstelle neue Projektionen")
        self._create_default_projections()
        self._save_projections()
    
    def _create_default_projections(self):
        """Erstelle alle 6 Standard-Projektionen für beide Modi"""
        logger.info(f"🎯 Erstelle alle 6 Projektions-Tabellen")
        
        # Erstelle Projektionen für StandardMode
        self._create_standard_projections()
        
        # Erstelle Projektionen für ExpertMode  
        self._create_expert_projections()
        
        # Debug: Sofortige Ausgabe der erstellten Projektionen
        logger.info(f"🔍 INIT: Standard Table ({len(self.table_projection_standard)}): {self.table_projection_standard[:5]}...")
        logger.info(f"🔍 INIT: Expert Table ({len(self.table_projection_expert)}): {self.table_projection_expert[:5]}...")
        
        logger.info(f"✅ Alle 6 Projektions-Tabellen erstellt")
    
    def _create_standard_projections(self):
        """Erstelle Projektionen für StandardMode"""
        logger.info(f"⭐⭐⭐ STANDARD-PROJEKTIONEN WERDEN ERSTELLT ⭐⭐⭐")
        
        # TABLE PROJECTION: Nur Controls mit show=True und NICHT expert_mode
        table_projection = []
        for key, config in self.controls.items():
            if key.endswith('_show'):
                show_value = config.get('show', False)
                is_expert_control = config.get('expert_mode', False)
                
                # StandardMode: Nur Controls mit show=True und NICHT expert_mode
                if show_value and not is_expert_control:
                    table_projection.append(key)
        
        # SEARCH PROJECTION: Identisch zur Table-Projektion
        search_projection = table_projection.copy()
        
        # MANAGEMENT PROJECTION: Alle Show-Controls für Konfiguration (außer dummy)
        management_projection = []
        for key, config in self.controls.items():
            if key.endswith('_show') and key != 'dummy_show':
                management_projection.append(key)
        
        # Weise den Standard-Tabellen zu
        self.table_projection_standard = table_projection
        self.search_projection_standard = search_projection
        self.management_projection_standard = management_projection
        
        logger.info(f"✅ StandardMode Projektionen erstellt:")
        logger.info(f"  📋 Table: {len(table_projection)} Keys")
        logger.info(f"  🔍 Search: {len(search_projection)} Keys") 
        logger.info(f"  ⚙️ Management: {len(management_projection)} Keys")
    
    def _create_expert_projections(self):
        """Erstelle Projektionen für ExpertMode"""
        logger.info(f"�🚀🚀 EXPERT-PROJEKTIONEN WERDEN ERSTELLT 🚀🚀🚀")
        
        # Debug: Alle verfügbaren Controls anzeigen
        original_controls = [k for k in self.controls.keys() if k.endswith('_original')]
        show_controls = [k for k in self.controls.keys() if k.endswith('_show')]
        logger.info(f"🔍 Verfügbare Controls: {len(original_controls)} original, {len(show_controls)} show")
        logger.info(f"🔍 Original Controls: {original_controls[:5]}...")
        logger.info(f"🔍 Show Controls: {show_controls[:5]}...")
        
        # TABLE PROJECTION: ALLE Spalten (original + show) außer dummy, sortiert nach expert_order
        table_projection = []
        for key, config in self.controls.items():
            # ExpertMode: Alle Original- UND Show-Controls (außer dummy)
            if (key.endswith('_original') or key.endswith('_show')) and not key.startswith('dummy'):
                table_projection.append((key, config.get('expert_order', 999)))
        
        # Sortiere nach expert_order
        table_projection.sort(key=lambda x: x[1])
        table_projection = [key for key, _ in table_projection]
        
        # SEARCH PROJECTION: Identisch zur Table-Projektion  
        search_projection = table_projection.copy()
        
        # MANAGEMENT PROJECTION: Alle Show-Controls für Konfiguration (außer dummy)
        management_projection = []
        for key, config in self.controls.items():
            if key.endswith('_show') and key != 'dummy_show':
                management_projection.append((key, config.get('expert_order', 999)))
        
        # Sortiere Management auch nach expert_order
        management_projection.sort(key=lambda x: x[1])
        management_projection = [key for key, _ in management_projection]
        
        # Weise den Expert-Tabellen zu
        self.table_projection_expert = table_projection
        self.search_projection_expert = search_projection
        self.management_projection_expert = management_projection
        
        # Debug-Ausgabe für ExpertMode-Projektionen
        logger.info(f"🎯🎯🎯 EXPERT TABLE PROJECTION: {len(table_projection)} Spalten")
        logger.info(f"� EXPERT ORIGINAL CONTROLS: {[k for k in table_projection if k.endswith('_original')]}")
        logger.info(f"� EXPERT SHOW CONTROLS: {[k for k in table_projection if k.endswith('_show')]}")
        logger.info(f"🎯🎯🎯 VOLLSTÄNDIGE EXPERT PROJECTION: {table_projection}")
        
        logger.info(f"✅ ExpertMode Projektionen erstellt:")
        logger.info(f"  📋 Table: {len(table_projection)} Keys (alle original + show)")
        logger.info(f"  🔍 Search: {len(search_projection)} Keys") 
        logger.info(f"  ⚙️ Management: {len(management_projection)} Keys")
    
    def _save_projections(self):
        """Speichere alle 6 Projektions-Tabellen in GCS"""
        try:
            gcs.db.set_value(self.view_guid, "table_projection_standard", self.table_projection_standard)
            gcs.db.set_value(self.view_guid, "table_projection_expert", self.table_projection_expert)
            gcs.db.set_value(self.view_guid, "search_projection_standard", self.search_projection_standard)
            gcs.db.set_value(self.view_guid, "search_projection_expert", self.search_projection_expert)
            gcs.db.set_value(self.view_guid, "management_projection_standard", self.management_projection_standard)
            gcs.db.set_value(self.view_guid, "management_projection_expert", self.management_projection_expert)
            gcs.db.save_all_values()
            logger.info(f"💾 Alle 6 Projektions-Tabellen gespeichert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
    
    def refresh_for_expert_mode(self):
        """Aktualisiere alle Projektionen (wird nicht mehr gebraucht, da 6 getrennte Tabellen)"""
        # Projektionen sind bereits für beide Modi erstellt
        logger.info(f"ℹ️ ExpertMode-Refresh: Alle 6 Tabellen bereits verfügbar")
    
    # MODE-BASIERTE GETTER-METHODEN
    def get_table_projection(self):
        """Liste der Keys für Tabellen-Anzeige basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            return self.table_projection_expert.copy()
        else:
            return self.table_projection_standard.copy()
    
    def get_search_projection(self):
        """Liste der Keys für Such-Panel basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            return self.search_projection_expert.copy()
        else:
            return self.search_projection_standard.copy()
    
    def get_management_projection(self):
        """Liste der Keys für Spalten-Management basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            return self.management_projection_expert.copy()
        else:
            return self.management_projection_standard.copy()
    
    # DIREKTER ZUGANG ZU SPEZIFISCHEN TABELLEN
    def get_table_projection_standard(self):
        """Standard-Tabellen-Projektion"""
        return self.table_projection_standard.copy()
    
    def get_table_projection_expert(self):
        """Expert-Tabellen-Projektion"""
        return self.table_projection_expert.copy()
    
    def get_search_projection_standard(self):
        """Standard-Search-Projektion"""
        return self.search_projection_standard.copy()
    
    def get_search_projection_expert(self):
        """Expert-Search-Projektion"""
        return self.search_projection_expert.copy()
    
    def get_management_projection_standard(self):
        """Standard-Management-Projektion"""
        return self.management_projection_standard.copy()
    
    def get_management_projection_expert(self):
        """Expert-Management-Projektion"""
        return self.management_projection_expert.copy()

    # SETTER-METHODEN FÜR PERSISTENTE SPEICHERUNG
    def set_table_projection(self, columns):
        """Setze Tabellen-Projektion basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            self.table_projection_expert = columns.copy()
        else:
            self.table_projection_standard = columns.copy()
        self._save_projections()
        logger.info(f"💾 Table-Projektion gesetzt: {len(columns)} Spalten ({'Expert' if gcs.expert_mode else 'Standard'})")
    
    def set_search_projection(self, columns):
        """Setze Search-Projektion basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            self.search_projection_expert = columns.copy()
        else:
            self.search_projection_standard = columns.copy()
        self._save_projections()
        logger.info(f"💾 Search-Projektion gesetzt: {len(columns)} Spalten ({'Expert' if gcs.expert_mode else 'Standard'})")
    
    def set_management_projection(self, columns):
        """Setze Management-Projektion basierend auf aktuellem ExpertMode"""
        if gcs.expert_mode:
            self.management_projection_expert = columns.copy()
        else:
            self.management_projection_standard = columns.copy()
        self._save_projections()
        logger.info(f"💾 Management-Projektion gesetzt: {len(columns)} Spalten ({'Expert' if gcs.expert_mode else 'Standard'})")


# GLOBALER MANAGER CACHE
_simple_managers = {}

def get_simple_projection_manager(view_guid):
    """Globaler Zugang zum SimpleProjectionManager"""
    if view_guid not in _simple_managers:
        manager = SimpleProjectionManager(view_guid)
        _simple_managers[view_guid] = manager
        
        # Automatische Initialisierung
        try:
            controls_config = gcs.db.get_static_value(view_guid, "controls")
            if controls_config:
                manager.initialize(controls_config)
                logger.info(f"✅ SimpleProjectionManager für {view_guid} initialisiert")
            else:
                logger.warning(f"⚠️ Keine Controls für {view_guid} gefunden")
        except Exception as e:
            logger.error(f"❌ Initialisierung fehlgeschlagen: {e}")
    
    return _simple_managers[view_guid]

def clear_simple_managers():
    """Alle Manager löschen (für Tests)"""
    global _simple_managers
    _simple_managers.clear()
    logger.info("🗑️ Alle SimpleProjectionManager gelöscht")