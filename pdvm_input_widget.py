# pdvm_input_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QMessageBox, QSizePolicy, QSpacerItem, QDialog,
    QDialogButtonBox, QFormLayout, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from pdvm_input_manager import PdvmInputManager, FieldMeta
from pd_datetime import Pdvm_DateTime
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_object_search_widget import PdvmObjectSearchWidget
from pdvm_search_list_widget  import PdvmSearchListWidget
from pdvm_field_widget import PdvmFieldWidget

import logging
import uuid
logger = logging.getLogger(__name__)
logger.info("🔹 PdvmInputWidget gestartet")

TEMPLATE_GUID = "11111111-1111-1111-1111-111111111111"  # Dummy-GUID für Template


class PdvmInputWidget(QWidget):
    selectionChanged = pyqtSignal()

    def __init__(self, call_data: dict, parent=None, manager=None):
        super().__init__(parent)
        # Manager explizit übernehmen, sonst wie bisher erzeugen
        if manager is not None:
            self.manager = manager
        else:
            self.manager = PdvmInputManager(call_data)
        logger.debug(f"🔹 PdvmInputWidget - PdvmInputManager gestartet mit call_data: {call_data}")
        self.st_inst = call_data['stichtag_inst']
        # Keine feste frame_width mehr, alles dynamisch
        self.width_ts_picker_only = 120  # Fallback-Wert, kann angepasst werden
        self.width_ts_picker_full = 200  # Fallback-Wert, kann angepasst werden

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        self.controls = {}
        main = QVBoxLayout(self)
        main.setContentsMargins(20,20,20,20)
        main.setSpacing(10)

        # Header
        header = QLabel(self.manager.header_text)
        header.setStyleSheet("font-size:18px; font-weight:bold;")
        main.addWidget(header, alignment=Qt.AlignLeft)

        # Stichtag + Buttons
        st_layout = QHBoxLayout()
        st_layout.addWidget(QLabel("Stichtag:"), alignment=Qt.AlignLeft)
        self.st_picker = PdvmDateTimePicker(
            self, self.st_inst,
            display=self.manager.display_st,
            default_date=None
        )
        w = self.width_ts_picker_full if self.manager.display_st=="all" else self.width_ts_picker_only
        self.st_picker.setFixedWidth(w)
        st_layout.addWidget(self.st_picker)
        btn_ref = QPushButton("Refresh")
        btn_ref.setFixedWidth(100)
        btn_ref.clicked.connect(self._on_refresh)
        st_layout.addWidget(btn_ref)
        btn_save = QPushButton("Speichern")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self._on_save)
        st_layout.addWidget(btn_save)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.close)
        st_layout.addWidget(btn_cancel)
        st_layout.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main.addLayout(st_layout)

        # Verwendeter Stichtag
        ts_layout = QHBoxLayout()
        lbl_ts = QLabel("Verwendeter Stichtag:")
        lbl_ts.setFixedWidth(self.manager.width_label or 150)
        ts_layout.addWidget(lbl_ts)
        self.ts_display = QLineEdit()
        self.ts_display.setEnabled(False)
        self.ts_display.setFixedWidth(125)
        ts_layout.addWidget(self.ts_display)
        ts_layout.addStretch()
        main.addLayout(ts_layout)

        # Scroll Area für Felder
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.container = QWidget()
        self.form_layout = QVBoxLayout(self.container)
        self.form_layout.setContentsMargins(5,5,5,5)
        self.form_layout.setSpacing(15)
        self.form_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.container)
        main.addWidget(self.scroll, stretch=1)

        # Layout leeren, damit keine alten Widgets übrig bleiben
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Debug: Welche Felder werden angezeigt?
        print(f"[DEBUG] Felder im InputFrame: {[meta.key for meta in self.manager.get_fields()]}", flush=True)

        # Eingabefelder
        for meta in self.manager.get_fields():
            table, grp, fld = self.manager._normalize_key(meta.key)
            # GUID für das Feld bestimmen (klassisch: aus Manager oder Root)
            guid = getattr(self.manager, 'get_guid_for_field', lambda t, g: self.manager.root_guid)(table, grp)
            field_widget = PdvmFieldWidget(
                table, grp, fld, guid, meta=meta,
                readOnly=getattr(self, 'readOnly', True),
                parent=self,
                manager=self.manager
            )
            self.form_layout.addWidget(field_widget)
            self.controls[meta.key] = {
                "meta": meta,
                "main_ctl": field_widget,
                "field_widget": field_widget,
                "table": table,
                "gruppe": grp,
                "feld": fld,
                "guid": guid
            }

        main.addStretch()
        # Entferne das doppelte self.setLayout(main)!
        # self.setLayout(main)  # ENTFERNT!

    def _load_values(self):
        self.ts_display.setText(self.st_inst.FormTimeStamp)
        self.st_picker.pdvm_datetime.PdvmDateTime = self.st_inst.PdvmDateTime
        self.st_picker.initial.PdvmDateTime = self.st_inst.PdvmDateTime  # Synchronisiere initial mit Instanz
        print(f"[DEBUG] _load_values: st_inst.PdvmDateTime={self.st_inst.PdvmDateTime}, st_picker.pdvm_datetime={self.st_picker.pdvm_datetime.PdvmDateTime}, st_picker.initial={self.st_picker.initial.PdvmDateTime}")
        self.st_picker.update_display()
        for key, entry in self.controls.items():
            meta = entry["meta"]
            ctl = entry["main_ctl"]
            val, ab = self.manager.get_value(key)
            # Für datetime: Wert aus Datenstruktur in value_inst und Widget schreiben
            if meta.type == "datetime":
                if "value_inst" in entry:
                    entry["value_inst"].PdvmDateTime = float(val or 1001.0)
                if hasattr(ctl, "pdvm_datetime"):
                    ctl.pdvm_datetime.PdvmDateTime = float(val or 1001.0)
                    ctl.initial.PdvmDateTime = float(val or 1001.0)  # Synchronisiere initial mit Instanz
                    print(f"[DEBUG] _load_values: key={key}, val={val}, ctl.pdvm_datetime={ctl.pdvm_datetime.PdvmDateTime}, ctl.initial={ctl.initial.PdvmDateTime}")
                    ctl.update_display()
            elif isinstance(ctl, PdvmDropdownPicker):
                ctl.refresh_options(self.st_inst.PdvmDateTime)
                ctl.set_selected_key(val)
            elif meta.type == "dropdown" and isinstance(ctl, QLineEdit):
                # Zeige immer die Übersetzung, nicht den Key
                display_val = entry["field_widget"]._get_dropdown_display(val)
                ctl.setText(display_val)
            elif isinstance(ctl, QLineEdit):
                ctl.setText(str(val))
            # Für abdatum: Wert der bestehenden Instanz setzen
            if "ab_ctl" in entry and "ab_inst" in entry:
                try:
                    entry["ab_inst"].PdvmDateTime = float(ab)
                    entry["ab_ctl"].setText(entry["ab_inst"].FormTimeStamp)
                except:
                    entry["ab_ctl"].setText("")

    def _on_refresh(self):
        self.st_picker.save()
        self.st_inst.PdvmDateTime = self.st_picker.get_pdvm_datetime().PdvmDateTime
        for entry in self.controls.values():
            ctl = entry['main_ctl']
            if isinstance(ctl, PdvmDropdownPicker):
                ctl.refresh_options(self.st_inst.PdvmDateTime)
        self._load_values()

    def _on_new_guid(self, key):
        # Neue GUID generieren, Daten kopieren, GUID ersetzen, Instanzen und UI aktualisieren
        new_guid = str(uuid.uuid4())
        # Hole aktuelle Daten (Template)
        template_data, ab = self.manager.get_value(key)
        # Kopiere Datenstruktur (hier ggf. anpassen, falls tiefer kopiert werden muss)
        import copy
        new_data = copy.deepcopy(template_data)
        # Setze neue GUID
        self.manager.set_value(key, new_guid, ab)
        self.manager.refresh_instances()
        self._build_ui()
        self._load_values()

    def _on_save(self):
        # Optional: Original-Instanz-Vergleich für Konfliktprüfung
        original_instances = getattr(self.manager, 'original_instances', None)
        if original_instances:
            for key, inst in self.manager.instance_dict.items():
                orig = original_instances.get(key)
                if orig and inst.data != orig.data:
                    QMessageBox.warning(self, "Konflikt", f"Instanz {key} wurde zwischenzeitlich geändert!")
                    return
        # Validierung: Keine Speicherung unter Template-GUID
        for key, entry in self.controls.items():
            meta = entry["meta"]
            val, _ = self.manager.get_value(key)
            if meta.type == "viewtable" and str(val) == TEMPLATE_GUID:
                QMessageBox.warning(self, "Fehler", f"Feld '{meta.label}' ist noch ein Template (000...-GUID). Bitte zuerst 'Neu' klicken.")
                return
        self.manager.save_all()
        QMessageBox.information(self, "Erfolg", "Daten erfolgreich gespeichert.")

    def show_history(self, key):
        """Öffnet den HistoryDialog für das Feld key und übergibt das passende FieldWidget für Dropdown-Übersetzung."""
        entry = self.controls.get(key)
        if not entry:
            return
        meta = entry["meta"]
        field_widget = entry["field_widget"]
        # Hole alle historischen Werte (Liste von Tupeln (val, ab))
        if hasattr(self.manager, 'get_history_values'):
            values = self.manager.get_history_values(key)
        else:
            # Fallback: Hole alle Werte aus der Instanz
            grp, fld = meta.key.split('_', 2)[1:]
            values = []
            if hasattr(entry["data_inst"], 'get_value_all'):
                history_dict = entry["data_inst"].get_value_all(grp, fld)
                values = [(v, ab) for ab, v in history_dict.items()]
        dlg = HistoryDialog(self, "Historie", meta, values, field_widget=field_widget)
        dlg.exec_()

    # History, edit and help dialogs unchanged
    def _on_edit(self, key: str):
        meta = self.controls[key]['meta']
        val, ab = self.manager.get_value(key)
        dlg = EditFieldDialog(
            self, meta, val, ab,
            value_inst=self.controls[key].get('value_inst'),
            ab_inst=self.controls[key].get('ab_inst')
        )
        if dlg.exec_() == QDialog.Accepted:
            new_val, new_ab = dlg.get_results()
            ab_to_use = self.manager.get_abdatum_for_field(key, new_ab)
            # Debug: IDs und Werte der Instanzen vor dem Setzen
            if meta.type == "datetime" and "value_inst" in self.controls[key]:
                print(f"[DEBUG] Vor Bearbeiten: value_inst id={id(self.controls[key]['value_inst'])} Wert={self.controls[key]['value_inst'].PdvmDateTime}")
                print(f"[DEBUG] Vor Bearbeiten: Picker id={id(dlg.value_ctl.pdvm_datetime)} Wert={dlg.value_ctl.pdvm_datetime.PdvmDateTime}")
            # Für datetime: Wert aus Picker explizit in value_inst schreiben
            if meta.type == "datetime" and "value_inst" in self.controls[key]:
                self.controls[key]["value_inst"].PdvmDateTime = dlg.value_ctl.get_pdvm_datetime().PdvmDateTime
                new_val = self.controls[key]["value_inst"].PdvmDateTime
                print(f"[DEBUG] Nach Bearbeiten: value_inst id={id(self.controls[key]['value_inst'])} Wert={self.controls[key]['value_inst'].PdvmDateTime}")
            if meta.has_abdatum and "ab_inst" in self.controls[key]:
                ab_to_use = self.controls[key]["ab_inst"].PdvmDateTime
            self.manager.set_value(key, new_val, ab_to_use)
            # Robustes Instanz-Update für viewtable (korrekte Tabelle/Gruppe aus Verweis holen)
            if meta.type == "viewtable":
                # Ziel-Tabelle und -Gruppe aus dem Verweis holen (z.B. meta.viewtable['table'], meta.viewtable['group'])
                viewtable = getattr(meta, 'viewtable', None)
                if viewtable and isinstance(viewtable, dict):
                    table = viewtable.get('table')
                    group = viewtable.get('group')
                else:
                    # Fallback: wie bisher aus Key ableiten
                    table, group, _ = self.manager._normalize_key_from_view(key)
                print(f"[DEBUG] reload_instance_guid: table={table}, group={group}, new_guid={new_val}")
                self.manager.reload_instance_guid(table, group, new_val)
            # Debug: Nach set_value
            if meta.type == "datetime" and "value_inst" in self.controls[key]:
                print(f"[DEBUG] Nach set_value: value_inst id={id(self.controls[key]['value_inst'])} Wert={self.controls[key]['value_inst'].PdvmDateTime}")
            self._load_values()
            print(f"[DEBUG] Nach _load_values: main_ctl={self.controls[key]['main_ctl'].text() if hasattr(self.controls[key]['main_ctl'], 'text') else self.controls[key]['main_ctl']}")

    def __init_ui__(self):
        # ...existing code...
        self._setup_dropdown()
        self._setup_helptext()
        # ...existing code...

    def _setup_dropdown(self):
        """Dropdown-Optionen direkt über Manager holen."""
        if self.meta.type == "dropdown":
            self.dropdown_options = self.manager.get_dropdown_options(self.meta)
            self.dropdown_keys = [o.get("key") for o in self.dropdown_options]
            self.dropdown_texts = [self.manager.translate_dropdown_value(self.meta, o.get("key")) for o in self.dropdown_options]
        else:
            self.dropdown_options = []
            self.dropdown_keys = []
            self.dropdown_texts = []

    def _setup_helptext(self):
        """Hilfetext direkt über Manager holen."""
        self.help_text = self.manager.get_help_text(self.meta)

    def _update_dropdown(self):
        """Dropdown-Optionen neu laden (z.B. nach Änderung)."""
        self._setup_dropdown()
        # ...bestehende Logik zur Aktualisierung der UI...

    def _update_helptext(self):
        self._setup_helptext()
        # ...bestehende Logik zur Aktualisierung der UI...

