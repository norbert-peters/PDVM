# start_app.py
# -*- coding: utf-8 -*-

import os
import sys
import logging

# Erzwinge UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_test.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🔹 Start Pdvm Dialog Test")

from PyQt5.QtWidgets import QApplication, QMainWindow
from pdvm_dialog_widget import PdvmDialogWidget

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    logger.info("🔹 Hauptanwendung gestartet")
    call_daten = {
        "user_guid":  "4886ad26-061b-4662-a762-c8c83f36692d",
        "view_guid":  "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "mode":        0,
    }

    # Erzeuge das Widget (intern nutzt es PdvmInputManager)
    widget = PdvmDialogWidget(call_daten, parent=window)
    window.setCentralWidget(widget)
    window.resize(800, 600)
    window.show()
#    sys.exit(app.exec_())

#    sys.exit(0)

if __name__ == "__main__":
    main()


