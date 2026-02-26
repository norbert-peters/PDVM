#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🎯 PDVM Menü-Pipeline - Lineare, robuste Menü-Verarbeitung
============================================================

ARCHITEKTUR:
-----------
Linear ohne Verzweigungen:
    BASIS (Daten laden) → PROJECT (Matrix erstellen) → UI (Ausgabe)

DATENQUELLE:
-----------
- sys_menudaten Tabelle in PdvmCentralDatenbank
- KEINE History, daher get_static_value/set_static_value
- Gruppe = Menu-Typ (VERTIKAL, GRUND, ZUSATZ)
- Feld = Item-GUID
- Wert = JSON mit Item-Properties

MATRIX-STRUKTUR:
---------------
Jede Zeile ist ein Menü-Item mit:
- guid: Eindeutige Item-ID
- label: Anzeigetext
- parent_guid: Parent-Item (None = Root-Level)
- sort_order: Sortierung innerhalb Parent
- type: SUBMENU, BUTTON, SEPARATOR, SPACER
- icon: Icon-Path (optional)
- visible: Sichtbarkeit
- enabled: Aktiviert/Deaktiviert
- tooltip: Tooltip-Text (optional)
- command: Aktion (Handler + Parameter)

PIPELINE-PHASEN:
---------------
1. BASIS: Lädt alle Items aus Gruppe (VERTIKAL/GRUND) in matrix_base
2. PROJECT: Sortiert nach sort_order, baut Hierarchie → matrix_project
3. UI: Externe Komponente rendert matrix_project als Menü-Buttons

SINGLETON-PATTERN:
-----------------
Pro Menü-GUID (Gruppe) eine Pipeline-Instanz:
    pipeline = get_menu_pipeline(menu_guid, menu_db_instance)
    pipeline.run('BASIS')  # Komplett neu laden
    pipeline.run('PROJECT')  # Nur Projektion neu

USAGE:
------
# System-Menü (in GCS)
gcs = get_gcs()
pipeline = gcs.get_system_menu_pipeline('VERTIKAL')
pipeline.run('BASIS')
matrix, structure = pipeline.get_projected_data()

# Editor-Menü (im MenuEditor)
menu_db = PdvmCentralDatenbank('systemsteuerung', user_guid)
pipeline = get_menu_pipeline('GRUND', menu_db)
pipeline.run('BASIS')

Autor: PDVM-System
Version: 2.0
Datum: 09.11.2025
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)

# 🎯 Singleton-Registry für Menu-Pipelines
_MENU_PIPELINE_REGISTRY: Dict[str, 'PdvmMenuPipeline'] = {}


def get_menu_pipeline(menu_guid: str, menu_db_instance) -> 'PdvmMenuPipeline':
    """
    Holt oder erstellt Menu-Pipeline-Instanz (Singleton pro menu_guid).
    
    Args:
        menu_guid: Gruppe (VERTIKAL, GRUND, ZUSATZ)
        menu_db_instance: PdvmCentralDatenbank Instanz
        
    Returns:
        PdvmMenuPipeline Instanz
    """
    if menu_guid not in _MENU_PIPELINE_REGISTRY:
        logger.info(f"🎯 Erstelle neue Menu-Pipeline für: {menu_guid}")
        _MENU_PIPELINE_REGISTRY[menu_guid] = PdvmMenuPipeline(menu_guid, menu_db_instance)
    else:
        logger.debug(f"🔄 Verwende existierende Menu-Pipeline: {menu_guid}")
    
    return _MENU_PIPELINE_REGISTRY[menu_guid]


