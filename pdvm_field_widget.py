# pdvm_field_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QDateTimeEdit, QSizePolicy, QSpacerItem
)
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_date_time_picker import PdvmDateTimePicker
from pd_datetime import Pdvm_DateTime, getFormTimeStamp

import logging
logger = logging.getLogger(__name__)

class PdvmFieldWidget(QWidget):
    # update_display_from_instance und refresh_from_instance entfernt – Widget ist rein display-orientiert
    def get_history(self):
        """
        Gibt die Historie für dieses Feld als Liste von Dicts mit 'db_value' und 'abdatum' zurück.
        Holt die Daten ausschließlich über das ControlObject (delegiert an Manager).
        """
        if hasattr(self.control, 'get_history') and callable(self.control.get_history):
            return self.control.get_history()
        return []
    """
    Universelles Widget für die Anzeige und Bearbeitung eines Feldes (Text, Dropdown, Datetime, Viewtable).
    Modus: readOnly (Anzeige) oder edit (Bearbeiten).
    Dieses Element wird intern als InputControl bezeichnet.
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
        self.indent_ab = control.indent_ab
        self.frame_width = control.frame_width
        self.help_text = control.help_text
        self.help_header = control.help_header
        self._build_widget()
        self._setup_helptext()
        # Callback für ControlObject-Refresh registrieren
        if hasattr(self.control, 'add_refresh_callback'):
            self.control.add_refresh_callback(self.update_view)

    def update_view(self):
        """
        Aktualisiert die Anzeige des Widgets nach einem Refresh im ControlObject.
        """
        # Werte aus ControlObject neu übernehmen
        self.display_value = self.control.display_value
        self.abdatum_inst = self.control.abdatum_inst
        self.value_inst = self.control.value_inst
        self.label_width = self.control.label_width
        self.value_width = self.control.value_width
        self.button_width = self.control.button_width
        self.indent_ab = self.control.indent_ab
        self.frame_width = self.control.frame_width
        self.help_text = self.control.help_text
        self.help_header = self.control.help_header
        # UI neu aufbauen
        self._build_widget()
        self._setup_helptext()

    def _get_dropdown_display(self, value):
        # Vereinfachte Anzeige: Zeige Key oder Wert direkt
        return str(value)

    def _build_widget(self):
        # Entferne evtl. bestehende Layouts/Widgets
        if self.layout() is not None:
            old_layout = self.layout()
            QWidget().setLayout(old_layout)
        for child in self.children():
            child.setParent(None)

        lbl = QLabel(self.meta.label, self)
        font_metrics = lbl.fontMetrics()
        row_height = font_metrics.height() + 6 if font_metrics else 28

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4,0,0,0)
        main_layout.setSpacing(2)

        # --- Zeile 1: Label, Value, Buttons ---
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        lbl.setFixedWidth(self.label_width)
        lbl.setMinimumHeight(row_height)
        row1.addWidget(lbl)

#        if hasattr(self.control, 'value_widget_factory') and callable(self.control.value_widget_factory):
#            self.val_widget = self.control.value_widget_factory(self)
#        elif hasattr(self.control, 'widget_type') and self.control.widget_type == 'datetime':
#            self.val_widget = PdvmDateTimePicker(self, self.value_inst,
#                display=getattr(self.meta, 'display_val', None) or 'all',
#                display_time_short=getattr(self.meta, 'display_ti_val_short', False))
#            self.val_widget.setReadOnly(True)
#            self.val_widget.setMinimumWidth(200)
#            self.val_widget.update_display()
#        else:
        self.val_widget = QLineEdit(str(self.display_value), self)
        self.val_widget.setReadOnly(True)
        self.val_widget.setStyleSheet("background-color: #fafafa; color:black;")
        self.val_widget.setFixedWidth(self.value_width)
        self.val_widget.setMinimumHeight(row_height)
        row1.addWidget(self.val_widget)

        btn_help = QPushButton("?", self)
        btn_help.setFixedWidth(row_height)
        btn_help.setFixedHeight(row_height)
        btn_help.setStyleSheet(
            f"QPushButton {{ background-color: #1976d2; color: white; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
        )
        btn_help.setToolTip("Hilfe anzeigen")
        btn_help.clicked.connect(self.show_help_dialog)
        row1.addWidget(btn_help)

        btn_edit = QPushButton("✎", self)
        btn_edit.setFixedWidth(row_height)
        btn_edit.setFixedHeight(row_height)
        btn_edit.setStyleSheet(
            f"QPushButton {{ background-color: #43a047; color: white; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
        )
        btn_edit.setToolTip("Feld bearbeiten")
        btn_edit.clicked.connect(self._on_edit_dialog)
        row1.addWidget(btn_edit)

        # Historie-Button
        # History-Button nur anzeigen, wenn show_history im ControlObject gesetzt ist
        if getattr(self.control, 'show_history', False):
            btn_history = QPushButton("⏳", self)
            btn_history.setFixedWidth(row_height)
            btn_history.setFixedHeight(row_height)
            btn_history.setStyleSheet(
                f"QPushButton {{ background-color: #bdbdbd; color: #333; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
            )
            btn_history.setToolTip("Historie anzeigen")
            def show_history():
                self._on_history_dialog()
            btn_history.clicked.connect(show_history)
            row1.addWidget(btn_history)

        row1.addStretch(1)

        main_layout.addLayout(row1)

        # --- Zeile 2: AbDatum (optional, exakt ausgerichtet) ---
        self.ab_val = None
        show_abdatum = getattr(self.control, 'show_abdatum', False)
        if show_abdatum and self.abdatum_inst:
            row2 = QHBoxLayout()
            row2.setSpacing(4)
            indent_width = getattr(self.control, 'indent_ab') or 0
            placeholder = QWidget(self)
            placeholder.setFixedWidth(self.label_width + indent_width)
            placeholder.setMinimumHeight(row_height)
            row2.addWidget(placeholder)
            ab_lbl = QLabel("Ab-Datum:", self)
            ab_lbl.setFixedWidth(60)
            ab_lbl.setMinimumHeight(row_height)
            row2.addWidget(ab_lbl)
            ab_val_text = str(self.abdatum_inst.FormTimeStamp)
            self.ab_val = QLabel(ab_val_text, self)
            self.ab_val.setFixedWidth(self.value_width)
            self.ab_val.setMinimumHeight(row_height)
            row2.addWidget(self.ab_val)
            row2.addStretch(1)
            main_layout.addLayout(row2)

        # Hilfetext als Tooltip setzen (Platzhalter)
        help_text = getattr(self.meta, 'tooltip', '')
        self.setToolTip(help_text)

    def show_help_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Hilfe: {self.meta.label}")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        header = QLabel(f"<b>{self.help_header}</b>")
        header.setWordWrap(True)
        layout.addWidget(header)
        text = QLabel(self.help_text)
        text.setWordWrap(True)
        layout.addWidget(text)
        btn_close = QPushButton("Schließen", dlg)
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)
        dlg.exec_()

    def refresh_after_viewtable_guid_change(self, new_guid):
        """
        Nach Änderung der Viewtable-GUID: Instanz für neue GUID holen, GUID anzeigen und Debug-Log.
        """
        table = getattr(self.meta, 'viewtable_table', None) or getattr(self.meta, 'table', None)
        if not table:
            return
        # Neue Instanz laden
        new_inst = self.manager.get_or_load_instance(table, new_guid)
        # Anzeige im IC aus der neuen Instanz aktualisieren
        self.update_display_from_instance()
        import logging
        logging.info(f"[PdvmFieldWidget] Neue viewtable-GUID übernommen: {new_guid}, Instanz-ID: {id(new_inst)}")

    def _setup_dropdown(self):
        """Dropdown-Optionen und Texte immer aktuell über Manager holen."""
        self.dropdown_options = self.manager.get_dropdown_options(self.meta)
        self.dropdown_keys = [o.get("key") for o in self.dropdown_options]
        self.dropdown_texts = [self.manager.translate_dropdown_value(self.meta, o.get("key"), lang=self.manager.language) for o in self.dropdown_options]

    def _setup_helptext(self):
        # Hilfetext und Header direkt aus ControlObject übernehmen
        # Falls ein Hilfe-Button oder Tooltip existiert, setze den Text explizit
        if hasattr(self, 'help_button') and self.help_button:
            self.help_button.setToolTip(self.help_text)
        if hasattr(self, 'help_label') and self.help_label:
            self.help_label.setText(self.help_header)
        self.setToolTip(self.help_text)

    def _update_dropdown(self):
        """Dropdown-Optionen neu laden (z.B. nach Änderung)."""
        self._setup_dropdown()
        # ...bestehende Logik zur Aktualisierung der UI...

    def _update_helptext(self):
        self._setup_helptext()
        # ...bestehende Logik zur Aktualisierung der UI...

    def __init_ui__(self):
        # ...existing code...
        self._setup_dropdown()
        self._setup_helptext()
        # ...existing code...

    def show_history_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QSizePolicy, QAbstractItemView
        from PyQt5.QtCore import Qt
        value_width = getattr(self.meta, 'ui_width_value', None)
        if value_width is None:
            value_width = getattr(self.manager, 'width_control', 250)
        value_width = value_width or 250
        abdatum_width = 160  # Mehr Platz für Datum+Uhrzeit
        button_width = 32
        button_size = 24  # Button kleiner als Spalte, damit Rundungen sichtbar
        class HistoryDialog(QDialog):
            def __init__(self, parent, history, meta, manager, value_width, abdatum_width, button_width):
                super().__init__(parent)
                self.setWindowTitle(f"Historie für {meta.label}")
                self.setMinimumWidth(abdatum_width + value_width + button_width + 60)
                self.meta = meta
                self.manager = manager
                self.value_width = value_width
                self.abdatum_width = abdatum_width
                self.button_width = button_width
                layout = QVBoxLayout(self)
                self.table = QTableWidget(self)
                layout.addWidget(self.table)
                self._refresh_table()
                btn_close = QPushButton("Schließen", self)
                btn_close.clicked.connect(self.accept)
                layout.addWidget(btn_close)

            def _refresh_table(self):
                # History aus Dateninstanz neu laden
                feld_key = getattr(self.meta, 'key', None)
                data_inst = None
                if feld_key and hasattr(self.manager, 'get_data_instance'):
                    data_inst = self.manager.get_data_instance(feld_key)
                if data_inst and hasattr(data_inst, 'get_value_all'):
                    parts = feld_key.split('_', 2)
                    if len(parts) == 3:
                        _, grp, fld = parts
                        history_dict = data_inst.get_value_all(grp, fld)
                        self.history = sorted([
                            {"db_value": v, "abdatum": ab} for ab, v in history_dict.items()
                        ], key=lambda row: row.get("abdatum", 0))
                else:
                    self.history = []
                self.table.clear()
                self.table.setRowCount(len(self.history))
                self.table.setColumnCount(3)
                self.table.setHorizontalHeaderLabels(["Ab-Datum", "Wert", ""])
                self.table.verticalHeader().setVisible(False)
                self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                self.table.setSelectionMode(QAbstractItemView.NoSelection)
                self.table.setShowGrid(True)
                self.table.setStyleSheet("QTableWidget { font-size: 13px; } QHeaderView::section { font-weight: bold; }")
                deletable = len(self.history) > 1
                button_size = 24
                for idx, row in enumerate(self.history):
                    ab_val = float(row.get("abdatum", 1001.0))
                    ab_label = QTableWidgetItem(getFormTimeStamp(ab_val, 'DEU'))
                    ab_label.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 0, ab_label)
                    # Dropdown-Übersetzung
                    raw_value = row.get("db_value", "")
                    if getattr(self.meta, 'type', None) == 'dropdown' and hasattr(self.manager, 'translate_dropdown_value'):
                        show_value = self.manager.translate_dropdown_value(self.meta, raw_value, lang=getattr(self.manager, 'language', None))
                    else:
                        show_value = str(raw_value)
                    value_item = QTableWidgetItem(show_value)
                    value_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 1, value_item)
                    btn_del = QPushButton("✕")
                    btn_del.setFixedSize(button_size, button_size)
                    btn_del.setStyleSheet("QPushButton { color: red; font-weight: bold; border: 1px solid #d0d0d0; border-radius: 8px; background: #f8f8f8; } QPushButton:disabled { opacity: 0.3; }")
                    btn_del.setCursor(Qt.PointingHandCursor)
                    from PyQt5.QtWidgets import QWidget, QHBoxLayout
                    cell_widget = QWidget()
                    cell_layout = QHBoxLayout(cell_widget)
                    cell_layout.setContentsMargins(0,0,0,0)
                    cell_layout.setAlignment(Qt.AlignCenter)
                    if deletable:
                        cell_layout.addWidget(btn_del)
                        def make_delete(idx):
                            return lambda: self.delete_row(idx)
                        btn_del.clicked.connect(make_delete(idx))
                        btn_del.setToolTip("Satz löschen")
                    else:
                        btn_del.setEnabled(False)
                        btn_del.setToolTip("Mindestens ein Satz muss erhalten bleiben.")
                        cell_layout.addWidget(btn_del)
                    self.table.setCellWidget(idx, 2, cell_widget)
                self.table.setColumnWidth(0, self.abdatum_width)
                self.table.setColumnWidth(1, self.value_width)
                self.table.setColumnWidth(2, self.button_width)
                self.table.horizontalHeader().setStretchLastSection(False)

            def delete_row(self, idx):
                if len(self.history) <= 1:
                    QMessageBox.warning(self, "Nicht erlaubt", "Mindestens ein Satz muss erhalten bleiben.")
                    return
                abdatum = self.history[idx].get("abdatum")
                db_value = self.history[idx].get("db_value")
                feld_key = getattr(self.meta, 'key', None)
                data_inst = None
                if feld_key and hasattr(self.manager, 'get_data_instance'):
                    data_inst = self.manager.get_data_instance(feld_key)
                if data_inst and hasattr(data_inst, 'delete_value'):
                    try:
                        parts = feld_key.split('_', 2)
                        if len(parts) == 3:
                            _, gruppe, feld = parts
                            data_inst.delete_value(gruppe, feld, abdatum)
                    except Exception as e:
                        QMessageBox.warning(self, "Fehler", f"Fehler beim Löschen: {e}")
                        return
                else:
                    QMessageBox.warning(self, "Fehler", "Dateninstanz oder delete_value-Methode nicht gefunden!")
                    return
                # Nach erfolgreichem Löschen: Tabelle und History neu aufbauen
                self._refresh_table()

        history = self.get_history()
        dlg = HistoryDialog(self, history, self.meta, self.manager, value_width, abdatum_width, button_width)
        dlg.exec_()
        # Nach Schließen des History-Dialogs: keine eigene Datenaktualisierung mehr nötig

    def get_main_control(self):
        """
        Gibt das Haupt-Eingabefeld-Widget (QLineEdit, DropdownPicker etc.) zurück.
        """
        return getattr(self, 'main_ctl', None)

    def _update_abdatum_display(self):
        if self.ab_val and self.abdatum_inst and hasattr(self.abdatum_inst, 'FormTimeStamp'):
            self.ab_val.setText(str(self.abdatum_inst.FormTimeStamp))

    def _on_edit_dialog(self):
        # Öffnet den Bearbeiten-Dialog für dieses Feld – alle Werte kommen aus dem ControlObject
        dlg = EditFieldDialog(self, self.control)
        if dlg.exec_() == QDialog.Accepted:
            # Save beim DateTimePicker, damit Wert übernommen wird
            if hasattr(dlg, 'abdatum_ctl') and hasattr(dlg.abdatum_ctl, 'save'):
                dlg.abdatum_ctl.save()
            # Ergebnis an ControlObject weitergeben (Widget selbst speichert nichts mehr)
            new_val, new_ab = dlg.get_results()
            if hasattr(self.control, 'set_value') and callable(self.control.set_value):
                self.control.set_value(new_val, new_ab)
            # Optional: Widget-Update/Callback
            if hasattr(self.parent(), 'on_field_edited'):
                self.parent().on_field_edited(self.meta, new_val, new_ab)

    def _on_history_dialog(self):
        # Öffnet den History-Dialog, alle Datenzugriffe laufen über das ControlObject
        history = []
        if hasattr(self.control, 'get_history') and callable(self.control.get_history):
            history = self.control.get_history()
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QSizePolicy, QAbstractItemView
        from PyQt5.QtCore import Qt
        value_width = self.value_width or 250
        abdatum_width = 160
        button_width = 32
        button_size = 24
        class HistoryDialog(QDialog):
            def __init__(self, parent, history, control, value_width, abdatum_width, button_width):
                super().__init__(parent)
                self.setWindowTitle(f"Historie für {control.meta.label}")
                self.setMinimumWidth(abdatum_width + value_width + button_width + 60)
                self.control = control
                self.value_width = value_width
                self.abdatum_width = abdatum_width
                self.button_width = button_width
                layout = QVBoxLayout(self)
                if not history:
                    layout.addWidget(QLabel("Keine Historie vorhanden."))
                else:
                    self.table = QTableWidget(self)
                    layout.addWidget(self.table)
                    self.history = history
                    self._refresh_table()
                btn_close = QPushButton("Schließen", self)
                btn_close.clicked.connect(self.accept)
                layout.addWidget(btn_close)

            def _refresh_table(self):
                self.table.clear()
                self.table.setRowCount(len(self.history))
                self.table.setColumnCount(3)
                self.table.setHorizontalHeaderLabels(["Ab-Datum", "Wert", ""])
                self.table.verticalHeader().setVisible(False)
                self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                self.table.setSelectionMode(QAbstractItemView.NoSelection)
                self.table.setShowGrid(True)
                self.table.setStyleSheet("QTableWidget { font-size: 13px; } QHeaderView::section { font-weight: bold; }")
                deletable = len(self.history) > 1
                button_size = 24
                for idx, row in enumerate(self.history):
                    ab_val = float(row.get("abdatum", 1001.0))
                    ab_label = QTableWidgetItem(getFormTimeStamp(ab_val, 'DEU'))
                    ab_label.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 0, ab_label)
                    # Dropdown-Übersetzung
                    raw_value = row.get("db_value", "")
                    if getattr(self.control.meta, 'type', None) == 'dropdown' and hasattr(self.control.manager, 'translate_dropdown_value'):
                        show_value = self.control.manager.translate_dropdown_value(self.control.meta, raw_value, lang=getattr(self.control.manager, 'language', None))
                    else:
                        show_value = str(raw_value)
                    value_item = QTableWidgetItem(show_value)
                    value_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 1, value_item)
                    btn_del = QPushButton("✕")
                    btn_del.setFixedSize(button_size, button_size)
                    btn_del.setStyleSheet("QPushButton { color: red; font-weight: bold; border: 1px solid #d0d0d0; border-radius: 8px; background: #f8f8f8; } QPushButton:disabled { opacity: 0.3; }")
                    btn_del.setCursor(Qt.PointingHandCursor)
                    from PyQt5.QtWidgets import QWidget, QHBoxLayout
                    cell_widget = QWidget()
                    cell_layout = QHBoxLayout(cell_widget)
                    cell_layout.setContentsMargins(0,0,0,0)
                    cell_layout.setAlignment(Qt.AlignCenter)
                    if deletable:
                        cell_layout.addWidget(btn_del)
                        def make_delete(idx):
                            return lambda: self.delete_row(idx)
                        btn_del.clicked.connect(make_delete(idx))
                        btn_del.setToolTip("Satz löschen")
                    else:
                        btn_del.setEnabled(False)
                        btn_del.setToolTip("Mindestens ein Satz muss erhalten bleiben.")
                        cell_layout.addWidget(btn_del)
                    self.table.setCellWidget(idx, 2, cell_widget)
                self.table.setColumnWidth(0, self.abdatum_width)
                self.table.setColumnWidth(1, self.value_width)
                self.table.setColumnWidth(2, self.button_width)
                self.table.horizontalHeader().setStretchLastSection(False)

            def delete_row(self, idx):
                if len(self.history) <= 1:
                    QMessageBox.warning(self, "Nicht erlaubt", "Mindestens ein Satz muss erhalten bleiben.")
                    return
                abdatum = self.history[idx].get("abdatum")
                # Delegiere das Löschen an das ControlObject
                ok = False
                if hasattr(self.control, 'delete_history_entry') and callable(self.control.delete_history_entry):
                    ok = self.control.delete_history_entry(abdatum)
                if ok:
                    self.accept()  # Fenster schließen
                else:
                    QMessageBox.warning(self, "Fehler", "Konnte Eintrag nicht löschen!")

        dlg = HistoryDialog(self, history, self.control, value_width, abdatum_width, button_width)
        dlg.exec_()

    def _delete_layout(self, layout):
        # Hilfsfunktion zum rekursiven Löschen von Layouts
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                child_layout = item.layout()
                if child_layout is not None:
                    self._delete_layout(child_layout)
            QWidget().setLayout(layout)
            del layout

class EditFieldDialog(QDialog):
    def __init__(self, parent, control):
        super().__init__(parent)
        self.control = control
        self.meta = control.meta
        self.value = control.display_value
        self.abdatum_inst = control.abdatum_inst
        self.value_inst = control.value_inst
        self.setWindowTitle(f"{self.meta.label} bearbeiten")
        layout = QVBoxLayout(self)
        # --- Zeile 1: Wert ---
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(self.meta.label+":"))
        if hasattr(control, 'edit_widget_factory') and callable(control.edit_widget_factory):
            self.value_ctl = control.edit_widget_factory(self)
        elif hasattr(control, 'widget_type') and control.widget_type == 'datetime':
            self.value_ctl = PdvmDateTimePicker(self, self.value_inst,
                display=getattr(self.meta, 'display_val', None) or 'all',
                display_time_short=getattr(self.meta, 'display_ti_val_short', False))
            self.value_ctl.setMinimumWidth(200)
        else:
            self.value_ctl = QLineEdit(str(self.value), self)
        row1.addWidget(self.value_ctl)
        layout.addLayout(row1)
        # --- Zeile 2: Ab-Datum (optional über ControlObject) ---
        if getattr(control, 'show_abdatum', False) and self.abdatum_inst:
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("Ab-Datum:"))
            from pdvm_date_time_picker import PdvmDateTimePicker
            display_ab = getattr(self.meta, 'display_ab', 'all')
            self.abdatum_ctl = PdvmDateTimePicker(self, self.abdatum_inst, display=display_ab)
            self.abdatum_ctl.setMinimumWidth(200)
            row2.addWidget(self.abdatum_ctl)
            layout.addLayout(row2)
        else:
            self.abdatum_ctl = None
        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("OK", self)
        btn_cancel = QPushButton("Abbrechen", self)
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)
    def get_results(self):
        # Vor dem Auslesen sicherstellen, dass der Wert gespeichert ist (wichtig für datetime)
        # Ergebnisermittlung für Edit-Dialog: alles display-orientiert, keine eigene Typ-Logik mehr
        if hasattr(self.value_ctl, 'save'):
            self.value_ctl.save()
        if hasattr(self.value_ctl, 'currentData'):
            new_val = self.value_ctl.currentData()
        elif hasattr(self.value_ctl, 'text'):
            new_val = self.value_ctl.text()
        else:
            new_val = getattr(self.value_ctl, 'value', None)
        # AbDatum immer aus der Instanz lesen
        new_ab = self.abdatum_inst.PdvmDateTime if hasattr(self.abdatum_inst, 'PdvmDateTime') else None
        return new_val, new_ab

    def _on_edit_dialog(self):
        # Öffnet den Bearbeiten-Dialog für dieses Feld
        dlg = EditFieldDialog(self, self.meta, self.val_widget.text() if hasattr(self.val_widget, 'text') else '',
                              self.abdatum_inst.PdvmDateTime if self.abdatum_inst else 1001.0,
                              self.manager, abdatum_inst=self.abdatum_inst)
        if dlg.exec_() == QDialog.Accepted:
            # Save beim DateTimePicker, damit Wert übernommen wird
            if hasattr(dlg, 'abdatum_ctl') and hasattr(dlg.abdatum_ctl, 'save'):
                dlg.abdatum_ctl.save()
            # Ergebnis an Manager/Parent weitergeben (Widget selbst speichert nichts mehr)
            new_val, new_ab = dlg.get_results()
            if hasattr(self.parent(), 'on_field_edited'):
                self.parent().on_field_edited(self.meta, new_val, new_ab)
