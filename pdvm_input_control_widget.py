# pdvm_input_control_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QDateTimeEdit, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_datetime import Pdvm_DateTime, getFormTimeStamp
import logging

logger = logging.getLogger(__name__)

class PdvmInputControlWidget(QWidget):
    """
    UI-Widget für die Anzeige und Bearbeitung eines Input-Controls.
    
    Dieses Widget ist rein für die UI-Darstellung zuständig:
    - Zeigt Label, Wert und Buttons an
    - Delegiert alle Datenoperationen an den InputManager über das ControlObject
    - Unterstützt verschiedene Feldtypen: Text, Dropdown, DateTime, ViewTable
    
    Das ControlObject enthält:
    - meta: Feld-Metadaten (Label, Typ, etc.)
    - display_value: Aktueller Anzeigewert
    - manager: Referenz zum InputManager für Datenoperationen
    - Konfiguration für UI-Layout (Breiten, etc.)
    """
    def __init__(self, control, parent=None):
        super().__init__(parent)
        self.control = control
        self.meta = control.meta
        self.display_value = control.display_value
        self.abdatum_inst = control.abdatum_inst
        self.value_inst = control.value_inst
        self.label_width = control.label_width
        self.value_width = control.value_width
        self.button_width = control.button_width
        self.help_text = getattr(control, 'help_text', '')
        self.help_header = getattr(control, 'help_header', '')
        self._build_widget()
        
        # Callback für ControlObject-Refresh registrieren
        if hasattr(self.control, 'add_refresh_callback'):
            self.control.add_refresh_callback(self.update_view)

    @property
    def manager(self):
        """Compatibility property for accessing the manager through the control object."""
        return self.control.manager

    def _build_widget(self):
        """Baut das Widget auf (Label + Wert + Buttons)."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # --- Zeile 1: Label, Wert, Buttons ---
        row_height = 25
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        # Label mit optionalem Einzug
        indent_width = getattr(self.control, 'indent', 0)
        label_text = getattr(self.meta, 'label', 'Unbekannt')
        self.lbl = QLabel(label_text, self)
        self.lbl.setFixedWidth(self.label_width)
        self.lbl.setMinimumHeight(row_height)
        if indent_width > 0:
            spacer = QSpacerItem(indent_width, 1, QSizePolicy.Fixed, QSizePolicy.Fixed)
            row1.addSpacerItem(spacer)
        row1.addWidget(self.lbl)

        # Wert - Darstellung abhängig vom Feldtyp
        self._build_value_display(row1, row_height)

        # Buttons
        self._build_buttons(row1, row_height)

        row1.addStretch(1)
        main_layout.addLayout(row1)

        # --- Zeile 2: AbDatum (optional) ---
        self._build_abdatum_display(main_layout, row_height)

    def _build_value_display(self, layout, row_height):
        """Erstellt die Wertanzeige abhängig vom Feldtyp."""
        field_type = getattr(self.meta, 'type', 'text')
        
        if field_type == 'datetime':
            # DateTime: PdvmDateTimePicker (readOnly) für korrekte Datum-Darstellung
            display_val = getattr(self.meta, 'display_val', 'all')  # Aus Framedaten
            self.val_widget = PdvmDateTimePicker(
                self, 
                self.value_inst,  # Die DateTime-Instanz
                display=display_val
            )
            self.val_widget.setFixedWidth(self.value_width)
            self.val_widget.setMinimumHeight(row_height)
            # ReadOnly-Modus aktivieren
            self.val_widget.setEnabled(False)  # Deaktiviert Bearbeitung
            print(f"[DEBUG] DateTime-Anzeige '{self.meta.key}': display_val={display_val}, value_inst={self.value_inst}", flush=True)
            
        elif field_type == 'viewtable':
            # ViewTable: GUID anzeigen (verkürzt für bessere Lesbarkeit)
            display_text = str(self.display_value)
            if len(display_text) > 36:  # Standard GUID-Länge
                display_text = f"{display_text[:8]}...{display_text[-8:]}"
            self.val_widget = QLabel(display_text, self)
            self.val_widget.setFixedWidth(self.value_width)
            self.val_widget.setMinimumHeight(row_height)
            self.val_widget.setStyleSheet("QLabel { background-color: #e8f4f8; border: 1px solid #4caf50; padding: 2px; font-family: monospace; }")
            self.val_widget.setToolTip(f"ViewTable GUID: {self.display_value}")
        else:
            # Standard-Textanzeige für alle anderen Feldtypen
            self.val_widget = QLabel(str(self.display_value), self)
            self.val_widget.setFixedWidth(self.value_width)
            self.val_widget.setMinimumHeight(row_height)
            self.val_widget.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; padding: 2px; }")
        
        layout.addWidget(self.val_widget)

    def _build_buttons(self, layout, row_height):
        """Erstellt die Aktions-Buttons."""
        # Help-Button
        btn_help = QPushButton("?", self)
        btn_help.setFixedWidth(row_height)
        btn_help.setFixedHeight(row_height)
        btn_help.setStyleSheet(
            f"QPushButton {{ background-color: #2196f3; color: white; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
        )
        btn_help.setToolTip("Hilfe anzeigen")
        btn_help.clicked.connect(self.show_help_dialog)
        layout.addWidget(btn_help)

        # Edit-Button
        btn_edit = QPushButton("✎", self)
        btn_edit.setFixedWidth(row_height)
        btn_edit.setFixedHeight(row_height)
        btn_edit.setStyleSheet(
            f"QPushButton {{ background-color: #43a047; color: white; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
        )
        btn_edit.setToolTip("Feld bearbeiten")
        btn_edit.clicked.connect(self._on_edit_dialog)
        layout.addWidget(btn_edit)

        # History-Button (nur wenn aktiviert)
        if getattr(self.control, 'show_history', False):
            btn_history = QPushButton("⏳", self)
            btn_history.setFixedWidth(row_height)
            btn_history.setFixedHeight(row_height)
            btn_history.setStyleSheet(
                f"QPushButton {{ background-color: #bdbdbd; color: #333; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
            )
            btn_history.setToolTip("Historie anzeigen")
            btn_history.clicked.connect(self._on_history_dialog)
            layout.addWidget(btn_history)

    def _build_abdatum_display(self, main_layout, row_height):
        """Erstellt die optionale AbDatum-Anzeige."""
        self.ab_val = None
        show_abdatum = getattr(self.control, 'show_abdatum', False)
        if show_abdatum and self.abdatum_inst:
            row2 = QHBoxLayout()
            row2.setSpacing(4)
            
            # Einzug wie bei der Hauptzeile
            indent_width = getattr(self.control, 'indent_ab', 0)
            placeholder = QWidget(self)
            placeholder.setFixedWidth(self.label_width + indent_width)
            placeholder.setMinimumHeight(row_height)
            row2.addWidget(placeholder)
            
            # Ab-Datum Label und Wert
            ab_lbl = QLabel("Ab-Datum:", self)
            ab_lbl.setFixedWidth(60)
            ab_lbl.setMinimumHeight(row_height)
            row2.addWidget(ab_lbl)
            
            ab_val_text = str(self.abdatum_inst.FormTimeStamp)
            self.ab_val = QLabel(ab_val_text, self)
            self.ab_val.setFixedWidth(self.value_width)
            self.ab_val.setMinimumHeight(row_height)
            self.ab_val.setStyleSheet("QLabel { background-color: #f9f9f9; border: 1px solid #ddd; padding: 2px; font-style: italic; }")
            row2.addWidget(self.ab_val)
            
            row2.addStretch(1)
            main_layout.addLayout(row2)

    def show_help_dialog(self):
        """Zeigt den Hilfe-Dialog an."""
        from PyQt5.QtWidgets import QMessageBox
        header = self.help_header or "Hilfe"
        text = self.help_text or "Keine Hilfe verfügbar."
        QMessageBox.information(self, header, text)

    def update_view(self):
        """
        Aktualisiert die Anzeige des Widgets.
        Wird vom ControlObject nach Datenänderungen aufgerufen.
        """
        if hasattr(self, 'val_widget') and self.val_widget:
            field_type = getattr(self.meta, 'type', 'text')
            
            if field_type == 'datetime':
                # Für DateTime-Felder: PdvmDateTimePicker mit neuer Instanz aktualisieren
                if hasattr(self.val_widget, 'update_with_new_instance') and self.control.value_inst:
                    self.val_widget.update_with_new_instance(self.control.value_inst)
                    print(f"[DEBUG] DateTime update_view: '{self.meta.key}' PdvmDateTimePicker mit neuer Instanz aktualisiert - neuer Wert: {self.control.value_inst.PdvmDateTime}", flush=True)
                elif hasattr(self.val_widget, 'update_display'):
                    self.val_widget.update_display()
                    print(f"[DEBUG] DateTime update_view: '{self.meta.key}' PdvmDateTimePicker mit update_display aktualisiert - neuer Wert: {self.control.value_inst.PdvmDateTime if self.control.value_inst else 'None'}", flush=True)
                else:
                    print(f"[DEBUG] DateTime update_view: '{self.meta.key}' hat keine update_display Methode", flush=True)
            elif field_type == 'viewtable':
                # Spezielle Behandlung für ViewTable (verkürzte GUID-Anzeige)
                display_value = str(self.control.display_value)
                print(f"[DEBUG] ViewTable update_view: '{self.meta.key}' - neuer display_value: '{display_value}'", flush=True)
                
                if len(display_value) > 36:
                    display_text = f"{display_value[:8]}...{display_value[-8:]}"
                    self.val_widget.setText(display_text)
                    self.val_widget.setToolTip(f"ViewTable GUID: {display_value}")
                    print(f"[DEBUG] ViewTable update_view: '{self.meta.key}' - verkürzte Anzeige: '{display_text}'", flush=True)
                else:
                    self.val_widget.setText(display_value)
                    print(f"[DEBUG] ViewTable update_view: '{self.meta.key}' - vollständige Anzeige: '{display_value}'", flush=True)
            else:
                # Standard-Text-Aktualisierung für andere Felder
                display_value = str(self.control.display_value)
                print(f"[DEBUG] Text update_view: '{self.meta.key}' - neuer display_value: '{display_value}', Widget-Text vorher: '{self.val_widget.text() if hasattr(self.val_widget, 'text') else 'N/A'}'", flush=True)
                self.val_widget.setText(display_value)
                print(f"[DEBUG] Text update_view: '{self.meta.key}' - Widget-Text nachher: '{self.val_widget.text() if hasattr(self.val_widget, 'text') else 'N/A'}'", flush=True)
        
        # AbDatum aktualisieren
        if hasattr(self, 'ab_val') and self.ab_val and self.abdatum_inst:
            self.ab_val.setText(str(self.abdatum_inst.FormTimeStamp))

    def _on_edit_dialog(self):
        """
        Öffnet den passenden Bearbeiten-Dialog für dieses Feld.
        Delegiert alle Datenoperationen an das ControlObject/InputManager.
        """
        from pdvm_input_widget import EditFieldDialog
        from PyQt5.QtWidgets import QDialog
        
        # Standard-Dialog für alle Feldtypen (inkl. ViewTable)
        dlg = EditFieldDialog(self, self.control)
        
        if dlg.exec_() == QDialog.Accepted:
            new_val, new_ab = dlg.get_results()
            print(f"[DEBUG] EditDialog OK geklickt: new_val={new_val}, new_ab={new_ab} für Feld '{self.control.key}'", flush=True)
            
            # Wert über das ControlObject/InputManager setzen
            if hasattr(self.control, 'set_value') and callable(self.control.set_value):
                self.control.set_value(new_val, new_ab)
                print(f"[DEBUG] set_value() aufgerufen für Feld '{self.control.key}'", flush=True)
                
                # WICHTIG: Erst das ControlObject refresh (ohne UI-Callbacks), dann Widget direkt aktualisieren
                if hasattr(self.control, 'refresh'):
                    # Sichere die alten Callbacks
                    old_callbacks = self.control._refresh_callbacks[:]
                    # Temporär entfernen, um gelöschte Widgets zu vermeiden
                    self.control._refresh_callbacks.clear()
                    # ControlObject-Daten aktualisieren
                    self.control.refresh()
                    # Callbacks wieder setzen (werden beim nächsten UI-Aufbau neu gesetzt)
                    self.control._refresh_callbacks = old_callbacks
                
                # Widget direkt mit den neuen Daten aktualisieren
                self.update_view()
                print(f"[DEBUG] Widget direkt aktualisiert für Feld '{self.control.key}'", flush=True)
        else:
            print(f"[DEBUG] EditDialog abgebrochen für Feld '{self.control.key}'", flush=True)

    def _on_history_dialog(self):
        """
        Öffnet den History-Dialog.
        Alle Datenzugriffe laufen über das ControlObject/InputManager.
        """
        history = []
        
        # History über den InputManager holen
        if hasattr(self.control, 'manager') and hasattr(self.control.manager, 'get_history'):
            history = self.control.manager.get_history(self.control.key)
        
        # Dialog-Parameter über das ControlObject holen (nicht über den Manager)
        if hasattr(self.control, 'value_width'):
            value_width = self.control.value_width
            button_width = self.control.button_width
            # abdatum_width ist nicht im ControlObject definiert, verwende einen Standard-Wert
            abdatum_width = 150
        else:
            value_width = 300
            abdatum_width = 150
            button_width = 30
            
        dlg = HistoryDialog(self, history, self.meta, self.control.manager if hasattr(self.control, 'manager') else None, value_width, abdatum_width, button_width)
        dlg.exec_()

    def refresh_after_viewtable_guid_change(self, new_guid):
        """
        Spezielle Methode für ViewTable-GUID-Änderungen.
        Delegiert an den InputManager zur Instanz-Aktualisierung.
        """
        if hasattr(self.control, 'manager') and hasattr(self.control.manager, 'refresh_viewtable_instance'):
            self.control.manager.refresh_viewtable_instance(self.control.key, new_guid)
            self.update_view()
        
        logger.info(f"[PdvmInputControlWidget] ViewTable-GUID geändert: {self.control.key} -> {new_guid}")


# Standard Edit-Dialog für Text/Dropdown/DateTime Felder
class EditFieldDialog(QDialog):
    def __init__(self, parent, control):
        super().__init__(parent)
        self.control = control
        self.meta = control.meta
        self.setWindowTitle(f"Bearbeiten: {getattr(self.meta, 'label', 'Feld')}")
        self.setModal(True)
        self.resize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # Feld-Info
        info_label = QLabel(f"Feldtyp: {getattr(self.meta, 'type', 'text').title()}")
        info_label.setStyleSheet("font-style: italic; color: #666;")
        layout.addWidget(info_label)
        
        # Wert-Eingabe
        self.value_edit = QLineEdit(str(control.display_value), self)
        layout.addWidget(QLabel("Wert:"))
        layout.addWidget(self.value_edit)
        
        # Buttons
        from PyQt5.QtWidgets import QHBoxLayout
        buttons = QHBoxLayout()
        btn_ok = QPushButton("OK", self)
        btn_cancel = QPushButton("Abbrechen", self)
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)
        
    def get_results(self):
        return self.value_edit.text(), None


# History-Dialog mit Tabelle
class HistoryDialog(QDialog):
    def __init__(self, parent, history, meta, manager, value_width, abdatum_width, button_width):
        super().__init__(parent)
        self.setWindowTitle(f"Historie: {getattr(meta, 'label', 'Feld')}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Header mit Feldname und Beschreibung
        header_label = QLabel(f"Historie für Feld: {getattr(meta, 'label', 'Unbekannt')}")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px; background-color: #e8f4f8; border: 1px solid #b8dce8;")
        layout.addWidget(header_label)
        
        # Info-Label mit Anzahl der Einträge
        info_label = QLabel(f"Anzahl Einträge: {len(history) if history else 0}")
        info_label.setStyleSheet("font-style: italic; padding: 5px;")
        layout.addWidget(info_label)
        
        # History-Tabelle
        if history and len(history) > 0:
            from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
            from PyQt5.QtCore import Qt
            
            table = QTableWidget(self)
            table.setRowCount(len(history))
            table.setColumnCount(3)  # Wert, Ab-Datum, Aktionen
            table.setHorizontalHeaderLabels(["Wert", "Ab-Datum", "Aktionen"])
            
            # Tabellen-Header konfigurieren
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # Wert-Spalte nimmt verfügbaren Platz
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Ab-Datum passt sich an
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Aktionen passt sich an
            
            # Daten in Tabelle füllen
            for row, h in enumerate(history):
                # Wert-Spalte
                value_text = str(h.get('value', h.get('db_value', 'N/A')))
                value_item = QTableWidgetItem(value_text)
                value_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Nicht editierbar
                table.setItem(row, 0, value_item)
                
                # Ab-Datum-Spalte
                ab_text = str(h.get('formatted_date', h.get('abdatum', 'N/A')))
                ab_item = QTableWidgetItem(ab_text)
                ab_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Nicht editierbar
                table.setItem(row, 1, ab_item)
                
                # Aktionen-Spalte mit Lösch-Button
                delete_btn = QPushButton("✕", self)
                delete_btn.setFixedSize(12, 12)  # Kleinerer runder Button
                delete_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #ff6b6b; 
                        color: white; 
                        border: none; 
                        border-radius: 6px; 
                        font-weight: bold; 
                        font-size: 9px;
                        margin: 0px;
                        padding: 0px;
                    } 
                    QPushButton:hover { 
                        background-color: #ff5252; 
                    } 
                    QPushButton:disabled { 
                        background-color: #cccccc; 
                        color: #666666; 
                    }
                """)
                
                # Container für Button mit zentrierter Positionierung
                button_container = QWidget()
                button_layout = QHBoxLayout(button_container)
                button_layout.addWidget(delete_btn)
                button_layout.setAlignment(Qt.AlignCenter)
                button_layout.setContentsMargins(0, 0, 0, 0)
                
                # Letzter Eintrag kann nicht gelöscht werden (mindestens ein Eintrag muss bleiben)
                if len(history) <= 1:
                    delete_btn.setEnabled(False)
                    delete_btn.setToolTip("Der letzte Eintrag kann nicht gelöscht werden")
                else:
                    delete_btn.setToolTip(f"Eintrag vom {ab_text} löschen")
                    # Lambda mit row und history-entry als Parameter
                    delete_btn.clicked.connect(lambda checked, r=row, entry=h: self.delete_history_entry(table, r, entry, meta, manager))
                
                table.setCellWidget(row, 2, button_container)
            
            # Tabellen-Stil
            table.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    selection-background-color: #e8f4f8;
                    selection-color: black;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                    color: black;
                }
                QTableWidget::item:selected {
                    background-color: #e8f4f8;
                    color: black;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    padding: 8px;
                    border: 1px solid #ddd;
                    font-weight: bold;
                }
            """)
            
            # Selektion konfigurieren
            table.setSelectionBehavior(QTableWidget.SelectRows)  # Ganze Zeile selektieren
            table.setSelectionMode(QTableWidget.SingleSelection)  # Nur eine Zeile zur Zeit
            
            layout.addWidget(table)
            
        else:
            # Keine Historie vorhanden
            no_history_label = QLabel("Keine Historie vorhanden.")
            no_history_label.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; padding: 20px; text-align: center; font-style: italic;")
            no_history_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_history_label)
        
        # Button-Bereich
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        btn_close = QPushButton("Schließen", self)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("QPushButton { padding: 8px 20px; }")
        button_layout.addWidget(btn_close)
        
        layout.addLayout(button_layout)
    
    def delete_history_entry(self, table, row, history_entry, meta, manager):
        """
        Löscht einen History-Eintrag nach Bestätigung durch den Benutzer.
        """
        from PyQt5.QtWidgets import QMessageBox
        
        # Bestätigung anfordern mit deutschen Buttons
        ab_text = str(history_entry.get('formatted_date', history_entry.get('abdatum', 'N/A')))
        value_text = str(history_entry.get('value', history_entry.get('db_value', 'N/A')))
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Eintrag löschen?")
        msg_box.setText("Möchten Sie den History-Eintrag wirklich löschen?")
        msg_box.setInformativeText(f"Wert: {value_text}\nAb-Datum: {ab_text}\n\nDiese Aktion kann nicht rückgängig gemacht werden.")
        msg_box.setIcon(QMessageBox.Question)
        
        # Deutsche Buttons
        ok_button = msg_box.addButton("OK", QMessageBox.AcceptRole)
        cancel_button = msg_box.addButton("Abbruch", QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == ok_button:
            # Löschung über den Manager durchführen
            if manager and hasattr(manager, 'delete_history_entry'):
                success = manager.delete_history_entry(
                    getattr(meta, 'key', ''), 
                    history_entry.get('timestamp', history_entry.get('ab_zeit', 0))
                )
                
                if success:
                    # Zeile aus Tabelle entfernen
                    table.removeRow(row)
                    
                    # WICHTIG: Refresh der InputControls nach Löschung
                    # Bei ViewTable-History-Löschung kann sich die GUID ändern -> prüfe auf ungespeicherte Änderungen
                    print(f"[DEBUG] History-Löschung erfolgreich, triggere intelligenten Refresh")
                    if manager and hasattr(manager, '_refresh_viewtable_instances'):
                        # Verwende _refresh_viewtable_instances für intelligenten Refresh mit Dirty-Check
                        manager._refresh_viewtable_instances()
                        print(f"[DEBUG] _refresh_viewtable_instances() aufgerufen - prüft auf GUID-Änderungen und ungespeicherte Daten")
                    elif manager and hasattr(manager, 'refresh_all_control_objects'):
                        manager.refresh_all_control_objects()
                        print(f"[DEBUG] refresh_all_control_objects() aufgerufen als Fallback")
                    elif manager and hasattr(manager, 'unified_refresh'):
                        manager.unified_refresh(skip_stichtag_save=True)
                        print(f"[DEBUG] unified_refresh() aufgerufen als Fallback")
                    else:
                        print(f"[WARNING] Manager hat keine Refresh-Methode verfügbar")
                    
                    # Wenn nur noch ein Eintrag übrig ist, alle Lösch-Buttons deaktivieren
                    if table.rowCount() <= 1:
                        for r in range(table.rowCount()):
                            container = table.cellWidget(r, 2)
                            if container and hasattr(container, 'layout'):
                                # Suche den Button im Container
                                layout = container.layout()
                                for i in range(layout.count()):
                                    item = layout.itemAt(i)
                                    if item and item.widget() and isinstance(item.widget(), QPushButton):
                                        btn = item.widget()
                                        btn.setEnabled(False)
                                        btn.setToolTip("Der letzte Eintrag kann nicht gelöscht werden")
                    
                    # Erfolg anzeigen und Dialog schließen
                    success_msg = QMessageBox(self)
                    success_msg.setWindowTitle("Erfolg")
                    success_msg.setText("History-Eintrag wurde erfolgreich gelöscht.")
                    success_msg.setIcon(QMessageBox.Information)
                    success_msg.addButton("OK", QMessageBox.AcceptRole)
                    success_msg.exec_()
                    
                    # History-Dialog schließen
                    self.close()
                else:
                    QMessageBox.warning(self, "Fehler", "Der History-Eintrag konnte nicht gelöscht werden.")
            else:
                QMessageBox.warning(self, "Fehler", "Lösch-Funktion nicht verfügbar.")
        
        # Aktualisiere Zeilennummerierung der verbleibenden Lösch-Buttons
        for r in range(table.rowCount()):
            container = table.cellWidget(r, 2)
            if container and hasattr(container, 'layout'):
                # Suche den Button im Container
                layout = container.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), QPushButton):
                        btn = item.widget()
                        if btn.isEnabled():
                            # Button-Click neu verbinden mit korrigierter Zeilennummer
                            try:
                                btn.clicked.disconnect()  # Alte Verbindung entfernen
                            except:
                                pass  # Ignoriere falls keine Verbindung vorhanden
