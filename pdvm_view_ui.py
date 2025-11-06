# pdvm_view_ui.py
"""
🎨 PDVM View UI - SAUBERE ARCHITEKTUR (Option B)

VERANTWORTLICHKEITEN:
- Nur Darstellung und UI-Komponenten
- QTableWidget Management
- UI-Events an Controller weitergeben
- KEINE Daten-Logik, KEINE Business-Logik

ARCHITEKTUR:
┌─────────────────────┐
│ PdvmViewController  │ ← Controller (empfängt Events)
├─────────────────────┤
│ PdvmViewUI          │ ← Display (DIESE KLASSE)
├─────────────────────┤
│ PdvmViewManager     │ ← Daten/Matrix
└─────────────────────┘

MIGRATION VON:
- PdvmViewDialog._create_ui() und Display-Logik
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMenu, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# 3-Ebenen Array-Struktur
from pdvm_matrix_constants import (
    WERT, ABDATUM, FORMATIERT,
    get_wert, get_abdatum, get_formatiert
)

# ========================================
# GLOBALER GCS-ZUGRIFF (ULTRA-EINFACH)
# ========================================
from pdvm_central_systemsteuerung import get_gcs as gcs

logger = logging.getLogger(__name__)


class PdvmViewUI(QWidget):
    """
    UI-Komponente für View-Darstellung
    
    VERANTWORTLICHKEITEN:
    - Table-Widget erstellen und verwalten
    - Daten in Tabelle darstellen
    - UI-Events erfassen und an Controller senden
    - Settings-Menü (Spalten, Filter, Sortierung)
    """
    
    # Signals für Controller-Kommunikation
    search_requested = pyqtSignal(str)  # (search_text)
    filter_requested = pyqtSignal(str, dict)  # (filter_type, filter_config)
    sort_requested = pyqtSignal(object)  # (sort_config) - object akzeptiert dict UND list!
    column_visibility_changed = pyqtSignal(str, bool)  # (column_name, visible)
    row_double_clicked = pyqtSignal(dict)  # (row_data) - Datensatz bei Doppelklick
    
    def __init__(self, controller, parent=None):
        """
        Initialisiert die UI-Komponente
        
        Args:
            controller: PdvmViewController-Instanz
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.controller = controller
        self.parent = parent
        
        # UI-Komponenten
        self.table_widget = None
        self.info_label = None
        self.settings_button = None
        
        # Daten-Container (nur für Display)
        self.current_instances = []
        self.current_controls = {}
        self.visible_columns = []
        
        # Sort-State für Header-Toggle
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        
        logger.info("🎨 PdvmViewUI initialisiert")
        
        # UI aufbauen
        self._create_ui()
    
    def _create_ui(self):
        """UI-Struktur erstellen"""
        logger.info("🔨 Erstelle UI-Struktur...")
        
        # Haupt-Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header-Bereich
        header_layout = self._create_header()
        layout.addLayout(header_layout)
        
        # Suchzeile über Tabelle
        search_layout = self._create_search_bar()
        layout.addLayout(search_layout)
        
        # Tabellen-Bereich
        self.table_widget = self._create_table()
        layout.addWidget(self.table_widget)
        
        logger.info("✅ UI-Struktur erstellt")
    
    def _create_header(self):
        """Header mit Titel und Settings erstellen"""
        header_layout = QHBoxLayout()
        
        # Titel
        title_label = QLabel(self.controller.title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
        """)
        header_layout.addWidget(title_label)
        
        # Test-Mode Indicator
        if self.controller.test_mode:
            test_label = QLabel("🧪 TEST MODE")
            test_label.setStyleSheet("""
                background-color: #fff3cd;
                color: #856404;
                padding: 5px 10px;
                border: 1px solid #ffc107;
                border-radius: 3px;
                font-weight: bold;
            """)
            header_layout.addWidget(test_label)
        
        header_layout.addStretch()
        
        # Expert Mode Button (nur für Admins)
        user_mode = self.controller.gcs.field_value('mode') if self.controller.gcs else None
        logger.info(f"🔍 User Mode aus GCS: '{user_mode}' (Type: {type(user_mode)})")
        
        if user_mode == 'admin':
            # Hole aktuellen Expert Mode Status aus GCS (persistent!)
            current_expert_mode = self.controller.gcs.expert_mode if self.controller.gcs else False
            
            self.expert_mode_button = QPushButton("👨‍💼 Expert Mode")
            self.expert_mode_button.setCheckable(True)
            self.expert_mode_button.setChecked(current_expert_mode)  # Aus GCS laden!
            self.expert_mode_button.setFixedHeight(32)
            self.expert_mode_button.setToolTip("Expert Mode ein/ausschalten (nur Admin)")
            self.expert_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #e74c3c;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:checked:hover {
                    background-color: #c0392b;
                }
            """)
            self.expert_mode_button.clicked.connect(self._toggle_expert_mode)
            header_layout.addWidget(self.expert_mode_button)
            
            # Button-Text initial setzen
            if current_expert_mode:
                self.expert_mode_button.setText("👨‍💼 Expert Mode: AN")
            
            logger.info(f"✅ Expert Mode Button hinzugefügt (Admin-Modus, Status aus GCS: {current_expert_mode})")
        else:
            self.expert_mode_button = None
            logger.info("ℹ️ Expert Mode Button nicht verfügbar (kein Admin)")
        
        # 🎯 SORT RESET BUTTON (für alle Benutzer)
        self.sort_reset_button = QPushButton("🔄 Sort")
        self.sort_reset_button.setFixedHeight(32)
        self.sort_reset_button.setToolTip("Sortierung zurücksetzen")
        self.sort_reset_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.sort_reset_button.clicked.connect(self._reset_sort)
        header_layout.addWidget(self.sort_reset_button)
        logger.info("✅ Sort Reset Button hinzugefügt")
        
        # 🆕 SUMMEN RESET BUTTON (für alle Benutzer)
        self.sum_reset_button = QPushButton("🔄 Σ")
        self.sum_reset_button.setFixedHeight(32)
        self.sum_reset_button.setToolTip("Summen zurücksetzen")
        self.sum_reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.sum_reset_button.clicked.connect(self._reset_sum)
        header_layout.addWidget(self.sum_reset_button)
        logger.info("✅ Summen Reset Button hinzugefügt")
        
        # 📂 COLLAPSE ALL BUTTON (Alle Gruppen zuklappen)
        self.collapse_all_button = QPushButton("◀ Alle")
        self.collapse_all_button.setFixedHeight(32)
        self.collapse_all_button.setToolTip("Alle Gruppen zuklappen")
        self.collapse_all_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.collapse_all_button.clicked.connect(self._collapse_all_groups)
        header_layout.addWidget(self.collapse_all_button)
        logger.info("✅ Collapse All Button hinzugefügt")
        
        # 📂 EXPAND ALL BUTTON (Alle Gruppen aufklappen)
        self.expand_all_button = QPushButton("▼ Alle")
        self.expand_all_button.setFixedHeight(32)
        self.expand_all_button.setToolTip("Alle Gruppen aufklappen")
        self.expand_all_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.expand_all_button.clicked.connect(self._expand_all_groups)
        header_layout.addWidget(self.expand_all_button)
        logger.info("✅ Expand All Button hinzugefügt")
        
        # Info-Label (Anzahl Datensätze)
        self.info_label = QLabel("Keine Daten")
        self.info_label.setStyleSheet("""
            color: #7f8c8d;
            padding: 5px;
        """)
        header_layout.addWidget(self.info_label)
        
        # Settings-Button (Zahnrad-Menü)
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setToolTip("Einstellungen")
        self.settings_button.clicked.connect(self._show_settings_menu)
        header_layout.addWidget(self.settings_button)
        
        return header_layout
    
    def _create_search_bar(self):
        """Suchzeile über Tabelle erstellen"""
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 2, 5, 2)
        
        # Label
        search_label = QLabel("🔍 Suchen:")
        search_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        search_layout.addWidget(search_label)
        
        # Suchfeld
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche in allen sichtbaren Spalten (enthält, UND-Verknüpfung)...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.returnPressed.connect(self._execute_search)  # Enter-Taste
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 2px solid #3498db;
                border-radius: 3px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #2980b9;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        # Suchen-Button (Lupe)
        search_button = QPushButton("🔍")
        search_button.setFixedSize(32, 28)
        search_button.setToolTip("Suche ausführen")
        search_button.clicked.connect(self._execute_search)
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        search_layout.addWidget(search_button)
        
        # Löschen-Button
        clear_search_button = QPushButton("❌")
        clear_search_button.setFixedSize(28, 28)
        clear_search_button.setToolTip("Suche löschen")
        clear_search_button.clicked.connect(self._clear_search)
        clear_search_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        search_layout.addWidget(clear_search_button)
        
        return search_layout
    
    def _create_table(self):
        """QTableWidget erstellen"""
        table = QTableWidget()
        
        # Styling
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.ExtendedSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Header
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsMovable(True)
        table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        table.horizontalHeader().customContextMenuRequested.connect(self._header_context_menu)
        
        # Sortierung durch Klick
        table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
        # 🔗 Gruppen-Collapse/Expand durch Klick auf Gruppen-Header
        table.cellClicked.connect(self._on_cell_clicked)
        
        # 🔗 Doppelklick für Datensatz-Auswahl (z.B. für GenerellerDialog)
        table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
        # Vertikaler Header
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultSectionSize(25)
        
        logger.info("✅ TableWidget erstellt")
        return table
    
    def set_data(self, instances, controls_config):
        """
        Daten in Tabelle darstellen (LEGACY)
        
        Args:
            instances: Liste von PdvmCentralDatenbank-Instanzen
            controls_config: Controls-Konfiguration
        """
        logger.info(f"📊 Setze Daten: {len(instances)} Instanzen")
        
        self.current_instances = instances
        self.current_controls = controls_config
        
        # Sichtbare Spalten ermitteln
        self._determine_visible_columns()
        
        # Tabelle befüllen
        self._populate_table()
        
        # Info aktualisieren
        self._update_info_label()
    
    def set_data_from_matrix(self, projected_matrix, column_keys, all_controls):
        """
        Daten aus Matrix Manager darstellen (NEUE Matrix-Pipeline)
        
        Args:
            projected_matrix: Matrix mit projizierten Daten (Liste von Dicts)
            column_keys: Liste der sichtbaren Spalten-Keys
            all_controls: Vollständige Control-Konfigurationen
        """
        logger.info(f"🎨 Setze Daten aus Matrix: {len(projected_matrix)} Zeilen, {len(column_keys)} Spalten")
        
        # Speichere für Zugriff
        self.projected_matrix = projected_matrix
        self.current_column_keys = column_keys
        self.current_controls = all_controls
        
        # WICHTIG: visible_columns für Header-Klick befüllen!
        self._determine_visible_columns()
        
        # ✅ Expert Mode Status direkt aus GCS
        expert_mode = gcs().expert_mode if gcs() else False
        
        # 🎯 KRITISCH: Tabelle KOMPLETT zurücksetzen (sonst bleiben alte Zeilen!)
        # Problem: clear() löscht nur Inhalt, nicht die Zeilen selbst
        # Lösung: Erst auf 0 setzen, dann auf neue Anzahl
        self.table_widget.setRowCount(0)  # ← ERST auf 0 setzen (löscht ALLE Zeilen)
        self.table_widget.setColumnCount(0)  # ← Spalten auch zurücksetzen
        
        # Jetzt neue Größe setzen
        self.table_widget.setRowCount(len(projected_matrix))
        self.table_widget.setColumnCount(len(column_keys))
        
        # Header setzen mit Tooltips und Expert Mode Formatierung
        header_labels = []
        header_tooltips = []
        for col_key in column_keys:
            control_config = all_controls.get(col_key, {})
            label = control_config.get('name', col_key)
            control_type = control_config.get('control_type', '')
            
            # FEATURE 3: Im Expert Mode Control-Key in zweiter Zeile anzeigen
            if expert_mode:
                header_text = f"{label}\n{col_key}"
            else:
                header_text = label
            
            header_labels.append(header_text)
            
            # FEATURE 2: Tooltip mit Control-Key und Typ
            tooltip_text = label
            tooltip_text += f"\nControl-Key: {col_key}"
            if control_type:
                tooltip_text += f"\nTyp: {control_type}"
            header_tooltips.append(tooltip_text)
        
        self.table_widget.setHorizontalHeaderLabels(header_labels)
        
        # ========================================================================
        # FEATURE 3: Header-Schriftgröße Bold + 2 Punkte größer (von GCS!)
        # ========================================================================
        header = self.table_widget.horizontalHeader()
        
        # Font-Größe aus GCS holen (zentral definiert)
        gcs_instance = self.controller.gcs
        if gcs_instance and hasattr(gcs_instance, 'header_font_size'):
            header_size = gcs_instance.header_font_size
        else:
            # Fallback falls GCS nicht verfügbar
            header_size = 11  # Default = 9pt Basis + 2pt
            logger.warning("⚠️ GCS nicht verfügbar, verwende Fallback-Header-Größe: 11pt")
        
        # Font erstellen mit fester Größe aus GCS
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(header_size)
        header.setFont(header_font)
        
        logger.debug(f"📏 Header-Font: {header_size}pt (aus GCS), Bold")
        
        # FEATURE 2: Header Tooltips setzen
        for col_idx, tooltip in enumerate(header_tooltips):
            header_item = self.table_widget.horizontalHeaderItem(col_idx)
            if header_item:
                header_item.setToolTip(tooltip)
        
        logger.info(f"  📋 Header: {', '.join(header_labels[:5])}{'...' if len(header_labels) > 5 else ''}")
        
        # ✅ ARRAY: Tabelle befüllen aus Matrix (Liste von Dicts) mit Tooltips
        for row_idx, row_data in enumerate(projected_matrix):
            # 🆕 PHASE 3: Prüfe row_type für unterschiedliche Zeilen-Typen
            row_type_dict = row_data.get('row_type', {})
            row_type = row_type_dict.get('type', 'data') if isinstance(row_type_dict, dict) else 'data'
            
            # === GRUPPEN-HEADER RENDERING ===
            if row_type == 'group_header':
                self._render_group_header_in_table(row_idx, row_type_dict, column_keys)
                continue  # Nächste Zeile
            
            # === SUMMEN-ZEILE RENDERING ===
            if row_type == 'sum_row':
                self._render_sum_row_in_table(row_idx, row_data, row_type_dict, column_keys)
                continue  # Nächste Zeile
            
            # === NORMALE DATEN-ZEILE ===
            for col_idx, col_key in enumerate(column_keys):
                # ✅ ARRAY: Zelle holen und Ebenen extrahieren
                cell = row_data.get(col_key, [None, None, None])
                
                # EBENE 1: Wert für Anzeige
                value = get_wert(cell)
                display_value = str(value) if value is not None else ""
                
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Nicht editierbar
                
                # FEATURE 1: Tooltip mit Abdatum erstellen
                tooltip_parts = []
                
                # Aktueller Wert
                if value is not None and str(value).strip():
                    tooltip_parts.append(f"Wert: {value}")
                else:
                    tooltip_parts.append("Wert: (leer)")
                
                # ✅ ARRAY: Formatiertes Abdatum aus Zelle holen (EBENE 3)
                formatted_abdatum = get_formatiert(cell)
                # EBENE 2: Roh-Abdatum
                raw_abdatum = get_abdatum(cell)
                
                if formatted_abdatum:
                    # Format: "Abdatum: formatiertes_abdatum (raw_abdatum)"
                    if raw_abdatum:
                        tooltip_parts.append(f"Abdatum: {formatted_abdatum} ({raw_abdatum})")
                    else:
                        tooltip_parts.append(f"Abdatum: {formatted_abdatum}")
                elif raw_abdatum:
                    tooltip_parts.append(f"Abdatum: {raw_abdatum}")
                else:
                    tooltip_parts.append("Abdatum: (nicht verfügbar)")
                
                # Zusätzliche Informationen im Expert Mode
                if expert_mode:
                    control_config = all_controls.get(col_key, {})
                    tooltip_parts.append(f"Control-Key: {col_key}")
                    if control_config.get('control_type'):
                        tooltip_parts.append(f"Typ: {control_config.get('control_type')}")
                    if control_config.get('feld'):
                        tooltip_parts.append(f"Feld: {control_config.get('feld')}")
                    if control_config.get('gruppe'):
                        tooltip_parts.append(f"Gruppe: {control_config.get('gruppe')}")
                
                # Tooltip setzen
                if tooltip_parts:
                    item.setToolTip("\n".join(tooltip_parts))
                
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Spaltenbreiten anpassen
        self.table_widget.resizeColumnsToContents()
        
        logger.info(f"✅ Tabelle aus Matrix befüllt: {len(projected_matrix)} Zeilen x {len(column_keys)} Spalten")
        
        # Info-Label aktualisieren
        self._update_info_label()
    
    def _render_group_header_in_table(self, row_idx: int, row_type_dict: dict, column_keys: list):
        """
        🆕 PHASE 3 + SUMMEN: Rendert Gruppen-Header-Zeile in Tabelle
        
        VARIANTE 2 (Spalten):
        - Erste Spalte: Gruppen-Text (KEIN Spanning)
        - Summen-Spalten: Zeigen Gruppen-Summen
        - Andere Spalten: Leer
        
        Args:
            row_idx: Zeilen-Index
            row_type_dict: row_type Dict mit Gruppen-Metadaten (inkl. group_sums)
            column_keys: Liste der Spalten-Keys
        """
        try:
            from PyQt5.QtGui import QColor, QFont
            from PyQt5.QtCore import Qt
            
            # Metadaten extrahieren
            group_level = row_type_dict.get('level', 0)
            group_column = row_type_dict.get('column', '')
            group_value = row_type_dict.get('value', '')
            group_count = row_type_dict.get('count', 0)
            is_collapsed = row_type_dict.get('collapsed', False)
            group_id = row_type_dict.get('group_id', '')
            group_sums = row_type_dict.get('group_sums', {})  # 🆕 Gruppen-Summen
            
            # 🔍 DEBUG: Gruppen-Summen prüfen
            if group_sums:
                logger.debug(f"🧮 Gruppen-Header hat Summen: {group_sums}")
            else:
                logger.warning(f"⚠️ Gruppen-Header OHNE Summen! row_type_dict keys: {row_type_dict.keys()}")
            
            # Font für alle Zellen
            gcs_instance = self.controller.gcs
            if gcs_instance and hasattr(gcs_instance, 'group_font_size'):
                group_size = gcs_instance.group_font_size
            else:
                group_size = 10  # Default
            
            group_font = QFont()
            group_font.setBold(True)
            group_font.setPointSize(group_size)
            
            # Hintergrund nach Ebene
            if group_level == 0:
                bg_color = QColor("#e3f2fd")  # Hellblau
            elif group_level == 1:
                bg_color = QColor("#bbdefb")  # Mittelblau
            else:
                bg_color = QColor("#90caf9")  # Dunkelblau
            
            # 🆕 VARIANTE 2: Jede Spalte einzeln befüllen (KEIN Spanning!)
            for col_idx, col_key in enumerate(column_keys):
                
                # === ERSTE SPALTE: Gruppen-Text ===
                if col_idx == 0:
                    indent = "  " * group_level
                    icon = "▶" if is_collapsed else "▼"
                    display_column = group_column.replace('_original', '').replace('_show', '').replace('_', ' ').title()
                    
                    text = f"{indent}{icon} {display_column}: {group_value}"
                    if group_count > 0:
                        text += f" ({group_count})"
                    
                    item = QTableWidgetItem(text)
                    
                    # Tooltip mit Gruppen-Info
                    tooltip = (
                        f"Gruppierung: {display_column}\n"
                        f"Wert: {group_value}\n"
                        f"Ebene: {group_level}\n"
                        f"Einträge: {group_count}\n"
                        f"Status: {'Eingeklappt' if is_collapsed else 'Ausgeklappt'}\n"
                        f"ID: {group_id}"
                    )
                    if group_sums:
                        tooltip += "\n\nGruppen-Summen:"
                        for sum_col, sum_val in group_sums.items():
                            tooltip += f"\n  {sum_col}: {sum_val}"
                    item.setToolTip(tooltip)
                    
                    # Group-ID speichern für Click-Handler
                    item.setData(Qt.UserRole, group_id)
                    item.setData(Qt.UserRole + 1, 'GROUP_HEADER')
                
                # === SUMMEN-SPALTE: Zeige Gruppen-Summe ===
                elif col_key in group_sums:
                    sum_value = group_sums[col_key]
                    
                    # Formatierung
                    if isinstance(sum_value, float):
                        display_value = f"Σ {sum_value:,.2f}".replace(',', ' ').replace('.', ',')
                    elif isinstance(sum_value, int):
                        display_value = f"Σ {sum_value:,}".replace(',', ' ')
                    else:
                        display_value = f"Σ {sum_value}"
                    
                    item = QTableWidgetItem(display_value)
                    
                    # Tooltip
                    item.setToolTip(f"Gruppen-Summe: {sum_value}\nÜber {group_count} Einträge")
                
                # === ANDERE SPALTEN: Leer ===
                else:
                    item = QTableWidgetItem("")
                
                # Styling für ALLE Zellen
                item.setBackground(bg_color)
                item.setFont(group_font)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # Item setzen
                self.table_widget.setItem(row_idx, col_idx, item)
            
            logger.debug(f"✅ Gruppen-Header gerendert: Row {row_idx}, Level {group_level}, {group_value}, {len(group_sums)} Summen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern von Gruppen-Header: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _render_sum_row_in_table(self, row_idx: int, row_data: dict, row_type_dict: dict, column_keys: list):
        """
        🆕 SUMMEN: Rendert Summen-Zeile in Tabelle
        
        Args:
            row_idx: Zeilen-Index
            row_data: Komplette Zeilen-Daten (mit Summen-Werten)
            row_type_dict: row_type Dict mit Summen-Metadaten
            column_keys: Liste der Spalten-Keys
        """
        try:
            from PyQt5.QtGui import QColor, QFont
            from PyQt5.QtCore import Qt
            
            # Metadaten extrahieren
            sum_label = row_type_dict.get('label', 'Summe')
            sum_columns = row_type_dict.get('columns', [])
            row_count = row_type_dict.get('row_count', 0)
            
            logger.debug(f"🧮 Rendere Summen-Zeile: {len(sum_columns)} Summen-Spalten")
            logger.debug(f"🔍 row_data keys: {list(row_data.keys())[:10]}...")  # Erste 10 Keys
            
            # Durch alle Spalten iterieren
            for col_idx, col_key in enumerate(column_keys):
                # Erste Spalte: Label "Summe (X Zeilen)"
                if col_idx == 0:
                    text = f"{sum_label}"
                    if row_count > 0:
                        text += f" ({row_count} Zeilen)"
                    
                    item = QTableWidgetItem(text)
                    
                # Spalte ist in sum_columns: Summen-Wert anzeigen
                elif col_key in sum_columns:
                    cell = row_data.get(col_key, [None, None, None])
                    
                    # 🔍 DEBUG: Zell-Wert prüfen
                    logger.debug(f"  Spalte {col_key}: cell={cell}")
                    
                    # EBENE 1: Summen-Wert (ist bereits berechnet)
                    sum_value = get_wert(cell)
                    
                    # Formatierung (z.B. Tausender-Trennzeichen)
                    if isinstance(sum_value, float):
                        display_value = f"{sum_value:,.2f}".replace(',', ' ').replace('.', ',')
                    elif isinstance(sum_value, int):
                        display_value = f"{sum_value:,}".replace(',', ' ')
                    else:
                        display_value = str(sum_value) if sum_value is not None else ""
                    
                    item = QTableWidgetItem(display_value)
                    
                    # Tooltip
                    tooltip = f"Summe: {sum_value}\nSummiert über: {row_count} Zeilen"
                    item.setToolTip(tooltip)
                    
                # Andere Spalten: Leer
                else:
                    item = QTableWidgetItem("")
                
                # 🎨 STYLING (ALLE Zellen)
                # Hintergrund: Gelb-Grau
                item.setBackground(QColor("#fff9c4"))  # Hellgelb
                
                # Font: Bold + 1 Punkt größer
                gcs_instance = self.controller.gcs
                if gcs_instance and hasattr(gcs_instance, 'group_font_size'):
                    sum_size = gcs_instance.group_font_size
                else:
                    sum_size = 10  # Default
                
                sum_font = QFont()
                sum_font.setBold(True)
                sum_font.setPointSize(sum_size)
                item.setFont(sum_font)
                
                # Nicht editierbar
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # 🎯 WICHTIG: Marker setzen für Collapse-Logik
                if col_idx == 0:  # Nur in erster Spalte
                    item.setData(Qt.UserRole + 1, 'SUM_ROW')
                
                # Item setzen
                self.table_widget.setItem(row_idx, col_idx, item)
            
            logger.debug(f"✅ Summen-Zeile gerendert: Row {row_idx}, {len(sum_columns)} Summen-Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern von Summen-Zeile: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _determine_visible_columns(self):
        """
        ✅ ULTRA-VEREINFACHT: Hole Projektion DIREKT aus GCS
        
        KEINE Wrapper-Methode mehr - direkter Zugriff auf GCS!
        """
        gcs_instance = self.controller.gcs
        if not gcs_instance:
            logger.error("❌ GCS nicht verfügbar!")
            self.visible_columns = []
            return
        
        # Expert Mode aus Button oder GCS
        expert_mode_active = False
        if self.expert_mode_button:
            expert_mode_active = self.expert_mode_button.isChecked()
        
        # ✅ DIREKTER GCS-ZUGRIFF: Index 0 (Standard) oder 5 (Expert)
        projection_index = 5 if expert_mode_active else 0
        column_keys = gcs_instance.get_projection_table(self.controller.view_guid, projection_index)
        
        logger.debug(f"📊 Projektion [{projection_index}] {'Expert' if expert_mode_active else 'Standard'}: {len(column_keys)} Spalten")
        
        # Konvertiere Keys zu visible_columns Format (für UI-Rendering)
        self.visible_columns = []
        for col_key in column_keys:
            control_config = self.current_controls.get(col_key)
            if control_config:
                self.visible_columns.append({
                    'key': col_key,
                    'label': control_config.get('name', col_key),
                    'type': control_config.get('type', 'string'),
                    'display_order': control_config.get('display_order', 999),
                    'expert_mode': control_config.get('expert_mode', False)
                })
            else:
                logger.warning(f"⚠️ Spalte {col_key} in Projektion, aber nicht in Controls!")
        
        logger.info(f"  ✅ {len(self.visible_columns)} Spalten aus GCS-Projektion [{projection_index}] geladen")
    
    def _populate_table(self):
        """Tabelle mit Daten befüllen"""
        logger.info("🔨 Befülle Tabelle...")
        
        # Tabelle leeren
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        
        if not self.visible_columns or not self.current_instances:
            logger.info("  ℹ️ Keine Daten zum Anzeigen")
            return
        
        # DEBUG: Erste Instanz prüfen
        if self.current_instances:
            first_inst = self.current_instances[0]
            logger.info(f"  📊 Erste Instanz: {first_inst.guid}")
            logger.info(f"  📊 Typ: {type(first_inst)}")
            logger.info(f"  📊 Hat get_value: {hasattr(first_inst, 'get_value')}")
        
        # Spalten setzen
        self.table_widget.setColumnCount(len(self.visible_columns))
        headers = [col['label'] for col in self.visible_columns]
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # DEBUG: Spalten-Info (ohne verschachtelte f-strings)
        spalten_info = ', '.join([f"{col['key']} ({col['label']})" for col in self.visible_columns[:3]])
        logger.info(f"  📋 Spalten: {spalten_info}...")
        
        # Zeilen setzen
        self.table_widget.setRowCount(len(self.current_instances))
        
        # Daten befüllen
        for row_idx, instance in enumerate(self.current_instances):
            if row_idx == 0:  # DEBUG: Nur erste Zeile detailliert loggen
                logger.info(f"  📊 Befülle Zeile {row_idx} (GUID: {instance.guid})...")
            
            for col_idx, col_info in enumerate(self.visible_columns):
                control_key = col_info['key']
                
                # Wert aus Instanz holen
                value = self._get_value_from_instance(instance, control_key)
                
                if row_idx == 0 and col_idx < 3:  # DEBUG: Erste 3 Werte der ersten Zeile
                    logger.info(f"    📊 Spalte {col_idx} ({control_key}): value={value}")
                
                # Item erstellen
                item = QTableWidgetItem(str(value) if value is not None else "")
                
                # Styling basierend auf Typ
                self._style_item(item, col_info['type'])
                
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Spaltenbreiten anpassen
        self.table_widget.resizeColumnsToContents()
        
        logger.info(f"✅ Tabelle befüllt: {len(self.current_instances)} Zeilen x {len(self.visible_columns)} Spalten")
    
    def _get_value_from_instance(self, instance, control_key):
        """
        Wert aus Instanz extrahieren
        
        WICHTIG: get_value() gibt Tupel zurück: (wert, abdatum)
        Wir müssen mit Stichtag abfragen!
        """
        # SPEZIALFALL: uid
        if control_key == 'uid_show':
            return instance.guid
        
        # Original-Key ermitteln (remove _show suffix)
        original_key = control_key.replace('_show', '')
        
        # Control-Config holen
        original_control_key = f"{original_key}_original"
        if original_control_key not in self.current_controls:
            logger.debug(f"⚠️ Control '{original_control_key}' nicht in controls_config gefunden")
            return None
        
        control_config = self.current_controls[original_control_key]
        control_type = control_config.get('type', 'string')
        feld = control_config.get('feld', original_key)
        gruppe = control_config.get('gruppe', 'ROOT')
        
        # Stichtag aus GCS holen (als PdvmDateTime Objekt!)
        stichtag = self.controller.gcs.st_inst.PdvmDateTime if (self.controller.gcs and self.controller.gcs.st_inst) else None
        
        # Wert aus Instanz holen mit STICHTAG
        try:
            # WICHTIG: get_value() erwartet POSITIONAL: (gruppe, feld, stichtag)
            # Gibt TUPEL zurück: (wert, abdatum)
            result = instance.get_value(gruppe, feld, stichtag)
            
            # Tupel auspacken
            if isinstance(result, tuple) and len(result) == 2:
                wert, abdatum = result
            else:
                # Fallback falls kein Tupel
                wert = result
                abdatum = None
            
            # Datum-Spezialfall: Formatiertes Datum anzeigen
            if control_type == 'date' and isinstance(wert, dict):
                # Wert ist bereits ein Dict mit formatiertem Datum
                return wert.get('formatiertes_abdatum', wert.get('datum', ''))
            
            # Datum-Zusatzfelder (alter, jahr, monat, tag)
            elif control_type.startswith('date_'):
                return wert
            
            # Normaler Wert
            else:
                return wert
                
        except Exception as e:
            logger.debug(f"❌ Fehler beim Lesen von {feld} aus Gruppe {gruppe}: {e}")
            return None
    
    def _style_item(self, item, item_type):
        """Item stylen basierend auf Typ"""
        # Rechtsbündig für Zahlen
        if item_type in ['integer', 'float', 'date_alter']:
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Zentriert für Datum
        elif item_type in ['date', 'date_jahr', 'date_monat', 'date_tag']:
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
    def _update_info_label(self):
        """Info-Label aktualisieren"""
        count = len(self.current_instances)
        if count == 0:
            self.info_label.setText("Keine Daten")
        elif count == 1:
            self.info_label.setText("1 Datensatz")
        else:
            self.info_label.setText(f"{count} Datensätze")
    
    # === EVENT HANDLER ===
    
    def _reset_sort(self):
        """
        Sortierung zurücksetzen - ANALOG ZU FILTER-RESET
        
        Workflow:
        1. sg_string und sg_source in app_db auf None setzen
        2. Pipeline ab SORT neu durchlaufen
        3. UI aktualisieren
        """
        logger.info("🔄 === SORT RESET ===")
        
        gcs_instance = gcs()
        if not gcs_instance:
            logger.error("❌ GCS nicht verfügbar - Sort Reset nicht möglich!")
            return
        
        # sg_string und sg_source auf None setzen
        gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_string', None)
        gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_source', None)
        gcs_instance._app_db.save_all_values()
        
        logger.info("✅ sg_string und sg_source zurückgesetzt (None)")
        
        # Pipeline ab SORT neu durchlaufen
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        pipeline.run('SORT')
        
        # UI aktualisieren
        self.controller.refresh_ui_from_pipeline()
        
        logger.info("✅ Sortierung zurückgesetzt - Original-Reihenfolge wiederhergestellt")
    
    def _reset_sum(self):
        """
        Summen-Konfiguration zurücksetzen - ANALOG ZU SORT-RESET
        
        Workflow:
        1. sum_string und sum_source in app_db auf None setzen
        2. Pipeline ab SUMMEN neu durchlaufen
        3. UI aktualisieren
        """
        logger.info("🔄 === SUMMEN RESET ===")
        
        gcs_instance = gcs()
        if not gcs_instance:
            logger.error("❌ GCS nicht verfügbar - Summen Reset nicht möglich!")
            return
        
        # sum_string und sum_source auf None setzen
        gcs_instance._app_db.set_value(self.controller.view_guid, 'sum_string', None)
        gcs_instance._app_db.set_value(self.controller.view_guid, 'sum_source', None)
        gcs_instance._app_db.save_all_values()
        
        logger.info("✅ sum_string und sum_source zurückgesetzt (None)")
        
        # Pipeline ab SUMMEN neu durchlaufen
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        pipeline.run('SUMMEN')
        
        # UI aktualisieren
        self.controller.refresh_ui_from_pipeline()
        
        logger.info("✅ Summen zurückgesetzt - Summen-Zeile entfernt")
    
    def _collapse_all_groups(self):
        """
        Klappt ALLE Gruppen zu
        
        Workflow:
        1. Findet alle Gruppen-Header in matrix_project
        2. Setzt collapsed=True für alle
        3. Aktualisiert UI (alle Zeilen ausblenden)
        """
        logger.info("📂 === COLLAPSE ALL GROUPS ===")
        
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        
        # Alle Gruppen-Header finden und collapsed setzen
        group_count = 0
        for row_data in pipeline.matrix_project:
            row_type = row_data.get('row_type')
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                row_type['collapsed'] = True
                group_count += 1
        
        logger.info(f"  ✅ {group_count} Gruppen auf collapsed=True gesetzt")
        
        # UI komplett neu rendern (einfachster Weg)
        self.controller.refresh_ui_from_pipeline()
        
        # 🎯 WICHTIG: Nach Rendering müssen Zeilen basierend auf collapsed-Status ausgeblendet werden
        self._apply_collapsed_state_to_ui()
        
        logger.info("✅ Alle Gruppen zugeklappt")
    
    def _expand_all_groups(self):
        """
        Klappt ALLE Gruppen auf
        
        Workflow:
        1. Findet alle Gruppen-Header in matrix_project
        2. Setzt collapsed=False für alle
        3. Aktualisiert UI (alle Zeilen einblenden)
        """
        logger.info("📂 === EXPAND ALL GROUPS ===")
        
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        
        # Alle Gruppen-Header finden und collapsed zurücksetzen
        group_count = 0
        for row_data in pipeline.matrix_project:
            row_type = row_data.get('row_type')
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                row_type['collapsed'] = False
                group_count += 1
        
        logger.info(f"  ✅ {group_count} Gruppen auf collapsed=False gesetzt")
        
        # UI komplett neu rendern (einfachster Weg)
        self.controller.refresh_ui_from_pipeline()
        
        # 🎯 WICHTIG: Nach Rendering müssen Zeilen basierend auf collapsed-Status eingeblendet werden
        self._apply_collapsed_state_to_ui()
        
        logger.info("✅ Alle Gruppen aufgeklappt")
    
    def _apply_collapsed_state_to_ui(self):
        """
        Wendet collapsed-Status aus Matrix auf UI-Zeilen an
        
        Diese Methode wird NACH refresh_ui_from_pipeline() aufgerufen,
        um die Zeilen-Sichtbarkeit basierend auf dem collapsed-Status zu setzen.
        
        Workflow:
        1. Collapsed-Status Map aus Matrix erstellen {group_id: collapsed}
        2. Durch alle Tabellen-Zeilen iterieren
        3. Bei GROUP_HEADER: Aktuelle Gruppe identifizieren
        4. Bei normalen Zeilen: setRowHidden() basierend auf collapsed-Status
        5. Bei SUM_ROW oder neuem Header: Gruppen-Kontext zurücksetzen
        """
        logger.info("🔧 === APPLY COLLAPSED STATE TO UI ===")
        
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        
        # SCHRITT 1: Collapsed-Status Map erstellen
        collapsed_groups = {}
        for row_data in pipeline.matrix_project:
            row_type = row_data.get('row_type')
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                group_id = row_type.get('group_id')
                collapsed = row_type.get('collapsed', False)
                collapsed_groups[group_id] = collapsed
        
        logger.info(f"  📊 Collapsed-Status Map: {len(collapsed_groups)} Gruppen")
        for gid, collapsed in collapsed_groups.items():
            status = "zugeklappt" if collapsed else "aufgeklappt"
            logger.info(f"    • {gid}: {status}")
        
        # SCHRITT 2: Durch Tabelle iterieren und Zeilen-Sichtbarkeit setzen
        total_rows = self.table_widget.rowCount()
        current_group_id = None
        current_group_collapsed = False
        hidden_count = 0
        visible_count = 0
        
        for row_idx in range(total_rows):
            item = self.table_widget.item(row_idx, 0)
            if not item:
                continue
            
            item_type = item.data(Qt.UserRole + 1)
            
            # SCHRITT 3: Neuer Gruppen-Header?
            if item_type == 'GROUP_HEADER':
                current_group_id = item.data(Qt.UserRole)
                current_group_collapsed = collapsed_groups.get(current_group_id, False)
                logger.info(f"  📂 Row {row_idx}: Header für Gruppe '{current_group_id}' "
                           f"({'collapsed' if current_group_collapsed else 'expanded'})")
                continue
            
            # SCHRITT 4: Summen-Zeile erreicht?
            if item_type == 'SUM_ROW':
                logger.info(f"  📊 Row {row_idx}: Summen-Zeile - Gruppen-Kontext zurückgesetzt")
                current_group_id = None
                current_group_collapsed = False
                continue
            
            # SCHRITT 5: Normale Zeile - Ausblenden wenn in collapsed Gruppe
            if current_group_id and current_group_collapsed:
                self.table_widget.setRowHidden(row_idx, True)
                hidden_count += 1
            else:
                self.table_widget.setRowHidden(row_idx, False)
                visible_count += 1
        
        logger.info(f"  ✅ Sichtbarkeit aktualisiert: {hidden_count} ausgeblendet, "
                   f"{visible_count} sichtbar")
        logger.info("✅ Collapsed-Status auf UI angewendet")
    
    def _toggle_expert_mode(self, checked):
        """Expert Mode ein/ausschalten - PERSISTENT in GCS - PIPELINE-PROJEKTION NEU DURCHLAUFEN"""
        logger.info(f"🔧 Expert Mode Toggle: {'AN' if checked else 'AUS'}")
        
        # ✅ Expert Mode in GCS persistent setzen - direkt ohne Zuweisung
        gcs_instance = gcs()
        if gcs_instance:
            gcs_instance.expert_mode = checked
            logger.info(f"✅ Expert Mode in GCS gesetzt: {gcs_instance.expert_mode}")
        else:
            logger.error("❌ GCS nicht verfügbar - Expert Mode nicht gesetzt!")
        
        # Button-Text aktualisieren
        if self.expert_mode_button:
            if checked:
                self.expert_mode_button.setText("👨‍💼 Expert Mode: AN")
            else:
                self.expert_mode_button.setText("👨‍💼 Expert Mode")
        
        # 🎯 KRITISCH: Pipeline-Projektion NEU durchlaufen!
        # Pipeline holt Expert Mode aus GCS und berechnet Projektion neu (Index 0 oder 5)
        logger.info("🔄 Pipeline-Projektion wird NEU berechnet (Expert Mode geändert)...")
        self.controller.refresh_ui_from_pipeline(rerun_projection=True)
        
        logger.info(f"✅ Expert Mode umgeschaltet und UI mit neuer Projektion aktualisiert")
    
    def _on_header_clicked(self, logical_index):
        """Header-Klick → Einfache Sortierung mit asc/desc Toggle"""
        logger.info(f"📊 Header geklickt: Spalte {logical_index}")
        logger.info(f"📋 Visible columns: {len(self.visible_columns)} Einträge")
        
        if logical_index < len(self.visible_columns):
            col_info = self.visible_columns[logical_index]
            column_key = col_info['key']
            logger.info(f"✅ Spalte gefunden: {column_key}")
            
            # Toggle-Logik
            if self.current_sort_column == column_key:
                # Gleiche Spalte: Richtung wechseln
                self.current_sort_direction = 'desc' if self.current_sort_direction == 'asc' else 'asc'
                logger.info(f"🔄 Toggle Richtung: {self.current_sort_direction}")
            else:
                # Neue Spalte: Start mit asc
                self.current_sort_column = column_key
                self.current_sort_direction = 'asc'
                logger.info(f"🆕 Neue Sortierung: {column_key}")
            
            # 🎯 ANALOG ZU FILTER: sg_string und sg_source in app_db speichern
            gcs_instance = gcs()
            if gcs_instance:
                # sg_string: Einfache Sort-Config
                sg_string = {
                    'column': column_key,
                    'direction': self.current_sort_direction
                }
                
                # In app_db speichern
                gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_string', sg_string)
                gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_source', 'einfach')
                gcs_instance._app_db.save_all_values()
                
                logger.info(f"✅ sg_string gespeichert: {sg_string}")
                logger.info(f"✅ sg_source gespeichert: 'einfach'")
                
                # 🎯 Pipeline ab SORT neu durchlaufen
                from pdvm_pipeline import get_pipeline
                pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
                pipeline.run('SORT')
                
                # UI aktualisieren
                self.controller.refresh_ui_from_pipeline()
                
                logger.info(f"✅ Header-Sort angewendet: {column_key} {self.current_sort_direction}")
            else:
                logger.error("❌ GCS nicht verfügbar - Sort nicht angewendet!")
        else:
            logger.warning(f"❌ Spalten-Index {logical_index} außerhalb von visible_columns ({len(self.visible_columns)} Spalten)")
            logger.warning(f"📋 Visible columns: {[c.get('key', '?') for c in self.visible_columns]}")
    
    def _on_cell_clicked(self, row, column):
        """
        Cell-Klick Handler → Prüft ob Gruppen-Header geklickt wurde
        
        Args:
            row: Zeilen-Index
            column: Spalten-Index
        """
        # Item holen
        item = self.table_widget.item(row, column)
        if not item:
            return
        
        # Prüfen ob es ein Gruppen-Header ist
        item_type = item.data(Qt.UserRole + 1)
        if item_type != 'GROUP_HEADER':
            return  # Normale Zeile, nichts tun
        
        # Group-ID holen
        group_id = item.data(Qt.UserRole)
        if not group_id:
            logger.warning("⚠️ Gruppen-Header ohne group_id geklickt")
            return
        
        logger.info(f"📂 Gruppen-Header geklickt: {group_id} (Zeile {row})")
        
        # Collapse/Expand Toggle
        self._toggle_group_collapse(group_id, row)
    
    def _on_cell_double_clicked(self, row, column):
        """
        Cell-Doppelklick Handler → Sendet row_data an Controller
        
        Args:
            row: Zeilen-Index
            column: Spalten-Index
        """
        try:
            # Prüfen ob es ein Gruppen-Header ist (diese ignorieren)
            item = self.table_widget.item(row, column)
            if item:
                item_type = item.data(Qt.UserRole + 1)
                if item_type == 'GROUP_HEADER':
                    logger.debug("📂 Gruppen-Header doppelt geklickt → ignoriert")
                    return
            
            # Row-Data aus Matrix holen
            if not hasattr(self.controller, 'matrix_manager'):
                logger.error("❌ Matrix Manager nicht verfügbar!")
                return
            
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
            
            # ✅ WICHTIG: matrix_sort verwenden, NICHT matrix_project!
            # matrix_project enthält nur sichtbare Felder (SHOW)
            # matrix_sort enthält ALLE Felder inkl. uid_original!
            
            # Finde die entsprechende Zeile in der Matrix (ohne Gruppen-Header)
            data_row_index = 0
            for matrix_row in pipeline.matrix_sort:
                row_type = matrix_row.get('row_type')
                
                # Überspringe Gruppen-Header
                if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                    continue
                
                # Ist das die gesuchte Zeile?
                if data_row_index == row:
                    # Signal mit row_data emittieren (enthält ALLE Felder!)
                    logger.info(f"🖱️ Doppelklick auf Zeile {row} → Signal emittiert")
                    self.row_double_clicked.emit(matrix_row)
                    return
                
                data_row_index += 1
            
            logger.warning(f"⚠️ Zeile {row} nicht in Matrix gefunden!")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Doppelklick-Handler: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _toggle_group_collapse(self, group_id: str, header_row: int):
        """
        Klappt eine Gruppe ein/aus
        
        Args:
            group_id: Eindeutige Gruppen-ID
            header_row: Zeilen-Index des Gruppen-Headers
        """
        logger.info(f"🔄 Toggle Collapse für Gruppe: {group_id}")
        
        # Aktuellen collapsed-Status aus matrix_project holen
        if not hasattr(self.controller, 'matrix_manager'):
            logger.error("❌ Matrix Manager nicht verfügbar!")
            return
        
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        
        # Finde die Header-Zeile in der Matrix
        collapsed_state = {}  # {group_id: collapsed}
        header_found = False
        
        for row_data in pipeline.matrix_project:
            row_type = row_data.get('row_type')
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                current_id = row_type.get('group_id')
                if current_id == group_id:
                    # Toggle den Status
                    current_collapsed = row_type.get('collapsed', False)
                    new_collapsed = not current_collapsed
                    row_type['collapsed'] = new_collapsed
                    header_found = True
                    logger.info(f"  ▶️ Status geändert: {'zugeklappt' if new_collapsed else 'aufgeklappt'}")
                    break
        
        if not header_found:
            logger.warning(f"⚠️ Gruppen-Header {group_id} nicht in Matrix gefunden!")
            return
        
        # UI neu rendern (nur die betroffenen Zeilen)
        self._update_group_visibility(group_id, header_row)
    
    def _update_group_visibility(self, group_id: str, header_row: int):
        """
        Aktualisiert die Sichtbarkeit der Gruppen-Mitglieder
        
        Args:
            group_id: Gruppen-ID
            header_row: Zeilen-Index des Headers
        """
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
        
        # Collapsed-Status holen
        is_collapsed = False
        for row_data in pipeline.matrix_project:
            row_type = row_data.get('row_type')
            if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
                if row_type.get('group_id') == group_id:
                    is_collapsed = row_type.get('collapsed', False)
                    break
        
        logger.info(f"  🔄 Update Visibility: {group_id} → {'collapsed' if is_collapsed else 'expanded'}")
        
        # Icon im Header aktualisieren
        header_item = self.table_widget.item(header_row, 0)
        if header_item:
            current_text = header_item.text()
            # Icon ersetzen (▼ → ▶ oder umgekehrt)
            if is_collapsed:
                new_text = current_text.replace("▼", "▶")
            else:
                new_text = current_text.replace("▶", "▼")
            header_item.setText(new_text)
        
        # Zeilen ein/ausblenden
        # Finde alle Zeilen die zur Gruppe gehören (bis zum nächsten Header, Ende oder SUMMEN-ZEILE)
        total_rows = self.table_widget.rowCount()
        current_row = header_row + 1
        
        while current_row < total_rows:
            item = self.table_widget.item(current_row, 0)
            if not item:
                break
            
            # Prüfen ob nächster Header erreicht
            item_type = item.data(Qt.UserRole + 1)
            if item_type == 'GROUP_HEADER':
                break  # Nächste Gruppe beginnt
            
            # 🎯 WICHTIG: Summen-Zeile NIEMALS ausblenden!
            if item_type == 'SUM_ROW':
                logger.info(f"  ⚠️ Summen-Zeile erreicht (Zeile {current_row}) - NICHT ausblenden!")
                break  # Summen-Zeile bleibt immer sichtbar
            
            # Zeile ein/ausblenden (nur normale Daten-Zeilen)
            if is_collapsed:
                self.table_widget.setRowHidden(current_row, True)
            else:
                self.table_widget.setRowHidden(current_row, False)
            
            current_row += 1
        
        hidden_count = current_row - header_row - 1
        logger.info(f"  ✅ {hidden_count} Zeilen {'ausgeblendet' if is_collapsed else 'eingeblendet'}")
    
    def _header_context_menu(self, pos):
        """Rechtsklick auf Header → Spalten-Menü"""
        menu = QMenu(self)
        
        # Spalten ein/ausblenden
        menu.addSection("Spalten")
        
        for col_info in self.visible_columns:
            action = menu.addAction(col_info['label'])
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(
                lambda checked, key=col_info['key']: self._toggle_column_visibility(key, checked)
            )
        
        menu.exec_(self.table_widget.horizontalHeader().mapToGlobal(pos))
    
    def _toggle_column_visibility(self, column_key, visible):
        """Spalten-Sichtbarkeit umschalten"""
        logger.info(f"👁️ Toggle Spalte '{column_key}': {visible}")
        self.column_visibility_changed.emit(column_key, visible)
    
    def _show_settings_menu(self):
        """Settings-Menü (Zahnrad) anzeigen"""
        menu = QMenu(self)
        
        # Filter
        filter_menu = menu.addMenu("🔍 Filter")
        filter_menu.addAction("Einfaches Filter", lambda: self._request_filter('simple'))
        filter_menu.addAction("Komplexes Filter", lambda: self._request_filter('complex'))
        filter_menu.addAction("Filter zurücksetzen", lambda: self._request_filter('reset'))
        
        # Sortierung
        sort_menu = menu.addMenu("📊 Sortierung")
        sort_menu.addAction("Sortierung konfigurieren", self._request_advanced_sort)
        sort_menu.addAction("Sortierung zurücksetzen", self._reset_sort)
        sort_menu.addAction("Alle Spalten sortierbar", self._enable_all_sortable)
        
        # Spalten-Verwaltung
        columns_menu = menu.addMenu("📋 Spalten")
        columns_menu.addAction("Spalten verwalten", self._show_column_management)
        columns_menu.addAction("Standard-Ansicht", self._reset_columns)
        
        # Exportieren
        menu.addSeparator()
        menu.addAction("💾 Exportieren...", self._export_data)
        
        # Aktualisieren
        menu.addSeparator()
        menu.addAction("🔄 Aktualisieren", self._refresh_view)
        
        # Menü anzeigen
        menu.exec_(self.settings_button.mapToGlobal(self.settings_button.rect().bottomLeft()))
    
    def _on_search_changed(self, text):
        """Suche wurde geändert - speichert nur Text"""
        # Speichert Suchtext, wird aber erst bei Button-Click ausgeführt
        self.search_requested.emit(text.strip())
    
    def _execute_search(self):
        """Führt Suche aus (Button oder Enter)"""
        logger.info("🔍 Suche ausführen Button geklickt")
        # Signal an Controller, um Suche auszuführen
        if hasattr(self.controller, 'execute_search'):
            self.controller.execute_search()
    
    def _clear_search(self):
        """Suche löschen"""
        logger.info("🗑️ Suche löschen Button geklickt")
        try:
            # ✅ V3: FilterResetManager für ALLE Filter-Löschungen
            from pdvm_filter_reset_manager import get_filter_reset_manager
            # Controller hat matrix_manager
            if not hasattr(self.controller, 'matrix_manager'):
                logger.error("❌ Controller hat keinen matrix_manager!")
                return
            reset_manager = get_filter_reset_manager(
                self.controller.view_guid,
                self.controller.matrix_manager
            )
            success = reset_manager.reset_all_filters()
            if success:
                # UI-Textfeld leeren
                self.search_input.clear()
                
                # UI aktualisieren aus Pipeline
                if hasattr(self.controller, 'refresh_ui_from_pipeline'):
                    self.controller.refresh_ui_from_pipeline()
                    
                logger.info("✅ Filter zurückgesetzt")
                # Erfolgsmeldung
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Filter zurückgesetzt",
                    "Alle aktiven Filter wurden erfolgreich entfernt."
                )
            else:
                logger.error("❌ Filter-Reset fehlgeschlagen")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Beim Zurücksetzen der Filter ist ein Fehler aufgetreten."
                )
        except Exception as e:
            logger.error(f"❌ Fehler beim Filter-Reset: {e}")
            import traceback
            logger.error(traceback.format_exc())
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Fehler",
                f"Kritischer Fehler beim Zurücksetzen der Filter:\n\n{str(e)}"
            )
    
    def _request_filter(self, filter_type):
        """Filter anfordern - öffnet entsprechenden Dialog"""
        logger.info(f"🔍 Filter angefordert: {filter_type}")
        
        if filter_type == 'reset':
            # Filter zurücksetzen
            self.filter_requested.emit('reset', {})
            return
        
        # Matrix Manager für Filter-Ausführung holen
        matrix_manager = self.controller.matrix_manager if hasattr(self.controller, 'matrix_manager') else None
        
        if not matrix_manager:
            logger.error("❌ Matrix Manager nicht verfügbar für Filter-Dialog")
            return
        
        try:
            # Hole Filter-Projektion aus GCS (V2)
            from pdvm_central_systemsteuerung import get_gcs
            gcs_inst = get_gcs()
            
            if not gcs_inst:
                logger.error("❌ GCS nicht verfügbar für Filter-Projektion")
                return
            
            # Filter-Projektion: Position 2 (Standard) oder 7 (Expert)
            filter_projection = gcs_inst.get_projection_table(
                self.controller.view_guid,
                'search_standard'  # Verwendet Position 2/7 je nach expert_mode
            )
            
            if not filter_projection:
                logger.error("❌ Keine Filter-Projektion verfügbar")
                return
            
            logger.info(f"📋 Filter-Projektion: {len(filter_projection)} Spalten")
            
            if filter_type == 'simple':
                # EINFACHER FILTER: V3 Dialog mit direkter Eingabe
                from pdvm_einfach_filter_dialog import SimpleFilterDialog
                
                dialog = SimpleFilterDialog(
                    parent=self,
                    view_guid=self.controller.view_guid,
                    controls_config=self.current_controls,
                    filter_projection=filter_projection,  # NEU: Nur Filter-Spalten
                    matrix_manager=matrix_manager
                )
                
            elif filter_type == 'complex':
                # KOMPLEXER FILTER: V3 Dialog mit 4-Positionen
                from pdvm_komplex_filter_dialog import ComplexFilterDialog
                
                dialog = ComplexFilterDialog(
                    parent=self,
                    view_guid=self.controller.view_guid,
                    controls_config=self.current_controls,
                    filter_projection=filter_projection,  # NEU: Nur Filter-Spalten
                    matrix_manager=matrix_manager
                )
            
            else:
                logger.error(f"❌ Unbekannter Filter-Typ: {filter_type}")
                return
            
            # Dialog ist MODAL und macht ALLES selbst:
            # 1. Sammelt Parameter aus UI
            # 2. Speichert in GCS unter 'einfach' oder 'komplex'
            # 3. Setzt s_string und s_source
            # 4. Ruft pipeline.run('FILTER') auf
            dialog.exec_()
            
            logger.info("✅ Filter-Dialog geschlossen")
            
            # UI aktualisieren nach Filter
            logger.info("🎨 UI-Refresh nach Filter-Dialog...")
            self.controller.refresh_ui_from_pipeline()
            
        except Exception as e:
            logger.error(f"❌ Filter-Dialog Fehler: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _request_advanced_sort(self):
        """Erweiterte Sortierung anfordern - DIALOG → sg_string + sg_source"""
        logger.info("📊 Erweiterte Sortierung angefordert")
        
        try:
            from pdvm_sort_summen_dialog import AdvancedSortDialog
            from pdvm_central_systemsteuerung import (
                get_gcs as gcs_func, 
                TABLE_INDEX_SORT, 
                EXPERT_MODE_OFFSET
            )
            
            gcs_instance = gcs_func()
            expert_mode = gcs_instance.expert_mode if gcs_instance else False
            
            # Berechne Array-Index: 3 (Standard) oder 8 (Expert = 3 + 5)
            table_index = TABLE_INDEX_SORT + (EXPERT_MODE_OFFSET if expert_mode else 0)
            
            # Hole Sort-Projektion (bereits gefiltert: NUR sortierbare Spalten!)
            projection = gcs_instance.get_projection_table(self.controller.view_guid, table_index)
            
            logger.info(f"  📋 Sort-Projektion Index {table_index}: {len(projection) if projection else 0} Spalten")
            
            dialog = AdvancedSortDialog(
                controls_config=self.current_controls,
                view_guid=self.controller.view_guid,
                projection=projection,  # Bereits NUR sortierbare Spalten - KEINE Filterung mehr nötig!
                parent=self
            )
            
            if dialog.exec_():
                sort_config = dialog.get_sort_config()
                
                # 🎯 ANALOG ZU FILTER: sg_string und sg_source in app_db speichern
                if gcs_instance and sort_config:
                    gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_string', sort_config)
                    gcs_instance._app_db.set_value(self.controller.view_guid, 'sg_source', 'multi')
                    gcs_instance._app_db.save_all_values()
                    
                    logger.info(f"✅ sg_string gespeichert: {sort_config}")
                    logger.info(f"✅ sg_source gespeichert: 'multi'")
                    
                    # 🎯 Pipeline ab SORT neu durchlaufen
                    from pdvm_pipeline import get_pipeline
                    pipeline = get_pipeline(self.controller.view_guid, self.controller.matrix_manager)
                    pipeline.run('SORT')
                    
                    # UI aktualisieren
                    self.controller.refresh_ui_from_pipeline()
                    
                    logger.info(f"✅ Advanced-Sort angewendet (multi)")
                else:
                    logger.warning("⚠️ Keine Sort-Config vom Dialog erhalten")
                
        except Exception as e:
            logger.error(f"❌ Sortier-Dialog Fehler: {e}")
            QMessageBox.warning(self, "Fehler", f"Sortier-Dialog konnte nicht geöffnet werden:\n{e}")
    
    def _enable_all_sortable(self):
        """Alle Spalten sortierbar machen"""
        logger.info("🔧 Aktiviere sortable für alle Spalten...")
        
        # An Controller senden
        for control_key in self.current_controls:
            if control_key.endswith('_show'):
                self.current_controls[control_key]['sortable'] = True
        
        # Speichern über Controller
        self.controller.gcs.db.set_value(
            gruppe=self.controller.view_guid,
            feld='controls',
            wert=self.current_controls
        )
        self.controller.gcs.db.save_all_values()
        
        QMessageBox.information(self, "Erfolg", "Alle Spalten sind jetzt sortierbar!")
    
    def _show_column_management(self):
        """
        Spalten-Verwaltungs-Dialog öffnen
        
        Verwendet den bestehenden column_management_dialog für:
        - Spalten ein-/ausblenden
        - Spalten-Reihenfolge ändern
        - Standard/Expert-Mode Ansicht
        """
        try:
            logger.info("📋 Öffne Spalten-Verwaltung...")
            
            from pdvm_column_management_dialog import show_column_management_dialog
            
            # Controls-Config vom Controller holen
            controls_config = self.current_controls if self.current_controls else {}
            
            if not controls_config:
                logger.warning("⚠️ Keine Controls-Config verfügbar")
                QMessageBox.warning(self, "Fehler", "Keine Spalten-Konfiguration verfügbar")
                return
            
            # Dialog öffnen (modal, blockiert bis Benutzer fertig ist)
            result = show_column_management_dialog(
                parent=self,
                view_guid=self.controller.view_guid,
                controls_config=controls_config,
                current_mode="table"
            )
            
            if result:
                logger.info("✅ Spalten-Konfiguration geändert - aktualisiere View...")
                
                # EFFIZIENT: Nur Projektion neu anwenden!
                # Controls wurden bereits vom Dialog geändert und persistent gemacht
                # → Projektions-Tabellen neu berechnen
                # → Projektion auf bestehende SortMatrix anwenden
                # → UI aktualisieren
                # KEINE BasisMatrix/Filter/Sort Rebuild nötig!
                self.controller.refresh_projection_only()
                
                logger.info("✅ View mit neuer Spalten-Konfiguration aktualisiert")
            else:
                logger.info("ℹ️ Spalten-Konfiguration nicht geändert (Abbruch)")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Verwaltung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Spalten-Verwaltung:\n{e}")
    
    def _reset_columns(self):
        """
        Spalten auf Standard zurücksetzen - EINFACH!
        
        WORKFLOW:
        1. Sicherheitsabfrage
        2. Reset-Flag in GCS setzen
        3. View KOMPLETT NEU aufrufen (wie Menüpunkt!)
        
        EINFACH UND SICHER: Kompletter Neustart der View!
        """
        try:
            logger.info("Spalten-Reset angefordert...")
            
            # SICHERHEITSABFRAGE
            reply = QMessageBox.question(
                self,
                "Standard-Ansicht wiederherstellen?",
                "ACHTUNG: Alle Spalten-Anpassungen gehen verloren!\n\n"
                "Folgende Einstellungen werden zurückgesetzt:\n"
                "- Spalten-Sichtbarkeit (show)\n"
                "- Spalten-Reihenfolge (display_order)\n"
                "- Expert-Mode Zuordnung\n"
                "- Sortier-Einstellungen\n\n"
                "Möchten Sie fortfahren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default: Nein
            )
            
            if reply != QMessageBox.Yes:
                logger.info("Spalten-Reset abgebrochen")
                return
            
            logger.info("Spalten-Reset bestätigt - Controller-Methode aufrufen...")
            
            # Controller macht ALLES (schließt UI, setzt Flag, initialisiert neu)
            self.controller.reset_controls_to_default()
            
            logger.info("Spalten erfolgreich auf Standard zurückgesetzt")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Spalten-Reset: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fehler", f"Fehler beim Zurücksetzen:\n{e}")
    
    def _export_data(self):
        """
        Daten als CSV exportieren
        
        Exportiert die aktuell gefilterte/sortierte SortMatrix aus dem Controller.
        Format: CSV mit Semikolon-Delimiter (deutsche Excel-Kompatibilität)
        Encoding: UTF-8 mit BOM (Excel-Kompatibilität)
        """
        try:
            logger.info("� CSV-Export gestartet...")
            
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            import csv
            from datetime import datetime
            from pdvm_matrix_constants import get_wert
            
            # Hole Matrix-Manager vom Controller
            if not self.controller or not hasattr(self.controller, 'matrix_manager'):
                QMessageBox.warning(self, "Export-Fehler", "Keine Daten zum Exportieren verfügbar")
                logger.warning("⚠️ Kein Matrix-Manager im Controller gefunden")
                return
            
            matrix_manager = self.controller.matrix_manager
            
            # Hole gefilterte/sortierte Daten aus SortMatrix
            export_data = matrix_manager.sort_matrix if hasattr(matrix_manager, 'sort_matrix') else []
            
            if not export_data:
                QMessageBox.warning(self, "Export-Fehler", "Keine Daten zum Exportieren (Matrix leer)")
                logger.warning("⚠️ SortMatrix ist leer")
                logger.info(f"  📊 Matrix-Status: basis={len(matrix_manager.basis_matrix) if matrix_manager.basis_matrix else 0}, "
                           f"filter={len(matrix_manager.filter_matrix) if matrix_manager.filter_matrix else 0}, "
                           f"sort={len(matrix_manager.sort_matrix) if matrix_manager.sort_matrix else 0}")
                return
            
            # Hole sichtbare Spalten (projizierte Spalten)
            visible_columns = []
            if hasattr(matrix_manager, 'get_projected_columns'):
                visible_columns = matrix_manager.get_projected_columns()
            
            if not visible_columns:
                QMessageBox.warning(self, "Export-Fehler", "Keine sichtbaren Spalten definiert")
                logger.warning("⚠️ Keine projizierten Spalten gefunden")
                return
            
            logger.info(f"  📊 Exportiere {len(export_data)} Zeilen x {len(visible_columns)} Spalten")
            
            # Standard-Dateiname mit Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            view_id = self.controller.view_guid[:8] if self.controller.view_guid else "export"
            default_filename = f"pdvm_export_{view_id}_{timestamp}.csv"
            
            # Datei-Dialog öffnen
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV-Export speichern",
                default_filename,
                "CSV Dateien (*.csv);;Alle Dateien (*.*)"
            )
            
            if not file_path:
                logger.info("ℹ️ Export vom Benutzer abgebrochen")
                return
            
            # CSV schreiben
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  # utf-8-sig für Excel-Kompatibilität
                writer = csv.writer(csvfile, delimiter=';')  # Semikolon für deutsche Excel-Version
                
                # Header schreiben (mit schönen Namen aus controls_config)
                header_row = []
                for col in visible_columns:
                    control = self.current_controls.get(col, {})
                    header_name = control.get('name', col)
                    header_row.append(header_name)
                writer.writerow(header_row)
                
                # Datenzeilen schreiben
                row_count = 0
                for row in export_data:
                    data_row = []
                    for col in visible_columns:
                        cell_value = row.get(col)
                        
                        # WICHTIG: Wert aus Array extrahieren!
                        if isinstance(cell_value, (list, tuple)):
                            value = get_wert(cell_value)
                        else:
                            value = cell_value
                        
                        # Konvertiere zu String, behandle None
                        data_row.append(str(value) if value is not None else '')
                    
                    writer.writerow(data_row)
                    row_count += 1
            
            # Erfolgs-Meldung
            col_count = len(visible_columns)
            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"✅ {row_count} Zeilen und {col_count} Spalten erfolgreich exportiert!\n\nDatei: {file_path}"
            )
            logger.info(f"✅ CSV-Export erfolgreich: {row_count} Zeilen x {col_count} Spalten → {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim CSV-Export: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Export:\n{e}")
    
    def _refresh_view(self):
        """View neu laden"""
        logger.info("🔄 View Refresh...")
        self.controller.refresh()
    
    def get_widget(self):
        """Widget für Parent zurückgeben"""
        return self

