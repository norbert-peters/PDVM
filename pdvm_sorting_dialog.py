#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Sortierung Dialog - Erweiterte Multi-Level Sortierung
========================================================

Features:
1. Drag & Drop Interface für Sortier-Reihenfolge
2. Links: Verfügbare Spalten, Rechts: Sortier-Queue
3. Multi-Level Sortierung mit Gruppierungsunterstützung
4. Persistente Speicherung der Sortier-Konfiguration
5. Vorbereitung für Gruppen-Summen und Statistiken

Interface:
- Spalten-Liste (nur sichtbare + sortierbare Spalten)
- Sortier-Bereich mit Reihenfolge und Richtung
- Anwenden/Abbrechen Buttons
- Vorschau der Sortier-Hierarchie
"""

import logging
from typing import Dict, List, Tuple, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QListWidget, QListWidgetItem, QComboBox,
                            QGroupBox, QFrame, QMessageBox, QCheckBox, QTreeWidget,
                            QTreeWidgetItem, QSplitter, QAbstractItemView)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QFont, QDrag, QPixmap, QPainter

logger = logging.getLogger(__name__)


class AvailableColumnsListWidget(QListWidget):
    """Custom ListWidget für verfügbare Spalten mit Custom Drag-Data"""
    
    def startDrag(self, supportedActions):
        """Start Drag mit Custom Mime-Data"""
        item = self.currentItem()
        if item:
            # Extrahiere Daten vom Item
            display_name = item.text()
            column_key = item.data(Qt.UserRole)
            
            if not column_key:
                logger.warning("⚠️ Kein column_key gefunden für Item")
                return
            
            # Erstelle Custom Drag-Data: "column_key|display_name"
            drag_data = f"{column_key}|{display_name}"
            logger.debug(f"🎯 Drag gestartet: '{drag_data}'")
            
            # Erstelle Drag
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(drag_data)
            drag.setMimeData(mimeData)
            
            # Starte Drag-Operation
            dropAction = drag.exec_(supportedActions)
            logger.debug(f"🎯 Drag beendet: Action={dropAction}")
        else:
            logger.warning("⚠️ Drag ohne gültiges Item")


class SortingTreeWidget(QTreeWidget):
    """Custom TreeWidget für Sortier-Queue mit Drop-Support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
    def dragEnterEvent(self, event):
        """Drag-Enter Event: Akzeptiere Drops von der Available-List"""
        if event.mimeData().hasText():
            logger.debug(f"🎯 Drag Enter: {event.mimeData().text()}")
            event.acceptProposedAction()
        else:
            logger.debug(f"❌ Drag Enter verweigert: Keine Text-Daten")
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Drag-Move Event: Zeige Drop-Position an"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Drop Event: Füge Spalte zur Sortier-Queue hinzu"""
        logger.debug(f"🎯 Drop Event gestartet")
        
        if event.mimeData().hasText():
            try:
                # Extrahiere Spalten-Info aus Drag-Data
                drag_data = event.mimeData().text()
                logger.debug(f"📋 Drop Daten empfangen: '{drag_data}'")
                
                parts = drag_data.split('|')
                if len(parts) >= 2:
                    column_key = parts[0]
                    display_name = parts[1]
                    logger.debug(f"🔧 Extrahiert: key='{column_key}', name='{display_name}'")
                    
                    # Hole das Dialog-Parent
                    dialog = self.parent()
                    while dialog and not hasattr(dialog, '_add_column_to_queue'):
                        dialog = dialog.parent()
                    
                    if dialog:
                        logger.debug(f"✅ Dialog gefunden: {type(dialog).__name__}")
                        # Füge zur Sortier-Queue hinzu
                        success = dialog._add_column_to_queue(column_key, display_name)
                        
                        if success:
                            # Gruppierung-Feedback sofort anzeigen (falls aktiviert)
                            if hasattr(dialog, '_update_grouping_visual_feedback'):
                                dialog._update_grouping_visual_feedback()
                            event.acceptProposedAction()
                            logger.info(f"✅ Drop erfolgreich: {column_key} → {display_name}")
                        else:
                            event.ignore()
                            logger.warning(f"⚠️ Drop fehlgeschlagen: {column_key}")
                    else:
                        logger.error("❌ Dialog-Parent nicht gefunden")
                        event.ignore()
                else:
                    logger.error(f"❌ Ungültiges Daten-Format: '{drag_data}' (erwartet: 'key|name')")
                    event.ignore()
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Drop: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                event.ignore()
        else:
            logger.debug(f"❌ Drop verweigert: Keine Text-Daten")
            event.ignore()


