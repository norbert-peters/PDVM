#!/usr/bin/env python3
"""
PDVM View Widget mit Tooltip-Unterstützung für 3-Ebenen-Matrix

Zeigt Tooltips mit AB-Datum (formatiert) für jede Tabellenzelle
"""

import logging
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, 
                             QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt

# 3-Ebenen Array-Struktur
from pdvm_matrix_constants import (
    WERT, ABDATUM, FORMATIERT,
    get_wert, get_abdatum, get_formatiert
)

logger = logging.getLogger(__name__)


class PdvmViewTableWidgetWithTooltips(QTableWidget):
    """
    Table Widget mit automatischer Tooltip-Generierung aus 3-Ebenen-Matrix
    
    TOOLTIP-FORMAT:
    ```
    Wert: <value>
    Geändert: <formatiertes_abdatum>
    ```
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.matrix_data = []  # Projection data mit allen 3 Ebenen
        self.visible_columns = []
        
    def populate_from_projection(self, projection_data, visible_columns):
        """
        Befüllt Tabelle aus Projection Matrix mit Tooltip-Unterstützung
        
        🆕 PHASE 3: Unterstützt Gruppen-Header-Zeilen!
        
        Args:
            projection_data: Liste von Row-Dicts aus ProjectionMatrix
            visible_columns: Liste der Spaltennamen (ohne __abdatum/__formatiert)
        """
        try:
            logger.info(f"📊 Befülle Tabelle: {len(projection_data)} Zeilen, {len(visible_columns)} Spalten")
            
            self.matrix_data = projection_data
            self.visible_columns = visible_columns
            
            # Tabelle konfigurieren
            self.setRowCount(len(projection_data))
            self.setColumnCount(len(visible_columns))
            
            # Header setzen
            headers = []
            for col_name in visible_columns:
                # Spaltennamen: _original → "Original", _show → anzeigbarer Name
                display_name = col_name.replace('_original', '').replace('_show', '').replace('_', ' ').title()
                headers.append(display_name)
            self.setHorizontalHeaderLabels(headers)
            
            # ✅ ARRAY: Daten befüllen mit Tooltips + Gruppen-Header (Phase 3)
            for row_idx, row_data in enumerate(projection_data):
                # 🆕 PHASE 3: Prüfe row_type Dict für Zeilen-Typ
                row_type_dict = row_data.get('row_type', {})
                row_type = row_type_dict.get('type', 'data') if isinstance(row_type_dict, dict) else 'data'
                
                if row_type == 'group_header':
                    # Gruppen-Header-Zeile rendern
                    self._render_group_header_row(row_idx, row_type_dict, visible_columns)
                    continue  # Nächste Zeile
                
                # Normale Daten-Zeile
                for col_idx, col_name in enumerate(visible_columns):
                    # ✅ ARRAY: Zelle holen und Ebenen extrahieren
                    cell = row_data.get(col_name, [None, None, None])
                    
                    # EBENE 1: Wert für Anzeige
                    value = get_wert(cell)
                    
                    # EBENE 2: AB-Datum (roh)
                    abdatum = get_abdatum(cell)
                    
                    # EBENE 3: Formatiertes AB-Datum
                    formatiert = get_formatiert(cell)
                    
                    # Table Item erstellen
                    item = QTableWidgetItem(str(value) if value is not None else '')
                    
                    # === TOOLTIP SETZEN ===
                    if formatiert:
                        tooltip = f"Wert: {value}\nGeändert: {formatiert}"
                        item.setToolTip(tooltip)
                        logger.debug(f"✅ Tooltip gesetzt für [{row_idx},{col_idx}] {col_name}: {tooltip}")
                    elif abdatum:
                        # Fallback: Zeige rohes Abdatum wenn Formatierung fehlt
                        tooltip = f"Wert: {value}\nGeändert: {abdatum} (roh)"
                        item.setToolTip(tooltip)
                    else:
                        # Kein Abdatum: Nur Wert im Tooltip
                        tooltip = f"Wert: {value}"
                        item.setToolTip(tooltip)
                    
                    # Item in Tabelle setzen
                    self.setItem(row_idx, col_idx, item)
            
            logger.info(f"✅ Tabelle befüllt mit Tooltips für {len(projection_data)} Zeilen")
            
            # Spaltenbreite anpassen
            self.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Tabelle: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_group_header_row(self, row_idx: int, row_type_dict: dict, visible_columns: list):
        """
        🆕 PHASE 3: Rendert eine Gruppen-Header-Zeile
        
        🆕 NEUE ARCHITEKTUR: row_type_dict enthält alle Metadaten
        
        Args:
            row_idx: Zeilen-Index
            row_type_dict: row_type Dict mit Gruppen-Metadaten
            visible_columns: Liste der sichtbaren Spalten
        """
        try:
            # 🆕 Gruppen-Informationen aus row_type Dict extrahieren
            group_level = row_type_dict.get('level', 0)
            group_column = row_type_dict.get('column', '')
            group_value = row_type_dict.get('value', '')
            group_count = row_type_dict.get('count', 0)
            is_collapsed = row_type_dict.get('collapsed', False)
            group_id = row_type_dict.get('group_id', '')
            
            # Einrückung nach Ebene
            indent = "  " * group_level
            
            # Icon: ▼ (offen) oder ▶ (zu)
            icon = "▶" if is_collapsed else "▼"
            
            # Spaltenname formatieren
            display_column = group_column.replace('_original', '').replace('_show', '').replace('_', ' ').title()
            
            # Text zusammenbauen
            text = f"{indent}{icon} {display_column}: {group_value}"
            if group_count > 0:
                text += f" ({group_count} Einträge)"
            
            # Item erstellen
            item = QTableWidgetItem(text)
            
            # 🎨 STYLING: Gruppen-Header hervorheben
            from PyQt5.QtGui import QColor, QFont
            
            # Hintergrund: Hellblau (je nach Ebene unterschiedliche Töne)
            if group_level == 0:
                item.setBackground(QColor("#e3f2fd"))  # Hellblau
            elif group_level == 1:
                item.setBackground(QColor("#bbdefb"))  # Mittelblau
            else:
                item.setBackground(QColor("#90caf9"))  # Dunkelblau
            
            # Font: Bold + größer
            font = item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            item.setFont(font)
            
            # Tooltip mit Details
            tooltip = (
                f"Gruppierung: {display_column}\n"
                f"Wert: {group_value}\n"
                f"Ebene: {group_level}\n"
                f"Einträge: {group_count}\n"
                f"Status: {'Eingeklappt' if is_collapsed else 'Ausgeklappt'}\n"
                f"ID: {group_id}"
            )
            item.setToolTip(tooltip)
            
            # Speichere Group-ID im Item für Click-Handler
            from PyQt5.QtCore import Qt
            item.setData(Qt.UserRole, group_id)
            item.setData(Qt.UserRole + 1, 'GROUP_HEADER')  # Marker
            
            # Item in erste Spalte setzen
            self.setItem(row_idx, 0, item)
            
            # 🔗 SPANNING: Über alle Spalten
            if len(visible_columns) > 1:
                self.setSpan(row_idx, 0, 1, len(visible_columns))
            
            logger.debug(f"✅ Gruppen-Header gerendert: Level {group_level}, {group_value} ({group_count})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern von Gruppen-Header: {e}")
            import traceback
            logger.error(traceback.format_exc())


class PdvmViewWidgetComplete(QWidget):
    """
    Vollständiges View Widget mit Tabelle und Steuerungs-Buttons
    """
    
    def __init__(self, daten_manager, parent=None):
        super().__init__(parent)
        self.daten_manager = daten_manager
        self.init_ui()
        
    def init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        
        # === HEADER mit Info ===
        header_layout = QHBoxLayout()
        self.info_label = QLabel("View")
        header_layout.addWidget(self.info_label)
        
        # Refresh Button
        self.refresh_btn = QPushButton("🔄 Stichtag Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.refresh_btn.setToolTip("Pipeline mit neuem Stichtag durchlaufen")
        header_layout.addWidget(self.refresh_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # === TABLE mit Tooltips ===
        self.table = PdvmViewTableWidgetWithTooltips(self)
        layout.addWidget(self.table)
        
        # Initiale Befüllung
        self.load_data()
    
    def load_data(self):
        """Lädt Daten aus DatenManager Pipeline"""
        try:
            logger.info("📥 Lade Daten aus Pipeline...")
            
            # Projection Data holen
            projection_data = self.daten_manager.matrix_pipeline.get_projection_data()
            visible_columns = self.daten_manager.matrix_pipeline.get_projection_columns()
            
            logger.info(f"📊 {len(projection_data)} Zeilen, {len(visible_columns)} Spalten")
            
            # Tabelle befüllen
            self.table.populate_from_projection(projection_data, visible_columns)
            
            # Info aktualisieren
            row_count = len(projection_data)
            view_guid = self.daten_manager.view_guid
            self.info_label.setText(f"View: {view_guid} | {row_count} Zeilen")
            
            logger.info("✅ Daten geladen und angezeigt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            import traceback
            traceback.print_exc()
    
    def on_refresh_clicked(self):
        """Refresh Button geklickt"""
        try:
            logger.info("🔄 === REFRESH BUTTON GEKLICKT ===")
            
            # Pipeline mit neuem Stichtag durchlaufen
            success = self.daten_manager.rebuild_pipeline_with_stichtag()
            
            if success:
                # View neu laden
                self.load_data()
                logger.info("✅ Refresh abgeschlossen")
            else:
                logger.error("❌ Refresh fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh: {e}")
            import traceback
            traceback.print_exc()


# === USAGE EXAMPLE ===
def create_view_widget_with_tooltips(daten_manager, parent=None):
    """
    Factory-Funktion: Erstellt View Widget mit Tooltip-Unterstützung
    
    Args:
        daten_manager: PdvmViewDatenManager Instanz
        parent: Parent Widget
        
    Returns:
        PdvmViewWidgetComplete mit funktionierenden Tooltips
    """
    widget = PdvmViewWidgetComplete(daten_manager, parent)
    logger.info(f"✅ View Widget mit Tooltips erstellt für: {daten_manager.view_guid}")
    return widget