class EditFieldDialog(QDialog):
    def __init__(self, parent, meta: FieldMeta,
                 current_value, current_ab,
                 value_inst=None, ab_inst=None):
        super().__init__(parent)
        self.meta       = meta
        self.current_ab = current_ab
        self.value_inst = value_inst  # Instanz aus Mapping!
        self.ab_inst    = ab_inst     # Instanz aus Mapping!
        self.manager    = parent.manager
        self.setWindowTitle(f"{meta.label} bearbeiten")
        self.setModal(True)
        form = QFormLayout(self)

        # — Wert-Widget —
        self.value_ctl = PdvmFieldWidget(self, meta, current_value, readOnly=False, manager=self.manager)
        form.addRow(meta.label + ":", self.value_ctl)

        # — Ab-Datum-Widget nur wenn abdatum:true —
        if meta.has_abdatum:
            ab_inst = self.ab_inst
            self.ab_picker = PdvmDateTimePicker(self, ab_inst)
            self.ab_picker.update_display()
            form.addRow("Ab-Datum:", self.ab_picker)
        else:
            self.ab_picker = None

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        form.addRow(btn_box)

    def get_results(self):
        # Wert extrahieren
        new_val = self.value_ctl.get_value()
        if self.value_inst:
            self.value_inst.Value = new_val
        # Ab-Datum
        if self.meta.has_abdatum and self.ab_picker:
            self.ab_picker.save()
            new_ab = self.ab_picker.get_pdvm_datetime().PdvmDateTime
            if self.ab_inst:
                self.ab_inst.PdvmDateTime = new_ab
        else:
            new_ab = self.current_ab or 1001.0
        logger.debug(f"[EditFieldDialog.get_results] Rückgabe: new_val={new_val} (type={type(new_val)}), new_ab={new_ab}")
        return new_val, new_ab

