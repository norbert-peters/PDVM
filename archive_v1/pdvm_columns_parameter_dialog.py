#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PdvmColumnsParameterDialog - Spalten-Parameter Dialog
Zeigt echte Show/Expert Parameter für alle Felder
Expert-Felder nur im Expert-Modus änderbar
Kompakte, effiziente Darstellung
"""

import logging
from typing import List, Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QCheckBox, QHeaderView, QButtonGroup,
    QGroupBox, QScrollArea, QWidget, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmColumnsParameterDialog(QDialog):
    """
    Dialog für Spalten-Parameter Verwaltung.
    Zeigt echte Show/Expert Parameter für alle Felder.
    Expert-Felder nur im Expert-Modus änderbar.
    """
    
    def __init__(self, view_manager, expert_mode=False, mode='user', parent=None):
        super().__init__(parent)
        self.view_manager = view_manager
        self.expert_mode = expert_mode
        self.mode = mode  # 'admin' oder 'user'
        self.column_data = []
        self.changes_made = False
        
        self.setWindowTitle("📊 Spalten Parameter")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_column_data()
        self._initialize_show_order_system()  # NEUES SYSTEM - vor UI-Aufbau
        self._reload_ui_only()  # UI nach show_order Initialisierung neu laden
        
        logger.info(f"📊 Spalten-Parameter Dialog geöffnet (Expert-Modus: {expert_mode}, App-Modus: {mode})")
    
    def _setup_ui(self):
        """Erstellt die UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        self._create_header(layout)
        
        # Spalten-Tabelle
        self._create_columns_table(layout)
        
        # Button-Bereich
        self._create_buttons(layout)
    
    def _create_header(self, parent_layout):
        """Erstellt den Header-Bereich"""
        header_layout = QVBoxLayout()
        
        # Titel
        title = QLabel("📊 Spalten Parameter verwalten")
        title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        header_layout.addWidget(title)
        
        # Info-Text basierend auf neuer Logik
        if self.expert_mode:
            info_text = "🔧 Expert-Modus: Alle Spalten können für 'expert' bearbeitet werden"
            info_style = "color: #ff6600; font-size: 12px; padding: 5px;"
        else:
            info_text = "👤 Normal-Modus: Nur Felder mit expert=false können für 'show' bearbeitet werden"
            info_style = "color: #666; font-size: 12px; padding: 5px;"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet(info_style)
        header_layout.addWidget(info_label)
        
        parent_layout.addLayout(header_layout)
    
    def _create_columns_table(self, parent_layout):
        """Erstellt die Spalten-Tabelle mit getrennten Modi"""
        # Scroll-Bereich für kompakte Darstellung
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Tabelle
        self.columns_table = QTableWidget()
        
        # GETRENNTE UI-MODI für bessere Stabilität
        if self.expert_mode:
            # EXPERT-MODUS: Vollständige Spalten-Verwaltung
            self.columns_table.setColumnCount(5)
            self.columns_table.setHorizontalHeaderLabels([
                "Spalte", "Anzeige", "Show", "Expert", "Typ"
            ])
            # Header-Konfiguration Expert-Modus
            header = self.columns_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Spalte
            header.setSectionResizeMode(1, QHeaderView.Stretch)          # Anzeige
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Show
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Expert
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Typ
        else:
            # NORMAL-MODUS: Vereinfachte Spalten-Verwaltung
            self.columns_table.setColumnCount(3)
            self.columns_table.setHorizontalHeaderLabels([
                "Spalte", "Anzeige", "Sichtbar"
            ])
            # Header-Konfiguration Normal-Modus
            header = self.columns_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Spalte
            header.setSectionResizeMode(1, QHeaderView.Stretch)          # Anzeige
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Sichtbar
        
        # ZEILEN-AUSWAHL für Verschiebung aktivieren - VERBESSERT
        self.columns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.columns_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Zeilen-Markierung visuell hervorheben
        self.columns_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: black;
                gridline-color: #ddd;
                selection-background-color: #0078d4;
                selection-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 2px;
                font-size: 11px;
                color: black;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
                border: 2px solid #005a9e;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: black;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # Row-Click Handler für bessere Auswahl
        self.columns_table.itemClicked.connect(self._on_row_clicked)
        
        # Zeilenhöhe reduzieren
        self.columns_table.verticalHeader().setDefaultSectionSize(25)
        self.columns_table.verticalHeader().setVisible(False)
        
        scroll_area.setWidget(self.columns_table)
        parent_layout.addWidget(scroll_area, 1)
    
    def _create_buttons(self, parent_layout):
        """Erstellt den Button-Bereich"""
        button_layout = QHBoxLayout()
        
        # Links: Spalten-Reordering-Bereich
        reorder_group = QGroupBox("🔄 Spalten-Reihenfolge")
        reorder_layout = QVBoxLayout(reorder_group)
        
        # Info-Text
        info_label = QLabel("Markieren Sie eine Spalte und verschieben Sie sie:")
        info_label.setStyleSheet("font-size: 11px; color: #666;")
        reorder_layout.addWidget(info_label)
        
        # Rauf/Runter Buttons
        reorder_buttons_layout = QHBoxLayout()
        
        self.move_up_button = QPushButton("� Nach oben")
        self.move_up_button.clicked.connect(self._move_column_up)
        self.move_up_button.setToolTip("Markierte Spalte nach oben verschieben")
        reorder_buttons_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("🔽 Nach unten")
        self.move_down_button.clicked.connect(self._move_column_down)
        self.move_down_button.setToolTip("Markierte Spalte nach unten verschieben")
        reorder_buttons_layout.addWidget(self.move_down_button)
        
        reorder_layout.addLayout(reorder_buttons_layout)
        button_layout.addWidget(reorder_group)
        
        # Spacer
        button_layout.addStretch(1)
        
        # Rechts: Standard-Buttons-Bereich
        standard_group = QGroupBox("🎛️ Aktionen")
        standard_layout = QVBoxLayout(standard_group)
        
        # Erste Zeile: Alle/Keine
        toggle_layout = QHBoxLayout()
        
        show_all_btn = QPushButton("👁️ Alle anzeigen")
        show_all_btn.clicked.connect(self._show_all_columns)
        toggle_layout.addWidget(show_all_btn)
        
        hide_all_btn = QPushButton("🙈 Alle verstecken")
        hide_all_btn.clicked.connect(self._hide_all_columns)
        toggle_layout.addWidget(hide_all_btn)
        
        standard_layout.addLayout(toggle_layout)
        
        # Zweite Zeile: OK/Abbrechen
        ok_cancel_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        ok_cancel_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._apply_changes)
        ok_cancel_layout.addWidget(ok_btn)
        
        standard_layout.addLayout(ok_cancel_layout)
        button_layout.addWidget(standard_group)
        
        parent_layout.addLayout(button_layout)
    
    def _load_column_data(self):
        """EINFACHES ORDER-SYSTEM - Lädt Spalten mit automatischer show_order"""
        try:
            # Spalten-Info vom ViewManager holen
            column_info = self.view_manager.get_spalten_info()
            if not column_info:
                logger.warning("⚠️ Keine Spalten-Information verfügbar")
                return
            
            self.column_data = column_info.copy()
            
            # Daten sind bereit - UI wird separat geladen nach show_order Initialisierung
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Spalten-Daten: {e}")
    
    def _reload_ui_only(self):
        """Lädt nur die UI neu ohne Daten vom ViewManager neu zu holen (für Move-Operationen)"""
        try:
            # Verwende das neue unabhängige System
            if self.expert_mode:
                self._load_expert_mode_simple()
            else:
                self._load_normal_mode_simple()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim UI-Neuladen: {e}")
    
    def _load_expert_mode_simple(self):
        """Expert-Modus: Alle Spalten nach 'order' sortiert"""
        # Verwende neue Funktion für Expert-Mode
        sorted_data = self._get_expert_mode_columns()
        self.columns_table.setRowCount(len(sorted_data))
        
        for row, col_info in enumerate(sorted_data):
            # Spalten-Name
            name_item = QTableWidgetItem(col_info.get('name', ''))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            from PyQt5.QtGui import QColor, QBrush
            name_item.setForeground(QBrush(QColor('black')))
            name_item.setBackground(QBrush(QColor('white')))
            self.columns_table.setItem(row, 0, name_item)
            
            # Anzeige-Name + Order-Info  
            order_info = col_info.get('order', 'N/A')
            display_text = f"{col_info.get('anzeige', '')} (#{order_info})"
            anzeige_item = QTableWidgetItem(display_text)
            anzeige_item.setFlags(anzeige_item.flags() & ~Qt.ItemIsEditable)
            anzeige_item.setForeground(QBrush(QColor('black')))
            anzeige_item.setBackground(QBrush(QColor('white')))
            self.columns_table.setItem(row, 1, anzeige_item)
            
            # Show Checkbox - MODUS-ABHÄNGIG!
            show_checkbox = QCheckBox()
            if self.expert_mode:
                # Expert-Mode: 'show' Feld verwenden
                show_checkbox.setChecked(col_info.get('show', False))
            else:
                # Normal-Mode: 'show_show' Feld verwenden!
                show_checkbox.setChecked(col_info.get('show_show', False))
            show_checkbox.setEnabled(True)
            show_checkbox.stateChanged.connect(self._on_column_changed)
            self.columns_table.setCellWidget(row, 2, show_checkbox)
            
            # Expert Checkbox
            expert_checkbox = QCheckBox()
            expert_checkbox.setChecked(col_info.get('expert', False))
            expert_checkbox.stateChanged.connect(self._on_column_changed)
            self.columns_table.setCellWidget(row, 3, expert_checkbox)
            
            # Typ
            typ_item = QTableWidgetItem(col_info.get('type', ''))
            typ_item.setFlags(typ_item.flags() & ~Qt.ItemIsEditable)
            typ_item.setForeground(QBrush(QColor('black')))
            
            # Typ-spezifische Farben
            typ = col_info.get('type', '')
            if typ == 'original':
                typ_item.setBackground(QBrush(QColor('#ffe6e6')))
            elif typ == 'show':
                typ_item.setBackground(QBrush(QColor('#e6ffe6')))
            elif typ == 'system':
                typ_item.setBackground(QBrush(QColor('#e6e6ff')))
            else:
                typ_item.setBackground(QBrush(QColor('white')))
            
            self.columns_table.setItem(row, 4, typ_item)
        
        # Sortierte Daten für Verschiebung speichern
        self.current_display_data = sorted_data
    
    def _load_normal_mode_simple(self):
        """Normal-Modus: Nur Normal-Spalten nach 'show_order' sortiert"""
        # Verwende neue Funktion für Normal-Mode (nur expert=false)
        sorted_data = self._get_normal_mode_columns()
        
        # Zusätzlicher Filter: Nur sichtbare Spalten anzeigen
        visible_data = [col for col in sorted_data if col.get('show', False)]
        
        logger.info(f"📊 Normal-Modus: {len(visible_data)} sichtbare von {len(sorted_data)} Normal-Spalten")
        
        self.columns_table.setRowCount(len(visible_data))
        
        for row, col_info in enumerate(visible_data):
            # Spalten-Name
            name_item = QTableWidgetItem(col_info.get('name', ''))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            from PyQt5.QtGui import QColor, QBrush
            name_item.setForeground(QBrush(QColor('black')))
            name_item.setBackground(QBrush(QColor('white')))
            self.columns_table.setItem(row, 0, name_item)
            
            # Anzeige-Name + show_order-Info
            show_order_info = col_info.get('show_order', 'N/A')
            display_text = f"{col_info.get('anzeige', '')} (#{show_order_info})"
            anzeige_item = QTableWidgetItem(display_text)
            anzeige_item.setFlags(anzeige_item.flags() & ~Qt.ItemIsEditable)
            anzeige_item.setForeground(QBrush(QColor('black')))
            anzeige_item.setBackground(QBrush(QColor('white')))
            self.columns_table.setItem(row, 1, anzeige_item)
            
            # Sichtbar Checkbox
            show_checkbox = QCheckBox()
            show_checkbox.setChecked(col_info.get('show', False))
            show_checkbox.setEnabled(True)
            show_checkbox.stateChanged.connect(self._on_column_changed)
            self.columns_table.setCellWidget(row, 2, show_checkbox)
        
        # Sortierte Daten für Verschiebung speichern
        self.current_display_data = visible_data
    
    def _on_column_changed(self):
        """Callback wenn Spalten-Parameter geändert wird"""
        self.changes_made = True
    
    def _show_all_columns(self):
        """Zeigt alle Spalten an"""
        for row in range(self.columns_table.rowCount()):
            if self.expert_mode:
                show_checkbox = self.columns_table.cellWidget(row, 2)
            else:
                show_checkbox = self.columns_table.cellWidget(row, 1)
                
            if show_checkbox and show_checkbox.isEnabled():
                show_checkbox.setChecked(True)
        
        logger.info("👁️ Alle Spalten auf 'anzeigen' gesetzt")
    
    def _move_column_up(self):
        """EINFACH: Tausche show_order/order-Werte zwischen Nachbarn"""
        current_row = self.columns_table.currentRow()
        if current_row <= 0:
            QMessageBox.information(self, "Info", "Erste Spalte kann nicht nach oben verschoben werden.")
            return
        
        try:
            current_data = getattr(self, 'current_display_data', [])
            if current_row >= len(current_data):
                return
            
            # Aktuelle und Ziel-Spalte
            current_col = current_data[current_row]
            target_col = current_data[current_row - 1]
            
            # Einfacher Tausch der relevanten Order-Felder
            if self.expert_mode:
                # Expert: order tauschen
                current_order = current_col.get('order', 0)
                target_order = target_col.get('order', 0)
                current_col['order'] = target_order
                target_col['order'] = current_order
                logger.info(f"🔼 Order getauscht: {current_col.get('name')} ↔ {target_col.get('name')}")
            else:
                # Normal: show_order tauschen
                current_show_order = current_col.get('show_order', 0)
                target_show_order = target_col.get('show_order', 0)
                current_col['show_order'] = target_show_order
                target_col['show_order'] = current_show_order
                logger.info(f"🔼 Show_order getauscht: {current_col.get('name')} ↔ {target_col.get('name')}")
            
            # UI neu laden und Position merken
            moved_column_name = current_col.get('name')
            self._reload_ui_only()
            self._select_column_by_name(moved_column_name)
            self.changes_made = True
            
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"❌ Fehler beim Verschieben: {e}")
            logger.error(f"❌ Fehler _move_column_up: {e}")
    
    def _move_column_down(self):
        """EINFACH: Tausche show_order/order-Werte zwischen Nachbarn"""
        current_row = self.columns_table.currentRow()
        current_data = getattr(self, 'current_display_data', [])
        
        if current_row < 0 or current_row >= len(current_data) - 1:
            QMessageBox.information(self, "Info", "Letzte Spalte kann nicht nach unten verschoben werden.")
            return
        
        try:
            # Aktuelle und Ziel-Spalte
            current_col = current_data[current_row]
            target_col = current_data[current_row + 1]
            
            # Einfacher Tausch der relevanten Order-Felder
            if self.expert_mode:
                # Expert: order tauschen
                current_order = current_col.get('order', 0)
                target_order = target_col.get('order', 0)
                current_col['order'] = target_order
                target_col['order'] = current_order
                logger.info(f"🔽 Order getauscht: {current_col.get('name')} ↔ {target_col.get('name')}")
            else:
                # Normal: show_order tauschen
                current_show_order = current_col.get('show_order', 0)
                target_show_order = target_col.get('show_order', 0)
                current_col['show_order'] = target_show_order
                target_col['show_order'] = current_show_order
                logger.info(f"🔽 Show_order getauscht: {current_col.get('name')} ↔ {target_col.get('name')}")
            
            # UI neu laden und Position merken
            moved_column_name = current_col.get('name')
            self._reload_ui_only()
            self._select_column_by_name(moved_column_name)
            self.changes_made = True
            
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"❌ Fehler beim Verschieben: {e}")
            logger.error(f"❌ Fehler _move_column_down: {e}")
    
    def _select_column_by_name(self, column_name):
        """Markiert eine Spalte anhand des Namens nach Neu-Laden"""
        if not column_name:
            return
        
        current_data = getattr(self, 'current_display_data', self.column_data)
        
        for row, col_info in enumerate(current_data):
            if col_info.get('name') == column_name:
                self.columns_table.selectRow(row)
                self.columns_table.setCurrentCell(row, 0)
                logger.debug(f"📍 Spalte '{column_name}' markiert in Zeile {row}")
                return
        
        logger.warning(f"⚠️ Spalte '{column_name}' nicht gefunden zum Markieren")
    
    def _on_row_clicked(self, item):
        """Behandelt Zeilen-Clicks für verbesserte Auswahl"""
        if item:
            row = item.row()
            self.columns_table.selectRow(row)
            # Visual Feedback - aktualisiere Button-Status
            self._update_move_buttons(row)
    
    def _update_move_buttons(self, current_row):
        """Aktualisiert den Status der Verschiebe-Buttons"""
        if not hasattr(self, 'move_up_button') or not hasattr(self, 'move_down_button'):
            return
        
        # Aktuelle Anzeige-Daten verwenden
        current_data = getattr(self, 'current_display_data', self.column_data)
        max_row = len(current_data) - 1
        
        # Button-Status setzen
        self.move_up_button.setEnabled(current_row > 0)
        self.move_down_button.setEnabled(current_row >= 0 and current_row < max_row)
        
        # Visual Feedback über aktuell markierte Zeile
        if current_row >= 0 and current_row < len(current_data):
            col_info = current_data[current_row]
            spalten_name = col_info.get('anzeige', f'Zeile {current_row + 1}')
            
            # Order-Info je nach Modus
            if self.expert_mode:
                order_info = f"order={col_info.get('order', 'N/A')}"
            else:
                order_info = f"show_order={col_info.get('show_order', 'N/A')}"
            
            info_text = f"Markiert: '{spalten_name}' ({order_info})"
            
            # Info in Button-Tooltips aktualisieren
            self.move_up_button.setToolTip(f"'{spalten_name}' nach oben verschieben" if current_row > 0 else "Erste Spalte - kann nicht nach oben")
            self.move_down_button.setToolTip(f"'{spalten_name}' nach unten verschieben" if current_row < max_row else "Letzte Spalte - kann nicht nach unten")

    def _hide_all_columns(self):
        """Versteckt alle Spalten (außer system-Spalten)"""
        for row in range(self.columns_table.rowCount()):
            # System-Spalten nicht verstecken (nur im Expert-Modus verfügbar)
            if self.expert_mode:
                typ_item = self.columns_table.item(row, 4)  # Typ-Spalte im Expert-Modus
                if typ_item and typ_item.text() == 'system':
                    continue
                show_checkbox = self.columns_table.cellWidget(row, 2)
            else:
                # Im Normal-Modus gibt es keine Typ-Spalte, also alle Spalten behandeln
                # Aber System-Spalten über column_data identifizieren
                if row < len(self.column_data) and self.column_data[row].get('type') == 'system':
                    continue
                show_checkbox = self.columns_table.cellWidget(row, 1)
                
            if show_checkbox and show_checkbox.isEnabled():
                show_checkbox.setChecked(False)
        
        logger.info("🙈 Alle Spalten (außer System) auf 'verstecken' gesetzt")
    
    def _apply_changes(self):
        """Wendet die Änderungen an"""
        try:
            if not self.changes_made:
                self.accept()
                return
            
            # Aktuell angezeigte Daten verwenden (nach Move-Operationen)
            current_data = getattr(self, 'current_display_data', self.column_data)
            
            # Änderungen sammeln basierend auf aktueller Tabelle
            for row in range(self.columns_table.rowCount()):
                if row >= len(current_data):
                    continue
                    
                current_col = current_data[row]
                col_name = current_col.get('name')
                
                # Show/Expert Checkboxes für diese Zeile holen
                if self.expert_mode:
                    show_checkbox = self.columns_table.cellWidget(row, 2)
                    expert_checkbox = self.columns_table.cellWidget(row, 3)
                else:
                    show_checkbox = self.columns_table.cellWidget(row, 1)
                    expert_checkbox = None  # Nicht verfügbar im Normal-Modus
                
                # Entsprechende Spalte in column_data finden und aktualisieren
                for col_data in self.column_data:
                    if col_data.get('name') == col_name:
                        # Show-Status aktualisieren - MODUS-ABHÄNGIG!
                        if show_checkbox:
                            if self.expert_mode:
                                # Expert-Mode: 'show' Feld verwenden
                                col_data['show'] = show_checkbox.isChecked()
                                logger.debug(f"🔧 Expert: {col_name} show={show_checkbox.isChecked()}")
                            else:
                                # Normal-Mode: 'show_show' Feld verwenden!
                                col_data['show_show'] = show_checkbox.isChecked()
                                logger.debug(f"👤 Normal: {col_name} show_show={show_checkbox.isChecked()}")
                        
                        # Expert-Status aktualisieren (nur im Expert-Modus)
                        if expert_checkbox and self.expert_mode:
                            col_data['expert'] = expert_checkbox.isChecked()
                        break
            
            # Änderungen an ViewManager übertragen
            self._save_to_view_manager()
            
            self.accept()
            logger.info("✅ Spalten-Parameter Änderungen angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Änderungen: {e}")
    
    def _save_to_view_manager(self):
        """Speichert den AKTUELLEN STAND ohne Änderungen"""
        try:
            # Display-Control Struktur vom ViewManager holen
            display_control = self.view_manager.display_view_control
            if not display_control or not hasattr(display_control, 'columns'):
                logger.error("❌ Keine Display-Control Struktur verfügbar")
                return
            
            # EINFACH: Aktuellen Stand der column_data speichern
            for col_data in self.column_data:
                col_name = col_data['name']
                
                # Entsprechende Spalte in Display-Control finden
                for control_col in display_control.columns:
                    if control_col['name'] == col_name:
                        # Aktuellen Stand übernehmen
                        control_col['show'] = col_data.get('show', control_col.get('show', False))
                        control_col['expert'] = col_data.get('expert', control_col.get('expert', False))
                        control_col['order'] = col_data.get('order', control_col.get('order', 0))
                        
                        # show_order nur speichern wenn vorhanden
                        if 'show_order' in col_data and col_data['show_order'] is not None:
                            control_col['show_order'] = col_data['show_order']
                        break
            
            # Display-Control-Spalten nach neuer Reihenfolge sortieren
            display_control.columns.sort(key=lambda x: x.get('order', 9999))
            
            # In Systemsteuerung speichern
            if self.view_manager.central_systemsteuerung:
                # Control-Struktur zu Dict konvertieren für Speicherung
                if hasattr(display_control, 'to_dict'):
                    control_dict = display_control.to_dict()
                else:
                    # Fallback: Manuelle Dict-Erstellung
                    control_dict = {
                        'columns': [dict(col) for col in display_control.columns]
                    }
                
                success = self.view_manager.central_systemsteuerung.set_value(
                    gruppe=self.view_manager.view_guid,
                    feld="display_view_control",
                    wert=control_dict,
                    ab_zeit=1001.0
                )
                
                # Speichern persistieren
                self.view_manager.central_systemsteuerung.save_values()
                
                if success:
                    # Tabelle im ViewManager neu aufbauen
                    if hasattr(self.view_manager, '_schritt3_tabelle_aufbauen'):
                        self.view_manager._schritt3_tabelle_aufbauen()
                    logger.info("💾 Spalten-Parameter und Reihenfolge in Systemsteuerung gespeichert")
                else:
                    logger.error("❌ Fehler beim Speichern in Systemsteuerung")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern im ViewManager: {e}")

    def _initialize_show_order_system(self):
        """Initialisiert das unabhängige show_order System (nur wenn nötig)"""
        
        # Prüfe, ob bereits show_order Werte vorhanden sind
        normal_columns = [col for col in self.column_data if not col.get('expert', False)]
        existing_show_orders = [col for col in normal_columns if 'show_order' in col and col['show_order'] is not None]
        
        if len(existing_show_orders) > 0:
            logger.info(f"🔧 Show-Order System bereits vorhanden ({len(existing_show_orders)} von {len(normal_columns)} Spalten)")
            return  # Bereits initialisiert, nicht überschreiben
        
        logger.info("🔧 Initialisiere unabhängiges show_order System...")
        
        # Sortiere: show=True zuerst, dann show=False
        normal_columns.sort(key=lambda col: (not col.get('show', False), col.get('order', 9999)))
        
        # Vergebe fortlaufende show_order
        for i, col in enumerate(normal_columns, 1):
            col['show_order'] = i
            logger.debug(f"   📊 {col['name']}: show_order={i} (show={col.get('show', False)})")
        
        # Expert-Spalten bekommen KEINE show_order
        for col in self.column_data:
            if col.get('expert', False):
                if 'show_order' in col:
                    del col['show_order']
                logger.debug(f"   🔧 {col['name']}: EXPERT - show_order entfernt")
        
        logger.info(f"✅ Show-Order System initialisiert: {len(normal_columns)} Normal-Spalten")

    def _get_normal_mode_columns(self):
        """Gibt nur Normal-Mode Spalten zurück, sortiert nach show_order"""
        normal_cols = [col for col in self.column_data if not col.get('expert', False)]
        return sorted(normal_cols, key=lambda col: col.get('show_order', 9999))

    def _get_expert_mode_columns(self):
        """Gibt alle Spalten zurück, sortiert nach order"""
        return sorted(self.column_data, key=lambda col: col.get('order', 9999))


if __name__ == "__main__":
    print("📊 PdvmColumnsParameterDialog")
    print("Funktionen:")
    print("- Echte Show/Expert Parameter für alle Felder")
    print("- Expert-Felder nur im Expert-Modus änderbar")
    print("- Kompakte, effiziente Darstellung")
    print("- Alle anzeigen/verstecken Funktionen")
