from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt

import logging
logger = logging.getLogger(__name__)

class PdvmDropdownPicker(QWidget):
    selectionChanged = pyqtSignal(str, name="selectionChanged")

    def __init__(self, parent, drop_inst, section_key, value=None, language="de", stichtag=1001.0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.drop_inst     = drop_inst
        self.section_key   = section_key
        self.language      = language
        self.stichtag      = float(stichtag)
        self.value         = value

        self.setObjectName("PdvmDropdownPicker")

        # Debug-Ausgabe: Zeige alle Gruppen und deren Optionen explizit
        debug_groups = []
        for g in drop_inst.get_fields():
            debug_groups.append({'gruppe': getattr(g, 'gruppe', None), 'options': getattr(g, 'options', None)})
        logger.debug(f"🔹 PdvmDropdownPicker: Gruppen/Optionen={debug_groups}, section_key={section_key}, language={language}, stichtag={stichtag}, value={value}")

        # Debug: Zeige explizit die Optionen für die aktuelle section_key
        options_for_section = None
        for g in drop_inst.get_fields():
            if getattr(g, 'gruppe', None) == section_key:
                options_for_section = getattr(g, 'options', None)
                break
        logger.debug(f"🔹 PdvmDropdownPicker: Optionen für section_key='{section_key}': {options_for_section}")

        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        lo = QHBoxLayout(self); lo.setContentsMargins(0,0,0,0)
        lo.addWidget(self.combo, stretch=1)

        self.key2disp = {}
        self.disp2key = {}

        self.refresh_options(self.stichtag)
        if self.value is not None:
            self.set_selected_key(str(self.value))

    def _load_options(self):
        # Holt die Werte-Liste direkt aus der Instanzdatenstruktur
        try:
            gruppe_dict = self.drop_inst.data.get('ROOT', {}).get(self.section_key, {})
            opts = gruppe_dict.get('werte', [])
            logger.debug(f"🔹 PdvmDropdownPicker: _load_options für section_key='{self.section_key}': {opts}")
            return opts
        except Exception as e:
            logger.error(f"Fehler beim Laden der Dropdown-Optionen für {self.section_key}: {e}")
            return []

    def refresh_options(self, stichtag: float):
        self.stichtag = float(stichtag)
        opts = self._load_options()
        self.combo.clear(); self.key2disp.clear(); self.disp2key.clear()
        for w in opts:
            key = w.get("key") if isinstance(w, dict) else w
            disp = w.get(self.language) if isinstance(w, dict) and self.language in w else (w.get("de") if isinstance(w, dict) else str(w))
            disp = disp or key
            self.key2disp[key] = disp
            self.disp2key[disp] = key
            self.combo.addItem(disp)
        if self.combo.count():
            self.combo.setCurrentIndex(0)

    def set_selected_key(self, key: str):
        if key is None:
            key = ''
        key = str(key)
        disp = self.key2disp.get(key)
        if disp:
            idx = self.combo.findText(disp, Qt.MatchExactly)
            if idx>=0:
                self.combo.setCurrentIndex(idx)
        else:
            if self.combo.count():
                self.combo.setCurrentIndex(0)

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