class PdvmMenuPipeline:
    """
    Lineare Pipeline für Menü-Verarbeitung.
    
    Verarbeitet Menü-Daten aus sys_menudaten in 2 Phasen:
    1. BASIS: Lädt alle Items aus Gruppe
    2. PROJECT: Sortiert und baut Hierarchie
    
    Keine If-Then-Logik, nur sequenzielle Ausführung!
    """
    
    def __init__(self, menu_guid: str, menu_db_instance):
        """
        Initialisiert Menu-Pipeline.
        
        Args:
            menu_guid: Gruppe (VERTIKAL, GRUND, ZUSATZ)
            menu_db_instance: PdvmCentralDatenbank Instanz für sys_menudaten
        """
        self.menu_guid = menu_guid
        self.db = menu_db_instance  # ✅ db statt menu_db (konsistent mit View-System)
        
        # 📊 Pipeline-Daten
        self.matrix_base: List[Dict[str, Any]] = []      # Rohdaten aus DB
        self.matrix_project: List[Dict[str, Any]] = []   # Sortiert + Hierarchie
        
        # 🎯 Rendering-Strategie aus META
        self.rendering_mode: Optional[str] = None  # 'vert', 'hori_1', 'hori_2'
        
        logger.info(f"🎯 Menu-Pipeline initialisiert: {menu_guid}")
    
    def run(self, start_phase: str = 'BASIS'):
        """
        Führt Pipeline ab angegebener Phase aus.
        
        Args:
            start_phase: 'BASIS' (alles neu) oder 'PROJECT' (nur Projektion)
        """
        logger.info(f"🚀 Menu-Pipeline START: {start_phase} für {self.menu_guid}")
        
        if start_phase == 'BASIS':
            self._load_basis()
        
        self._project_menu()
        
        logger.info(f"✅ Menu-Pipeline FERTIG: {len(self.matrix_project)} Items")
    
    def _load_basis(self):
        """
        PHASE 1: BASIS - Lädt alle Menü-Items aus Gruppe.
        
        PdvmCentralDatenbank('sys_menudaten', 'Menu_guid') verwaltet:
        - Tabelle: sys_menudaten
        - UID-Spalte: Menu_guid (in uid-Spalte)
        - Daten-Spalte: JSON dict mit Gruppe/Feld/Wert Struktur
        
        Zugriff:
        - get_static_value(GRUPPE, FELD) → Wert (kein Stichtag)
        - get_value_by_group(GRUPPE) → {feld: wert, ...}
        
        Struktur:
        - GRUPPE = 'VERTIKAL', 'GRUND', 'ZUSATZ'
        - FELD = item_guid (z.B. 'Apps', 'MeineApps')  
        - WERT = JSON dict mit {type, label, sort_order, parent_guid, ...}
        """
        logger.info(f"📂 [BASIS] Lade Menü-Items für GRUPPE='{self.menu_guid}'")
        
        self.matrix_base = []
        
        try:
            # 🎯 SCHRITT 1: Hole Rendering-Mode aus META
            try:
                meta_value = self.db.get_static_value('META', self.menu_guid)
                if meta_value:
                    self.rendering_mode = meta_value
                    logger.info(f"  🎯 Rendering-Mode aus META: {self.menu_guid} → {self.rendering_mode}")
                else:
                    raise KeyError("Kein META-Wert")
            except KeyError:
                logger.warning(f"  ⚠️ Kein Rendering-Mode in META für {self.menu_guid}, verwende Fallback")
                # Fallback: VERTIKAL → vert, GRUND → hori_1, ZUSATZ → hori_2
                fallback_modes = {'VERTIKAL': 'vert', 'GRUND': 'hori_1', 'ZUSATZ': 'hori_2'}
                self.rendering_mode = fallback_modes.get(self.menu_guid, 'vert')
                logger.info(f"  🔧 Fallback Rendering-Mode: {self.menu_guid} → {self.rendering_mode}")
            
            # 🎯 SCHRITT 2: Hole alle Felder aus Gruppe (VERTIKAL/GRUND/ZUSATZ)
            # get_value_by_group gibt dict zurück: {item_guid: json_value, ...}
            gruppe_data = self.db.get_value_by_group(self.menu_guid)
            
            if not gruppe_data:
                logger.warning(f"⚠️ [BASIS] Keine Daten für Gruppe '{self.menu_guid}' gefunden")
                logger.info(f"📊 [BASIS] Verfügbare Gruppen prüfen mit: db.get_alle_gruppen()")
                return
            
            logger.info(f"✅ [BASIS] {len(gruppe_data)} Felder in Gruppe '{self.menu_guid}' gefunden")
            
            # Verarbeite jedes Item (Feld = item_guid, Wert = JSON oder Dict)
            for item_guid, item_value in gruppe_data.items():
                logger.debug(f"🔍 Verarbeite Item: {item_guid}, Typ: {type(item_value)}")
                
                try:
                    # Parse JSON-Wert falls String
                    if isinstance(item_value, str):
                        item_data = json.loads(item_value)
                        logger.debug(f"  ✅ JSON geparst für {item_guid}")
                    else:
                        item_data = item_value
                        logger.debug(f"  ℹ️ Bereits Dict für {item_guid}")
                    
                    # Stelle sicher dass guid im Item ist
                    if isinstance(item_data, dict):
                        if 'guid' not in item_data:
                            item_data['guid'] = item_guid
                        self.matrix_base.append(item_data)
                        logger.debug(f"  ✅ Item hinzugefügt: {item_guid}")
                    else:
                        logger.warning(f"⚠️ Item {item_guid} ist kein Dictionary: {type(item_data)}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON-Parse-Fehler für Item {item_guid}: {e}")
                    logger.error(f"   Rohdaten: {item_value[:200] if len(str(item_value)) > 200 else item_value}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Fehler beim Laden von Item {item_guid}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info(f"✅ [BASIS] Matrix erstellt: {len(self.matrix_base)} Items")
            
            # 🎯 SCHRITT 3: Template-Expansion
            self._expand_templates()
            
        except Exception as e:
            logger.error(f"❌ [BASIS] Kritischer Fehler beim Laden der Gruppe '{self.menu_guid}': {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _expand_templates(self):
        """
        TEMPLATE-EXPANSION - Ersetzt SPACER mit template_guid durch Template-Items.
        
        Regeln:
        1. Template = SPACER mit template_guid
        2. Templates nur in gleicher Gruppe (GRUND→GRUND)
        3. Erstes Template-Item (SUBMENU) ersetzt SPACER (übernimmt parent_guid + sort_order)
        4. Restliche Template-Items werden nach erstem Item eingefügt
        5. Keine Persistierung (runtime only)
        """
        spacers = [item for item in self.matrix_base if item.get('type') == 'SPACER' and item.get('template_guid')]
        
        if not spacers:
            logger.debug("ℹ️ [TEMPLATE] Keine SPACER mit template_guid gefunden")
            return
        
        logger.info(f"🔧 [TEMPLATE] {len(spacers)} SPACER mit Templates gefunden")
        
        for spacer in spacers:
            template_guid = spacer.get('template_guid')
            spacer_guid = spacer.get('guid')
            spacer_parent = spacer.get('parent_guid')
            spacer_sort = spacer.get('sort_order', 0)
            
            logger.info(f"  🎯 Expandiere Template: {template_guid} für SPACER {spacer_guid}")
            
            try:
                # Lade Template-Menü (gleiche Gruppe!)
                from pdvm_central_datenbank import PdvmCentralDatenbank
                template_db = PdvmCentralDatenbank('sys_menudaten', template_guid)
                template_data = template_db.get_value_by_group(self.menu_guid)
                
                if not template_data:
                    logger.warning(f"    ⚠️ Kein Template in Gruppe '{self.menu_guid}' für GUID {template_guid}")
                    continue
                
                # Parse Template-Items
                template_items = []
                for item_guid, item_value in template_data.items():
                    try:
                        if isinstance(item_value, str):
                            item_data = json.loads(item_value)
                        else:
                            item_data = item_value
                        
                        if isinstance(item_data, dict):
                            if 'guid' not in item_data:
                                item_data['guid'] = item_guid
                            template_items.append(item_data)
                    except Exception as e:
                        logger.error(f"    ❌ Fehler beim Parsen von Template-Item {item_guid}: {e}")
                        continue
                
                if not template_items:
                    logger.warning(f"    ⚠️ Template {template_guid} hat keine Items")
                    continue
                
                # Sortiere Template-Items nach sort_order
                template_items.sort(key=lambda x: x.get('sort_order', 0))
                
                logger.info(f"    ✅ {len(template_items)} Template-Items geladen")
                
                # REGEL 3: Erstes Item muss SUBMENU sein und ersetzt SPACER
                first_item = template_items[0]
                if first_item.get('type') != 'SUBMENU':
                    logger.warning(f"    ⚠️ Erstes Template-Item ist kein SUBMENU: {first_item.get('type')}")
                    continue
                
                # Übernehme parent_guid und sort_order vom SPACER
                first_item['parent_guid'] = spacer_parent
                first_item['sort_order'] = spacer_sort
                
                logger.info(f"    🔄 Ersetze SPACER {spacer_guid} mit SUBMENU {first_item.get('guid')}")
                logger.info(f"       parent_guid: {spacer_parent}, sort_order: {spacer_sort}")
                
                # Ersetze SPACER in matrix_base
                spacer_index = self.matrix_base.index(spacer)
                self.matrix_base[spacer_index] = first_item
                
                # REGEL 4: Restliche Items nach erstem Item einfügen
                if len(template_items) > 1:
                    remaining_items = template_items[1:]
                    logger.info(f"    ➕ Füge {len(remaining_items)} weitere Template-Items ein")
                    
                    # Füge nach dem ersten Item ein
                    insert_position = spacer_index + 1
                    for i, item in enumerate(remaining_items):
                        self.matrix_base.insert(insert_position + i, item)
                        logger.debug(f"       ➕ Item {item.get('guid')} eingefügt an Position {insert_position + i}")
                
                logger.info(f"    ✅ Template-Expansion erfolgreich für {spacer_guid}")
                
            except Exception as e:
                logger.error(f"    ❌ Fehler bei Template-Expansion für {spacer_guid}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"✅ [TEMPLATE] Template-Expansion abgeschlossen, Matrix hat jetzt {len(self.matrix_base)} Items")
    
    def _project_menu(self):
        """
        PHASE 2: PROJECT - Sortiert Items und baut Hierarchie.
        
        Sortiert nach:
        1. parent_guid (Root-Items zuerst)
        2. sort_order innerhalb gleicher Parent-Ebene
        
        Erstellt flache Liste mit hierarchischer Sortierung für UI.
        """
        logger.info(f"🔄 Projektiere Menü-Struktur")
        
        self.matrix_project = []
        
        if not self.matrix_base:
            logger.warning("⚠️ Keine Basis-Daten für Projektion vorhanden")
            return
        
        # 🎯 Root-Items (parent_guid = None)
        root_items = [
            item for item in self.matrix_base 
            if item.get('parent_guid') is None
        ]
        
        # Sortiere Root-Items nach sort_order
        root_items.sort(key=lambda x: x.get('sort_order', 0))
        
        # 🔄 Rekursiv Child-Items hinzufügen
        for root_item in root_items:
            self._add_item_and_children(root_item)
        
        logger.info(f"✅ Projektion fertig: {len(self.matrix_project)} Items")
    
    def _add_item_and_children(self, item: Dict[str, Any]):
        """
        Fügt Item und alle Child-Items rekursiv zur Projekt-Matrix hinzu.
        
        Args:
            item: Menü-Item Dictionary
        """
        # Füge Item selbst hinzu
        self.matrix_project.append(item)
        
        # Finde Child-Items
        children = [
            child for child in self.matrix_base
            if child.get('parent_guid') == item.get('guid')
        ]
        
        # Sortiere Children nach sort_order
        children.sort(key=lambda x: x.get('sort_order', 0))
        
        # Rekursiv Children hinzufügen
        for child in children:
            self._add_item_and_children(child)
    
    def get_projected_data(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Liefert projektierte Menü-Daten für UI.
        
        Returns:
            Tuple mit:
            - matrix_project: Sortierte flache Item-Liste
            - structure_info: Meta-Informationen über Struktur
        """
        structure_info = {
            'menu_guid': self.menu_guid,
            'total_items': len(self.matrix_project),
            'root_items': len([
                item for item in self.matrix_project 
                if item.get('parent_guid') is None
            ])
        }
        
        return self.matrix_project, structure_info
    
    def save_menu(self):
        """
        Schreibt aktuelle matrix_base zurück in DB.
        
        WICHTIG: Nur matrix_base wird gespeichert, matrix_project ist temporär!
        """
        logger.info(f"💾 Speichere Menü: {self.menu_guid}")
        
        for item in self.matrix_base:
            item_guid = item.get('guid')
            if not item_guid:
                logger.warning(f"⚠️ Item ohne GUID gefunden, überspringe")
                continue
            
            # Konvertiere zu JSON
            json_value = json.dumps(item, ensure_ascii=False)
            
            # Speichere in DB (Gruppe = menu_guid, Feld = item_guid)
            self.menu_db.set_static_value(
                gruppe=self.menu_guid,
                feld=item_guid,
                wert=json_value
            )
        
        # Persistiere alle Änderungen
        self.menu_db.save_all_values()
        
        logger.info(f"✅ Menü gespeichert: {len(self.matrix_base)} Items")
    
    def add_item(self, item_data: Dict[str, Any]):
        """
        Fügt neues Item zur Basis-Matrix hinzu.
        
        Args:
            item_data: Item-Dictionary mit allen Properties
        """
        if 'guid' not in item_data:
            logger.error("❌ Item muss 'guid' Property haben!")
            return
        
        self.matrix_base.append(item_data)
        logger.info(f"✅ Item hinzugefügt: {item_data.get('label', 'N/A')}")
    
    def update_item(self, item_guid: str, updated_data: Dict[str, Any]):
        """
        Aktualisiert existierendes Item in Basis-Matrix.
        
        Args:
            item_guid: GUID des zu aktualisierenden Items
            updated_data: Neue Properties (partielles Update möglich)
        """
        for i, item in enumerate(self.matrix_base):
            if item.get('guid') == item_guid:
                # Merge mit existierenden Daten
                self.matrix_base[i].update(updated_data)
                logger.info(f"✅ Item aktualisiert: {item_guid}")
                return
        
        logger.warning(f"⚠️ Item nicht gefunden: {item_guid}")
    
    def delete_item(self, item_guid: str):
        """
        Löscht Item aus Basis-Matrix.
        
        Args:
            item_guid: GUID des zu löschenden Items
        """
        original_count = len(self.matrix_base)
        self.matrix_base = [
            item for item in self.matrix_base 
            if item.get('guid') != item_guid
        ]
        
        if len(self.matrix_base) < original_count:
            logger.info(f"✅ Item gelöscht: {item_guid}")
        else:
            logger.warning(f"⚠️ Item nicht gefunden: {item_guid}")


# 🎯 TEST & DEBUG FUNKTIONEN
def test_menu_pipeline():
    """Test-Funktion für Menu-Pipeline (ohne DB)."""
    from pdvm_central_datenbank import PdvmCentralDatenbank
    
    logger.info("🧪 TEST: Menu-Pipeline")
    
    # Mock DB-Instanz
    class MockDB:
        def get_value_by_group(self, gruppe):
            # Test-Daten
            return {
                'guid-1': json.dumps({
                    'guid': 'guid-1',
                    'type': 'SUBMENU',
                    'label': 'Apps',
                    'parent_guid': None,
                    'sort_order': 1,
                    'visible': True,
                    'enabled': True
                }),
                'guid-2': json.dumps({
                    'guid': 'guid-2',
                    'type': 'BUTTON',
                    'label': 'MeineApps',
                    'parent_guid': 'guid-1',
                    'sort_order': 0,
                    'visible': True,
                    'enabled': True,
                    'command': {'handler': 'open_app_menu', 'params': {}}
                })
            }
        
        def set_static_value(self, gruppe, feld, wert):
            pass
        
        def save_all_values(self):
            pass
    
    # Test Pipeline
    mock_db = MockDB()
    pipeline = get_menu_pipeline('GRUND', mock_db)
    pipeline.run('BASIS')
    
    matrix, info = pipeline.get_projected_data()
    
    logger.info(f"✅ Test erfolgreich: {len(matrix)} Items")
    for item in matrix:
        logger.info(f"   - {item.get('label')} (Parent: {item.get('parent_guid')})")
    
    return True


if __name__ == '__main__':
    # Setup Logging für Tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_menu_pipeline()
