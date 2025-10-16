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
        
        # Expert Mode Status prüfen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        expert_mode = gcs.expert_mode if gcs else False
        
        # Tabelle leeren und neu konfigurieren
        self.table_widget.clear()
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
        
        # FEATURE 3: Header-Schriftgröße etwas größer machen
        header = self.table_widget.horizontalHeader()
        font = header.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        header.setFont(font)
        
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
        🆕 PHASE 3: Rendert Gruppen-Header-Zeile in Tabelle
        
        Args:
            row_idx: Zeilen-Index
            row_type_dict: row_type Dict mit Gruppen-Metadaten
            column_keys: Liste der Spalten-Keys
        """
        try:
            # Metadaten extrahieren
            group_level = row_type_dict.get('level', 0)
            group_column = row_type_dict.get('column', '')
            group_value = row_type_dict.get('value', '')
            group_count = row_type_dict.get('count', 0)
            is_collapsed = row_type_dict.get('collapsed', False)
            group_id = row_type_dict.get('group_id', '')
            
            # Einrückung + Icon
            indent = "  " * group_level
            icon = "▶" if is_collapsed else "▼"
            
            # Spaltenname formatieren
            display_column = group_column.replace('_original', '').replace('_show', '').replace('_', ' ').title()
            
            # Text
            text = f"{indent}{icon} {display_column}: {group_value}"
            if group_count > 0:
                text += f" ({group_count} Einträge)"
            
            # Item erstellen
            item = QTableWidgetItem(text)
            
            # 🎨 STYLING
            from PyQt5.QtGui import QColor, QFont
            
            # Hintergrund nach Ebene
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
            
            # Tooltip
            tooltip = (
                f"Gruppierung: {display_column}\n"
                f"Wert: {group_value}\n"
                f"Ebene: {group_level}\n"
                f"Einträge: {group_count}\n"
                f"Status: {'Eingeklappt' if is_collapsed else 'Ausgeklappt'}\n"
                f"ID: {group_id}"
            )
            item.setToolTip(tooltip)
            
            # Group-ID speichern für Click-Handler (Phase 3.3)
            from PyQt5.QtCore import Qt
            item.setData(Qt.UserRole, group_id)
            item.setData(Qt.UserRole + 1, 'GROUP_HEADER')
            
            # Item setzen + Spanning
            self.table_widget.setItem(row_idx, 0, item)
            if len(column_keys) > 1:
                self.table_widget.setSpan(row_idx, 0, 1, len(column_keys))
            
            logger.debug(f"✅ Gruppen-Header gerendert: Row {row_idx}, Level {group_level}, {group_value}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern von Gruppen-Header: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _determine_visible_columns(self):
        """Sichtbare Spalten aus Controls ermitteln"""
        # Expert Mode Status prüfen
        expert_mode_active = False
        if self.expert_mode_button:
            expert_mode_active = self.expert_mode_button.isChecked()
        
        # Delegiere an neue Methode
        self._determine_visible_columns_with_expert_mode(expert_mode_active)
    
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
    
    def _toggle_expert_mode(self, checked):
        """Expert Mode ein/ausschalten - PERSISTENT in GCS"""
        logger.info(f"🔧 Expert Mode Toggle: {'AN' if checked else 'AUS'}")
        
        # Expert Mode in GCS persistent setzen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if gcs:
            gcs.expert_mode = checked
            logger.info(f"✅ Expert Mode in GCS gesetzt: {gcs.expert_mode}")
        else:
            logger.error("❌ GCS nicht verfügbar - Expert Mode nicht gesetzt!")
        
        # Button-Text aktualisieren
        if self.expert_mode_button:
            if checked:
                self.expert_mode_button.setText("👨‍💼 Expert Mode: AN")
            else:
                self.expert_mode_button.setText("👨‍💼 Expert Mode")
        
        # MATRIX-PIPELINE: Controller auffordern, UI mit neuer Projektion neu zu laden
        # Controller wählt automatisch die richtige Projektions-Tabelle basierend auf GCS expert_mode
        logger.info("🔄 Lade UI mit neuer Projektion (basierend auf GCS expert_mode)...")
        self.controller.refresh_ui_from_matrix()
        
        logger.info(f"✅ Expert Mode umgeschaltet und UI aktualisiert")
    
    def _determine_visible_columns_with_expert_mode(self, expert_mode_active):
        """Sichtbare Spalten mit Expert Mode ermitteln"""
        self.visible_columns = []
        
        # Nur _show Controls
        for control_key, control_config in self.current_controls.items():
            if control_config.get('control_type') != 'show':
                continue
            
            # Expert Mode Prüfung
            is_expert = control_config.get('expert_mode', False)
            
            # WICHTIG: Im Expert-Modus ALLE Spalten anzeigen
            if expert_mode_active:
                # Expert Mode: ALLE _show Controls (ignoriere 'show' Flag)
                self.visible_columns.append({
                    'key': control_key,
                    'label': control_config.get('name', control_key),
                    'type': control_config.get('type', 'string'),
                    'display_order': control_config.get('display_order', 999),
                    'expert_mode': is_expert
                })
            else:
                # Normal Mode: Nur Spalten mit show=True UND nicht expert_mode
                if control_config.get('show', False) and not is_expert:
                    self.visible_columns.append({
                        'key': control_key,
                        'label': control_config.get('name', control_key),
                        'type': control_config.get('type', 'string'),
                        'display_order': control_config.get('display_order', 999),
                        'expert_mode': is_expert
                    })
        
        # Nach display_order sortieren
        self.visible_columns.sort(key=lambda x: x['display_order'])
        
        logger.info(f"  📋 {len(self.visible_columns)} Spalten ermittelt (Expert Mode: {expert_mode_active})")
    
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
            
            # Sortier-Config erstellen
            sort_config = {
                'column': column_key,
                'direction': self.current_sort_direction
            }
            
            logger.info(f"🚀 Emit sort_requested Signal: {sort_config}")
            
            # An Controller senden
            self.sort_requested.emit(sort_config)
        else:
            logger.warning(f"❌ Spalten-Index {logical_index} außerhalb von visible_columns ({len(self.visible_columns)} Spalten)")
            logger.warning(f"📋 Visible columns: {[c.get('key', '?') for c in self.visible_columns]}")
    
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
            from filter_reset_manager import get_filter_reset_manager
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
            # Hole Filter-Projektion aus GCS
            from global_gcs import gcs
            
            if not gcs:
                logger.error("❌ GCS nicht verfügbar für Filter-Projektion")
                return
            
            # Filter-Projektion: Position 2 (Standard) oder 7 (Expert)
            filter_projection = gcs.get_projection_table(
                self.controller.view_guid,
                'search_standard'  # Verwendet Position 2/7 je nach expert_mode
            )
            
            if not filter_projection:
                logger.error("❌ Keine Filter-Projektion verfügbar")
                return
            
            logger.info(f"📋 Filter-Projektion: {len(filter_projection)} Spalten")
            
            if filter_type == 'simple':
                # EINFACHER FILTER: V3 Dialog mit direkter Eingabe
                from einfach_filter_dialog import SimpleFilterDialog
                
                dialog = SimpleFilterDialog(
                    parent=self,
                    view_guid=self.controller.view_guid,
                    controls_config=self.current_controls,
                    filter_projection=filter_projection,  # NEU: Nur Filter-Spalten
                    matrix_manager=matrix_manager
                )
                
            elif filter_type == 'complex':
                # KOMPLEXER FILTER: V3 Dialog mit 4-Positionen
                from komplex_filter_dialog import ComplexFilterDialog
                
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
        """Erweiterte Sortierung anfordern"""
        logger.info("📊 Erweiterte Sortierung angefordert")
        
        try:
            from advanced_sort_dialog import AdvancedSortDialog
            from pdvm_central_systemsteuerung import (
                get_gcs, 
                TABLE_INDEX_SORT, 
                EXPERT_MODE_OFFSET
            )
            
            gcs = get_gcs()
            expert_mode = gcs.expert_mode if gcs else False
            
            # Berechne Array-Index: 3 (Standard) oder 8 (Expert = 3 + 5)
            table_index = TABLE_INDEX_SORT + (EXPERT_MODE_OFFSET if expert_mode else 0)
            
            # Hole Sort-Projektion (bereits gefiltert: NUR sortierbare Spalten!)
            projection = gcs.get_projection_table(self.controller.view_guid, table_index)
            
            logger.info(f"  📋 Sort-Projektion Index {table_index}: {len(projection) if projection else 0} Spalten")
            
            dialog = AdvancedSortDialog(
                controls_config=self.current_controls,
                view_guid=self.controller.view_guid,
                projection=projection,  # Bereits NUR sortierbare Spalten - KEINE Filterung mehr nötig!
                parent=self
            )
            
            if dialog.exec_():
                sort_config = dialog.get_sort_config()
                self.sort_requested.emit(sort_config)
                
        except Exception as e:
            logger.error(f"❌ Sortier-Dialog Fehler: {e}")
            QMessageBox.warning(self, "Fehler", f"Sortier-Dialog konnte nicht geöffnet werden:\n{e}")
    
    def _reset_sort(self):
        """Sortierung zurücksetzen"""
        logger.info("🔄 Sortierung zurücksetzen")
        
        # State zurücksetzen
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        
        # An Controller senden (None = keine Sortierung)
        if hasattr(self.controller, 'reset_sort'):
            self.controller.reset_sort()
    
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
            
            from column_management_dialog import show_column_management_dialog
            
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
