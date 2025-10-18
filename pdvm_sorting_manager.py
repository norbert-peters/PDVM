#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Sorting Manager - Erweiterte Sortierung und Gruppierung
========================================================

Features:
1. Header-Click Sortierung mit visueller Anzeige
2. Persistente Sortierung über GCS Controls
3. Multi-Level Sortierung für Gruppierung
4. Sortier-Dialog für erweiterte Konfiguration
5. Gruppierungsunterstützung (vorbereitet)

Architektur:
- Integration mit bestehender GCS Controls-Struktur
- Verwendung der SortDirection-Eigenschaft in Controls
- Kompatibel mit pdvm_view_dialog.py und pdvm_modern_view_widget.py
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from pdvm_central_systemsteuerung import get_gcs as gcs

logger = logging.getLogger(__name__)


class PdvmSortingManager:
    """
    Zentraler Manager für Sortierung und Gruppierung in PDVM Views
    
    FUNKTIONEN:
    1. Header-Click Sortierung mit Toggle (asc/desc)
    2. Persistente Speicherung in GCS Controls
    3. Multi-Level Sortierung (für Gruppierung)
    4. Visuelle Sortier-Indikatoren
    """
    
    def __init__(self, view_dialog, gcs_instance=None):
        """
        Initialisiert den Sorting Manager
        
        Args:
            view_dialog: PdvmViewDialog Instanz mit controls_config
            gcs_instance: GCS Instanz (optional, wird automatisch geholt)
        """
        self.view_dialog = view_dialog
        self.gcs = gcs_instance or gcs()
        
        # Aktueller Sortier-Status
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        
        # Multi-Level Sortierung (für Gruppierung)
        self.sort_levels = []  # [(column, direction), ...]
        
        # Lade gespeicherte Sortierung
        self._load_saved_sorting()
        
        logger.info(f"✅ Sorting Manager initialisiert - Current: {self.current_sort_column} ({self.current_sort_direction})")
    
    def setup_table_sorting(self, table_widget: QTableWidget):
        """
        Richtet Sortierung für eine Tabelle ein
        
        Args:
            table_widget: QTableWidget Instanz
        """
        if not table_widget:
            return
        
        # Sortierung aktivieren
        table_widget.setSortingEnabled(True)
        
        # Header-Click Handler verbinden
        header = table_widget.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(lambda logical_index: self._on_header_clicked(table_widget, logical_index))
        
        # Gespeicherte Sortierung anwenden
        self._apply_saved_sorting(table_widget)
        
        logger.info("✅ Tabellen-Sortierung eingerichtet")
    
    def _on_header_clicked(self, table_widget: QTableWidget, logical_index: int):
        """
        Handler für Header-Klicks
        
        Args:
            table_widget: QTableWidget Instanz
            logical_index: Index der geklickten Spalte
        """
        try:
            # Spalten-Name ermitteln
            if logical_index >= table_widget.columnCount():
                logger.warning(f"⚠️ Ungültiger Spalten-Index: {logical_index}")
                return
            
            # Column Name aus Header holen
            header_item = table_widget.horizontalHeaderItem(logical_index)
            if not header_item:
                logger.warning(f"⚠️ Kein Header-Item für Index {logical_index}")
                return
            
            column_text = header_item.text()
            # Multi-line Header berücksichtigen (Expert Mode)
            column_name = column_text.split('\n')[0].replace(' (Orig.)', '')
            
            # Control-Key aus controls_config ermitteln
            control_key = self._get_control_key_by_display_name(column_name)
            if not control_key:
                logger.warning(f"⚠️ Kein Control-Key für Spalte '{column_name}' gefunden")
                return
            
            # Sortierrichtung togglen
            if self.current_sort_column == control_key:
                # Gleiche Spalte: Richtung umkehren
                new_direction = 'desc' if self.current_sort_direction == 'asc' else 'asc'
            else:
                # Neue Spalte: Standard = asc
                new_direction = 'asc'
            
            # Sortierung anwenden
            self.apply_sorting(table_widget, control_key, new_direction)
            
            logger.info(f"🔄 Header-Click Sortierung: {control_key} -> {new_direction}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click: {e}")
    
    def apply_sorting(self, table_widget: QTableWidget, column_key: str, direction: str = 'asc'):
        """
        Wendet Sortierung auf Tabelle und Daten an
        WICHTIG: Zeigt immer _show Spalte an, sortiert aber nach _original wenn sortByOriginal=true
        
        Args:
            table_widget: QTableWidget Instanz
            column_key: Control-Key der zu sortierenden Spalte (immer _show)
            direction: 'asc' oder 'desc'
        """
        try:
            # Update internal state
            self.current_sort_column = column_key
            self.current_sort_direction = direction
            
            # Angezeigten Spalten-Index ermitteln (immer _show)
            display_column_index = self._get_column_index_by_key(column_key)
            if display_column_index is None:
                logger.warning(f"⚠️ Anzeige-Spalte '{column_key}' nicht in aktueller Ansicht")
                return
            
            # Bestimme Sortier-Spalte basierend auf sortByOriginal
            sort_column_key = self._get_sort_column_key(column_key)
            
            # Custom Sortierung wenn sortByOriginal=true
            if sort_column_key != column_key:
                logger.info(f"🔄 Custom Sortierung: Anzeige='{column_key}' Sortierung='{sort_column_key}'")
                self._apply_custom_sorting(table_widget, column_key, sort_column_key, direction)
            else:
                # Standard Qt-Sortierung
                qt_order = Qt.AscendingOrder if direction == 'asc' else Qt.DescendingOrder
                table_widget.sortItems(display_column_index, qt_order)
            
            # Visual Indicator im Header setzen (immer auf Anzeige-Spalte)
            header = table_widget.horizontalHeader()
            qt_order = Qt.AscendingOrder if direction == 'asc' else Qt.DescendingOrder
            header.setSortIndicator(display_column_index, qt_order)
            
            # In GCS Controls speichern
            self._save_sort_to_controls(column_key, direction)
            
            # Display Matrix sortieren mit UID-Referenz
            self._sort_display_matrix_by_uid(column_key, sort_column_key, direction)
            
            logger.info(f"✅ Sortierung angewendet: Anzeige='{column_key}' Sortierung='{sort_column_key}' -> {direction}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Sortierung: {e}")
    
    def _get_sort_column_key(self, display_column_key: str) -> str:
        """
        Bestimmt die tatsächliche Sortier-Spalte basierend auf sortByOriginal
        
        Args:
            display_column_key: Der angezeigten Spalten-Key
            
        Returns:
            Sortier-Spalten-Key (_original oder _show)
        """
        try:
            if not self.view_dialog or not hasattr(self.view_dialog, 'controls_config'):
                return display_column_key
            
            # Control-Konfiguration holen
            control = self.view_dialog.controls_config.get(display_column_key, {})
            
            # sortByOriginal prüfen
            sort_by_original = control.get('sortByOriginal', False)
            
            if sort_by_original:
                # Nach _original Spalte sortieren
                if display_column_key.endswith('_show'):
                    original_key = display_column_key.replace('_show', '_original')
                elif not display_column_key.endswith('_original'):
                    original_key = display_column_key + '_original'
                else:
                    original_key = display_column_key
                
                logger.debug(f"🔄 sortByOriginal=true: {display_column_key} -> {original_key}")
                return original_key
            else:
                # Nach angezeigter Spalte sortieren
                logger.debug(f"🔄 sortByOriginal=false: {display_column_key} -> {display_column_key}")
                return display_column_key
                
        except Exception as e:
            logger.error(f"❌ Fehler bei _get_sort_column_key: {e}")
            return display_column_key
    
    def _apply_custom_sorting(self, table_widget: QTableWidget, display_column_key: str, sort_column_key: str, direction: str):
        """
        Wendet Custom Sortierung an: Zeigt _show Spalte, sortiert nach _original
        
        Args:
            table_widget: QTableWidget Instanz
            display_column_key: Angezeigte Spalte (_show)
            sort_column_key: Spalte für Sortierung (_original)
            direction: Sortierrichtung
        """
        try:
            # Sortier-Daten aus Matrix holen
            if not hasattr(self.view_dialog, 'display_matrix') or not self.view_dialog.display_matrix:
                logger.warning("⚠️ Keine Display-Matrix für Custom Sortierung verfügbar")
                return
            
            # UID-basierte Sortierung vorbereiten
            rows_with_sort_values = []
            
            for row_data in self.view_dialog.display_matrix:
                if not row_data.get('display', True):
                    continue  # Versteckte Zeilen überspringen
                
                uid = row_data.get('uid', '')
                sort_value = row_data.get(sort_column_key, '')
                
                # Sortier-Wert normalisieren
                normalized_value = self._normalize_sort_value(sort_value)
                
                rows_with_sort_values.append((normalized_value, uid, row_data))
            
            # Nach Sortier-Wert sortieren
            reverse_order = (direction == 'desc')
            rows_with_sort_values.sort(key=lambda x: x[0], reverse=reverse_order)
            
            # UIDs in sortierter Reihenfolge extrahieren
            sorted_uids = [row[1] for row in rows_with_sort_values]
            
            # Tabelle entsprechend sortieren (basierend auf UID-Spalte)
            self._sort_table_by_uids(table_widget, sorted_uids)
            
            logger.debug(f"🔄 Custom Sortierung: {len(sorted_uids)} Zeilen nach '{sort_column_key}' sortiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Custom Sortierung: {e}")
    
    def _normalize_sort_value(self, value):
        """
        Normalisiert Sortier-Werte für korrekte Sortierung
        
        Args:
            value: Zu normalisierender Wert
            
        Returns:
            Normalisierter Sortier-Schlüssel
        """
        if value is None:
            return (2, "")  # None-Werte ans Ende
        
        # Numerische Werte
        try:
            return (0, float(str(value).replace(',', '.')))
        except (ValueError, TypeError):
            pass
        
        # String-Werte
        return (1, str(value).lower())
    
    def _sort_table_by_uids(self, table_widget: QTableWidget, sorted_uids: List[str]):
        """
        Sortiert QTableWidget basierend auf UID-Reihenfolge
        
        Args:
            table_widget: QTableWidget Instanz
            sorted_uids: Liste der UIDs in gewünschter Reihenfolge
        """
        try:
            # UID-Spalten-Index finden
            uid_column_index = None
            for col_idx in range(table_widget.columnCount()):
                header_item = table_widget.horizontalHeaderItem(col_idx)
                if header_item and header_item.text() == 'uid':
                    uid_column_index = col_idx
                    break
            
            if uid_column_index is None:
                logger.warning("⚠️ UID-Spalte nicht in Tabelle gefunden")
                return
            
            # Zeilen-Mapping erstellen: UID -> Zeilen-Index
            uid_to_row = {}
            for row_idx in range(table_widget.rowCount()):
                uid_item = table_widget.item(row_idx, uid_column_index)
                if uid_item:
                    uid = uid_item.text()
                    uid_to_row[uid] = row_idx
            
            # Zeilen entsprechend der UID-Reihenfolge neu anordnen
            # Hinweis: QTableWidget hat keine direkte moveRow Methode
            # Wir müssen die Daten zwischenspeichern und neu setzen
            
            # Alle Zeilen-Daten sammeln
            all_row_data = []
            for row_idx in range(table_widget.rowCount()):
                row_data = []
                for col_idx in range(table_widget.columnCount()):
                    item = table_widget.item(row_idx, col_idx)
                    row_data.append(item.text() if item else "")
                all_row_data.append(row_data)
            
            # Tabelle leeren
            table_widget.setRowCount(0)
            table_widget.setRowCount(len(sorted_uids))
            
            # Zeilen in neuer Reihenfolge einfügen
            new_row_idx = 0
            for uid in sorted_uids:
                if uid in uid_to_row:
                    old_row_idx = uid_to_row[uid]
                    old_row_data = all_row_data[old_row_idx]
                    
                    # Zeile neu setzen
                    for col_idx, cell_value in enumerate(old_row_data):
                        item = QTableWidgetItem(str(cell_value))
                        table_widget.setItem(new_row_idx, col_idx, item)
                    
                    new_row_idx += 1
            
            logger.debug(f"🔄 Tabelle nach UID-Reihenfolge sortiert: {new_row_idx} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren der Tabelle nach UIDs: {e}")
    
    def _get_control_key_by_display_name(self, display_name: str) -> Optional[str]:
        """
        Ermittelt Control-Key anhand des Anzeige-Namens
        PRIORITÄT: _show Spalten finden, da diese in der Tabelle angezeigt werden
        
        Args:
            display_name: Anzeige-Name der Spalte
            
        Returns:
            Control-Key oder None
        """
        if not self.view_dialog or not hasattr(self.view_dialog, 'controls_config'):
            return None
        
        # 1. Priorität: _show Spalten mit passendem Namen finden
        for key, control in self.view_dialog.controls_config.items():
            if key.endswith('_show') and control.get('name', '') == display_name:
                return key
        
        # 2. Priorität: Beliebige Spalte mit passendem Namen
        for key, control in self.view_dialog.controls_config.items():
            if control.get('name', '') == display_name:
                return key
        
        # 3. Fallback: Direkter Vergleich mit Key
        if display_name in self.view_dialog.controls_config:
            return display_name
        
        return None
    
    def _get_column_index_by_key(self, column_key: str) -> Optional[int]:
        """
        Ermittelt Spalten-Index anhand des Control-Keys
        
        Args:
            column_key: Control-Key
            
        Returns:
            Spalten-Index oder None
        """
        try:
            # Sichtbare Spalten holen
            if hasattr(self.view_dialog, 'display') and hasattr(self.view_dialog.display, '_get_visible_columns_from_gcs'):
                visible_columns = self.view_dialog.display._get_visible_columns_from_gcs()
            else:
                # Fallback: Alle Controls
                visible_columns = list(self.view_dialog.controls_config.keys())
            
            if column_key in visible_columns:
                return visible_columns.index(column_key)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ermitteln des Spalten-Index: {e}")
            return None
    
    def _save_sort_to_controls(self, column_key: str, direction: str):
        """
        Speichert Sortierung in GCS Controls
        
        Args:
            column_key: Control-Key der sortierten Spalte
            direction: Sortierrichtung
        """
        try:
            if not self.gcs or not hasattr(self.view_dialog, 'controls_config'):
                logger.warning("⚠️ GCS oder Controls nicht verfügbar für Sortier-Persistierung")
                return
            
            # Alle anderen Spalten auf None setzen
            for key in self.view_dialog.controls_config.keys():
                if key != column_key:
                    self.gcs.set_property(
                        "controls",
                        f"{key}_SortDirection",
                        ""
                    )
            
            # Aktuelle Spalte setzen
            self.gcs.set_property(
                "controls",
                f"{column_key}_SortDirection",
                direction
            )
            
            # Sortierte Spalte merken
            self.gcs.set_property(
                "controls",
                "current_sort_column",
                column_key
            )
            
            # 💾 Speichern in Datenbank
            if hasattr(self.gcs, 'save_values'):
                self.gcs.save_values()
            
            logger.info(f"💾 Sortierung in Controls gespeichert: {column_key} -> {direction}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Sortierung: {e}")
    
    def _load_saved_sorting(self):
        """Lädt gespeicherte Sortierung aus GCS Controls"""
        try:
            if not self.gcs:
                return
            
            # Aktuell sortierte Spalte
            sort_column = self.gcs.get_property("controls", "current_sort_column")
            if sort_column:
                self.current_sort_column = sort_column
                
                # Sortierrichtung für diese Spalte
                sort_direction = self.gcs.get_property(
                    "controls", 
                    f"{sort_column}_SortDirection"
                )
                if sort_direction:
                    self.current_sort_direction = sort_direction
                
                logger.info(f"📖 Gespeicherte Sortierung geladen: {self.current_sort_column} -> {self.current_sort_direction}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Sortierung: {e}")
    
    def _apply_saved_sorting(self, table_widget: QTableWidget):
        """
        Wendet gespeicherte Sortierung auf Tabelle an
        
        Args:
            table_widget: QTableWidget Instanz
        """
        if not self.current_sort_column:
            return
        
        try:
            column_index = self._get_column_index_by_key(self.current_sort_column)
            if column_index is not None:
                qt_order = Qt.AscendingOrder if self.current_sort_direction == 'asc' else Qt.DescendingOrder
                table_widget.sortItems(column_index, qt_order)
                
                # Visual Indicator setzen
                header = table_widget.horizontalHeader()
                header.setSortIndicator(column_index, qt_order)
                
                logger.info(f"🔄 Gespeicherte Sortierung angewendet: {self.current_sort_column} -> {self.current_sort_direction}")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden gespeicherter Sortierung: {e}")
    
    def _sort_display_matrix(self, column_key: str, direction: str):
        """
        Sortiert die display_matrix entsprechend der Tabellen-Sortierung
        
        Args:
            column_key: Control-Key der Sortierspalte
            direction: Sortierrichtung
        """
        try:
            if not hasattr(self.view_dialog, 'display_matrix') or not self.view_dialog.display_matrix:
                return
            
            # Nur sichtbare Zeilen sortieren
            visible_rows = [row for row in self.view_dialog.display_matrix if row.get('display', True)]
            hidden_rows = [row for row in self.view_dialog.display_matrix if not row.get('display', True)]
            
            # Einfache Sortier-Funktion - _original Spalten sind bereits korrekt formatiert
            def sort_key(row):
                value = row.get(column_key, '')
                
                # None-Werte ans Ende
                if value is None:
                    return ('zzz_none', 999999)
                
                # Numerische Sortierung versuchen
                try:
                    return (0, float(str(value).replace(',', '.')))
                except (ValueError, TypeError):
                    # Alphabetische Sortierung für Strings
                    return (1, str(value).lower())
            
            # Sortierung anwenden
            reverse_order = (direction == 'desc')
            visible_rows.sort(key=sort_key, reverse=reverse_order)
            
            # Matrix neu zusammensetzen: Sichtbare + Versteckte
            self.view_dialog.display_matrix = visible_rows + hidden_rows
            
            logger.debug(f"📊 Display Matrix sortiert nach '{column_key}': {len(visible_rows)} sichtbare Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren der Display Matrix: {e}")
    
    def _sort_display_matrix_by_uid(self, display_column_key: str, sort_column_key: str, direction: str):
        """
        Sortiert die Display-Matrix mit UID-Referenz-Erhaltung
        
        Args:
            display_column_key: Angezeigte Spalte
            sort_column_key: Spalte für Sortierung
            direction: Sortierrichtung
        """
        try:
            if not hasattr(self.view_dialog, 'display_matrix') or not self.view_dialog.display_matrix:
                return
            
            # Nur sichtbare Zeilen sortieren, UID-Referenz erhalten
            visible_rows = [row for row in self.view_dialog.display_matrix if row.get('display', True)]
            hidden_rows = [row for row in self.view_dialog.display_matrix if not row.get('display', True)]
            
            # UID-basierte Sortierung
            def sort_key(row):
                value = row.get(sort_column_key, '')
                
                # None-Werte ans Ende
                if value is None:
                    return ('zzz_none', 999999)
                
                # Numerische Sortierung versuchen
                try:
                    return (0, float(str(value).replace(',', '.')))
                except (ValueError, TypeError):
                    # Alphabetische Sortierung für Strings
                    return (1, str(value).lower())
            
            # Sortierung anwenden
            reverse_order = (direction == 'desc')
            visible_rows.sort(key=sort_key, reverse=reverse_order)
            
            # Matrix neu zusammensetzen: Sichtbare + Versteckte, UID-Referenzen erhalten
            self.view_dialog.display_matrix = visible_rows + hidden_rows
            
            logger.debug(f"📊 Display Matrix mit UID-Referenz sortiert: Display='{display_column_key}' Sort='{sort_column_key}' ({len(visible_rows)} sichtbare)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim UID-basierten Sortieren der Display Matrix: {e}")
    
    def get_sortable_columns(self) -> List[Tuple[str, str]]:
        """
        Gibt sortierbare Spalten zurück
        
        Returns:
            Liste von (control_key, display_name) Tupeln
        """
        sortable = []
        
        if not hasattr(self.view_dialog, 'controls_config'):
            return sortable
        
        for key, control in self.view_dialog.controls_config.items():
            # Prüfe ob Spalte sortierbar ist
            if control.get('sortable', True):  # Default: sortierbar
                display_name = control.get('name', key)
                sortable.append((key, display_name))
        
        return sortable
    
    def clear_sorting(self, table_widget: QTableWidget):
        """
        Entfernt alle Sortierung
        
        Args:
            table_widget: QTableWidget Instanz
        """
        try:
            # Internal state zurücksetzen
            self.current_sort_column = None
            self.current_sort_direction = 'asc'
            
            # Visual indicators entfernen
            header = table_widget.horizontalHeader()
            header.setSortIndicator(-1, Qt.AscendingOrder)
            
            # Controls löschen
            if self.gcs:
                self.gcs.set_property("controls", "current_sort_column", "")
            
            logger.info("🧹 Sortierung zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Sortierung: {e}")
    
    def apply_advanced_sorting(self, engine, group_config):
        """
        Bridge-Methode für erweiterte Sortierung mit Gruppierung
        
        Args:
            engine: PdvmAdvancedSortingEngine Instanz
            group_config: GroupConfig Instanz
            
        Returns:
            bool: True wenn erfolgreich angewendet
        """
        try:
            from pdvm_advanced_sorting_manager import PdvmAdvancedSortingManager
            
            # Verwende den erweiterten Manager
            advanced_manager = PdvmAdvancedSortingManager()
            
            # Anwenden
            success = advanced_manager.apply_advanced_sorting(engine, group_config)
            
            if success and hasattr(self.view_dialog, 'display') and hasattr(self.view_dialog.display, 'table'):
                # Auf Tabelle anwenden
                table = self.view_dialog.display.table
                
                # Daten aus der Matrix extrahieren
                data = []
                for row_data in self.view_dialog.display_matrix:
                    if row_data.get('display', True):  # Nur sichtbare Zeilen
                        data.append(row_data)
                
                # Auf Tabelle anwenden
                success = advanced_manager.apply_to_table(table, data)
                
                if success:
                    # Status in view_dialog speichern für spätere Referenz
                    self.view_dialog.advanced_sorting_manager = advanced_manager
                    
                    logger.info("✅ Erweiterte Sortierung erfolgreich angewendet")
                    
                    # Sortier-Indikatoren setzen
                    if engine.sort_levels:
                        first_level = engine.sort_levels[0]
                        column_key = first_level.column_key
                        direction = first_level.direction
                        
                        # Versuche Spalten-Index zu finden
                        header = table.horizontalHeader()
                        for i in range(table.columnCount()):
                            header_item = table.horizontalHeaderItem(i)
                            if header_item:
                                column_name = header_item.text().split('\n')[0].replace(' (Orig.)', '')
                                control_key = self._get_control_key_by_display_name(column_name)
                                if control_key == column_key:
                                    sort_order = Qt.AscendingOrder if direction == 'asc' else Qt.DescendingOrder
                                    header.setSortIndicator(i, sort_order)
                                    break
                
                return success
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweiterter Sortierung: {e}")
            return False


if __name__ == "__main__":
    print("📊 PDVM Sorting Manager")
    print("Features:")
    print("- Header-Click Sortierung mit Toggle")
    print("- Persistente Speicherung in GCS Controls")
    print("- Multi-Level Sortierung (vorbereitet)")
    print("- Visuelle Sortier-Indikatoren")