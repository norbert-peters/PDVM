# menu_handler.py
import pdvm_datenbank as db
from pdvm_menu import PdvmMenu
from pdvm_menu_template_handler import PdvmMenuTemplateHandler
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer
from PyQt5.QtWidgets import QMenuBar, QMenu, QPushButton, QFrame
from PyQt5.QtGui import QKeyEvent

import logging
logger = logging.getLogger(__name__)
logger.info("🔹 PdvmMenuHandler initialisiert")

class PdvmMenuHandler:
    def __init__(self, root, menu_widget, menu_id, command_handler):
        self.root = root
        self.menu_widget = menu_widget
        self.menu_id = menu_id
        self.command_handler = command_handler

        # Template-Handler für Menü-Wiederverwendung (falls extern benötigt)
        self.template_handler = PdvmMenuTemplateHandler()

        # Menü-Objekt - Templates werden automatisch in PdvmMenu verarbeitet
        self.menu = PdvmMenu(menu_id)

        # Diese Dicts werden aus der bereits template-verarbeiteten Struktur gezogen:
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

        # 3) Buttons neu anlegen mit Tastaturnavigation
        self.menu_buttons = []  # Liste für Tastaturnavigation
        for menu_name, submenus in self.vertical_menu.items():
            # Separator-Erkennung auch hier
            if self._is_separator(menu_name):
                # Separator-Frame erstellen
                separator_frame = self._create_separator_widget()
                layout.addWidget(separator_frame)
                continue
                
            btn = QPushButton(menu_name)
            btn.setFocusPolicy(Qt.StrongFocus)  # Tastatur-Fokus aktivieren
            
            # Bessere Fokus-Anzeige
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                }
                QPushButton:hover {
                    background-color: #e6f3ff;
                    border-color: #0078d4;
                }
                QPushButton:focus {
                    background-color: #e6f3ff;
                    border: 2px solid #0078d4;
                    outline: none;
                }
                QPushButton:pressed {
                    background-color: #cce7ff;
                }
            """)
            
            if isinstance(submenus, dict) and submenus:
                popup = QMenu()
                self.add_menu_items(popup, submenus, parent_path=menu_name)
                btn.setMenu(popup)
            else:
                btn.clicked.connect(lambda checked=False, key=menu_name: self.handle_command(key))
            
            layout.addWidget(btn)
            self.menu_buttons.append(btn)

        # 4) EIN Stretch, damit der Rest unten bleibt
        layout.addStretch(1)
        
        # 5) Tastatur-Navigation einrichten
        self._setup_keyboard_navigation()
        
        # 6) Standard-Fokus auf ersten Button setzen
        if self.menu_buttons:
            # Kurze Verzögerung für vollständige Widget-Initialisierung
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._set_initial_focus())
    
    def _create_separator_widget(self):
        """Erstellt ein visuelles Separator-Widget."""
        from PyQt5.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin: 2px 0px; color: gray;")
        separator.setMaximumHeight(2)
        return separator
    
    def _setup_keyboard_navigation(self):
        """Richtet die Tastaturnavigation für das vertikale Menü ein."""
        if not self.menu_buttons:
            return
        
        # Event-Filter für Tastaturnavigation
        from PyQt5.QtCore import QObject, QEvent
        from PyQt5.QtGui import QKeyEvent
        
        class MenuKeyFilter(QObject):
            def __init__(self, menu_handler):
                super().__init__()
                self.menu_handler = menu_handler
            
            def eventFilter(self, obj, event):
                if (event.type() == QEvent.KeyPress and 
                    isinstance(event, QKeyEvent) and 
                    obj in self.menu_handler.menu_buttons):
                    
                    current_index = self.menu_handler.menu_buttons.index(obj)
                    
                    if event.key() == Qt.Key_Down:
                        # Nächster Button
                        next_index = (current_index + 1) % len(self.menu_handler.menu_buttons)
                        self.menu_handler.menu_buttons[next_index].setFocus()
                        logger.debug(f"🔽 Fokus nach unten: {self.menu_handler.menu_buttons[next_index].text()}")
                        return True
                    elif event.key() == Qt.Key_Up:
                        # Vorheriger Button
                        prev_index = (current_index - 1) % len(self.menu_handler.menu_buttons)
                        self.menu_handler.menu_buttons[prev_index].setFocus()
                        logger.debug(f"🔼 Fokus nach oben: {self.menu_handler.menu_buttons[prev_index].text()}")
                        return True
                    elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                        # Button aktivieren
                        logger.info(f"⚡ Button aktiviert: {obj.text()}")
                        obj.click()
                        return True
                
                return super().eventFilter(obj, event)
        
        # Event-Filter installieren
        self.key_filter = MenuKeyFilter(self)
        for btn in self.menu_buttons:
            btn.installEventFilter(self.key_filter)
    
    def _set_initial_focus(self):
        """Setzt den initialen Fokus auf den ersten Menü-Button."""
        if self.menu_buttons:
            first_button = self.menu_buttons[0]
            first_button.setFocus(Qt.OtherFocusReason)
            logger.info(f"🎯 Initial-Fokus gesetzt auf: {first_button.text()}")
            logger.info("💡 Tipp: Verwenden Sie ↑/↓ Pfeiltasten zur Navigation, Enter zum Aktivieren")

    def add_menu_items(self, menu_obj, items: dict, parent_path=""):
        """Fügt Einträge in QMenuBar oder QMenu ein."""
        if not isinstance(items, dict): return
        for key, value in items.items():
            full_key = f"{parent_path}.{key}" if parent_path else key
            # Separator - erweiterte Erkennung für nummierte Separatoren
            if self._is_separator(key):
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
    
    def _is_separator(self, text):
        """Prüft ob es sich um einen Separator handelt (--- oder ---(nummer))."""
        import re
        return (text.lower() in ("separator", "---") or 
                bool(re.match(r'^---\(\d+\)$', text)))

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
