# pdvm_field_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QDateTimeEdit, QSizePolicy, QSpacerItem
)
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_datetime import Pdvm_DateTime, getFormTimeStamp
import logging

logger = logging.getLogger(__name__)

class PdvmFieldWidget(QWidget):
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
        if hasattr(self.control, 'add_refresh_callback'):
            self.control.add_refresh_callback(self.update_view)

    def _build_widget(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        row_height = 25
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        label_text = getattr(self.meta, 'label', 'Unbekannt')
        self.lbl = QLabel(label_text, self)
        self.lbl.setFixedWidth(self.label_width)
        self.lbl.setMinimumHeight(row_height)
        row1.addWidget(self.lbl)
        self.val_widget = QLabel(str(self.display_value), self)
        self.val_widget.setFixedWidth(self.value_width)
        self.val_widget.setMinimumHeight(row_height)
        self.val_widget.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; padding: 2px; }")
        row1.addWidget(self.val_widget)
        btn_help = QPushButton("?", self)
        btn_help.setFixedWidth(row_height)
        btn_help.setFixedHeight(row_height)
        btn_help.clicked.connect(self.show_help_dialog)
        row1.addWidget(btn_help)
        btn_edit = QPushButton("?", self)
        btn_edit.setFixedWidth(row_height)
        btn_edit.setFixedHeight(row_height)
        btn_edit.clicked.connect(self._on_edit_dialog)
        row1.addWidget(btn_edit)
        if getattr(self.control, 'show_history', False):
            btn_history = QPushButton("?", self)
            btn_history.setFixedWidth(row_height)
            btn_history.setFixedHeight(row_height)
            btn_history.clicked.connect(self._on_history_dialog)
            row1.addWidget(btn_history)
        row1.addStretch(1)
        main_layout.addLayout(row1)

    def show_help_dialog(self):
        from PyQt5.QtWidgets import QMessageBox
        header = self.help_header or "Hilfe"
        text = self.help_text or "Keine Hilfe verfügbar."
        QMessageBox.information(self, header, text)

    def update_view(self):
        if hasattr(self, 'val_widget') and self.val_widget:
            self.val_widget.setText(str(self.control.display_value))

    def _on_edit_dialog(self):
        if hasattr(self.control, 'meta') and getattr(self.control.meta, 'type', None) == 'viewtable':
            from pdvm_input_widget import EditViewTableDialog
            dlg = EditViewTableDialog(self, self.control)
        else:
            dlg = EditFieldDialog(self, self.control)
        if dlg.exec_() == QDialog.Accepted:
            new_val, new_ab = dlg.get_results()
            if hasattr(self.control, 'set_value') and callable(self.control.set_value):
                self.control.set_value(new_val, new_ab)
                if hasattr(self.control, 'manager') and hasattr(self.control.manager, 'unified_refresh'):
                    self.control.manager.unified_refresh(skip_stichtag_save=True)

    def _on_history_dialog(self):
        history = []
        if hasattr(self.control, 'manager') and hasattr(self.control.manager, 'get_history'):
            history = self.control.manager.get_history(self.control.key)
        dlg = HistoryDialog(self, history, self.meta, None, 300, 150, 30)
        dlg.exec_()

class EditFieldDialog(QDialog):
    def __init__(self, parent, control):
        super().__init__(parent)
        self.control = control
        self.meta = control.meta
        self.setWindowTitle(f"Bearbeiten: {getattr(self.meta, 'label', 'Feld')}")
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.value_edit = QLineEdit(str(control.display_value), self)
        layout.addWidget(QLabel("Wert:"))
        layout.addWidget(self.value_edit)
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

class HistoryDialog(QDialog):
    def __init__(self, parent, history, meta, manager, value_width, abdatum_width, button_width):
        super().__init__(parent)
        self.setWindowTitle(f"Historie: {getattr(meta, 'label', 'Feld')}")
        self.setModal(True)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Historie für Feld: {getattr(meta, 'label', 'Unbekannt')}"))
        history_text = "\n".join([f"Wert: {h.get('db_value', 'N/A')}, Ab: {h.get('abdatum', 'N/A')}" for h in history])
        history_label = QLabel(history_text if history_text else "Keine Historie vorhanden.")
        layout.addWidget(history_label)
        btn_close = QPushButton("Schließen", self)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
