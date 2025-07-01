from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from pdvm_view_manager import PdvmViewManager
from pdvm_search_list_widget import PdvmSearchListWidget

class PdvmSearchListWidgetDialog(QDialog):
    def __init__(self, parent, view_guid, user_guid=None, frame_guid=None, call_data=None):
        super().__init__(parent)
        self.setWindowTitle("Auswahl aus View")
        # ViewManager initialisieren
        if call_data is None:
            call_data = {}
        call_data = dict(call_data)  # Kopie
        call_data["view_guid"] = view_guid
        if user_guid:
            call_data["user_guid"] = user_guid
        if frame_guid:
            call_data["frame_guid"] = frame_guid
        self.vm = PdvmViewManager(call_data)
        self.widget = PdvmSearchListWidget(self.vm, self.vm.view_table)
        layout = QVBoxLayout(self)
        layout.addWidget(self.widget)
        # Buttons
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Abbrechen")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        self.selected_guid = None
        self.widget.selectionChanged.connect(self._on_selection)

    def _on_selection(self, guids):
        if guids:
            self.selected_guid = guids[0]

    def get_selected_guid(self):
        # Immer aktuelle Auswahl aus dem Widget holen, nicht nur das letzte selectionChanged
        sel = self.widget.table_view.selectionModel().selectedRows()
        if sel:
            guids = [self.widget.model.guid_for_row(idx.row()) for idx in sel]
            if guids:
                return guids[0]
        return self.selected_guid
