"""
🎯 UNIFIED LINEAR FILTER SYSTEM
============================

DESIGN-PRINZIP:
1. EIN zentraler Filterprozess für alle drei Filterarten:
   - Gesamtsuche (globale Suche)
   - Einzelsuche (spalten-spezifisch)
   - Komplexsuche (erweitert)

2. LINEARER ABLAUF:
   - show_all_rows() → Filter anwenden → Fertig
   
3. EINHEITLICHE SCHNITTSTELLE:
   - Alle Filter werden zu einheitlicher FilterConfig konvertiert
   - EIN apply_filter_unified() für alle
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class FilterConfig:
    """Einheitliche Filter-Konfiguration für alle Filterarten"""
    filter_type: str  # "gesamtsuche", "einzelsuche", "komplexsuche"
    search_text: str  # Der eigentliche Suchtext
    field_name: Optional[str] = None  # Für Einzelsuche: Spaltenname
    operator: Optional[str] = None    # Für Komplexsuche: "enthält", "ist gleich", etc.
    case_sensitive: bool = False
    whole_word: bool = False


class UnifiedLinearFilter:
    """
    🎯 ZENTRALER LINEARER FILTER
    
    Alle drei Filterarten laufen durch EINEN linearen Prozess:
    1. show_all_rows() - Reset
    2. Filter anwenden
    3. Fertig
    """
    
    def __init__(self, table_widget, data_records=None, view_guid: str = "", column_mapping: dict = None):
        """
        Args:
            table_widget: PyQt5 QTableWidget
            data_records: Optional - Originaldaten für komplexere Filter
            view_guid: View-GUID für Logging
            column_mapping: Control-Key -> Column-Index Mapping
        """
        self.table = table_widget
        self.data_records = data_records or []
        self.view_guid = view_guid
        self.column_mapping = column_mapping or {}  # Control-Key -> Column-Index
        logger.info("✅ UnifiedLinearFilter initialisiert")
    
    def apply_filter_unified(self, filter_config: FilterConfig) -> bool:
        """
        🎯 ZENTRALE LINEARE FILTER-ANWENDUNG
        
        Args:
            filter_config: Einheitliche Filter-Konfiguration
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            logger.info("🎯 === UNIFIED LINEAR FILTER GESTARTET ===")
            logger.info(f"📋 Filter-Type: {filter_config.filter_type}")
            logger.info(f"🔍 Search-Text: '{filter_config.search_text}'")
            
            # SCHRITT 1: RESET - Alle Zeilen anzeigen
            logger.info("🧹 SCHRITT 1: Reset - alle Zeilen anzeigen")
            self._show_all_rows()
            
            # SCHRITT 2: Filter anwenden basierend auf Type
            logger.info("🔧 SCHRITT 2: Filter anwenden")
            
            if filter_config.filter_type == "gesamtsuche":
                success = self._apply_global_search(filter_config)
            elif filter_config.filter_type == "einzelsuche":
                success = self._apply_single_column_search(filter_config)
            elif filter_config.filter_type == "komplexsuche":
                success = self._apply_complex_search(filter_config)
            else:
                logger.error(f"❌ Unbekannter Filter-Type: {filter_config.filter_type}")
                return False
            
            # SCHRITT 3: Ergebnis
            if success:
                visible_count = self._count_visible_rows()
                total_count = self.table.rowCount()
                logger.info(f"✅ UNIFIED LINEAR FILTER ERFOLGREICH: {visible_count}/{total_count} Zeilen")
                return True
            else:
                logger.error("❌ UNIFIED LINEAR FILTER FEHLGESCHLAGEN")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler in Unified Linear Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _show_all_rows(self):
        """RESET: Alle Tabellenzeilen sichtbar machen"""
        try:
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            logger.info(f"✅ Alle {self.table.rowCount()} Zeilen sichtbar")
        except Exception as e:
            logger.error(f"❌ Fehler bei show_all_rows: {e}")
    
    def _apply_global_search(self, filter_config: FilterConfig) -> bool:
        """Gesamtsuche: Sucht in allen Spalten"""
        try:
            search_text = filter_config.search_text.strip()
            if not search_text:
                return True  # Kein Filter = alle anzeigen
            
            if not filter_config.case_sensitive:
                search_text = search_text.lower()
            
            hidden_count = 0
            
            for row in range(self.table.rowCount()):
                row_matches = False
                
                # Durch alle Spalten der Zeile suchen
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        cell_text = item.text()
                        if not filter_config.case_sensitive:
                            cell_text = cell_text.lower()
                        
                        if filter_config.whole_word:
                            # Ganzes Wort suchen
                            if search_text == cell_text:
                                row_matches = True
                                break
                        else:
                            # Teil-String suchen
                            if search_text in cell_text:
                                row_matches = True
                                break
                
                # Zeile verstecken wenn kein Match
                if not row_matches:
                    self.table.setRowHidden(row, True)
                    hidden_count += 1
            
            logger.info(f"✅ Gesamtsuche: {hidden_count} Zeilen ausgeblendet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Gesamtsuche: {e}")
            return False
    
    def _apply_single_column_search(self, filter_config: FilterConfig) -> bool:
        """Einzelsuche: Sucht in einer bestimmten Spalte"""
        try:
            if not filter_config.field_name:
                logger.error("❌ Einzelsuche: Kein field_name angegeben")
                return False

            search_text = filter_config.search_text.strip()
            if not search_text:
                return True

            # Spalten-Index finden
            target_col = None
            logger.info(f"� Suche Spalte: '{filter_config.field_name}'")
            
            # DEBUG: Zeige alle verfügbaren Spalten-Header
            available_headers = []
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                if header_item:
                    header_text = header_item.text()
                    available_headers.append(header_text)
                    logger.info(f"   📋 Spalte {col}: '{header_text}'")
                    if header_text == filter_config.field_name:
                        target_col = col
                        logger.info(f"   ✅ Match gefunden bei Index {col}")

            if target_col is None:
                logger.error(f"❌ Spalte '{filter_config.field_name}' nicht gefunden")
                logger.error(f"❌ Verfügbare Spalten ({len(available_headers)}): {available_headers}")
                return False
            
            if not filter_config.case_sensitive:
                search_text = search_text.lower()
            
            hidden_count = 0
            
            for row in range(self.table.rowCount()):
                item = self.table.item(row, target_col)
                row_matches = False
                
                if item:
                    cell_text = item.text()
                    if not filter_config.case_sensitive:
                        cell_text = cell_text.lower()
                    
                    if filter_config.whole_word:
                        row_matches = (search_text == cell_text)
                    else:
                        row_matches = (search_text in cell_text)
                
                if not row_matches:
                    self.table.setRowHidden(row, True)
                    hidden_count += 1
            
            logger.info(f"✅ Einzelsuche in '{filter_config.field_name}': {hidden_count} Zeilen ausgeblendet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Einzelsuche: {e}")
            return False
    
    def _apply_complex_search(self, filter_config: FilterConfig) -> bool:
        """Komplexsuche: Erweiterte Suchkriterien"""
        try:
            # Für jetzt erstmal wie Einzelsuche behandeln
            # Kann später erweitert werden für "beginnt mit", "endet mit", etc.
            
            operator = filter_config.operator or "enthält"
            logger.info(f"🔧 Komplexsuche mit Operator: {operator}")
            
            if operator == "enthält":
                # Behandeln wie normale Suche
                return self._apply_single_column_search(filter_config)
            elif operator == "ist gleich":
                # Ganzes Wort suchen
                config_copy = FilterConfig(
                    filter_type="einzelsuche",
                    search_text=filter_config.search_text,
                    field_name=filter_config.field_name,
                    whole_word=True,
                    case_sensitive=filter_config.case_sensitive
                )
                return self._apply_single_column_search(config_copy)
            else:
                logger.warning(f"⚠️ Operator '{operator}' nicht implementiert, verwende 'enthält'")
                return self._apply_single_column_search(filter_config)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Komplexsuche: {e}")
            return False
    
    def _count_visible_rows(self) -> int:
        """Zählt sichtbare Zeilen"""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                count += 1
        return count
    
    def clear_all_filters(self) -> bool:
        """Alle Filter löschen"""
        try:
            logger.info("🧹 Lösche alle Filter")
            self._show_all_rows()
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen aller Filter: {e}")
            return False


# ===== HELPER-FUNKTIONEN =====

def create_gesamtsuche_config(search_text: str, case_sensitive: bool = False, whole_word: bool = False) -> FilterConfig:
    """Erstellt FilterConfig für Gesamtsuche"""
    return FilterConfig(
        filter_type="gesamtsuche",
        search_text=search_text,
        case_sensitive=case_sensitive,
        whole_word=whole_word
    )

def create_einzelsuche_config(field_name: str, search_text: str, case_sensitive: bool = False, whole_word: bool = False) -> FilterConfig:
    """Erstellt FilterConfig für Einzelsuche"""
    return FilterConfig(
        filter_type="einzelsuche",
        search_text=search_text,
        field_name=field_name,
        case_sensitive=case_sensitive,
        whole_word=whole_word
    )

def create_komplexsuche_config(field_name: str, search_text: str, operator: str = "enthält", case_sensitive: bool = False) -> FilterConfig:
    """Erstellt FilterConfig für Komplexsuche"""
    return FilterConfig(
        filter_type="komplexsuche",
        search_text=search_text,
        field_name=field_name,
        operator=operator,
        case_sensitive=case_sensitive
    )