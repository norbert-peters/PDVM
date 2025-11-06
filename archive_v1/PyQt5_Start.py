# PyQt5_Start.py

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from pdvm_frame_manager import PdvmFrameManager

class MainWindow(QMainWindow):
    def __init__(self, call_daten, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDVM Frame Manager Test")

        # 1) FrameManager instanziieren
        self.fm = PdvmFrameManager(call_daten)

        # 2) Erstes Widget (wahlweise Suchliste oder Detail) holen
        w = self.fm.widget_for_input_frame()

        # 3) ins zentrale Widget packen
        self.setCentralWidget(w)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    call_daten = {
      "user_guid":     "4886ad26-061b-4662-a762-c8c83f36692d",
      "stichtag":      "2025106.0",
      "mode":          0,
      # framing: GUID auf framedaten-Tabelle
      "framedaten": {
          "GUID": "4078079f-4028-45ed-879c-3c779ecf3d0d",
          "HIST": False
      },
      # ggf. Dropdown, pdvmperson, protokolldaten …
    }

    window = MainWindow(call_daten)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
