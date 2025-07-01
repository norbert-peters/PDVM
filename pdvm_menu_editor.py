# pdvm_menu_editor.py
import inspect
from PyQt5.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QLabel, QLineEdit, QMessageBox, QAbstractItemView, QMenu
)
#from PyQt5.QtCore import Qt
#from pdvm_datenbank import PdvmDatenbank

import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmMenuEdditor gestartet")


class PdvmMenuEditor(QWidget):
    """
    Ein Editor für die Menüstruktur. Erlaubt Hinzufügen, Löschen,
    Umbenennen und Verschieben von Menüeinträgen sowie Speichern.
    Unterstützt Drag&Drop und Vorschläge für Kommandos.
    """
    def __init__(self, parent, menu_instance, menu_type, main_app, call_path=None):
        super().__init__(parent)
        self.main_app = main_app
        self.menu_instance = menu_instance
        self.menu_type = menu_type
        self.call_path = call_path
        self.is_zusatz = menu_type.startswith("PD_zusatz")

        # Hauptlayout setup
        layout = QVBoxLayout(self)
        header = f"Menütyp: {menu_type}"
        if self.is_zusatz and call_path:
            header += f" (Schlüssel: {call_path})"
        lbl = QLabel(header)
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)

        # Baumansicht konfigurieren
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        layout.addWidget(self.tree)
        self.load_tree()
        self.tree.itemClicked.connect(self.on_select)
        self.current_item = None

        # Buttons für Operationen
        btn_layout = QHBoxLayout()
        for name, handler in [
            ("Hinzufügen", self.add_entry),
            ("Bearbeiten", self.edit_entry),
            ("Löschen", self.delete_entry),
#            ("⬆", self.move_up),
#            ("⬇", self.move_down),
#            ("-- Ebene außen", self.move_out),
#            ("++ Ebene innen", self.move_in),
            ("Zusatzmenü", self.open_zusatz_menu),
            ("Speichern", self.save_changes)
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def load_tree(self):
        """Lädt die Menüstruktur in den QTreeWidget."""
        self.tree.clear()
        section = self.menu_instance.menu_section(self.menu_type)
        self._add_items(None, section)
        self.tree.expandAll()

    def _add_items(self, parent, data):
        """Rekursives Hinzufügen der Einträge."""
        for key, val in data.items():
            item = QTreeWidgetItem([key])
            item.val = val  # None = Leaf, dict = Submenu
            item.full_path = (parent.full_path + '.' + key) if parent else key
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if isinstance(val, dict) and val:
                self._add_items(item, val)

    def on_select(self, item, col):
        """Speichert das aktuell selektierte Item."""
        self.current_item = item

    def _show_entry_dialog(self, mode, parent_item=None, item=None):
        """Dialog zum Hinzufügen/Bearbeiten mit Vorschlagssystem."""
        dlg = QDialog(self)
        dlg.setWindowTitle('Eintrag ' + ('hinzufügen' if mode=='add' else 'bearbeiten'))
        dlg_layout = QVBoxLayout(dlg)

        lbl_name = QLabel('Name:')
        txt_name = QLineEdit()
        lbl_cmd = QLabel('Kommando:')
        txt_cmd = QLineEdit()
        lbl_suggestion = QLabel('')
        lbl_suggestion.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")

        dlg_layout.addWidget(lbl_name)
        dlg_layout.addWidget(txt_name)
        dlg_layout.addWidget(lbl_cmd)
        dlg_layout.addWidget(txt_cmd)
        dlg_layout.addWidget(lbl_suggestion)

        # Vorbefüllen im Edit-Modus
        if mode == 'edit' and item:
            txt_name.setText(item.text(0))
            cmd_key = item.full_path.replace('.', '_')
            txt_cmd.setText(self.menu_instance.get_command(cmd_key) or '')

        # Leaf-Einschränkung
        leaf = (mode == 'add') or (item and item.childCount() == 0)
        txt_cmd.setEnabled(leaf)

        def get_methods():
            return {n for n, _ in inspect.getmembers(self.main_app, predicate=inspect.ismethod)}

        def update_suggestion():
            nm = txt_name.text().strip()
            if nm and not txt_cmd.text().strip():
                sug = f"open_{nm.lower().replace(' ', '_')}"
                lbl_suggestion.setText(f"Vorschlag: {sug}()" if sug in get_methods() else '')
            else:
                lbl_suggestion.clear()

        txt_name.textChanged.connect(update_suggestion)
        txt_cmd.textChanged.connect(update_suggestion)

        btns = QHBoxLayout()
        ok = QPushButton('Speichern')
        cancel = QPushButton('Abbrechen')
        ok.clicked.connect(dlg.accept)
        cancel.clicked.connect(dlg.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        dlg_layout.addLayout(btns)

        if dlg.exec_() == QDialog.Accepted:
            name = txt_name.text().strip()
            cmd = txt_cmd.text().strip()
            parent_path = parent_item.full_path if parent_item else ''
            if mode == 'add':
                self.menu_instance.add_menu_entry(parent_path, name, cmd, self.menu_type)
                self.load_tree()
            else:
                idx = parent_item.indexOfChild(item) if parent_item else self.tree.indexOfTopLevelItem(item)
                old = item.full_path
                new_full = f"{parent_path}.{name}" if parent_path else name
                self.menu_instance.rename_menu_entry(old, new_full, self.menu_type)
                self.menu_instance.set_command(new_full, cmd)
                self.load_tree()
                # Selektiere neuen Knoten
                def find(node):
                    if node.full_path == new_full:
                        return node
                    for i in range(node.childCount()):
                        r = find(node.child(i))
                        if r:
                            return r
                    return None
                for i in range(self.tree.topLevelItemCount()):
                    top = self.tree.topLevelItem(i)
                    found = find(top)
                    if found:
                        self.tree.setCurrentItem(found)
                        self.current_item = found
                        break

    def _sync_structure(self):
        """Synchronisiert den QTreeWidget-Baum zurück in menu_instance."""
        def rec(item):
            if item.childCount() == 0:
                return None
            sd = {}
            for i in range(item.childCount()):
                ch = item.child(i)
                sd[ch.text(0)] = rec(ch)
            return sd
        new_struct = {}
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            new_struct[top.text(0)] = rec(top)
        if self.menu_type == 'PD_grund':
            self.menu_instance.pdvm_grund = new_struct
        elif self.menu_type == 'PD_menu':
            self.menu_instance.pdvm_menu = new_struct
        else:
            parts = self.menu_type.split('.')
            section = self.menu_instance.pdvm_zusatz
            for p in parts[1:-1]:
                section = section.setdefault(p, {})
            section[parts[-1]] = new_struct

    def add_entry(self):
        self._show_entry_dialog('add', parent_item=self.current_item)

    def edit_entry(self):
        if not self.current_item:
            return
        parent = self.current_item.parent()
        self._show_entry_dialog('edit', parent_item=parent, item=self.current_item)

    def delete_entry(self):
        if not self.current_item:
            return
        path = self.current_item.full_path
        if QMessageBox.question(self, "Löschen", f"Eintrag '{path}' wirklich löschen?") == QMessageBox.Yes:
            self.menu_instance.delete_menu_entry(path, self.menu_type)
            self.load_tree()

    def move_up(self):
        self.menu_instance.move_item(self.tree, self.menu_type, direction='up')
        self.load_tree()

    def move_down(self):
        self.menu_instance.move_item(self.tree, self.menu_type, direction='down')
        self.load_tree()

    def move_out(self):
        self.menu_instance.move_item(self.tree, self.menu_type, direction='out')
        self.load_tree()

    def move_in(self):
        self.menu_instance.move_item(self.tree, self.menu_type, direction='in')
        self.load_tree()

    def open_zusatz_menu(self):
        """Öffnet das Zusatzmenü passend zum aktuellen Eintrag."""
        if self.is_zusatz:
            QMessageBox.warning(self, 'Fehler', 'Für Zusatzmenüs können keine weiteren Zusatzmenüs erstellt werden.')
            return
        if not self.current_item:
            QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen, um ein Zusatzmenü zu öffnen.')
            return
        if self.menu_type == 'PD_grund':
            prefix = 'PD_zusatz.PD_z_Grund.'
        elif self.menu_type == 'PD_menu':
            prefix = 'PD_zusatz.PD_z_Menu.'
        else:
            QMessageBox.warning(self, 'Fehler', 'Zusatzmenü für diesen Typ nicht möglich.')
            return
        key = self.current_item.full_path.replace('.', '_')
        new_menu_type = prefix + key
        self.main_app.open_menu_editor(new_menu_type, key)

    def save_changes(self):
        """
        Speichert die aktuelle Menüstruktur:
        1) Sync Tree → Modell
        2) Modell speichert selbst in der DB
        """
        self._sync_structure()
        try:
            self.menu_instance.save_to_db()
        except AttributeError:
            self.menu_instance.save(self.menu_type)
        QMessageBox.information(self, "Gespeichert", "Änderungen wurden gespeichert.")
