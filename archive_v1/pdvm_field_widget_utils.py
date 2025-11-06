from PyQt5.QtWidgets import QPushButton, QHBoxLayout
from pdvm_search_list_widget_dialog import PdvmSearchListWidgetDialog

def add_viewtable_select_button(parent, line_edit, meta, manager, user_guid=None, frame_guid=None, call_data=None):
    """
    Fügt einen Auswahl-Button für Viewtable-Felder hinzu, öffnet den PdvmSearchListWidgetDialog und setzt die GUID ins Textfeld.
    """
    btn = QPushButton("Auswählen…", parent)
    btn.setMinimumWidth(120)
    btn.setToolTip("Datensatz auswählen")
    def on_select():
        # Für die Auswahl immer die View-GUID aus den Metadaten oder call_data verwenden!
        viewtable_guid = getattr(meta, 'viewtable_guid', None)
        if not viewtable_guid:
            viewtable_guid = getattr(meta, 'view_guid', None)
        if not viewtable_guid and call_data:
            viewtable_guid = call_data.get('view_guid')
        dlg = PdvmSearchListWidgetDialog(parent, viewtable_guid, user_guid=user_guid, frame_guid=frame_guid, call_data=call_data)
        if dlg.exec_() == dlg.Accepted:
            selected_guid = getattr(dlg, 'selected_guid', None)
            if selected_guid:
                line_edit.setText(str(selected_guid))
    btn.clicked.connect(on_select)
    row = QHBoxLayout()
    row.addWidget(btn)
    return row