class HistoryDialog(QDialog):
    def __init__(self, parent, titel: str, meta: FieldMeta, values: list, field_widget=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.meta = meta
        self.key  = meta.key
        self.values = values  # Liste von (wert, ab)
        self.field_widget = field_widget  # Zentrale Referenz für Dropdown-Übersetzung

        if not values:
            QMessageBox.information(self, "Keine Historie", "Keine historischen Daten vorhanden.")
            self.reject()
            return

        self.setWindowTitle(f"{titel}: {meta.label}")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(QLabel("<b>Gültig-ab-Datum/Zeit</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Wert</b>"), 0, 1)
        grid.addWidget(QWidget(), 0, 2)

        # wenn es mehr als einen Eintrag gibt, darf jeder gelöscht werden
        deletable = len(values) > 1

        for row, (val, ab) in enumerate(values, start=1):
            dt = Pdvm_DateTime("DEU")
            dt.PdvmDateTime = float(ab)
            lbl_ab = QLabel(dt.FormTimeStamp)
            grid.addWidget(lbl_ab, row, 0)

            lbl_val = QLabel(self._format_value(val))
            grid.addWidget(lbl_val, row, 1)

            if deletable:
                btn_del = QPushButton("✕")
                btn_del.setFixedWidth(24)
                btn_del.setStyleSheet("color:red; font-weight:bold;")
                btn_del.clicked.connect(lambda _, a=ab: self._on_delete_entry(a))
                grid.addWidget(btn_del, row, 2)

        layout.addLayout(grid)

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def _format_value(self, val):
        # Dropdown-Übersetzung immer über FieldWidget, falls vorhanden
        if self.meta.type == "datetime":
            try:
                dt = Pdvm_DateTime("DEU")
                dt.PdvmDateTime = float(val)
                return dt.FormTimeStamp
            except:
                return str(val)
        if self.meta.type == "dropdown":
            if self.field_widget and hasattr(self.field_widget, '_get_dropdown_display'):
                return self.field_widget._get_dropdown_display(val)
            # Fallback: wie bisher
            key = str(val)
            for entry in self.meta.dropdown_options or []:
                if entry.get("key") == key:
                    return entry.get(self.parent_widget.manager.language) or key
            return key
        return str(val)

    def _on_delete_entry(self, ab: float):
        # Sicherheitsabfrage
        dt = Pdvm_DateTime("DEU")
        dt.PdvmDateTime = float(ab)
        stamp = dt.FormTimeStamp
        reply = QMessageBox.question(
            self,
            "Eintrag löschen?",
            f"Eintrag ab {stamp} wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Löschen im Manager
        self.parent_widget.manager.delete_value(self.key, ab)
        # Dialog schließen und UI neu laden
        self.accept()
        self.parent_widget._load_values()

class EditViewTableDialog(QDialog):
    def __init__(self, parent, meta: FieldMeta, current_value, current_ab, value_inst=None, ab_inst=None):
        super().__init__(parent)
        self.meta = meta
        self.current_ab = current_ab
        self.value_inst = value_inst
        self.ab_inst = ab_inst
        self.manager = parent.manager
        self.setWindowTitle(f"{meta.label} bearbeiten")
        self.setModal(True)
        form = QFormLayout(self)

        # — Viewtable-Auswahl —
        from pdvm_search_list_widget_dialog import PdvmSearchListWidgetDialog
        self.guid = current_value
        self.viewtable_guid = meta.viewtable_guid
        self.select_dialog = PdvmSearchListWidgetDialog(self, self.viewtable_guid)
        # Setze die aktuelle GUID als vorausgewählt, falls vorhanden
        if self.guid:
            try:
                self.select_dialog.widget.set_selected_guid(self.guid)
            except AttributeError:
                pass  # Falls das Widget diese Methode nicht hat, ignorieren
        form.addRow("Auswahl:", self.select_dialog.widget)

        # — Ab-Datum —
        if meta.historical and meta.has_abdatum:
            if self.ab_inst:
                abi = self.ab_inst
                abi.PdvmDateTime = float(current_ab or self.manager.stichtag)
                default_dt = abi.PdvmDateTime
            else:
                abi = Pdvm_DateTime("DEU")
                default_dt = None
            self.ab_picker = PdvmDateTimePicker(
                self, abi,
                display=meta.display_ab,
                display_time_short=meta.display_ti_ab_short,
                default_date=default_dt
            )
            self.ab_picker.update_display()
            form.addRow("Ab-Datum:", self.ab_picker)

        # — Buttons —
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                     Qt.Horizontal, self)
        ok = self.btns.button(QDialogButtonBox.Ok)
        ok.setText("Speichern")
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        form.addRow(self.btns)

    def get_results(self):
        # GUID
        selected_guid = self.select_dialog.get_selected_guid()
        if selected_guid is not None:
            new_val = selected_guid
        else:
            # Wenn keine neue Auswahl, übernehme die aktuelle GUID
            new_val = self.guid
        # Ab-Datum
        if self.meta.historical and self.meta.has_abdatum:
            self.ab_picker.save()
            new_ab = self.ab_picker.get_pdvm_datetime().PdvmDateTime
            if self.ab_inst:
                self.ab_inst.PdvmDateTime = new_ab
        else:
            new_ab = self.current_ab or 1001.0
        return new_val, new_ab
