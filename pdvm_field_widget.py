# pdvm_field_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QDateTimeEdit, QSizePolicy, QSpacerItem
)
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_date_time_picker import PdvmDateTimePicker
from pd_datetime import Pdvm_DateTime

import logging
logger = logging.getLogger(__name__)

class PdvmFieldWidget(QWidget):
    def get_history(self):
        """
        Gibt die Historie für dieses Feld als Liste von Dicts mit 'db_value' und 'abdatum' zurück.
        Für Dropdowns ist 'db_value' der gespeicherte Key.
        """
        try:
            parts = self.meta.key.split('_', 2)
            if len(parts) < 3:
                return []
            grp, fld = parts[1], parts[2]
            if hasattr(self.data_inst, 'get_value_all'):
                history_dict = self.data_inst.get_value_all(grp, fld)
                # history_dict: {abdatum: wert, ...}
                return [{"db_value": v, "abdatum": ab} for ab, v in history_dict.items()]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[get_history] Fehler beim Laden der Historie: {e}")
        return []
    """
    Universelles Widget für die Anzeige und Bearbeitung eines Feldes (Text, Dropdown, Datetime, Viewtable).
    Modus: readOnly (Anzeige) oder edit (Bearbeiten).
    Dieses Element wird intern als InputControl bezeichnet.
    """
    def __init__(self, table, gruppe, feld, guid, meta=None, readOnly=True, parent=None, manager=None):
        super().__init__(parent)
        self.table = table
        self.gruppe = gruppe
        self.feld = feld
        self.guid = guid
        self.meta = meta
        self.readOnly = readOnly
        # Hilfetexte initialisieren (Default)
        self.help_header = ""
        self.help_text = ""
        # Manager explizit übergeben (robust!)
        if manager is None:
            manager = getattr(parent, 'manager', None)
        self.manager = manager
        feld_key = f"{self.table}_{self.gruppe}_{self.feld}"
        if manager and hasattr(manager, 'get_data_instance'):
            self.data_inst = manager.get_data_instance(feld_key)
            if self.data_inst is None:
                raise RuntimeError(f"[PdvmFieldWidget] Keine Dateninstanz für {feld_key} im Manager gefunden!")
        else:
            raise RuntimeError(f"[PdvmFieldWidget] Kein Manager oder keine get_data_instance-Methode für {feld_key} verfügbar!")
        logger.debug(f"[PdvmFieldWidget] Parameter {self.table}.{self.gruppe}.{self.feld} (Instanz: {self.data_inst}) erstellt")
        self._build_widget()
        # Hilfetexte nach dem Aufbau setzen
        self._setup_helptext()

    def _get_dropdown_display(self, value):
        # Vereinfachte Anzeige: Zeige Key oder Wert direkt
        return str(value)

    def _build_widget(self):
        # Entferne evtl. bestehende Layouts/Widgets
        for child in self.children():
            child.setParent(None)

        # UI-Parameter (aus Metadaten/Manager oder Fallback)
        label_width = getattr(self.meta, 'ui_width_label', None)
        if label_width is None:
            label_width = getattr(self.manager, 'width_label', 120)
        label_width = label_width or 120

        value_width = getattr(self.meta, 'ui_width_value', None)
        if value_width is None:
            value_width = getattr(self.manager, 'width_control', 250)
        value_width = value_width or 250

        button_width = getattr(self.meta, 'ui_width_button', None)
        if button_width is None:
            button_width = getattr(self.manager, 'width_button', 60)
        button_width = button_width or 60

        indent_ab = getattr(self.meta, 'ui_indent_ab', None)
        if indent_ab is None:
            indent_ab = getattr(self.manager, 'width_indent_ab', 100)
        indent_ab = indent_ab or 100

        frame_width = getattr(self.manager, 'width_frame', 600) or 600

        # Label-Widget zuerst erzeugen, damit fontMetrics verfügbar ist
        lbl = QLabel(self.meta.label, self)
        font_metrics = lbl.fontMetrics()
        row_height = font_metrics.height() + 6 if font_metrics else 28

        # Hauptlayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4,0,0,0)
        # Hilfetexte werden nach dem Aufbau gesetzt (im Konstruktor)

        # --- Zeile 1: Label, Value, Buttons ---
        row_widget = QWidget(self)
        row_widget.setFixedWidth(frame_width)
        row = QHBoxLayout(row_widget)
        row.setSpacing(4)
        row.setContentsMargins(0,2,0,0)
        lbl.setParent(row_widget)
        lbl.setFixedWidth(label_width)
        lbl.setMinimumHeight(row_height)
        row.addWidget(lbl)

        # Value-Widget: Immer aus der Instanz lesen, Instanzen nur über Manager!
        manager = getattr(self.parent(), 'manager', None)
        feld_key = f"{self.table}_{self.gruppe}_{self.feld}"
        # Datenwert holen
        try:
            value_dict = self.data_inst.get_value(self.gruppe, self.feld)
            value = value_dict.get("wert", "")
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Werts aus der Instanz für {self.table}_{self.gruppe}_{self.feld}: {e}")
            value = ""
        self.val_widget = None
        self.value_inst = None  # Für datetime
        field_type = getattr(self.meta, 'type', 'text')
        # --- AbDatum-Instanz: immer EINE pro IC, zentral im Manager ---
        abdatum_val = 1001.0
        try:
            abdatum_val = self.data_inst.get_value(self.gruppe, 'abdatum').get('wert', 1001.0)
        except Exception:
            pass
        if manager:
            ab_inst = manager.get_abdatum_instance(feld_key)
            if ab_inst is None:
                ab_inst = Pdvm_DateTime("DEU")
                ab_inst.PdvmDateTime = float(abdatum_val)
                manager.register_abdatum_instance(feld_key, ab_inst)
            self.abdatum_inst = ab_inst
        else:
            self.abdatum_inst = Pdvm_DateTime("DEU")
            self.abdatum_inst.PdvmDateTime = float(abdatum_val)

        if field_type == "text":
            self.val_widget = QLineEdit(str(value), self)
            self.val_widget.setReadOnly(self.readOnly)
            if self.readOnly:
                self.val_widget.setStyleSheet("background-color: #fafafa; color:black;")
        elif field_type == "dropdown":
            key = value.get("wert", value) if isinstance(value, dict) else value
            display_val = key
            if manager and hasattr(manager, 'translate_dropdown_value'):
                display_val = manager.translate_dropdown_value(self.meta, key, lang="de")
            self.val_widget = QLineEdit(str(display_val), self)
            self.val_widget.setReadOnly(self.readOnly)
            if self.readOnly:
                self.val_widget.setStyleSheet("background-color: #fafafa; color:black;")
        elif field_type == "datetime":
            # Value-Instanz zentral im Manager
            if manager:
                value_inst = manager.get_value_instance(feld_key)
                if value_inst is None:
                    value_inst = Pdvm_DateTime("DEU")
                    value_inst.PdvmDateTime = float(value or 1001.0)
                    manager.register_value_instance(feld_key, value_inst)
                self.value_inst = value_inst
            else:
                self.value_inst = Pdvm_DateTime("DEU")
                self.value_inst.PdvmDateTime = float(value or 1001.0)
            display_val = getattr(self.meta, 'display_val', None) or 'all'
            self.val_widget = PdvmDateTimePicker(self, self.value_inst,
                display=display_val,
                display_time_short=getattr(self.meta, 'display_ti_val_short', False))
            self.val_widget.setReadOnly(self.readOnly)
            self.val_widget.setMinimumWidth(200)
            self.val_widget.update_display()
        elif field_type == "viewtable":
            if self.readOnly:
                current_guid = value if value else "(keine Auswahl)"
                self.val_widget = QLineEdit(str(current_guid), self)
                self.val_widget.setReadOnly(True)
                self.val_widget.setStyleSheet("background-color: #fafafa; color:black;")
            else:
                self.val_widget = QLabel(str(value), self)
        if self.val_widget:
            self.val_widget.setFixedWidth(value_width)
            self.val_widget.setMinimumHeight(row_height)
            row.addWidget(self.val_widget)

        # Buttons
        btn_help = QPushButton("?", self)
        btn_help.setFixedWidth(row_height)
        btn_help.setFixedHeight(row_height)
        btn_help.setStyleSheet(
            f"QPushButton {{ background-color: #1976d2; color: white; font-weight: bold; border-radius: {row_height//2}px; font-size: 16px; }}"
        )
        btn_help.setToolTip("Hilfe anzeigen")
        btn_help.clicked.connect(self.show_help_dialog)

        btn_edit = QPushButton("Bearbeiten", self)
        btn_edit.setFixedWidth(button_width)
        btn_edit.setFixedHeight(row_height)

        btn_hist = QPushButton("Historie", self)
        btn_hist.setFixedWidth(button_width)
        btn_hist.setFixedHeight(row_height)
        show_history = getattr(self.meta, "has_abdatum", False)
        if not show_history:
            btn_hist.setEnabled(False)
            btn_hist.setStyleSheet("background-color: transparent; color: transparent; border: none; opacity: 0;")
        else:
            btn_hist.clicked.connect(self.show_history_dialog)
        for btn in [btn_help, btn_edit, btn_hist]:
            row.addWidget(btn)

        # --- Ausgleichs-Spacer am rechten Rand ---
        total_used = label_width + value_width + button_width*2 + row_height + 20 # 20px für Spacing
        spacer_width = max(0, frame_width - total_used)
        if spacer_width > 0:
            spacer = QWidget(row_widget)
            spacer.setFixedWidth(spacer_width)
            spacer.setFixedHeight(row_height)
            row.addWidget(spacer)
        main_layout.addWidget(row_widget)

        # --- Zeile 2: AbDatum ---
        self.ab_val = None  # Referenz für spätere Updates
        if getattr(self.meta, "has_abdatum", False):
            ab_row_widget = QWidget(self)
            ab_row = QHBoxLayout(ab_row_widget)
            ab_row.setContentsMargins(0,0,0,0)
            indent_widget = QWidget(ab_row_widget)
            indent_widget.setFixedWidth(indent_ab)
            ab_row.addWidget(indent_widget)
            ab_lbl = QLabel("Ab-Datum:", ab_row_widget)
            ab_row.addWidget(ab_lbl)
            self.ab_val = QLabel(str(self.abdatum_inst.FormTimeStamp), ab_row_widget)
            ab_row.addWidget(self.ab_val)
            ab_row.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            ab_row_widget.setFixedHeight(row_height)
            main_layout.addWidget(ab_row_widget)

        # --- Editier-Logik für alle Typen ---
        btn_edit.clicked.connect(self._on_edit_dialog)

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
        Nach Änderung der Viewtable-GUID: Instanz für neue GUID holen (wie bisher) und alle abhängigen ICs refreshen.
        """
        table = getattr(self.meta, 'viewtable_table', None) or getattr(self.meta, 'table', None)
        if not table:
            return
        # Instanz holen (wie bisher, ggf. aus Cache)
        new_inst = self.manager.get_or_load_instance(table, new_guid)
        # Alle ICs, die auf diese Instanz zeigen, gezielt aktualisieren
        if hasattr(self.manager, 'refresh_all_ics_for_instance'):
            self.manager.refresh_all_ics_for_instance(new_inst)

    def _setup_dropdown(self):
        """Dropdown-Optionen und Texte immer aktuell über Manager holen."""
        self.dropdown_options = self.manager.get_dropdown_options(self.meta)
        self.dropdown_keys = [o.get("key") for o in self.dropdown_options]
        self.dropdown_texts = [self.manager.translate_dropdown_value(self.meta, o.get("key"), lang=self.manager.language) for o in self.dropdown_options]

    def _setup_helptext(self):
        """Hilfetext und Header immer aktuell über Manager holen und an UI-Komponenten weitergeben."""
        self.help_text = self.manager.get_help_text(self.meta, lang=getattr(self.manager, 'language', None))
        self.help_header = self.manager.get_help_header(self.meta, lang=getattr(self.manager, 'language', None))
        # Falls ein Hilfe-Button oder Tooltip existiert, setze den Text explizit
        if hasattr(self, 'help_button') and self.help_button:
            self.help_button.setToolTip(self.help_text)
        if hasattr(self, 'help_label') and self.help_label:
            self.help_label.setText(self.help_header)
        # Optional: Tooltip für das ganze Widget setzen
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
        class HistoryDialog(QDialog):
            def __init__(self, parent, history, meta, manager):
                super().__init__(parent)
                self.setWindowTitle("Historie für " + meta.label)
                self.setMinimumWidth(520)
                self.history = sorted(history, key=lambda row: row.get("abdatum", 0))
                self.meta = meta
                self.manager = manager
                self.deleted_indices = set()
                layout = QVBoxLayout(self)
                # Tabelle für die History
                self.table = QTableWidget(len(self.history), 3, self)
                self.table.setHorizontalHeaderLabels(["Ab-Datum", "Wert", ""])
                self.table.verticalHeader().setVisible(False)
                self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                self.table.setSelectionMode(QAbstractItemView.NoSelection)
                self.table.setShowGrid(True)
                self.table.setStyleSheet("QTableWidget { font-size: 13px; } QHeaderView::section { font-weight: bold; }")
                for idx, row in enumerate(self.history):
                    ab_inst = Pdvm_DateTime("DEU")
                    ab_inst.PdvmDateTime = float(row.get("abdatum", 1001.0))
                    ab_label = QTableWidgetItem(str(ab_inst.FormTimeStamp))
                    ab_label.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 0, ab_label)
                    if meta.type == "dropdown":
                        show_value = manager.translate_dropdown_value(meta, row["db_value"], lang=manager.language)
                    else:
                        show_value = str(row.get("db_value", ""))
                    value_item = QTableWidgetItem(show_value)
                    value_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, 1, value_item)
                    btn_del = QPushButton("✕")
                    btn_del.setFixedSize(28, 28)
                    btn_del.setStyleSheet("QPushButton { color: red; font-weight: bold; border: 1px solid #d0d0d0; border-radius: 6px; background: #f8f8f8; } QPushButton:disabled { opacity: 0.3; }")
                    if idx == len(self.history) - 1:
                        btn_del.setEnabled(False)
                        btn_del.setToolTip("Letzter Satz kann nicht gelöscht werden")
                    else:
                        btn_del.setToolTip("Satz löschen")
                        def make_delete(idx):
                            return lambda: self.delete_row(idx)
                        btn_del.clicked.connect(make_delete(idx))
                    self.table.setCellWidget(idx, 2, btn_del)
                self.table.resizeColumnsToContents()
                self.table.horizontalHeader().setStretchLastSection(True)
                layout.addWidget(self.table)
                btn_close = QPushButton("Schließen", self)
                btn_close.clicked.connect(self.accept)
                layout.addWidget(btn_close)

            def delete_row(self, idx):
                if idx == len(self.history) - 1:
                    QMessageBox.warning(self, "Nicht erlaubt", "Der letzte Satz kann nicht gelöscht werden.")
                    return
                # TODO: Löschlogik in Dateninstanz implementieren
                self.deleted_indices.add(idx)
                self.rows[idx][0].hide()
                self.rows[idx][1].setEnabled(False)

        history = self.get_history()
        dlg = HistoryDialog(self, history, self.meta, self.manager)
        dlg.exec_()

    def get_main_control(self):
        """
        Gibt das Haupt-Eingabefeld-Widget (QLineEdit, DropdownPicker etc.) zurück.
        """
        return getattr(self, 'main_ctl', None)

    def _update_abdatum_display(self):
        if self.ab_val and self.abdatum_inst and hasattr(self.abdatum_inst, 'FormTimeStamp'):
            self.ab_val.setText(str(self.abdatum_inst.FormTimeStamp))

    def _on_edit_dialog(self):
        # Öffnet den Bearbeiten-Dialog für dieses Feld
        # Wert für Dialog initialisieren
        if self.meta.type == "datetime":
            dlg_value = None
        elif self.meta.type == "dropdown":
            # Key aus Instanz extrahieren
            try:
                table, grp, fld = self.meta.key.split("_", 2)
                val_dict = self.data_inst.get_value(grp, fld)
                dlg_value = val_dict.get("wert", "") if isinstance(val_dict, dict) else val_dict
            except Exception:
                dlg_value = ""
        else:
            dlg_value = self.val_widget.text() if hasattr(self.val_widget, 'text') else ''

        dlg = EditFieldDialog(
            self,
            self.meta,
            dlg_value,
            self.abdatum_inst.PdvmDateTime if self.abdatum_inst else 1001.0,
            self.manager,
            abdatum_inst=self.abdatum_inst,
            value_inst=self.value_inst if self.meta.type == "datetime" else None
        )

        if dlg.exec_() == QDialog.Accepted:
            # Save beim DateTimePicker, damit Wert übernommen wird
            if self.meta.type == "datetime" and hasattr(dlg.value_ctl, 'save'):
                dlg.value_ctl.save()
            if getattr(dlg, 'abdatum_ctl', None) and hasattr(dlg.abdatum_ctl, 'save'):
                dlg.abdatum_ctl.save()
            new_val, new_ab = dlg.get_results()
            table, grp, fld = self.meta.key.split("_", 2)
            import logging
            logging.debug(f"[IC] data_inst vor Dialog: {id(self.data_inst)} Wert: {self.data_inst.get_value(grp, fld)}")
            if self.meta.type == "datetime" and self.value_inst:
                new_val = self.value_inst.PdvmDateTime
            self.data_inst.set_value(grp, fld, new_val, new_ab)
            logging.debug(f"[IC] data_inst nach Dialog: {id(self.data_inst)} Wert: {self.data_inst.get_value(grp, fld)}")
            # Halte die interne Instanz synchron
            if self.abdatum_inst:
                self.abdatum_inst.PdvmDateTime = new_ab
            # Anzeige gezielt aktualisieren
            # Für alle Typen: Anzeige nach Änderung aus Instanz aktualisieren
            if self.meta.type in ("text", "viewtable") and hasattr(self.val_widget, 'setText'):
                aktueller_wert = self.data_inst.get_value(grp, fld)
                anzeige_wert = aktueller_wert.get("wert", "") if isinstance(aktueller_wert, dict) else (aktueller_wert or "")
                self.val_widget.setText(str(anzeige_wert))
            if self.meta.type == "dropdown" and hasattr(self.val_widget, 'setText'):
                aktueller_wert = self.data_inst.get_value(grp, fld)
                key = aktueller_wert.get("wert", "") if isinstance(aktueller_wert, dict) else (aktueller_wert or "")
                display_val = self._get_dropdown_display(key)
                self.val_widget.setText(str(display_val))
            if self.meta.type == "datetime" and hasattr(self.val_widget, 'refresh_from_instance'):
                self.val_widget.refresh_from_instance()
            self._update_abdatum_display()
        # Kein kompletter Neuaufbau, kein Parent-Refresh

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
    def __init__(self, parent, meta, value, abdatum, manager, abdatum_inst=None, value_inst=None):
        super().__init__(parent)
        self.setWindowTitle(f"{meta.label} bearbeiten")
        self.meta = meta
        self.manager = manager
        self.value = value
        self.abdatum = abdatum
        self.value_inst = value_inst
        # Immer zentrale Instanz aus Manager verwenden
        feld_key = f"{getattr(meta, 'table', 'TBL')}_{getattr(meta, 'gruppe', 'GRP')}_{getattr(meta, 'feld', 'FELD')}"
        if abdatum_inst is not None:
            self.abdatum_inst = abdatum_inst
        elif hasattr(manager, 'get_abdatum_instance'):
            ab_inst = manager.get_abdatum_instance(feld_key)
            if ab_inst is None:
                logger.error(f"[EditFieldDialog] Keine Abdatum-Instanz für {feld_key} im Manager! (Feld: {meta.label})")
                raise RuntimeError(f"Abdatum-Instanz für {feld_key} fehlt! (Feld: {meta.label})")
            self.abdatum_inst = ab_inst
        else:
            logger.error(f"[EditFieldDialog] Kein Manager für Abdatum-Instanz verfügbar! (Feld: {meta.label})")
            raise RuntimeError(f"Kein Manager für Abdatum-Instanz verfügbar! (Feld: {meta.label})")
        self.result_value = value
        self.result_abdatum = abdatum
        layout = QVBoxLayout(self)
        # --- Zeile 1: Wert ---
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(meta.label+":"))
        if meta.type == "text":
            self.value_ctl = QLineEdit(str(value), self)
            row1.addWidget(self.value_ctl)
        elif meta.type == "dropdown":
            # Wert ggf. aus Dict extrahieren
            key_value = value.get("wert", value) if isinstance(value, dict) else value
            self.value_ctl = QComboBox(self)
            opts = manager.get_dropdown_options(meta)
            for o in opts:
                text = manager.translate_dropdown_value(meta, o.get("key"), lang=manager.language)
                self.value_ctl.addItem(text, o.get("key"))
            idx = self.value_ctl.findData(key_value)
            if idx >= 0:
                self.value_ctl.setCurrentIndex(idx)
            row1.addWidget(self.value_ctl)
        elif meta.type == "datetime":
            from pdvm_date_time_picker import PdvmDateTimePicker
            # display_val-Logik: IC > Default 'all'
            display_val = getattr(meta, 'display_val', None) or 'all'
            # Wichtig: value_inst verwenden, damit dieselbe Instanz wie im Widget genutzt wird
            if value_inst is not None:
                self.value_inst = value_inst
            else:
                # Pdvm_DateTime ist global importiert
                self.value_inst = Pdvm_DateTime("DEU")
                self.value_inst.PdvmDateTime = float(value or 1001.0)
            self.value_ctl = PdvmDateTimePicker(self, self.value_inst, display=display_val, display_time_short=meta.display_ti_val_short)
            self.value_ctl.setMinimumWidth(200)
            row1.addWidget(self.value_ctl)
        elif meta.type == "viewtable":
            # Zeile 1: Button
            btn_row = QHBoxLayout()
            from PyQt5.QtWidgets import QSizePolicy
            btn_select = QPushButton("Objekt auswählen ...", self)
            btn_select.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_select.setToolTip("Objekt suchen und auswählen")
            import logging, json
            def select_object():
                # View-GUID direkt aus FieldMeta-Attribut
                view_guid = getattr(meta, 'viewtable_guid', None)
                logging.debug(f"[EditFieldDialog] meta.viewtable_guid: {repr(view_guid)}")
                if not view_guid:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Fehler", f"Kein View-GUID für die Objektsuche definiert.\nmeta: {repr(meta)}")
                    return
                user_guid = getattr(manager, 'user_guid', None)
                frame_guid = getattr(manager, 'frame_guid', None)
                call_data = getattr(manager, 'call_data', None)
                from pdvm_search_list_widget_dialog import PdvmSearchListWidgetDialog
                dlg = PdvmSearchListWidgetDialog(self, view_guid, user_guid=user_guid, frame_guid=frame_guid, call_data=call_data)
                if dlg.exec_() == QDialog.Accepted:
                    guid = dlg.get_selected_guid()
                    if guid:
                        self.value_ctl.setText(str(guid))
            btn_select.clicked.connect(select_object)
            btn_row.addWidget(btn_select)
            layout.addLayout(btn_row)
            # Zeile 2: Feld
            row1 = QHBoxLayout()
            self.value_ctl = QLineEdit(str(value), self)
            self.value_ctl.setReadOnly(True)
            row1.addWidget(self.value_ctl)
        else:
            self.value_ctl = QLineEdit(str(value), self)
            row1.addWidget(self.value_ctl)
        layout.addLayout(row1)
        # --- Zeile 2: Ab-Datum (falls vorhanden) ---
        if getattr(meta, "has_abdatum", False):
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("Ab-Datum:"))
            from pdvm_date_time_picker import PdvmDateTimePicker
            display_ab = meta.display_ab if getattr(meta, 'display_ab', None) else getattr(manager, 'display_ab', 'all')
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
        if self.meta.type == "datetime" and hasattr(self.value_ctl, 'save'):
            self.value_ctl.save()
        if self.meta.type == "text":
            new_val = self.value_ctl.text()
        elif self.meta.type == "dropdown":
            new_val = self.value_ctl.currentData()
        elif self.meta.type == "datetime":
            # Wert direkt aus value_inst lesen, damit Instanz synchron bleibt
            new_val = self.value_inst.PdvmDateTime
        elif self.meta.type == "viewtable":
            new_val = self.value_ctl.text()
        else:
            new_val = self.value_ctl.text()
        # AbDatum immer aus der Instanz lesen
        new_ab = self.abdatum_inst.PdvmDateTime
        return new_val, new_ab

    def _on_edit_dialog(self):
        # Öffnet den Bearbeiten-Dialog für dieses Feld
        dlg = EditFieldDialog(self, self.meta, self.val_widget.text() if hasattr(self.val_widget, 'text') else '',
                              self.abdatum_inst.PdvmDateTime if self.abdatum_inst else 1001.0,
                              self.manager, abdatum_inst=self.abdatum_inst)
        if dlg.exec_() == QDialog.Accepted:
            # Save beim DateTimePicker, damit Wert übernommen wird
            if getattr(dlg, 'abdatum_ctl', None) and hasattr(dlg.abdatum_ctl, 'save'):
                dlg.abdatum_ctl.save()
            new_val, new_ab = dlg.get_results()
            table, grp, fld = self.meta.key.split("_", 2)
            self.data_inst.set_value(grp, fld, new_val, new_ab)
            # Halte die interne Instanz synchron
            if self.abdatum_inst:
                self.abdatum_inst.PdvmDateTime = new_ab
            # Anzeige gezielt aktualisieren
            if self.meta.type == "text" and hasattr(self.val_widget, 'setText'):
                aktueller_wert = self.data_inst.get_value(grp, fld)
                anzeige_wert = aktueller_wert.get("wert", "") if isinstance(aktueller_wert, dict) else (aktueller_wert or "")
                self.val_widget.setText(str(anzeige_wert))
            self._update_abdatum_display()
            # Kein kompletter Neuaufbau, kein Parent-Refresh