class PdvmSortingDialog(QDialog):
    """
    Dialog für erweiterte Multi-Level Sortierung und Gruppierung
    
    ARCHITEKTUR:
    - Links: Verfügbare Spalten (drag source)
    - Rechts: Sortier-Queue (drop target) mit Reihenfolge
    - Buttons: Anwenden, Abbrechen
    - Vorschau: Hierarchie-Anzeige der Sortierung
    """
    
    def __init__(self, sorting_manager, parent=None):
        super().__init__(parent)
        self.sorting_manager = sorting_manager
        self.view_dialog = sorting_manager.view_dialog
        
        # View-GUID aus view_dialog extrahieren
        self.view_guid = getattr(self.view_dialog, 'view_guid', None)
        if not self.view_guid:
            logger.error("❌ Keine view_guid verfügbar!")
        
        # Sortier-Konfiguration
        self.sort_levels = []  # [(column_key, direction, display_name), ...]
        
        self.setWindowTitle("Sortierung verwalten")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # UI aufbauen
        self._setup_ui()
        
        # Aktuelle Sortierung laden
        self._load_current_sorting()
        
        # Gruppierung-Einstellungen laden
        self._load_grouping_settings()
        
        logger.info("✅ Sortierung Dialog initialisiert")
    
    def _setup_ui(self):
        """Baut die Benutzeroberfläche auf"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_label = QLabel("📊 Sortierung und Gruppierung verwalten")
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Info-Text
        info_label = QLabel(
            "💡 Ziehen Sie Spalten von links nach rechts für die Sortier-Reihenfolge"
        )
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(info_label)
        
        # Mode-Label für Expert/Normal Anzeige
        self.mode_label = QLabel("👤 Lade Modus...")
        self.mode_label.setStyleSheet("color: #333; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.mode_label)
        
        # Hauptbereich: Split zwischen verfügbaren Spalten und Sortier-Queue
        splitter = QSplitter(Qt.Horizontal)
        
        # Links: Verfügbare Spalten
        left_group = QGroupBox("📋 Verfügbare Spalten")
        left_layout = QVBoxLayout(left_group)
        
        self.available_list = AvailableColumnsListWidget()
        self.available_list.setDragEnabled(True)
        self.available_list.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.available_list)
        
        # Rechts: Sortier-Queue
        right_group = QGroupBox("📊 Sortier-Reihenfolge")
        right_layout = QVBoxLayout(right_group)
        
        self.sorting_tree = SortingTreeWidget()
        self.sorting_tree.setHeaderLabels(['Spalte', 'Richtung'])
        self.sorting_tree.setRootIsDecorated(False)
        right_layout.addWidget(self.sorting_tree)
        
        # Queue-Management Buttons
        queue_buttons = QHBoxLayout()
        
        self.move_up_button = QPushButton("↑ Nach oben")
        self.move_up_button.clicked.connect(self._move_selected_up)
        queue_buttons.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("↓ Nach unten")
        self.move_down_button.clicked.connect(self._move_selected_down)
        queue_buttons.addWidget(self.move_down_button)
        
        self.remove_button = QPushButton("🗑️ Entfernen")
        self.remove_button.clicked.connect(self._remove_selected)
        queue_buttons.addWidget(self.remove_button)
        
        self.toggle_direction_button = QPushButton("🔄 Richtung ändern")
        self.toggle_direction_button.clicked.connect(self._toggle_selected_direction)
        self.toggle_direction_button.setToolTip("Sortier-Richtung zwischen Aufsteigend/Absteigend umschalten")
        queue_buttons.addWidget(self.toggle_direction_button)
        
        self.reset_button = QPushButton("🔄 Zurücksetzen")
        self.reset_button.clicked.connect(self._reset_sorting)
        queue_buttons.addWidget(self.reset_button)
        
        right_layout.addLayout(queue_buttons)
        
        # Zu Splitter hinzufügen
        splitter.addWidget(left_group)
        splitter.addWidget(right_group)
        splitter.setSizes([300, 400])  # Links schmaler, rechts breiter
        
        layout.addWidget(splitter)
        
        # Gruppierung-Optionen (AKTIV) - robuste Titel-Darstellung mit linksbündigem Titel
        grouping_group = QGroupBox("🏷️ Gruppierung")
        
        # Robuste Lösung für QGroupBox-Titel Darstellung (alle Buchstaben sichtbar)
        grouping_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #888888;
                border-radius: 5px;
                margin-top: 16px;     /* Ausreichend Platz für Titel */
                padding-top: 12px;    /* Innen-Abstand nach Titel */
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;    /* Linksbündig wie Standard */
                left: 8px;                        /* Kleiner Abstand vom linken Rand */
                padding: 4px 12px;                /* Großzügiges Padding um Titel */
                background-color: palette(window);
                min-height: 20px;                 /* Minimale Höhe für 'p' und 'g' */
                max-height: 24px;                 /* Maximale Höhe begrenzen */
                font-size: 12px;                  /* Konsistente Schriftgröße */
                font-weight: bold;
            }
        """)
        
        grouping_group.setMinimumHeight(120)  # Angemessene Mindesthöhe
        grouping_layout = QVBoxLayout(grouping_group)
        grouping_layout.setContentsMargins(10, 10, 10, 10)  # Ausgewogene Margins
        
        self.enable_grouping_checkbox = QCheckBox("Gruppierung aktivieren")
        self.enable_grouping_checkbox.setChecked(False)
        grouping_layout.addWidget(self.enable_grouping_checkbox)
        
        self.show_group_sums_checkbox = QCheckBox("Gruppen-Summen anzeigen")
        self.show_group_sums_checkbox.setEnabled(False)  # Abhängig von Gruppierung
        grouping_layout.addWidget(self.show_group_sums_checkbox)
        
        self.collapsible_groups_checkbox = QCheckBox("Gruppen zu-/aufklappbar")
        self.collapsible_groups_checkbox.setEnabled(False)  # Abhängig von Gruppierung
        grouping_layout.addWidget(self.collapsible_groups_checkbox)
        
        # Gruppierung-Verhalten
        self.enable_grouping_checkbox.toggled.connect(self._on_grouping_toggled)
        
        layout.addWidget(grouping_group)
        
        # Dialog-Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Sortierung anwenden")
        self.apply_button.clicked.connect(self._apply_sorting)
        self.apply_button.setDefault(True)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def _refresh_available_columns(self):
        """Aktualisiert verfügbare Spalten basierend auf Sortier-Projektions-Tabellen"""
        self.available_list.clear()
        
        try:
            # Verfügbare Spalten aus Sortier-Projektions-Tabellen holen
            available_columns = self._get_available_columns_for_sorting()
            
            if not available_columns:
                # Keine Spalten verfügbar
                self.mode_label.setText("❌ Keine Sortier-Projektions-Tabellen verfügbar")
                logger.error("❌ Keine verfügbaren Spalten für Sortierung - prüfen Sie die Projektions-Tabellen")
                return
            
            for column_key, display_name in available_columns:
                # Bereits in Sortier-Queue? Dann nicht in verfügbarer Liste
                if any(level[0] == column_key for level in self.sort_levels):
                    continue
                
                # Item erstellen
                item = QListWidgetItem(f"{display_name}")
                item.setData(Qt.UserRole, column_key)  # Control-Key speichern
                item.setToolTip(f"Spalte: {display_name}\nControl-Key: {column_key}")
                
                self.available_list.addItem(item)
            
            # Mode-Label aktualisieren
            mode_text = "🔧 Expert Mode (Alle Spalten)" if self._is_expert_mode() else "👤 Normal Mode (Sichtbare + Sortierbare)"
            self.mode_label.setText(mode_text)
            
            logger.debug(f"📋 {self.available_list.count()} verfügbare Sortier-Spalten geladen ({mode_text})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden verfügbarer Spalten: {e}")
            self.mode_label.setText("❌ Fehler beim Laden der Spalten")
    
    def _is_expert_mode(self) -> bool:
        """Prüft ob Expert-Mode aktiv ist über zentrales GCS-System"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs:
                return gcs.expert_mode
            else:
                logger.error("❌ GCS nicht verfügbar für Expert-Mode Prüfung")
                return False
        except Exception as e:
            logger.error(f"❌ Fehler bei Expert-Mode Prüfung: {e}")
            return False
    
    def _get_available_columns_for_sorting(self) -> List[Tuple[str, str]]:
        """Lädt verfügbare Spalten aus den Sortier-Projektions-Tabellen"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                raise ValueError("GCS nicht initialisiert! Rufe initialize_gcs() auf.")
            
            # Expert-Mode-Abhängige Projektion laden
            expert_mode = gcs.expert_mode
            projection_key = 'sort_expert' if expert_mode else 'sort_standard'
            
            # ✅ KORRIGIERT: Verwende korrekte GCS-Methode
            sort_projection = gcs.get_projection_table(self.view_guid, projection_key)
            
            if not sort_projection:
                logger.error(f"❌ Keine {projection_key} Projektion für View {self.view_guid} verfügbar")
                return []
            
            # Controls-Config vom View-Dialog holen
            result = []
            controls_config = getattr(self.view_dialog, 'controls_config', {})
            
            for column_key in sort_projection:
                # Controls-Config holen für Display-Namen
                control_data = controls_config.get(column_key, {})
                display_name = control_data.get('original', column_key)
                
                # Alle Spalten aus der Projektion sind sortierbar
                result.append((column_key, str(display_name)))
            
            logger.debug(f"📊 Sortier-Projektions-Tabelle ({projection_key}): {len(result)} Spalten verfügbar")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Sortier-Projektions-Tabelle: {e}")
            return []

    def _load_current_sorting(self):
        """Lädt die aktuelle Sortierung"""
        try:
            # Aktuell aktive Sortierung
            if self.sorting_manager.current_sort_column:
                control_key = self.sorting_manager.current_sort_column
                direction = self.sorting_manager.current_sort_direction
                
                # Display-Name ermitteln
                display_name = self._get_display_name_for_key(control_key)
                
                # Als erstes Level hinzufügen
                self.sort_levels = [(control_key, direction, display_name)]
            
            # UI aktualisieren
            self._refresh_available_columns()
            self._refresh_sorting_tree()
            
            logger.info(f"📖 Aktuelle Sortierung geladen: {len(self.sort_levels)} Level")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der aktuellen Sortierung: {e}")
    
    def _get_display_name_for_key(self, control_key: str) -> str:
        """Ermittelt Anzeige-Name für Control-Key"""
        try:
            if hasattr(self.view_dialog, 'controls_config'):
                control = self.view_dialog.controls_config.get(control_key, {})
                return control.get('name', control_key)
            return control_key
        except Exception:
            return control_key
    
    def _refresh_sorting_tree(self):
        """Aktualisiert die Sortier-Queue Anzeige mit verbesserter visueller Darstellung"""
        self.sorting_tree.clear()
        
        for i, (column_key, direction, display_name) in enumerate(self.sort_levels):
            # Verbesserte visuelle Darstellung mit Icons
            if direction == 'asc':
                direction_text = "🔼 Aufsteigend"
            else:
                direction_text = "🔽 Absteigend"
            
            # Prioritäts-Anzeige hinzufügen
            priority_text = f"{i+1}. {display_name}"
            
            item = QTreeWidgetItem([priority_text, direction_text])
            item.setData(0, Qt.UserRole, column_key)
            item.setData(1, Qt.UserRole, direction)
            
            # Tooltip mit Hinweisen
            item.setToolTip(0, f"Sortier-Priorität: {i+1}")
            item.setToolTip(1, "Klicken Sie 'Richtung ändern' um zwischen Aufsteigend/Absteigend zu wechseln")
            
            # Klickbar für Richtung-Änderung (bereits editierbar)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            
            self.sorting_tree.addTopLevelItem(item)
        
        # Update verfügbare Spalten (entferne die, die bereits in der Queue sind)
        self._refresh_available_columns()
    
    def _move_selected_up(self):
        """Bewegt ausgewähltes Item nach oben"""
        current = self.sorting_tree.currentItem()
        if not current:
            return
        
        index = self.sorting_tree.indexOfTopLevelItem(current)
        if index > 0:
            # In sort_levels tauschen
            self.sort_levels[index], self.sort_levels[index - 1] = self.sort_levels[index - 1], self.sort_levels[index]
            
            # UI aktualisieren
            self._refresh_sorting_tree()
            self.sorting_tree.setCurrentItem(self.sorting_tree.topLevelItem(index - 1))
    
    def _move_selected_down(self):
        """Bewegt ausgewähltes Item nach unten"""
        current = self.sorting_tree.currentItem()
        if not current:
            return
        
        index = self.sorting_tree.indexOfTopLevelItem(current)
        if index < len(self.sort_levels) - 1:
            # In sort_levels tauschen
            self.sort_levels[index], self.sort_levels[index + 1] = self.sort_levels[index + 1], self.sort_levels[index]
            
            # UI aktualisieren
            self._refresh_sorting_tree()
            self.sorting_tree.setCurrentItem(self.sorting_tree.topLevelItem(index + 1))
    
    def _remove_selected(self):
        """Entfernt ausgewähltes Item"""
        current = self.sorting_tree.currentItem()
        if not current:
            return
        
        index = self.sorting_tree.indexOfTopLevelItem(current)
        if 0 <= index < len(self.sort_levels):
            # Aus sort_levels entfernen
            del self.sort_levels[index]
            
            # UI aktualisieren
            self._refresh_sorting_tree()
            self._refresh_available_columns()
    
    def _reset_sorting(self):
        """Setzt die Sortierung zurück"""
        self.sort_levels.clear()
        self._refresh_sorting_tree()
        self._refresh_available_columns()
        
        logger.info("🔄 Sortierung zurückgesetzt")
    
    def _toggle_selected_direction(self):
        """Schaltet die Sortier-Richtung des ausgewählten Items um"""
        current = self.sorting_tree.currentItem()
        if not current:
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie eine Sortier-Ebene aus.")
            return
        
        index = self.sorting_tree.indexOfTopLevelItem(current)
        if 0 <= index < len(self.sort_levels):
            # Aktuelle Richtung umschalten
            column_key, current_direction, display_name = self.sort_levels[index]
            new_direction = 'desc' if current_direction == 'asc' else 'asc'
            
            # In sort_levels aktualisieren
            self.sort_levels[index] = (column_key, new_direction, display_name)
            
            # UI aktualisieren
            self._refresh_sorting_tree()
            
            # Item wieder auswählen
            self.sorting_tree.setCurrentItem(self.sorting_tree.topLevelItem(index))
            
            direction_text = "Absteigend" if new_direction == 'desc' else "Aufsteigend"
            logger.info(f"🔄 Sortier-Richtung geändert: {display_name} → {direction_text}")
        else:
            QMessageBox.warning(self, "Fehler", "Ungültiger Index für Sortier-Ebene.")
    
    def _add_column_to_queue(self, column_key: str, display_name: str):
        """Fügt eine Spalte zur Sortier-Queue hinzu"""
        try:
            # Prüfe ob Spalte bereits vorhanden ist
            for level in self.sort_levels:
                if level[0] == column_key:
                    logger.info(f"⚠️ Spalte '{display_name}' bereits in Queue")
                    return False  # Bereits vorhanden
            
            # Füge zum sort_levels hinzu (kompatibel mit existierendem System)
            self.sort_levels.append((column_key, 'asc', display_name))
            
            # Aktualisiere UI
            self._refresh_sorting_tree()
            self._refresh_available_columns()
            
            logger.info(f"✅ Spalte '{display_name}' zur Queue hinzugefügt")
            return True  # Erfolgreich hinzugefügt
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen zur Queue: {e}")
            return False  # Fehler aufgetreten
    
    def _apply_sorting(self):
        """Wendet die konfigurierte Multi-Level Sortierung mit Gruppierung an"""
        try:
            if not self.sort_levels:
                # Keine Sortierung = Sortierung löschen
                if hasattr(self.view_dialog, 'display') and hasattr(self.view_dialog.display, 'table'):
                    self.sorting_manager.clear_sorting(self.view_dialog.display.table)
                
                QMessageBox.information(self, "Sortierung", "Sortierung wurde entfernt.")
                self.accept()
                return
            
            # Import der erweiterten Sortierungs-Engine
            from pdvm_advanced_sorting_engine import PdvmAdvancedSortingEngine, GroupConfig
            
            # Gruppierungs-Konfiguration erstellen
            group_config = GroupConfig(
                enabled=self.enable_grouping_checkbox.isChecked(),
                show_sums=self.show_group_sums_checkbox.isChecked(),
                collapsible=self.collapsible_groups_checkbox.isChecked(),
                sum_columns=self._get_numeric_columns()  # Automatisch numerische Spalten finden
            )
            
            # Erweiterte Sortierungs-Engine konfigurieren
            engine = PdvmAdvancedSortingEngine()
            engine.set_sort_configuration(self.sort_levels, group_config)
            
            # Anwenden über Sorting Manager
            if hasattr(self.sorting_manager, 'apply_advanced_sorting'):
                # Neue erweiterte Methode verwenden
                success = self.sorting_manager.apply_advanced_sorting(engine, group_config)
                
                if success:
                    if group_config.enabled:
                        group_info = f" mit Gruppierung nach '{self.sort_levels[0][2]}'"
                        if len(self.sort_levels) > 1:
                            internal_sorts = [level[2] for level in self.sort_levels[1:]]
                            group_info += f" und interner Sortierung: {', '.join(internal_sorts)}"
                    else:
                        group_info = f" nach {len(self.sort_levels)} Ebenen"
                    
                    QMessageBox.information(
                        self, 
                        "Erweiterte Sortierung", 
                        f"Multi-Level Sortierung angewendet{group_info}"
                    )
                else:
                    QMessageBox.warning(self, "Sortierung", "Erweiterte Sortierung konnte nicht angewendet werden.")
            else:
                # Fallback: Nur erste Ebene anwenden (Kompatibilität)
                first_level = self.sort_levels[0]
                column_key, direction, display_name = first_level
                
                if hasattr(self.view_dialog, 'display') and hasattr(self.view_dialog.display, 'table'):
                    self.sorting_manager.apply_sorting(
                        self.view_dialog.display.table, 
                        column_key, 
                        direction
                    )
                
                info_text = f"Basis-Sortierung angewendet: {display_name} ({('Aufsteigend' if direction == 'asc' else 'Absteigend')})"
                if len(self.sort_levels) > 1:
                    info_text += f"\n\nHinweis: {len(self.sort_levels)-1} weitere Sortier-Ebenen wurden ignoriert."
                    info_text += "\nFür Multi-Level Sortierung ist ein Update des Sorting Managers erforderlich."
                
                QMessageBox.information(self, "Sortierung", info_text)
            
            # Konfiguration speichern
            self._save_sorting_configuration()
            
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der erweiterten Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Fehler", f"Erweiterte Sortierung konnte nicht angewendet werden:\n{e}")

    def _get_numeric_columns(self) -> List[str]:
        """Ermittelt automatisch numerische Spalten für Summen-Berechnung"""
        numeric_columns = []
        
        try:
            # Prüfe verfügbare Spalten auf numerische Typen
            available_columns = self._get_available_columns_for_sorting()
            
            for column_info in available_columns:
                if isinstance(column_info, dict):
                    column_key = column_info.get('key', '')
                    field_type = column_info.get('type', '')
                    
                    # Suche nach numerischen Typen
                    if any(num_type in field_type.lower() for num_type in ['int', 'float', 'decimal', 'number', 'currency']):
                        numeric_columns.append(column_key)
                    # Oder nach numerischen Hinweisen im Namen
                    elif any(hint in column_key.lower() for hint in ['amount', 'price', 'cost', 'salary', 'betrag', 'preis']):
                        numeric_columns.append(column_key)
            
            logger.debug(f"🔢 Numerische Spalten gefunden: {numeric_columns}")
            
        except Exception as e:
            logger.warning(f"⚠️ Konnte numerische Spalten nicht automatisch ermitteln: {e}")
        
        return numeric_columns

    def _save_sorting_configuration(self):
        """Speichert die aktuelle Sortier-Konfiguration"""
        if not hasattr(self, 'view_guid') or not self.view_guid:
            return
            
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs or not gcs._app_db:
                return
            
            # Sortier-Konfiguration speichern
            sort_config = {
                'levels': self.sort_levels,
                'grouping': {
                    'enabled': self.enable_grouping_checkbox.isChecked(),
                    'show_sums': self.show_group_sums_checkbox.isChecked(),
                    'collapsible': self.collapsible_groups_checkbox.isChecked()
                }
            }
            
            gcs._app_db.set_value(self.view_guid, 'advanced_sort_config', sort_config)
            logger.debug(f"💾 Erweiterte Sortier-Konfiguration gespeichert für {self.view_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Sortier-Konfiguration: {e}")

    def _on_grouping_toggled(self, enabled):
        """Behandelt Aktivierung/Deaktivierung der Gruppierung"""
        logger.info(f"🏷️ Gruppierung {'aktiviert' if enabled else 'deaktiviert'}")
        
        # Sub-Optionen aktivieren/deaktivieren
        self.show_group_sums_checkbox.setEnabled(enabled)
        self.collapsible_groups_checkbox.setEnabled(enabled)
        
        # Gruppierung-Modi in der Queue aktualisieren
        self._update_grouping_visual_feedback()
        
        # Status speichern
        if hasattr(self, 'view_guid') and self.view_guid:
            try:
                from pdvm_central_systemsteuerung import get_gcs
                gcs = get_gcs()
                if gcs and gcs._app_db:
                    gcs._app_db.set_value(self.view_guid, 'grouping_enabled', enabled)
                    gcs._app_db.set_value(self.view_guid, 'show_group_sums', 
                                        self.show_group_sums_checkbox.isChecked())
                    gcs._app_db.set_value(self.view_guid, 'collapsible_groups',
                                        self.collapsible_groups_checkbox.isChecked())
                    logger.debug(f"✅ Gruppierung-Status gespeichert für {self.view_guid}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Speichern Gruppierung-Status: {e}")
    
    def _update_grouping_visual_feedback(self):
        """Aktualisiert visuelle Gruppierung-Hinweise im Tree"""
        try:
            grouping_enabled = self.enable_grouping_checkbox.isChecked()
            
            # Durchlaufe alle Items im Sorting Tree
            root = self.sorting_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                current_text = item.text(0)
                
                if grouping_enabled:
                    # Füge Gruppierung-Symbol hinzu (wenn nicht vorhanden)
                    if not current_text.startswith("🏷️ "):
                        item.setText(0, f"🏷️ {current_text}")
                        item.setToolTip(0, "Diese Spalte wird für Gruppierung verwendet")
                else:
                    # Entferne Gruppierung-Symbol
                    if current_text.startswith("🏷️ "):
                        clean_text = current_text.replace("🏷️ ", "")
                        item.setText(0, clean_text)
                        item.setToolTip(0, "Sortierung")
                        
            logger.debug(f"🎯 Gruppierung-Feedback aktualisiert: {grouping_enabled}")
                        
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren Gruppierung-Feedback: {e}")
    
    def is_grouping_enabled(self):
        """Gibt zurück, ob Gruppierung aktiviert ist"""
        return self.enable_grouping_checkbox.isChecked()
    
    def get_grouping_options(self):
        """Gibt alle Gruppierung-Optionen zurück"""
        return {
            'enabled': self.enable_grouping_checkbox.isChecked(),
            'show_sums': self.show_group_sums_checkbox.isChecked(),
            'collapsible': self.collapsible_groups_checkbox.isChecked()
        }
    
    def _load_grouping_settings(self):
        """Lädt gespeicherte Gruppierung-Einstellungen"""
        if not hasattr(self, 'view_guid') or not self.view_guid:
            logger.debug("💡 Keine view_guid - verwende Standard-Gruppierung")
            return
            
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs or not gcs._app_db:
                logger.debug("💡 Keine GCS/App-DB - verwende Standard-Gruppierung")
                return
                
            # Lade gespeicherte Gruppierung-Optionen
            grouping_enabled, exists1 = gcs._app_db.get_value(self.view_guid, 'grouping_enabled')
            show_sums, exists2 = gcs._app_db.get_value(self.view_guid, 'show_group_sums')
            collapsible, exists3 = gcs._app_db.get_value(self.view_guid, 'collapsible_groups')
            
            if exists1:
                self.enable_grouping_checkbox.setChecked(bool(grouping_enabled))
                logger.debug(f"📋 Gruppierung geladen: {grouping_enabled}")
            
            if exists2:
                self.show_group_sums_checkbox.setChecked(bool(show_sums))
                
            if exists3:
                self.collapsible_groups_checkbox.setChecked(bool(collapsible))
            
            # UI-Status aktualisieren
            self._on_grouping_toggled(self.enable_grouping_checkbox.isChecked())
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Gruppierung-Einstellungen: {e}")


if __name__ == "__main__":
    print("📊 PDVM Sortierung Dialog")
    print("Features:")
    print("- Drag & Drop Interface für Sortier-Reihenfolge")
    print("- Multi-Level Sortierung vorbereitet")
    print("- Gruppierungsunterstützung geplant")
    print("- Persistente Speicherung")