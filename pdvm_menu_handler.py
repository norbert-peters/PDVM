# menu_handler.py
import pdvm_datenbank as db
from pdvm_menu import PdvmMenu
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenuBar, QMenu, QPushButton

import logging
logger = logging.getLogger(__name__)
logger.info("🔹 PdvmMenuHandler initialisiert")

class PdvmMenuHandler:
    def __init__(self, root, menu_widget, menu_id, command_handler):
        self.root = root
        self.menu_widget = menu_widget
        self.menu_id = menu_id
        self.command_handler = command_handler

        # Neues Modell-Objekt kümmert sich ums Laden
        self.menu = PdvmMenu(menu_id)

        # Diese Dicts werden intern aus self.menu._pd_structure gezogen:
        self.commands_structure = self.menu.get_pdvm_commands()
        self.grund_menu = self.menu.pdvm_grund
        self.vertical_menu = self.menu.pdvm_menu
        self.zusatz_menues = self.menu.get_all_zusatz_menues()

        # Menüleiste oben
        self.menu_bar = QMenuBar(self.root)
        self.root.setMenuBar(self.menu_bar)
        self.current_additional_menu = None

    def clear_menu_bar(self):
        for action in list(self.menu_bar.actions()):
            self.menu_bar.removeAction(action)

    def create_horizontal_menu(self):
        self.clear_menu_bar()
        self.add_menu_items(self.menu_bar, self.grund_menu)

    def create_vertical_menus(self):
        layout = self.menu_widget.layout()

        # 1) Komplett leeren – Widgets UND Spacer
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # 2) Ganz oben ausrichten
        layout.setAlignment(Qt.AlignTop)

        # 3) Buttons neu anlegen
        for menu_name, submenus in self.vertical_menu.items():
            btn = QPushButton(menu_name)
            if isinstance(submenus, dict) and submenus:
                popup = QMenu()
                self.add_menu_items(popup, submenus, parent_path=menu_name)
                btn.setMenu(popup)
            else:
                btn.clicked.connect(lambda checked=False, key=menu_name: self.handle_command(key))
            layout.addWidget(btn)

        # 4) EIN Stretch, damit der Rest unten bleibt
        layout.addStretch(1)

    def add_menu_items(self, menu_obj, items: dict, parent_path=""):
        """Fügt Einträge in QMenuBar oder QMenu ein."""
        if not isinstance(items, dict): return
        for key, value in items.items():
            full_key = f"{parent_path}.{key}" if parent_path else key
            # Separator
            if key.lower() in ("separator", "---"):
                menu_obj.addSeparator()
                continue
            # Untermenü
            if isinstance(value, dict):
                # addMenu(str) returns a QMenu
                sub_menu = menu_obj.addMenu(key)
                self.add_menu_items(sub_menu, value, full_key)
            # Einfache Aktion
            else:
                action = menu_obj.addAction(key)
                action.triggered.connect(lambda checked=False, opt=full_key: self.handle_command(opt))

    def handle_command(self, command_key):
        """Verarbeitet einen Menü-Befehl."""
        logger.debug(f"🔹 handle_command: {command_key}")

        # Zusatzmenü-Handling
        new_aux = next((k for k in self.zusatz_menues if k in command_key), None)
        if new_aux != self.current_additional_menu:
            self.current_additional_menu = new_aux
            self.update_additional_menu()
        self.command_handler.execute_command(command_key)

    def update_additional_menu(self):
        self.clear_menu_bar()
        self.add_menu_items(self.menu_bar, self.grund_menu)
        if self.current_additional_menu:
            zus = self.zusatz_menues.get(self.current_additional_menu, {})
            self.add_menu_items(self.menu_bar, zus, parent_path=self.current_additional_menu)

    def create_menus(self):
        self.create_horizontal_menu()
        self.create_vertical_menus()

    def get_commands(self):
        return self.commands_structure
