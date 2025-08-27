# pdvm_menu_editor.py
import inspect
from PyQt5.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QLabel, QLineEdit, QMessageBox, QAbstractItemView, QMenu
)
from PyQt5.QtCore import Qt
#from pdvm_datenbank import PdvmDatenbank

import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmMenuEditor gestartet")


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
        self.tree.setFocusPolicy(Qt.StrongFocus)  # Starker Fokus für Tastatur
        
        # Styling für bessere Fokus-Anzeige
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ccc;
                alternate-background-color: #f9f9f9;
            }
            QTreeWidget::item {
                padding: 4px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTreeWidget::item:focus {
                background-color: #e6f3ff;
                border: 1px solid #0078d4;
            }
            QTreeWidget::item:selected:focus {
                background-color: #005a9e;
                color: white;
            }
        """)
        
        layout.addWidget(self.tree)
        self.load_tree()
        self.tree.itemClicked.connect(self.on_select)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)  # Für Tastaturnavigation
        self.tree.keyPressEvent = self.handle_key_press  # Keyboard-Handler
        self.current_item = None

        # Buttons für Operationen
        btn_layout = QHBoxLayout()
        for name, handler in [
            ("Hinzufügen", self.add_entry),
            ("Separator", self.add_separator),
            ("Bearbeiten", self.edit_entry),
            ("Löschen", self.delete_entry),
            ("⬆ Hoch", self.move_up),
            ("⬇ Runter", self.move_down),
            ("← Rausziehen", self.move_out),
            ("→ Reinziehen", self.move_in),
            ("Zusatzmenü", self.open_zusatz_menu),
            ("Speichern", self.save_changes)
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(handler)
            # Separator-Button hervorheben
            if name == "Separator":
                btn.setStyleSheet("QPushButton { background-color: #e6f3ff; font-weight: bold; }")
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        
        # Initial-Fokus setzen - NACH dem vollständigen Layout-Setup
        self._setup_initial_focus()
    
    def _setup_initial_focus(self):
        """Setzt den initialen Fokus auf das erste Tree-Item."""
        from PyQt5.QtCore import QTimer
        # Längere Verzögerung für vollständige Widget-Initialisierung
        QTimer.singleShot(300, self._set_initial_tree_focus)
    
    def _set_initial_tree_focus(self):
        """Setzt den Fokus auf das erste Item im Tree."""
        try:
            if self.tree.topLevelItemCount() > 0:
                first_item = self.tree.topLevelItem(0)
                # Sicherheitsprüfung ob das Item noch existiert
                if first_item is not None:
                    # Test ob das Qt-Objekt noch zugänglich ist
                    item_text = first_item.text(0)
                    
                    self.tree.setCurrentItem(first_item)
                    self.current_item = first_item
                    self.tree.setFocus(Qt.OtherFocusReason)
                    logger.info(f"🎯 Menüeditor-Fokus gesetzt auf: {item_text}")
                    logger.info("💡 Tipp: Verwenden Sie ↑/↓ zur Navigation, Ctrl+Pfeiltasten zum Verschieben, Enter zum Bearbeiten")
                else:
                    logger.warning("⚠️ Erstes Tree-Item ist None")
            else:
                logger.warning("⚠️ Kein Tree-Item verfügbar für Initial-Fokus")
        except RuntimeError as e:
            logger.error(f"❌ Fehler beim Setzen des Initial-Fokus: {e}")
            # Fallback: Fokus auf Tree selbst setzen
            self.tree.setFocus(Qt.OtherFocusReason)
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler beim Initial-Fokus: {e}")

    def _validate_current_item(self):
        """
        Validiert das aktuelle Item und setzt es auf None wenn es ungültig ist.
        
        Returns:
            bool: True wenn current_item gültig ist
        """
        if self.current_item is None:
            return False
        
        try:
            # Test ob das Qt-Objekt noch zugänglich ist
            _ = self.current_item.text(0)
            return True
        except RuntimeError as e:
            logger.error(f"❌ current_item Qt-Objekt wurde gelöscht: {e}")
            self.current_item = None
            return False

    def _safe_get_item_property(self, item, property_name):
        """
        Sichere Methode um Eigenschaften von Qt-Items zu holen.
        
        Args:
            item: Das Qt-Item
            property_name: Name der Eigenschaft ('text', 'full_path', etc.)
            
        Returns:
            Der Wert oder None wenn das Item ungültig ist
        """
        if item is None:
            return None
        
        try:
            if property_name == 'text':
                return item.text(0)
            elif property_name == 'full_path':
                return item.full_path
            elif property_name == 'parent':
                return item.parent()
            else:
                return getattr(item, property_name, None)
        except RuntimeError as e:
            logger.error(f"❌ Fehler beim Zugriff auf Qt-Item-Eigenschaft '{property_name}': {e}")
            return None

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
        """Speichert das aktuell selektierte Item mit Sicherheitsprüfung."""
        try:
            if item is not None:
                # Test ob das Objekt zugänglich ist
                _ = item.text(0)
                self.current_item = item
            else:
                self.current_item = None
        except RuntimeError as e:
            logger.error(f"❌ Qt-Objekt beim Auswählen bereits gelöscht: {e}")
            self.current_item = None
            # Optional: Tree neu laden
    
    def on_selection_changed(self):
        """Wird bei Änderung der Selektion aufgerufen (auch bei Tastaturnavigation)."""
        current = self.tree.currentItem()
        if current:
            try:
                # Test ob das Objekt zugänglich ist
                _ = current.text(0)
                self.current_item = current
            except RuntimeError as e:
                logger.error(f"❌ Qt-Objekt bei Selektionsänderung bereits gelöscht: {e}")
                self.current_item = None
        else:
            self.current_item = None
            self.load_tree()

    def _show_entry_dialog(self, mode, parent_item=None, item=None):
        """Dialog zum Hinzufügen/Bearbeiten mit Vorschlagssystem und Separator-Unterstützung."""
        dlg = QDialog(self)
        dlg.setWindowTitle('Eintrag ' + ('hinzufügen' if mode=='add' else 'bearbeiten'))
        dlg_layout = QVBoxLayout(dlg)

        lbl_name = QLabel('Name:')
        txt_name = QLineEdit()
        lbl_cmd = QLabel('Kommando:')
        txt_cmd = QLineEdit()
        lbl_suggestion = QLabel('')
        lbl_suggestion.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")

        # Separator-Info hinzufügen
        lbl_separator_info = QLabel('💡 Tipp: Für Separatoren verwenden Sie "---" oder nutzen Sie den Separator-Button!')
        lbl_separator_info.setStyleSheet("color: blue; font-style: italic; font-size: 10px; margin: 5px;")

        dlg_layout.addWidget(lbl_name)
        dlg_layout.addWidget(txt_name)
        dlg_layout.addWidget(lbl_separator_info)
        dlg_layout.addWidget(lbl_cmd)
        dlg_layout.addWidget(txt_cmd)
        dlg_layout.addWidget(lbl_suggestion)

        # Vorbefüllen im Edit-Modus
        if mode == 'edit' and item:
            txt_name.setText(item.text(0))
            
            # Prüfe ob es ein Separator ist
            if self._is_separator(item.text(0)):
                txt_cmd.setEnabled(False)
                txt_cmd.setPlaceholderText("Separatoren haben keine Kommandos")
                lbl_suggestion.setText("✂️ Dies ist ein Separator")
            else:
                # Für Zusatzmenüs: Verwende korrekten Kommando-Key
                if self.menu_type.startswith("PD_zusatz"):
                    correct_key = self._generate_zusatz_command_key(item.full_path)
                    current_cmd = self.menu_instance.pd_structure["PD_commands"].get(correct_key)
                    if current_cmd is None:
                        # Fallback: Versuche auch den alten Key
                        old_key = item.full_path.replace('.', '_')
                        current_cmd = self.menu_instance.pd_structure["PD_commands"].get(old_key, '')
                    txt_cmd.setText(current_cmd or '')
                else:
                    cmd_key = item.full_path.replace('.', '_')
                    txt_cmd.setText(self.menu_instance.get_command(cmd_key) or '')

        # Leaf-Einschränkung (aber nicht für Separatoren)
        leaf = (mode == 'add') or (item and item.childCount() == 0)
        if not (mode == 'edit' and item and self._is_separator(item.text(0))):
            txt_cmd.setEnabled(leaf)

        def get_methods():
            return {n for n, _ in inspect.getmembers(self.main_app, predicate=inspect.ismethod)}

        def update_suggestion():
            nm = txt_name.text().strip()
            
            # Separator-Erkennung
            if self._is_separator(nm):
                txt_cmd.setEnabled(False)
                txt_cmd.clear()
                txt_cmd.setPlaceholderText("Separatoren haben keine Kommandos")
                lbl_suggestion.setText("✂️ Dies wird ein Separator")
                return
            else:
                # Kommando-Feld wieder aktivieren wenn kein Separator
                if leaf:
                    txt_cmd.setEnabled(True)
                    txt_cmd.setPlaceholderText("")
            
            if nm and not txt_cmd.text().strip() and not self._is_separator(nm):
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
                
                # Für Zusatzmenüs: Korrigiere den Kommando-Key
                if self.menu_type.startswith("PD_zusatz"):
                    full_path = f"{parent_path}.{name}" if parent_path else name
                    correct_key = self._generate_zusatz_command_key(full_path)
                    if correct_key != full_path.replace('.', '_'):
                        # Korrigiere den Kommando-Key
                        old_key = full_path.replace('.', '_')
                        if old_key in self.menu_instance.pd_structure["PD_commands"]:
                            # Verschiebe das Kommando zum korrekten Key
                            self.menu_instance.pd_structure["PD_commands"][correct_key] = cmd
                            del self.menu_instance.pd_structure["PD_commands"][old_key]
                            logger.info(f"🔑 Kommando-Key korrigiert: {old_key} → {correct_key}")
                
                self.load_tree()
            else:
                idx = parent_item.indexOfChild(item) if parent_item else self.tree.indexOfTopLevelItem(item)
                old = item.full_path
                new_full = f"{parent_path}.{name}" if parent_path else name
                
                # Umbenennung mit Fehlerbehandlung
                success = self.menu_instance.rename_menu_entry(old, new_full, self.menu_type)
                if success:
                    # Für Zusatzmenüs: Verwende korrekten Kommando-Key
                    if self.menu_type.startswith("PD_zusatz"):
                        correct_key = self._generate_zusatz_command_key(new_full)
                        self.menu_instance.pd_structure["PD_commands"][correct_key] = cmd
                        logger.info(f"🔑 Zusatzmenü-Kommando gesetzt: {correct_key} = {cmd}")
                    else:
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
                else:
                    QMessageBox.warning(self, "Fehler", f"Umbenennung von '{old}' nach '{new_full}' fehlgeschlagen!")

    def _generate_zusatz_command_key(self, full_path):
        """
        Generiert den korrekten Kommando-Key für Zusatzmenüs basierend auf der Menülogik:
        
        Beispiel:
        - Zusatzmenü-Typ: "PD_zusatz.PD_z_Grund.Testbereich_Dialog_Inputframe"
        - Item-Pfad: "Lupe Eingaben"
        - Generierter Key: "Testbereich_Dialog_Inputframe_Lupe Eingaben"
        """
        if not self.menu_type.startswith("PD_zusatz"):
            # Für normale Menüs: Standard-Logik
            return full_path.replace('.', '_')
        
        # Für Zusatzmenüs: Spezielle Logik
        parts = self.menu_type.split('.')
        if len(parts) >= 3:
            # Hole den Basis-Pfad aus dem Menü-Typ (letzter Teil)
            base_key = parts[-1]  # z.B. "Testbereich_Dialog_Inputframe"
            
            # Kombiniere mit dem Item-Pfad
            item_key = full_path.replace('.', '_')
            command_key = f"{base_key}_{item_key}"
            
            logger.info(f"🔑 Zusatzmenü-Key generiert: {command_key}")
            logger.info(f"   Menu-Type: {self.menu_type}")
            logger.info(f"   Full-Path: {full_path}")
            logger.info(f"   Base-Key: {base_key}")
            
            return command_key
        else:
            logger.warning(f"⚠️ Ungültiger Zusatzmenü-Typ: {self.menu_type}")
            return full_path.replace('.', '_')

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
        
        # Baue neue Struktur auf
        new_struct = {}
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            new_struct[top.text(0)] = rec(top)
        
        # Aktualisiere die entsprechende Menüsektion
        if self.menu_type == 'PD_grund':
            self.menu_instance.pdvm_grund = new_struct
        elif self.menu_type == 'PD_menu':
            self.menu_instance.pdvm_menu = new_struct
        else:
            # Zusatzmenü-Behandlung
            parts = self.menu_type.split('.')
            if len(parts) >= 3:  # z.B. PD_zusatz.PD_z_Grund.Testbereich_Dialog_Inputframe
                # Navigiere zur korrekten Sektion
                section = self.menu_instance.pdvm_zusatz
                for p in parts[1:-1]:  # Überspringe 'PD_zusatz' und den letzten Teil
                    if p not in section:
                        section[p] = {}
                    section = section[p]
                
                # Setze die neue Struktur
                section[parts[-1]] = new_struct
                
                logger.info(f"🔄 Zusatzmenü-Struktur aktualisiert: {self.menu_type}")
                logger.info(f"   Parts: {parts}")
                logger.info(f"   Neue Struktur: {new_struct}")
            else:
                logger.error(f"❌ Ungültiger Zusatzmenü-Typ: {self.menu_type}")
        
        # WICHTIG: Synchronisiere auch die gesamte Struktur zurück
        self.menu_instance.update_structure()

    def add_entry(self):
        # Sichere Validierung für add_entry
        if self.current_item and self._validate_current_item():
            self._show_entry_dialog('add', parent_item=self.current_item)
        else:
            # Fallback: Hinzufügen auf Root-Ebene
            self._show_entry_dialog('add', parent_item=None)

    def add_separator(self):
        """
        Fügt einen neuen Separator hinzu mit automatischer Nummerierung.
        
        Separatoren haben das Format ---(1), ---(2), etc.
        """
        try:
            # Finde die nächste verfügbare Separator-Nummer
            next_number = self._get_next_separator_number()
            separator_name = f"---({next_number})"
            
            # Bestimme das Parent-Element
            parent_item = None
            if self.current_item and self._validate_current_item():
                # Wenn ein Item ausgewählt ist, prüfe ob es ein Container ist
                if self.current_item.childCount() > 0:
                    # Ausgewähltes Item ist ein Container -> füge als Child hinzu
                    parent_item = self.current_item
                else:
                    # Ausgewähltes Item ist ein Leaf -> füge auf gleicher Ebene hinzu
                    parent_item = self.current_item.parent()
            
            # Neues Separator-Item erstellen
            separator_item = QTreeWidgetItem([separator_name])
            separator_item.val = None  # Separatoren haben keinen Kommando-Wert
            
            # full_path bestimmen
            if parent_item:
                separator_item.full_path = f"{parent_item.full_path}.{separator_name}"
                parent_item.addChild(separator_item)
                parent_item.setExpanded(True)
            else:
                separator_item.full_path = separator_name
                self.tree.addTopLevelItem(separator_item)
            
            # Neuen Separator auswählen
            self.tree.setCurrentItem(separator_item)
            self.current_item = separator_item
            
            logger.info(f"➕ Separator hinzugefügt: {separator_name}")
            QMessageBox.information(self, "Separator hinzugefügt", 
                                  f"Separator '{separator_name}' wurde erfolgreich hinzugefügt.")
                                  
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen des Separators: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen des Separators:\n{str(e)}")

    def _get_next_separator_number(self):
        """
        Findet die nächste verfügbare Nummer für einen Separator.
        
        Returns:
            int: Die nächste verfügbare Separator-Nummer
        """
        existing_numbers = set()
        
        def check_item(item):
            """Rekursiv alle Items prüfen"""
            text = item.text(0)
            if self._is_separator(text):
                # Extrahiere Nummer aus Format ---(X)
                import re
                match = re.search(r'---\((\d+)\)', text)
                if match:
                    existing_numbers.add(int(match.group(1)))
                # Auch einfache --- ohne Nummer zählen als Nummer 0
                elif text == "---":
                    existing_numbers.add(0)
            
            # Rekursiv Kinder prüfen
            for i in range(item.childCount()):
                check_item(item.child(i))
        
        # Alle Top-Level Items prüfen
        for i in range(self.tree.topLevelItemCount()):
            check_item(self.tree.topLevelItem(i))
        
        # Finde die nächste verfügbare Nummer (beginnend bei 1)
        next_num = 1
        while next_num in existing_numbers:
            next_num += 1
            
        return next_num

    def _is_separator(self, text):
        """
        Prüft ob ein Text ein Separator ist.
        
        Args:
            text: Der zu prüfende Text
            
        Returns:
            bool: True wenn es ein Separator ist
        """
        if not text:
            return False
        return text.startswith("---")

    def edit_entry(self):
        if not self._validate_current_item():
            return
        
        # Sichere Methode verwenden
        try:
            parent = self._safe_get_item_property(self.current_item, 'parent')
            self._show_entry_dialog('edit', parent_item=parent, item=self.current_item)
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler beim Bearbeiten: {e}")
            QMessageBox.warning(self, "Fehler", "Fehler beim Bearbeiten des Elements. Bitte laden Sie die Ansicht neu.")
            self.load_tree()

    def delete_entry(self):
        if not self._validate_current_item():
            return
        
        # Sichere Methode verwenden
        try:
            path = self._safe_get_item_property(self.current_item, 'full_path')
            if path and QMessageBox.question(self, "Löschen", f"Eintrag '{path}' wirklich löschen?") == QMessageBox.Yes:
                self.menu_instance.delete_entry(path, self.menu_type)
                self.load_tree()
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler beim Löschen: {e}")
            QMessageBox.warning(self, "Fehler", "Fehler beim Löschen des Elements. Bitte laden Sie die Ansicht neu.")
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
        2) Sync Kommandos 
        3) Modell speichert selbst in der DB
        """
        try:
            # 1. Synchronisiere Baumstruktur
            self._sync_structure()
            
            # 2. Für Zusatzmenüs: Sammle alle Kommandos aus dem aktuellen Baum
            if self.menu_type.startswith('PD_zusatz'):
                self._sync_zusatz_commands()
            
            # 3. Speichere in Datenbank
            self.menu_instance.save_to_db()
            
            logger.info(f"✅ Menüstruktur erfolgreich gespeichert: {self.menu_type}")
            QMessageBox.information(self, "Gespeichert", "Änderungen wurden erfolgreich gespeichert.")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Speichern der Menüstruktur: {e}")
            QMessageBox.critical(self, "Speicherfehler", f"Fehler beim Speichern:\n{str(e)}")

    def _sync_zusatz_commands(self):
        """
        Synchronisiert Kommandos für Zusatzmenüs mit korrekter Key-Generierung.
        Sammelt alle Kommandos aus dem aktuellen Baum und aktualisiert die PD_commands.
        """
        try:
            def collect_commands(item, path_prefix=""):
                """Sammelt rekursiv alle Kommandos aus dem Baum"""
                current_path = f"{path_prefix}.{item.text(0)}" if path_prefix else item.text(0)
                
                # Wenn es ein Blatt-Knoten ist, sammle das Kommando
                if item.childCount() == 0:
                    # Generiere korrekten Kommando-Key für Zusatzmenüs
                    correct_key = self._generate_zusatz_command_key(current_path)
                    
                    # Hole aktuelles Kommando - suche sowohl mit korrektem als auch altem Key
                    current_command = None
                    old_key = current_path.replace('.', '_')
                    
                    # Prüfe beide Keys
                    if correct_key in self.menu_instance.pd_structure["PD_commands"]:
                        current_command = self.menu_instance.pd_structure["PD_commands"][correct_key]
                    elif old_key in self.menu_instance.pd_structure["PD_commands"]:
                        current_command = self.menu_instance.pd_structure["PD_commands"][old_key]
                        # Verschiebe zum korrekten Key
                        if current_command is not None:
                            self.menu_instance.pd_structure["PD_commands"][correct_key] = current_command
                            del self.menu_instance.pd_structure["PD_commands"][old_key]
                            logger.info(f"🔄 Kommando verschoben: {old_key} → {correct_key}")
                    
                    if current_command is not None:
                        logger.info(f"🔄 Sammle Kommando: {correct_key} = {current_command}")
                        return {correct_key: current_command}
                
                # Für Knoten mit Kindern, sammle rekursiv
                commands = {}
                for i in range(item.childCount()):
                    child_commands = collect_commands(item.child(i), current_path)
                    commands.update(child_commands)
                
                return commands
            
            # Sammle alle Kommandos aus dem aktuellen Baum
            all_commands = {}
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                top_commands = collect_commands(top)
                all_commands.update(top_commands)
            
            # Aktualisiere die PD_commands mit den gesammelten Kommandos
            if hasattr(self.menu_instance, 'pd_structure') and 'PD_commands' in self.menu_instance.pd_structure:
                for cmd_key, cmd_value in all_commands.items():
                    self.menu_instance.pd_structure['PD_commands'][cmd_key] = cmd_value
                    logger.info(f"✅ Kommando aktualisiert: {cmd_key}")
            
            logger.info(f"🎯 Zusatzmenü-Kommandos synchronisiert: {len(all_commands)} Kommandos")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Synchronisieren der Zusatzmenü-Kommandos: {e}")
            raise

    def handle_key_press(self, event):
        """
        Behandelt Keyboard-Events für Navigation und Verschieben.
        
        Tastenbelegung:
        - ↑/↓: Navigation im Tree
        - Ctrl+↑/↓: Nach oben/unten verschieben  
        - Ctrl+←: Eine Ebene rausziehen
        - Ctrl+→: Eine Ebene reinziehen
        - Enter: Bearbeiten
        - Del: Löschen
        - F2: Bearbeiten (Windows-Standard)
        - Space: Auf-/Zuklappen
        """
        key = event.key()
        modifiers = event.modifiers()
        
        # Aktuelle Auswahl aktualisieren
        current = self.tree.currentItem()
        if current:
            self.current_item = current
        
        # Ctrl+Pfeiltasten für Verschieben
        if modifiers == Qt.ControlModifier:
            if not self.current_item:
                QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen.')
                return
                
            if key == Qt.Key_Up:
                self.move_up()
                return
            elif key == Qt.Key_Down:
                self.move_down()
                return
            elif key == Qt.Key_Left:
                self.move_out()
                return
            elif key == Qt.Key_Right:
                self.move_in()
                return
        
        # Normale Tasten
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            if self.current_item:
                self.edit_entry()
            return
        elif key == Qt.Key_F2:
            if self.current_item:
                self.edit_entry()
            return
        elif key == Qt.Key_Delete:
            if self.current_item:
                self.delete_entry()
            return
        elif key == Qt.Key_Space:
            if self.current_item:
                # Tree-Item auf-/zuklappen
                if self.current_item.isExpanded():
                    self.current_item.setExpanded(False)
                else:
                    self.current_item.setExpanded(True)
            return
            
        # Normale Navigation (↑/↓) an den Tree weiterleiten
        super(QTreeWidget, self.tree).keyPressEvent(event)
        
        # Nach Navigation: current_item aktualisieren
        new_current = self.tree.currentItem()
        if new_current:
            try:
                # Sicherheitsprüfung
                item_text = new_current.text(0)
                self.current_item = new_current
                logger.debug(f"🎯 Navigation zu: {item_text}")
            except RuntimeError as e:
                logger.error(f"❌ Navigation-Item bereits gelöscht: {e}")
                self.current_item = None

    def move_up(self):
        """Verschiebt den ausgewählten Eintrag nach oben."""
        if not self._validate_current_item():
            QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen.')
            return
            
        try:
            # Aktuellen Text für Logging speichern
            item_text = self.current_item.text(0)
            
            parent = self.current_item.parent()
            if parent:
                # Item in Untermenü
                index = parent.indexOfChild(self.current_item)
                if index > 0:
                    # Item entfernen und neu einfügen
                    taken_item = parent.takeChild(index)
                    parent.insertChild(index - 1, taken_item)
                    
                    # Fokus und Selektion wiederherstellen
                    self.tree.setCurrentItem(taken_item)
                    self.current_item = taken_item
                    taken_item.setSelected(True)
                    
                    logger.info(f"🔄 Item '{item_text}' nach oben verschoben")
                else:
                    QMessageBox.information(self, 'Info', 'Eintrag ist bereits ganz oben.')
            else:
                # Top-level Item
                index = self.tree.indexOfTopLevelItem(self.current_item)
                if index > 0:
                    # Item entfernen und neu einfügen
                    taken_item = self.tree.takeTopLevelItem(index)
                    self.tree.insertTopLevelItem(index - 1, taken_item)
                    
                    # Fokus und Selektion wiederherstellen
                    self.tree.setCurrentItem(taken_item)
                    self.current_item = taken_item
                    taken_item.setSelected(True)
                    
                    logger.info(f"🔄 Top-Level Item '{item_text}' nach oben verschoben")
                else:
                    QMessageBox.information(self, 'Info', 'Eintrag ist bereits ganz oben.')
                    
            # Tree-Update erzwingen
            self.tree.update()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verschieben nach oben: {e}")
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Verschieben: {str(e)}')

    def move_down(self):
        """Verschiebt den ausgewählten Eintrag nach unten."""
        if not self._validate_current_item():
            QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen.')
            return
            
        try:
            # Aktuellen Text für Logging speichern
            item_text = self.current_item.text(0)
            
            parent = self.current_item.parent()
            if parent:
                # Item in Untermenü
                index = parent.indexOfChild(self.current_item)
                if index < parent.childCount() - 1:
                    # Item entfernen und neu einfügen
                    taken_item = parent.takeChild(index)
                    parent.insertChild(index + 1, taken_item)
                    
                    # Fokus und Selektion wiederherstellen
                    self.tree.setCurrentItem(taken_item)
                    self.current_item = taken_item
                    taken_item.setSelected(True)
                    
                    logger.info(f"🔄 Item '{item_text}' nach unten verschoben")
                else:
                    QMessageBox.information(self, 'Info', 'Eintrag ist bereits ganz unten.')
            else:
                # Top-level Item
                index = self.tree.indexOfTopLevelItem(self.current_item)
                if index < self.tree.topLevelItemCount() - 1:
                    # Item entfernen und neu einfügen
                    taken_item = self.tree.takeTopLevelItem(index)
                    self.tree.insertTopLevelItem(index + 1, taken_item)
                    
                    # Fokus und Selektion wiederherstellen
                    self.tree.setCurrentItem(taken_item)
                    self.current_item = taken_item
                    taken_item.setSelected(True)
                    
                    logger.info(f"🔄 Top-Level Item '{item_text}' nach unten verschoben")
                else:
                    QMessageBox.information(self, 'Info', 'Eintrag ist bereits ganz unten.')
                    
            # Tree-Update erzwingen
            self.tree.update()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verschieben nach unten: {e}")
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Verschieben: {str(e)}')

    def move_out(self):
        """Zieht den ausgewählten Eintrag eine Ebene nach außen."""
        if not self._validate_current_item():
            QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen.')
            return
            
        try:
            # Aktuellen Text für Logging speichern
            item_text = self.current_item.text(0)
            
            parent = self.current_item.parent()
            if not parent:
                QMessageBox.information(self, 'Info', 'Top-Level-Einträge können nicht weiter nach außen gezogen werden.')
                return
                
            grandparent = parent.parent()
            
            # Item aus der aktuellen Ebene entfernen
            taken_item = parent.takeChild(parent.indexOfChild(self.current_item))
            
            if grandparent:
                # Einfügen nach dem Parent in der Großeltern-Ebene
                grandparent_index = grandparent.indexOfChild(parent)
                grandparent.insertChild(grandparent_index + 1, taken_item)
            else:
                # Einfügen nach dem Parent auf Top-Level
                parent_index = self.tree.indexOfTopLevelItem(parent)
                self.tree.insertTopLevelItem(parent_index + 1, taken_item)
            
            # Fokus und Selektion wiederherstellen
            self.tree.setCurrentItem(taken_item)
            self.current_item = taken_item
            taken_item.setSelected(True)
            
            # full_path aktualisieren
            self._update_full_paths()
            
            # Tree-Update erzwingen
            self.tree.update()
            
            logger.info(f"🔄 Item '{item_text}' eine Ebene nach außen gezogen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rausziehen: {e}")
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Rausziehen: {str(e)}')
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Rausziehen: {str(e)}')

    def move_in(self):
        """Zieht den ausgewählten Eintrag eine Ebene nach innen (als Child des vorherigen Items)."""
        if not self._validate_current_item():
            QMessageBox.information(self, 'Hinweis', 'Bitte einen Menüpunkt auswählen.')
            return
            
        try:
            # Aktuellen Text für Logging speichern
            item_text = self.current_item.text(0)
            
            parent = self.current_item.parent()
            current_index = 0
            
            if parent:
                current_index = parent.indexOfChild(self.current_item)
                if current_index == 0:
                    QMessageBox.information(self, 'Info', 'Kein vorheriges Geschwister-Element vorhanden.')
                    return
                target_sibling = parent.child(current_index - 1)
            else:
                current_index = self.tree.indexOfTopLevelItem(self.current_item)
                if current_index == 0:
                    QMessageBox.information(self, 'Info', 'Kein vorheriges Top-Level-Element vorhanden.')
                    return
                target_sibling = self.tree.topLevelItem(current_index - 1)
            
            # Item aus der aktuellen Ebene entfernen
            if parent:
                taken_item = parent.takeChild(current_index)
            else:
                taken_item = self.tree.takeTopLevelItem(current_index)
            
            # Als Child des vorherigen Elements hinzufügen
            target_sibling.addChild(taken_item)
            target_sibling.setExpanded(True)
            
            # Fokus und Selektion wiederherstellen
            self.tree.setCurrentItem(taken_item)
            self.current_item = taken_item
            taken_item.setSelected(True)
            
            # full_path aktualisieren
            self._update_full_paths()
            
            # Tree-Update erzwingen
            self.tree.update()
            
            logger.info(f"🔄 Item '{item_text}' als Child von '{target_sibling.text(0)}' eingefügt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Reinziehen: {e}")
            QMessageBox.critical(self, 'Fehler', f'Fehler beim Reinziehen: {str(e)}')

    def _update_full_paths(self):
        """Aktualisiert die full_path Attribute nach Verschiebungen."""
        def update_item(item, path_prefix=""):
            current_path = f"{path_prefix}.{item.text(0)}" if path_prefix else item.text(0)
            item.full_path = current_path
            
            for i in range(item.childCount()):
                update_item(item.child(i), current_path)
        
        # Aktualisiere alle Top-Level Items
        for i in range(self.tree.topLevelItemCount()):
            update_item(self.tree.topLevelItem(i))

    def _sync_structure(self):
        """Synchronisiert die Baumstruktur mit dem Modell."""
        section = self.menu_instance.menu_section(self.menu_type)
        section.clear()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            self._sync_item(top, section)

    def _sync_item(self, item, parent_dict):
        """Rekursive Synchronisation eines Items."""
        key = item.text(0)
        if item.childCount() == 0:
            parent_dict[key] = item.val
        else:
            parent_dict[key] = {}
            for i in range(item.childCount()):
                child = item.child(i)
                self._sync_item(child, parent_dict[key])