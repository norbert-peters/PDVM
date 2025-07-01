# pdvm_dropdown_picker.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt

class PdvmDropdownPicker(QWidget):

    def refresh_from_instance(self):
        """
        Aktualisiert die Anzeige des Dropdowns aus der zugehörigen Instanz (z.B. PdvmCentralDatenbank),
        sodass der aktuelle Wert (Key) gesetzt und übersetzt angezeigt wird.
        """
        # Versuche, die Instanz und das Feld zu finden
        # Annahme: drop_inst hat Attribute data_inst, meta oder ähnlich
        try:
            # Für Kompatibilität: Suche nach data_inst und meta
            data_inst = getattr(self.drop_inst, 'data_inst', None)
            meta = getattr(self.drop_inst, 'meta', None)
            if data_inst and meta:
                table, grp, fld = meta.key.split('_', 2)
                val_dict = data_inst.get_value(grp, fld)
                key = val_dict.get('wert', '') if isinstance(val_dict, dict) else val_dict
                self.set_selected_key(key)
        except Exception:
            pass
    """
    Qt-Widget für historischen/aktuellen Dropdown.
    Konstruktor:
      PdvmDropdownPicker(parent, drop_inst, section_key,
                         language="de", stichtag=1001.0)
    """
    selectionChanged = pyqtSignal(str, name="selectionChanged")

    def __init__(self, parent, drop_inst, section_key,
                 language="de", stichtag=1001.0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.drop_inst     = drop_inst
        self.section_key   = section_key
        self.language      = language
        self.stichtag      = float(stichtag)

        # Layout
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        lo = QHBoxLayout(self); lo.setContentsMargins(0,0,0,0)
        lo.addWidget(self.combo, stretch=1)

        # Maps
        self.key2disp = {}
        self.disp2key = {}

        # initial
        self.refresh_options(self.stichtag)

    def _load_options(self):
        # Holt alle Optionen aus dem Manager-Cache
        fm = next((f for f in self.drop_inst.get_fields()
                   if f.dropdown_section == self.section_key), None)
        if not fm:
            return []
        opts = fm.dropdown_options
        if fm.historical:
            opts = [w for w in opts if float(w.get("abdatum","1001.0")) <= self.stichtag]
            opts.sort(key=lambda w: float(w.get("abdatum","1001.0")))
        return opts

    def refresh_options(self, stichtag: float):
        self.stichtag = float(stichtag)
        opts = self._load_options()
        self.combo.clear(); self.key2disp.clear(); self.disp2key.clear()
        for w in opts:
            key  = w.get("key")
            disp = w.get(self.language) or key
            self.key2disp[key]  = disp
            self.disp2key[disp] = key
            self.combo.addItem(disp)
        if self.combo.count():
            self.combo.setCurrentIndex(0)

    def set_selected_key(self, key: str):
        disp = self.key2disp.get(key)
        if disp:
            idx = self.combo.findText(disp, Qt.MatchExactly)
            if idx>=0:
                self.combo.setCurrentIndex(idx)

    def get_selected_key(self) -> str:
        return self.disp2key.get(self.combo.currentText(), "")

    def _on_index_changed(self, idx: int):
        key = self.get_selected_key()
        self.selectionChanged.emit(key)

    def setReadOnly(self, ro: bool=True):
        self.combo.setEnabled(not ro)
        if ro:
            self.combo.setEditable(True)
            self.combo.lineEdit().setReadOnly(True)
            self.combo.setFrame(False)
            self.combo.setStyleSheet("""
                QComboBox { background: #fafafa; color:black; border:1px solid #d0d0d0; }
                QComboBox::drop-down { width:0px; }
                QComboBox::down-arrow { image:none; }
            """)
        else:
            self.combo.setEditable(False)
            self.combo.setFrame(True)
            self.combo.setStyleSheet("")
