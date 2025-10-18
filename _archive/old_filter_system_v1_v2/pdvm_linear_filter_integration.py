"""
🎯 INTEGRATION WRAPPER FÜR UNIFIED LINEAR FILTER
==============================================

Integration des neuen linearen Filtersystems in die bestehende PDVM-Anwendung.
Ersetzt das komplexe Multi-Klassen Filter-System durch eine einheitliche Lösung.

INKLUDIERT: Control-Key Patch für vereinfachte Filter-Suche ohne Column-Mapping
"""

import logging
from typing import Optional

from unified_linear_filter import UnifiedLinearFilter, create_gesamtsuche_config, create_einzelsuche_config, create_komplexsuche_config

logger = logging.getLogger(__name__)

# ===== CONTROL-KEY PATCH ANWENDEN =====
try:
    from unified_filter_control_key_patch import apply_unified_filter_patch
    apply_unified_filter_patch()
    logger.info("✅ Control-Key Patch erfolgreich angewendet")
except Exception as e:
    logger.warning(f"⚠️ Control-Key Patch konnte nicht angewendet werden: {e}")

class PDVMLinearFilterIntegration:
    """
    🎯 INTEGRATION WRAPPER
    
    Integriert das neue UnifiedLinearFilter System in die bestehende PDVM-Anwendung.
    Ersetzt alle drei bisherigen Filter-Methoden durch EINEN linearen Prozess.
    """
    
    def __init__(self, table_widget, view_guid: str = None, column_mapping: dict = None):
        """
        Args:
            table_widget: PyQt5 QTableWidget aus PdvmViewDisplay
            view_guid: Optional - GUID für Logging/Debugging
            column_mapping: DEPRECATED - wird durch Control-Key Patch nicht verwendet
        """
        self.table = table_widget
        self.view_guid = view_guid
        
        if column_mapping:
            logger.info("⚠️ Column-Mapping übergeben, aber Control-Key Patch verwendet direkte Suche")
        
        # Das neue lineare Filter-System mit Control-Key Patch
        self.unified_filter = UnifiedLinearFilter(
            table_widget=table_widget,
            view_guid=view_guid or "unknown"
        )
        
        logger.info(f"✅ PDVM Linear Filter Integration mit Control-Key Patch initialisiert (GUID: {view_guid})")
    
    # ===========================================
    # NEUE EINHEITLICHE API - ERSETZT ALLES ALTE
    # ===========================================
    
    def apply_filter_unified(self, filter_string: str) -> bool:
        """
        🎯 EINZIGE FILTER-METHODE - ersetzt alle anderen
        
        Erkennt automatisch den Filter-Type und führt lineare Filterung durch.
        
        Args:
            filter_string (str): 
                - "suchtext" → Gesamtsuche
                - "feldname:suchtext" → Einzelsuche  
                - "EXTENDED:feldname:operator:suchtext" → Komplexsuche
                - "" → Alle Filter löschen
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            logger.info("🎯 === PDVM LINEARE FILTER-INTEGRATION GESTARTET ===")
            logger.info(f"📂 View-GUID: {self.view_guid}")
            logger.info(f"🔍 Filter-String: '{filter_string}'")
            
            # LEERER FILTER: Alle Filter löschen
            if not filter_string or filter_string.strip() == "":
                logger.info("🧹 Leerer Filter - lösche alle Filter")
                return self.unified_filter.clear_all_filters()
            
            filter_string = filter_string.strip()
            
            # EXTENDED FILTER (Komplex)
            if filter_string.startswith("EXTENDED:"):
                return self._handle_extended_filter(filter_string)
            
            # STRUKTURIERTER FILTER (Einzelsuche)
            elif ":" in filter_string:
                return self._handle_structured_filter(filter_string)
            
            # GESAMTFILTER (Globale Suche)
            else:
                return self._handle_global_filter(filter_string)
                
        except Exception as e:
            logger.error(f"❌ Fehler in PDVM Linear Filter Integration: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _handle_extended_filter(self, filter_string: str) -> bool:
        """Behandelt EXTENDED Filter (Komplexsuche) - kann mehrere Filter enthalten"""
        try:
            logger.info(f"🔧 EXTENDED Filter-String: '{filter_string}'")
            
            # Multi-Filter durch || getrennt
            if "||" in filter_string:
                return self._handle_multi_extended_filter(filter_string)
            
            # Einzelner EXTENDED Filter - verwende dedicated Methode
            return self._handle_extended_filter_single(filter_string)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei EXTENDED Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _parse_extended_details(self, details: str) -> tuple:
        """Parse EXTENDED Details: 'FIRST IS beginnt mit 'm'' → ('beginnt mit', 'm')"""
        try:
            # Format: "FIRST IS operator 'wert'"
            # oder: "FIRST IS operator wert"
            details = details.strip()
            
            if not details.startswith("FIRST IS "):
                logger.warning(f"⚠️ Unerwartetes EXTENDED Format: {details}")
                return "enthält", details  # Fallback
            
            # Entferne "FIRST IS "
            operator_and_value = details[9:]  # len("FIRST IS ") = 9
            
            # Suche nach quotes
            if "'" in operator_and_value:
                # Format: "beginnt mit 'm'"
                quote_pos = operator_and_value.find("'")
                if quote_pos > 0:
                    operator = operator_and_value[:quote_pos].strip()
                    # Extrahiere Wert zwischen Quotes
                    rest = operator_and_value[quote_pos+1:]
                    end_quote = rest.find("'")
                    if end_quote != -1:
                        search_text = rest[:end_quote]
                    else:
                        search_text = rest  # Quote nicht geschlossen
                else:
                    # Fallback
                    operator = "enthält"
                    search_text = operator_and_value.replace("'", "")
            else:
                # Kein Quote - Split am letzten Wort
                parts = operator_and_value.split()
                if len(parts) >= 2:
                    search_text = parts[-1]
                    operator = " ".join(parts[:-1])
                else:
                    operator = "enthält"
                    search_text = operator_and_value
                    
            logger.info(f"📝 EXTENDED Details parsed: '{details}' → Operator='{operator}', Text='{search_text}'")
            return operator, search_text
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen EXTENDED Details: {e}")
            return "enthält", details  # Fallback

    def _handle_multi_extended_filter(self, filter_string: str) -> bool:
        """Behandelt mehrere EXTENDED Filter getrennt durch || - ALLE VERARBEITEN MIT UND-VERKNÜPFUNG"""
        try:
            logger.info(f"🔧 Multi-EXTENDED Filter: '{filter_string}'")
            
            # Split nach ||
            filter_parts = [part.strip() for part in filter_string.split("||")]
            logger.info(f"📝 Gefunden {len(filter_parts)} Teil-Filter")
            
            # KORREKTE LÖSUNG: Verwende UnifiedLinearFilter für ersten, dann manuelle Filter für weitere
            success_count = 0
            
            # SCHRITT 1: Ersten Filter normal anwenden (mit Reset)
            first_filter = filter_parts[0]
            if first_filter.startswith("EXTENDED:"):
                logger.info(f"🎯 Ersten Filter anwenden (mit Reset): '{first_filter}'")
                if self._apply_single_extended_filter(first_filter):
                    success_count += 1
                    logger.info(f"✅ Erster Filter erfolgreich angewendet")
                else:
                    logger.error(f"❌ Erster Filter fehlgeschlagen")
                    return False
            
            # SCHRITT 2: Weitere Filter OHNE Reset anwenden (kumulativ)
            for i in range(1, len(filter_parts)):
                filter_part = filter_parts[i]
                logger.info(f"🎯 Zusätzlichen Filter anwenden (OHNE Reset): '{filter_part}'")
                
                if filter_part.startswith("EXTENDED:"):
                    if self._apply_additional_extended_filter(filter_part):
                        success_count += 1
                        logger.info(f"✅ Zusätzlicher Filter {i+1} erfolgreich angewendet")
                    else:
                        logger.error(f"❌ Zusätzlicher Filter {i+1} fehlgeschlagen")
                else:
                    logger.warning(f"⚠️ Filter {i+1} ist kein EXTENDED Format: {filter_part}")
            
            logger.info(f"🎯 Multi-Filter Ergebnis: {success_count}/{len(filter_parts)} erfolgreich")
            return success_count == len(filter_parts)  # Alle müssen erfolgreich sein
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Multi-EXTENDED Filter: {e}")
            return False
    
    def _apply_single_extended_filter(self, filter_string: str) -> bool:
        """Wendet einen einzelnen EXTENDED Filter an (mit Reset)"""
        try:
            # Verwende die normale _handle_extended_filter Logik
            return self._handle_extended_filter_single(filter_string)
        except Exception as e:
            logger.error(f"❌ Fehler bei einzelnem EXTENDED Filter: {e}")
            return False
    
    def _apply_additional_extended_filter(self, filter_string: str) -> bool:
        """Wendet zusätzlichen EXTENDED Filter an (OHNE Reset) - kumulativ"""
        try:
            # Parse den EXTENDED Filter
            content = filter_string[9:]  # Entferne "EXTENDED:"
            colon_pos = content.find(":")
            if colon_pos == -1:
                return False
                
            field_name = content[:colon_pos]
            operator_details = content[colon_pos + 1:]
            
            # Parse Details
            operator, search_text = self._parse_extended_details(operator_details)
            
            logger.info(f"🔧 Zusätzlicher Filter: Feld='{field_name}', Operator='{operator}', Text='{search_text}'")
            
            # Wende Filter OHNE Reset an - direkt auf bereits gefilterte Tabelle
            return self._apply_cumulative_filter(field_name, search_text, operator)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei zusätzlichem EXTENDED Filter: {e}")
            return False
    
    def _apply_cumulative_filter(self, field_name: str, search_text: str, operator: str) -> bool:
        """Wendet Filter kumulativ an (OHNE Reset der bereits gefilterten Zeilen)"""
        try:
            from control_key_filter_simple import find_column_by_control_key
            
            # Finde Column-Index für Control-Key
            column_index = find_column_by_control_key(self.table, field_name)
            if column_index == -1:
                logger.error(f"❌ Control-Key '{field_name}' nicht gefunden")
                return False
            
            logger.info(f"✅ Control-Key '{field_name}' → Spalte {column_index}")
            
            hidden_count = 0
            total_rows = self.table.rowCount()
            
            # Iteriere über alle Zeilen und verstecke weitere (die noch sichtbar sind)
            for row in range(total_rows):
                # NUR sichtbare Zeilen prüfen
                if not self.table.isRowHidden(row):
                    item = self.table.item(row, column_index)
                    if item:
                        cell_value = str(item.text())
                        
                        # Prüfe Filter-Bedingung
                        if not self._matches_operator(cell_value, search_text, operator):
                            self.table.setRowHidden(row, True)
                            hidden_count += 1
            
            logger.info(f"✅ Kumulativer Filter '{field_name}': {hidden_count} weitere Zeilen ausgeblendet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei kumulativem Filter: {e}")
            return False
    
    def _matches_operator(self, cell_value: str, search_text: str, operator: str) -> bool:
        """Prüft ob Zellwert der Operator-Bedingung entspricht"""
        try:
            cell_lower = cell_value.lower()
            search_lower = search_text.lower()
            
            if operator == "beginnt mit":
                return cell_lower.startswith(search_lower)
            elif operator == "enthält":
                return search_lower in cell_lower
            elif operator == "endet mit":
                return cell_lower.endswith(search_lower)
            elif operator == "ist gleich":
                return cell_lower == search_lower
            else:
                # Fallback: enthält
                return search_lower in cell_lower
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Operator-Prüfung: {e}")
            return False
    
    def _handle_extended_filter_single(self, filter_string: str) -> bool:
        """Behandelt einzelnen EXTENDED Filter (Original-Logik)"""
        try:
            # Entferne "EXTENDED:" Prefix
            content = filter_string[9:]  # len("EXTENDED:") = 9
            
            # Finde ersten Doppelpunkt für Feldname
            colon_pos = content.find(":")
            if colon_pos == -1:
                logger.error(f"❌ Ungültiges EXTENDED Format - kein Feldname: {filter_string}")
                return False
                
            field_name = content[:colon_pos]
            operator_details = content[colon_pos + 1:]
            
            logger.info(f"🔧 EXTENDED Einzelfilter: Feld='{field_name}', Details='{operator_details}'")
            
            # Parse EXTENDED Details: "FIRST IS beginnt mit 'm'"
            operator, search_text = self._parse_extended_details(operator_details)
            
            logger.info(f"🎯 EXTENDED Parsed: Operator='{operator}', Text='{search_text}'")
            
            config = create_komplexsuche_config(field_name, search_text, operator)
            return self.unified_filter.apply_filter_unified(config)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei einzelnem EXTENDED Filter: {e}")
            return False
    
    def _handle_structured_filter(self, filter_string: str) -> bool:
        """Behandelt strukturierten Filter (Einzelsuche)"""
        try:
            # Format: "feldname:suchtext"
            if "||" in filter_string:
                # Multiple Filter - für jetzt nehmen wir den ersten
                first_part = filter_string.split("||")[0]
            else:
                first_part = filter_string
            
            if ":" not in first_part:
                logger.error(f"❌ Kein ':' in strukturiertem Filter: {first_part}")
                return False
            
            field_name, search_text = first_part.split(":", 1)
            
            logger.info(f"🎛️ Strukturierter Filter: Feld='{field_name}', Text='{search_text}'")
            
            config = create_einzelsuche_config(field_name, search_text)
            return self.unified_filter.apply_filter_unified(config)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei strukturiertem Filter: {e}")
            return False
    
    def _handle_global_filter(self, filter_string: str) -> bool:
        """Behandelt globalen Filter (Gesamtsuche)"""
        try:
            logger.info(f"🌐 Globaler Filter: Text='{filter_string}'")
            
            config = create_gesamtsuche_config(filter_string)
            return self.unified_filter.apply_filter_unified(config)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei globalem Filter: {e}")
            return False
    
    # ========================================
    # KOMPATIBILITÄTS-METHODEN (für Migration)
    # ========================================
    
    def clear_all_filters(self) -> bool:
        """Alle Filter löschen - Kompatibilitäts-Methode"""
        return self.unified_filter.clear_all_filters()
    
    def count_visible_rows(self) -> int:
        """Zählt sichtbare Zeilen"""
        return self.unified_filter._count_visible_rows()


# ===============================
# HELPER-FUNKTIONEN FÜR MIGRATION  
# ===============================

def create_pdvm_linear_filter(table_widget, view_guid: str = None, column_mapping: dict = None) -> PDVMLinearFilterIntegration:
    """
    Factory-Funktion: Erstellt PDVM Linear Filter Integration
    
    Args:
        table_widget: PyQt5 QTableWidget
        view_guid: Optional View-GUID
        column_mapping: DEPRECATED - wird nicht mehr verwendet (Control-Key Patch)
        
    Returns:
        PDVMLinearFilterIntegration: Neues Filter-System mit Control-Key Unterstützung
    """
    if column_mapping:
        logger.info("⚠️ Column-Mapping übergeben, aber wird durch Control-Key Patch nicht verwendet")
    
    logger.info(f"🏭 Erstelle PDVM Linear Filter mit Control-Key Unterstützung")
    return PDVMLinearFilterIntegration(table_widget, view_guid)


def migrate_old_filter_calls(old_filter_manager, table_widget, view_guid: str = None):
    """
    Migration-Helper: Ersetzt alte Filter-Manager durch neue Integration
    
    Args:
        old_filter_manager: Alter Filter-Manager (wird ersetzt)
        table_widget: PyQt5 QTableWidget  
        view_guid: Optional View-GUID
        
    Returns:
        PDVMLinearFilterIntegration: Neues System
    """
    logger.info(f"🔄 Migriere Filter-System für View-GUID: {view_guid}")
    
    # Neue Integration erstellen
    new_integration = create_pdvm_linear_filter(table_widget, view_guid)
    
    logger.info("✅ Migration abgeschlossen - verwende neues lineares System")
    return new_integration