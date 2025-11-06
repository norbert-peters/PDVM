# pdvm_sort_summen_dialog.py
"""
🎓 ERWEITERTE SORTIERUNG & SUMMEN DIALOG

Ermöglicht:
- Multi-Level Sortierung
- Gruppierung mit Unter-Gruppen
- Summierung von Spalten
- Persistierung der Einstellungen
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QComboBox,
    QGroupBox, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class AdvancedSortDialog(QDialog):
    """Dialog für erweiterte Sortierung mit Gruppierung und Summierung"""
    
    def __init__(self, controls_config: dict, view_guid: str, projection: list = None, parent=None):
        """
        Initialisiert Dialog
        
        Args:
            controls_config: Controls-Konfiguration (FIRST!)
            view_guid: View-GUID für Persistierung
            projection: Liste der Spalten-Keys in aktueller Projektion (optional)
            parent: Eltern-Widget
        """
        super().__init__(parent)
        self.view_guid = view_guid
        self.controls_config = controls_config
        self.projection = projection  # Speichere Projektion
        self.sort_config = []
        self.sum_columns = []
        
        logger.info(f"🎓 Advanced Sort Dialog initialisiert")
        logger.info(f"  📋 View GUID: {view_guid}")
        logger.info(f"  📊 Controls Config: {len(controls_config)} Spalten")
        if projection:
            logger.info(f"  📋 Projektion: {len(projection)} Spalten")
        
        self._setup_ui()
        self._load_sortable_columns()
        self._load_persisted_sort()  # Lade letzte Sortierung
    
    def _setup_ui(self):
        """UI aufbauen"""
        self.setWindowTitle("🎓 Erweiterte Sortierung")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("Erweiterte Sortierung, Gruppierung und Summierung")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # === SORTIERUNG SECTION ===
        sort_group = QGroupBox("📊 Sortier-Reihenfolge")
        sort_layout = QVBoxLayout(sort_group)
        
        info_label = QLabel(
            "Ziehen Sie Spalten per Drag&Drop, um die Sortier-Reihenfolge festzulegen.\n"
            "Die oberste Spalte ist die primäre Sortierung."
        )
        info_label.setWordWrap(True)
        sort_layout.addWidget(info_label)
        
        # Verfügbare Spalten
        available_layout = QVBoxLayout()
        available_label = QLabel("Verfügbare Spalten:")
        available_layout.addWidget(available_label)
        
        self.available_columns_list = QListWidget()
        self.available_columns_list.setDragDropMode(QAbstractItemView.DragOnly)
        self.available_columns_list.setSelectionMode(QAbstractItemView.SingleSelection)
        available_layout.addWidget(self.available_columns_list)
        
        # Sortier-Reihenfolge
        sort_order_layout = QVBoxLayout()
        sort_order_label = QLabel("Sortier-Reihenfolge:")
        sort_order_layout.addWidget(sort_order_label)
        
        self.sort_order_list = QListWidget()
        self.sort_order_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.sort_order_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sort_order_list.itemDoubleClicked.connect(self._toggle_sort_direction)
        sort_order_layout.addWidget(self.sort_order_list)
        
        sort_hint_label = QLabel(
            "💡 Doppelklick auf Spalte wechselt Sortier-Richtung (↑/↓)\n"
            "💡 Rechtsklick für Gruppierung aktivieren"
        )
        sort_hint_label.setStyleSheet("QLabel { color: #666; font-size: 10pt; }")
        sort_order_layout.addWidget(sort_hint_label)
        
        # Buttons zwischen Listen
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        
        add_button = QPushButton("→")
        add_button.setToolTip("Spalte zur Sortierung hinzufügen")
        add_button.clicked.connect(self._add_column_to_sort)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("←")
        remove_button.setToolTip("Spalte aus Sortierung entfernen")
        remove_button.clicked.connect(self._remove_column_from_sort)
        button_layout.addWidget(remove_button)
        
        button_layout.addStretch()
        
        # Kombiniere Listen und Buttons
        lists_layout = QHBoxLayout()
        lists_layout.addLayout(available_layout, 1)
        lists_layout.addLayout(button_layout, 0)
        lists_layout.addLayout(sort_order_layout, 1)
        
        sort_layout.addLayout(lists_layout)
        layout.addWidget(sort_group)
        
        # === SUMMIERUNG SECTION ===
        sum_group = QGroupBox("Σ Summierung")
        sum_layout = QVBoxLayout(sum_group)
        
        sum_info_label = QLabel(
            "Wählen Sie Spalten für Summierung aus.\n"
            "Numerische Werte werden summiert, andere Spalten zeigen Anzahl."
        )
        sum_info_label.setWordWrap(True)
        sum_layout.addWidget(sum_info_label)
        
        self.sum_columns_list = QListWidget()
        self.sum_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        sum_layout.addWidget(self.sum_columns_list)
        
        layout.addWidget(sum_group)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("✅ Übernehmen")
        self.apply_button.clicked.connect(self._save_and_accept)  # Speichern VOR accept()
        button_layout.addWidget(self.apply_button)
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _load_sortable_columns(self):
        """
        Lade sortierbare Spalten aus Sort-Projektion.
        
        WICHTIG: Die Projektion kommt jetzt aus GCS Position 3/8 (Sort-Projektion)
        und enthält BEREITS NUR sortierbare Spalten! KEINE weitere Filterung nötig!
        """
        try:
            logger.info("📋 Lade Spalten aus Sort-Projektion...")
            
            # Bestimme welche Spalten geladen werden sollen
            if self.projection:
                # Sort-Projektion enthält BEREITS NUR sortierbare Spalten!
                columns_to_load = self.projection
                logger.info(f"  ✅ Sort-Projektion: {len(columns_to_load)} Spalten (bereits gefiltert)")
            else:
                # FALLBACK: Alte Logik falls keine Projektion übergeben wurde
                logger.warning("  ⚠️ Keine Projektion - verwende Fallback mit sortable-Filter")
                columns_to_load = [
                    key for key, control in self.controls_config.items()
                    if control.get('sortable', False)
                ]
            
            loaded_count = 0
            
            for column_key in columns_to_load:
                control = self.controls_config.get(column_key)
                if not control:
                    logger.warning(f"  ⚠️ Control nicht gefunden: {column_key}")
                    continue
                
                name = control.get('name', column_key)
                
                # Füge zu verfügbaren Spalten hinzu
                item = QListWidgetItem(f"{name}")
                item.setData(Qt.UserRole, column_key)
                item.setToolTip(f"Spalte: {column_key}\nAus Sort-Projektion (bereits sortierbar)")
                self.available_columns_list.addItem(item)
                
                # Füge zu Summierungs-Liste hinzu
                sum_item = QListWidgetItem(f"{name}")
                sum_item.setData(Qt.UserRole, column_key)
                sum_item.setToolTip(f"Spalte: {column_key}")
                self.sum_columns_list.addItem(sum_item)
                
                loaded_count += 1
                logger.debug(f"  ✅ Geladen: {name} ({column_key})")
            
            logger.info(f"✅ {loaded_count} Spalten aus Sort-Projektion geladen (KEINE weitere Filterung)")
            
            if loaded_count == 0:
                logger.warning("⚠️ KEINE Spalten in Sort-Projektion gefunden!")
                logger.warning(f"  📊 Projektion hat {len(columns_to_load)} Einträge")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Spalten: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _add_column_to_sort(self):
        """Fügt ausgewählte Spalte zur Sortierung hinzu"""
        current_item = self.available_columns_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie eine Spalte aus.")
            return
        
        column_key = current_item.data(Qt.UserRole)
        
        # Prüfe ob bereits in Sortierung
        for i in range(self.sort_order_list.count()):
            existing_item = self.sort_order_list.item(i)
            if existing_item.data(Qt.UserRole) == column_key:
                QMessageBox.information(self, "Bereits vorhanden", 
                                      "Diese Spalte ist bereits in der Sortierung.")
                return
        
        # Hole Control-Config
        control = self.controls_config.get(column_key, {})
        name = control.get('name', column_key)
        # WICHTIG: sortDirection ist DIREKT im Control, NICHT in 'ui' Sub-Dict!
        default_direction = control.get('sortDirection', 'asc')
        
        # Erstelle Sortier-Item
        item_text = f"{name} {'↑' if default_direction == 'asc' else '↓'}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, column_key)
        item.setData(Qt.UserRole + 1, default_direction)  # Direction
        item.setData(Qt.UserRole + 2, False)  # is_group
        
        self.sort_order_list.addItem(item)
        
        logger.info(f"✅ Spalte zur Sortierung hinzugefügt: {column_key}")
    
    def _remove_column_from_sort(self):
        """Entfernt ausgewählte Spalte aus Sortierung"""
        current_row = self.sort_order_list.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Keine Auswahl", 
                              "Bitte wählen Sie eine Spalte zum Entfernen aus.")
            return
        
        self.sort_order_list.takeItem(current_row)
        logger.info(f"✅ Spalte aus Sortierung entfernt")
    
    def _toggle_sort_direction(self, item: QListWidgetItem):
        """Wechselt Sortier-Richtung bei Doppelklick"""
        column_key = item.data(Qt.UserRole)
        current_direction = item.data(Qt.UserRole + 1)
        is_group = item.data(Qt.UserRole + 2)
        
        # Toggle Direction
        new_direction = 'desc' if current_direction == 'asc' else 'asc'
        
        # Aktualisiere Item
        control = self.controls_config.get(column_key, {})
        name = control.get('name', column_key)
        
        arrow = '↑' if new_direction == 'asc' else '↓'
        group_marker = ' [Gruppe]' if is_group else ''
        
        item.setText(f"{name} [{column_key}] {arrow}{group_marker}")
        item.setData(Qt.UserRole + 1, new_direction)
        
        logger.info(f"🔄 Sortier-Richtung gewechselt: {column_key} → {new_direction}")
    
    def contextMenuEvent(self, event):
        """Context-Menü für Gruppierung"""
        # Prüfe ob in sort_order_list
        if self.sort_order_list.underMouse():
            current_item = self.sort_order_list.currentItem()
            
            if current_item:
                column_key = current_item.data(Qt.UserRole)
                direction = current_item.data(Qt.UserRole + 1)
                is_group = current_item.data(Qt.UserRole + 2)
                
                # Toggle Gruppierung
                new_is_group = not is_group
                
                # Aktualisiere Item
                control = self.controls_config.get(column_key, {})
                name = control.get('name', column_key)
                
                arrow = '↑' if direction == 'asc' else '↓'
                group_marker = ' [Gruppe]' if new_is_group else ''
                
                current_item.setText(f"{name} [{column_key}] {arrow}{group_marker}")
                current_item.setData(Qt.UserRole + 2, new_is_group)
                
                logger.info(f"🔄 Gruppierung {'aktiviert' if new_is_group else 'deaktiviert'}: {column_key}")
    
    def get_sort_config(self) -> list:
        """
        Gibt Sortier-Konfiguration zurück
        
        Returns:
            Liste von Sortier-Definitionen
        """
        sort_config = []
        
        for i in range(self.sort_order_list.count()):
            item = self.sort_order_list.item(i)
            
            config = {
                'column_key': item.data(Qt.UserRole),
                'direction': item.data(Qt.UserRole + 1),
                'is_group': item.data(Qt.UserRole + 2)
            }
            
            sort_config.append(config)
        
        return sort_config
    
    def get_sum_columns(self) -> list:
        """
        Gibt ausgewählte Summierungs-Spalten zurück
        
        Returns:
            Liste von Column-Keys
        """
        sum_columns = []
        
        for item in self.sum_columns_list.selectedItems():
            column_key = item.data(Qt.UserRole)
            sum_columns.append(column_key)
        
        return sum_columns
    
    def _save_and_accept(self):
        """
        Speichert Sortier-Konfiguration persistent und schließt Dialog.
        
        🆕 PERSISTENCE:
        - Speichert sort_config in App-DB unter view_guid/sort
        - Format: [{'column': 'key', 'direction': 'asc/desc', 'is_group': bool}, ...]
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung möglich")
                self.accept()
                return
            
            # Aktuelle Konfiguration holen
            sort_config = self.get_sort_config()
            sum_columns = self.get_sum_columns()  # ← SUMMEN-SPALTEN HOLEN
            
            # In App-DB speichern
            gcs._app_db.set_value(self.view_guid, 'sort', sort_config)
            
            # 🆕 SUMMEN als eigenständiger Schritt: sum_string + sum_source
            if sum_columns:
                gcs._app_db.set_value(self.view_guid, 'sum_string', sum_columns)
                gcs._app_db.set_value(self.view_guid, 'sum_source', 'multi')  # Vom Dialog
            else:
                # Keine Summen → Werte löschen
                gcs._app_db.set_value(self.view_guid, 'sum_string', None)
                gcs._app_db.set_value(self.view_guid, 'sum_source', None)
            
            gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!
            
            logger.info(f"💾 Sortierung persistent gespeichert: {len(sort_config)} Spalten")
            for idx, cfg in enumerate(sort_config):
                group_marker = " [GRUPPE]" if cfg.get('is_group') else ""
                logger.info(f"  {idx+1}. {cfg['column_key']} → {cfg['direction']}{group_marker}")
            
            if sum_columns:
                logger.info(f"💾 Summen-Spalten gespeichert: {len(sum_columns)} Spalten")
                logger.info(f"  Σ {', '.join(sum_columns)}")
                logger.info(f"  sum_source: 'multi' (Dialog)")
            else:
                logger.info(f"ℹ️ Keine Summen-Spalten ausgewählt - sum_string/sum_source gelöscht")
            
            # Dialog schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Sortierung: {e}")
            # Trotzdem schließen
            self.accept()
    
    def _load_persisted_sort(self):
        """
        Lädt persistierte Sortierung aus App-DB und befüllt Dialog
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar für Persistierung")
                return
            
            # Lade Sort-Config aus App-DB
            sort_config_data, _ = gcs._app_db.get_value(self.view_guid, 'sort')
            
            if not sort_config_data:
                logger.info("📋 Keine persistierte Sortierung vorhanden")
                return
            
            logger.info(f"📋 Lade persistierte Sortierung: {sort_config_data}")
            
            # 🆕 NEUES FORMAT: Liste von {'column_key', 'direction', 'is_group'}
            if isinstance(sort_config_data, list):
                logger.info(f"  ✅ Neues Format (Liste): {len(sort_config_data)} Spalten")
                
                for col_config in sort_config_data:
                    column_key = col_config.get('column_key')
                    direction = col_config.get('direction', 'asc')
                    is_group = col_config.get('is_group', False)
                    
                    if column_key:
                        self._add_persisted_column(column_key, direction, is_group)
                        logger.info(f"    Spalte geladen: {column_key} {direction} {'[GRUPPE]' if is_group else ''}")
            
            # ❌ ALTES FORMAT: dict mit 'columns' (Multi-Sort) oder 'column' (Single-Sort)  
            # Wird nicht mehr verwendet, aber für Rückwärts-Kompatibilität beibehalten
            elif isinstance(sort_config_data, dict):
                if 'columns' in sort_config_data:
                    # MULTI-SORT: Liste von Spalten
                    columns_list = sort_config_data['columns']
                    logger.info(f"  ⚠️ Altes Format (Multi-Sort): {len(columns_list)} Spalten - wird konvertiert")
                    
                    for col_config in columns_list:
                        self._add_persisted_column(
                            col_config.get('column'),
                            col_config.get('direction', 'asc'),
                            False  # Keine Gruppierung im alten Format
                        )
                
                elif 'column' in sort_config_data:
                    # SINGLE-SORT: Eine Spalte
                    logger.info(f"  ⚠️ Altes Format (Single-Sort): {sort_config_data['column']} - wird konvertiert")
                    self._add_persisted_column(
                        sort_config_data['column'],
                        sort_config_data.get('direction', 'asc'),
                        False  # Keine Gruppierung im alten Format
                    )
            
            logger.info(f"✅ Persistierte Sortierung geladen: {self.sort_order_list.count()} Spalten")
            
            # 🆕 SUMMEN-SPALTEN LADEN (sum_string statt sum_columns)
            sum_columns_data, _ = gcs._app_db.get_value(self.view_guid, 'sum_string')
            sum_source, _ = gcs._app_db.get_value(self.view_guid, 'sum_source')
            
            if sum_columns_data and isinstance(sum_columns_data, list):
                logger.info(f"📋 Lade Summen-Spalten: {len(sum_columns_data)} Spalten (sum_source={sum_source})")
                
                # Markiere Summen-Spalten im sum_columns_list
                for row in range(self.sum_columns_list.count()):
                    item = self.sum_columns_list.item(row)
                    column_key = item.data(Qt.UserRole)
                    
                    if column_key in sum_columns_data:
                        item.setSelected(True)
                        logger.info(f"  Σ {column_key}")
                
                logger.info(f"✅ {len(sum_columns_data)} Summen-Spalten geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der persistierten Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _add_persisted_column(self, column_key: str, direction: str, is_group: bool = False):
        """
        Fügt eine persistierte Spalte zur Sortier-Liste hinzu
        
        Args:
            column_key: Spalten-Key
            direction: Richtung ('asc' oder 'desc')
            is_group: Gruppierung aktiv (default: False)
        """
        if not column_key:
            return
        
        # Prüfe ob bereits vorhanden
        for i in range(self.sort_order_list.count()):
            existing_item = self.sort_order_list.item(i)
            if existing_item.data(Qt.UserRole) == column_key:
                logger.warning(f"  ⚠️ Spalte {column_key} bereits in Liste")
                return
        
        # Hole Control-Config
        control = self.controls_config.get(column_key, {})
        name = control.get('name', column_key)
        
        # Erstelle Sortier-Item
        arrow = '↑' if direction == 'asc' else '↓'
        group_marker = ' [Gruppe]' if is_group else ''
        item_text = f"{name} [{column_key}] {arrow}{group_marker}"
        
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, column_key)
        item.setData(Qt.UserRole + 1, direction)  # Direction
        item.setData(Qt.UserRole + 2, is_group)  # 🆕 is_group aus Parameter
        
        self.sort_order_list.addItem(item)
        logger.info(f"  ➕ Spalte hinzugefügt: {name} ({direction}){' [GRUPPE]' if is_group else ''}")
