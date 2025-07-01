# pdvm_frame_manager_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from pdvm_frame_manager import PdvmFrameManager

class PdvmFrameManagerWidget(QWidget):
    """
    Ein QWidget, das einen PdvmFrameManager enthält und automatisch
    zwischen Such-Liste und Detail-Form umschaltet.
    """
    # wir feuern hier ein Signal, falls außen jemand reagieren will
    selectionChanged = pyqtSignal(list)
    detailRequested  = pyqtSignal(object)  # übergeben wird das neue Detail-Widget

    def __init__(self, call_daten: dict, parent=None):
        super().__init__(parent)
        self.fm = PdvmFrameManager(call_daten)

        # Layout
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0,0,0,0)

        # Wenn der Manager „Detail anfordern“ intern feuert, fangen wir es ab:
        # wir überschreiben einfach die Platzhalter-Methoden:
        self.fm._detailRequested = self._on_detail_requested

        # und jetzt das erste Widget einbauen:
        w = self.fm.widget_for_input_frame()
        self._lay.addWidget(w)

    def _on_detail_requested(self, widget):
        # lösche altes Child
        while self._lay.count():
            _w = self._lay.takeAt(0).widget()
            if _w:
                _w.setParent(None)
        # und baue das neue ein
        self._lay.addWidget(widget)
        # und gib das weiter, falls außen jemand hören will
        self.detailRequested.emit(widget)
