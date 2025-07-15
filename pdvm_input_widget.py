# pdvm_input_widget.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QMessageBox, QSizePolicy, QSpacerItem, QDialog,
    QDialogButtonBox, QFormLayout, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from pdvm_input_manager import PdvmInputManager, FieldMeta
from pd_datetime import Pdvm_DateTime
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_dropdown_picker import PdvmDropdownPicker
from pdvm_input_control_widget import PdvmInputControlWidget

import logging
import uuid
logger = logging.getLogger(__name__)

TEMPLATE_GUID = "11111111-1111-1111-1111-111111111111"  # Dummy-GUID für Template


class PdvmInputWidget(QWidget):
    backToSelection = pyqtSignal()
    def on_field_edited(self, meta, new_val, new_ab):
        """
        Wird nach dem Editieren eines Feldes vom FieldWidget aufgerufen.
        Führt einen vollständigen Refresh durch, damit alle Felder (inkl. GUID-/Stichtags-Änderungen) korrekt angezeigt werden.
        """
        logger.info(f"[PdvmInputWidget] on_field_edited: meta={getattr(meta, 'key', meta)}, new_val={new_val}, new_ab={new_ab}")
        self._on_refresh()
    selectionChanged = pyqtSignal()

    def __init__(self, call_data: dict, parent=None):
        super().__init__(parent)
        self._init_with_call_data(call_data)

    def _init_with_call_data(self, call_data: dict):
        from pdvm_instance_manager import PdvmInstanceManager
        from pdvm_central_datenbank import PdvmCentralDatenbank
        from pdvm_input_manager import PdvmInputManager
        
        # call_data als Attribut speichern für spätere Verwendung
        self.call_data = call_data
        
        self.st_inst = call_data['stichtag_inst']
        frame_guid = call_data.get("frame_guid")
        frm_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="framedaten", guid=frame_guid)
        raw_frame = frm_db.lesen() or {}
        metadaten = raw_frame.get("Metadaten", {})
        root_table = raw_frame.get("ROOT", {}).get("root_table")
        root_guid = call_data.get("root_guid")
        instance_manager = PdvmInstanceManager(root_table, root_guid, self.st_inst.PdvmDateTime, metadaten)
        self.manager = PdvmInputManager(call_data, instance_manager=instance_manager)
        self.manager.st_inst = self.st_inst
        logger.debug(f"🔹 PdvmInputWidget - PdvmInputManager gestartet mit call_data: {call_data}")
        self.width_ts_picker_only = 120
        self.width_ts_picker_full = 200
        self.build_fields_and_values()
        if hasattr(self, 'ts_display'):
            self.ts_display.setText(self.st_inst.FormTimeStamp)

    def reload_with_root_guid(self, root_guid):
        # Holt aktuelle call_data, setzt neue root_guid und lädt neu
        call_data = dict(self.manager.call_data)
        call_data['root_guid'] = root_guid
        self._init_with_call_data(call_data)

    def cleanup(self):
        """Deregistriere alle ControlObjects beim Manager"""
        if hasattr(self, 'controls') and hasattr(self, 'manager'):
            for control_data in self.controls.values():
                if 'control' in control_data:
                    self.manager.unregister_control_object(control_data['control'])

    def __del__(self):
        """Cleanup beim Zerstören des Widgets"""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during cleanup

    def build_fields_and_values(self):
        # Vor jedem Build: Stichtag im Manager synchronisieren
        self.manager.st_inst = self.st_inst
        if hasattr(self.manager, 'refresh_instances_for_stichtag'):
            self.manager.refresh_instances_for_stichtag()

        # --- Logging: Metadaten und Feldliste für Debug ---
        try:
            # Metadaten aus Manager extrahieren, falls möglich
            metadaten = getattr(self.manager, 'fields', {})
            logger.debug(f"[DEBUG] Aktuelle Metadaten-Keys: {list(metadaten.keys())}")
            for k, meta in metadaten.items():
                logger.debug(f"[DEBUG] FieldMeta: key={getattr(meta, 'key', None)}, type={getattr(meta, 'type', None)}, data_instance={getattr(meta, 'data_instance', None)}, abdatum={getattr(meta, 'abdatum', None)}")
        except Exception as e:
            logger.warning(f"[DEBUG] Fehler beim Logging der Metadaten: {e}")

        # Remove old layout tree (including main layout)
        old_layout = self.layout() if hasattr(self, 'layout') else None
        if old_layout is not None:
            QWidget().setLayout(old_layout)  # Detach from self
        self.controls = {}
        main = QVBoxLayout()
        main.setContentsMargins(20,20,20,20)
        main.setSpacing(10)

        # Button zum Wechsel in die Auswahl (View)
        btn_back = QPushButton("Zur Auswahl")
#        btn_back.setMinimumWidth(0)
#        btn_back.setMaximumWidth(600)  # Begrenze auf typische Framebreite
#        btn_back.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#        btn_back.setStyleSheet("font-size: 15px; font-weight: bold; padding: 8px 0;")
        btn_back.clicked.connect(self.backToSelection.emit)
        main.addWidget(btn_back)

        # Header (always present)
        header = QLabel(self.manager.header_text)
        header.setStyleSheet("font-size:18px; font-weight:bold;")
        main.addWidget(header, alignment=Qt.AlignLeft)

        # Stichtag + Input-Buttons (immer im InputFrame!)
        st_layout = QHBoxLayout()
        st_layout.addWidget(QLabel("Stichtag:"), alignment=Qt.AlignLeft)
        display_st = self.manager.display_st
        self.st_picker = PdvmDateTimePicker(
            self, self.st_inst,
            display = display_st,
            default_date=None
        )
        w = self.width_ts_picker_full if display_st=="all" else self.width_ts_picker_only
        self.st_picker.setFixedWidth(w)
        st_layout.addWidget(self.st_picker)
        btn_ref = QPushButton("Refresh")
        btn_ref.setFixedWidth(100)
        btn_ref.clicked.connect(self._on_refresh)
        st_layout.addWidget(btn_ref)
        btn_save = QPushButton("Speichern")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self._on_save)
        st_layout.addWidget(btn_save)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.close)
        st_layout.addWidget(btn_cancel)
        st_layout.addItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main.addLayout(st_layout)

        # Used Stichtag
        ts_layout = QHBoxLayout()
        lbl_ts = QLabel("Verwendeter Stichtag:")
        lbl_ts.setFixedWidth(self.manager.width_label or 150)
        ts_layout.addWidget(lbl_ts)
        self.ts_display = QLineEdit()
        self.ts_display.setEnabled(False)
        self.ts_display.setFixedWidth(125)
        ts_layout.addWidget(self.ts_display)
        ts_layout.addStretch()
        main.addLayout(ts_layout)

        # Scroll Area for fields
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.container = QWidget()
        self.form_layout = QVBoxLayout(self.container)
        self.form_layout.setContentsMargins(5,5,5,5)
        self.form_layout.setSpacing(15)
        self.form_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.container)
        main.addWidget(self.scroll, stretch=1)

        # Clear layout so no old widgets remain
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Debug: Which fields are shown?
        print(f"[DEBUG] Felder im InputFrame: {[meta.key for meta in self.manager.get_fields()]}", flush=True)

        # --- Always use fresh FieldMeta from manager, never mutate meta ---
        for meta in self.manager.get_fields():
            # Log the meta flags for debug
            print(f"[DEBUG] build_fields_and_values: key={meta.key} abdatum={getattr(meta, 'abdatum', None)} historical={getattr(meta, 'historical', None)}", flush=True)
            # Always fetch value and abdatum from the correct instance
            val, ab = self.manager.get_value(meta.key)
            # Always create a fresh ControlObject from the current meta
            control = self.manager.get_control_object(meta, value=val, abdatum=ab)
            # Registriere ControlObject beim Manager für ViewTable-Refresh
            self.manager.register_control_object(control)
            field_widget = PdvmInputControlWidget(control, parent=self)
            self.form_layout.addWidget(field_widget)
            self.controls[meta.key] = {"control": control, "main_ctl": field_widget, "field_widget": field_widget, "meta": meta, "data_instance": getattr(meta, 'data_instance', None)}

        main.addStretch()
        self.setLayout(main)
        # Nach Build: Verwendeter Stichtag immer aus Instanz anzeigen
        if hasattr(self, 'ts_display'):
            self.ts_display.setText(self.st_inst.FormTimeStamp)
        self.setLayout(main)

    def _load_values(self):
        # Anzeige immer aus der Instanz
        self.ts_display.setText(self.st_inst.FormTimeStamp)
        # Picker zeigt immer die Instanz
        self.st_picker.pdvm_datetime = self.st_inst
        self.st_picker.initial.PdvmDateTime = self.st_inst.PdvmDateTime
        print(f"[DEBUG] _load_values: st_inst.PdvmDateTime={self.st_inst.PdvmDateTime}, st_picker.pdvm_datetime={self.st_picker.pdvm_datetime.PdvmDateTime}, st_picker.initial={self.st_picker.initial.PdvmDateTime}")
        self.st_picker.update_display()
        for key, entry in self.controls.items():
            meta = entry["meta"]
            ctl = entry["main_ctl"]
            # Hole das ControlObject (mit Wert, Abdatum, Instanz etc.) zentral aus dem Manager
            control = self.manager.get_control_object(meta)
            # Setze das ControlObject im Widget neu (UI-Logik)
            entry["control"] = control
            # Aktualisiere das Feld-Widget mit dem neuen ControlObject
            if hasattr(ctl, "set_control_object"):
                ctl.set_control_object(control)
            # UI-Update je nach Typ
            if meta.type == "datetime":
                if hasattr(ctl, "update_display"):
                    ctl.update_display()
            elif isinstance(ctl, PdvmDropdownPicker):
                ctl.refresh_options(self.st_inst.PdvmDateTime)
                ctl.set_selected_key(control.value)
            elif meta.type == "dropdown" and isinstance(ctl, QLineEdit):
                display_val = entry["field_widget"]._get_dropdown_display(control.value)
                ctl.setText(display_val)
            elif isinstance(ctl, QLineEdit):
                ctl.setText(str(control.value))
            try:
                if "field_widget" in entry and hasattr(entry["field_widget"], "_update_abdatum_display"):
                    entry["field_widget"]._update_abdatum_display()
            except Exception as e:
                logger.warning(f"[PdvmInputWidget] Fehler beim Aktualisieren des Abdatums für key={key}: {e}")

    def _on_refresh(self):
        # Save schreibt direkt in die Instanz!
        self.st_picker.save()  # Wert wird direkt in self.st_inst geschrieben
        # Stichtag im Manager synchronisieren
        self.manager.st_inst = self.st_inst
        
        # **WICHTIG**: Neuen Stichtag in der Systemsteuerung speichern
        self._save_stichtag_to_systemsteuerung()
        
        # Nach Save: Anzeige immer aus Instanz aktualisieren
        if hasattr(self, 'ts_display'):
            self.ts_display.setText(self.st_inst.FormTimeStamp)
            
        # **NEUE EINHEITLICHE REFRESH-METHODE** (speichert Stichtag UND refresht alles)
        if hasattr(self.manager, 'unified_refresh'):
            self.manager.unified_refresh(skip_stichtag_save=False)  # False = wie Button-Refresh
        else:
            # Fallback zur alten Methode falls unified_refresh noch nicht existiert
            # Stichtagsgenaue Instanzen neu laden
            if hasattr(self.manager, 'refresh_instances_for_stichtag'):
                self.manager.refresh_instances_for_stichtag()
            
            # **WICHTIG**: Alle ControlObjects refreshen (inkl. Abdatum-Anzeige)
            if hasattr(self.manager, 'refresh_all_control_objects'):
                self.manager.refresh_all_control_objects()
            
        # Felder und Werte komplett wie bei Initialisierung neu aufbauen
        self.build_fields_and_values()

    def _on_new_guid(self, key):
        # Neue GUID generieren, Daten kopieren, GUID ersetzen, Instanzen und UI aktualisieren
        new_guid = str(uuid.uuid4())
        # Hole aktuelle Daten (Template)
        template_data, ab = self.manager.get_value(key)
        # Kopiere Datenstruktur (hier ggf. anpassen, falls tiefer kopiert werden muss)
        import copy
        new_data = copy.deepcopy(template_data)
        # Setze neue GUID
        self.manager.set_value(key, new_guid, ab)
        self.manager.refresh_instances()
        self._build_ui()
        self._load_values()

    def _on_save(self):
        # Validierung: Keine Speicherung unter Template-GUID
        for key, entry in self.controls.items():
            meta = entry["meta"]
            val, _ = self.manager.get_value(key)
            if meta.type == "viewtable" and str(val) == TEMPLATE_GUID:
                QMessageBox.warning(self, "Fehler", f"Feld '{meta.label}' ist noch ein Template (000...-GUID). Bitte zuerst 'Neu' klicken.")
                return
        # Speichere alle Instanzen, die in den Controls referenziert sind
        already_saved = set()
        for entry in self.controls.values():
            data_instance = entry.get("data_instance")
            if data_instance and id(data_instance) not in already_saved:
                data_instance.save_values()
                already_saved.add(id(data_instance))
        
        # ViewTable-Refresh nach Save durchführen
        if hasattr(self.manager, 'unified_refresh'):
            self.manager.unified_refresh(skip_stichtag_save=True, rebuild_ui_callback=self.build_fields_and_values)
        elif hasattr(self.manager, 'force_viewtable_refresh'):
            self.manager.force_viewtable_refresh()
        
        QMessageBox.information(self, "Erfolg", "Daten erfolgreich gespeichert.")

    def show_history(self, key):
        """Öffnet den HistoryDialog für das Feld key und übergibt das passende FieldWidget für Dropdown-Übersetzung."""
        entry = self.controls.get(key)
        if not entry:
            return
        meta = entry["meta"]
        field_widget = entry["field_widget"]
        # Hole alle historischen Werte (Liste von Tupeln (val, ab))
        if hasattr(self.manager, 'get_history_values'):
            values = self.manager.get_history_values(key)
        else:
            # Fallback: Hole alle Werte aus der Instanz
            grp, fld = meta.key.split('_', 2)[1:]
            values = []
            if hasattr(entry["data_inst"], 'get_value_all'):
                history_dict = entry["data_inst"].get_value_all(grp, fld)
                values = [(v, ab) for ab, v in history_dict.items()]
        dlg = HistoryDialog(self, "Historie", meta, values, field_widget=field_widget)
        dlg.exec_()

    # History, edit and help dialogs unchanged
    def _on_edit(self, key: str):
        meta = self.controls[key]['meta']
        val, ab = self.manager.get_value(key)
        dlg = EditFieldDialog(
            self, meta, val, ab,
            value_inst=self.controls[key].get('value_inst'),
            ab_value=ab
        )
        if dlg.exec_() == QDialog.Accepted:
            new_val, new_ab = dlg.get_results()
            ab_to_use = self.manager.get_abdatum_for_field(key, new_ab)
            # Für datetime: Wert aus Picker explizit in value_inst schreiben
            if meta.type == "datetime" and "value_inst" in self.controls[key]:
                self.controls[key]["value_inst"].PdvmDateTime = dlg.value_ctl.get_pdvm_datetime().PdvmDateTime
                new_val = self.controls[key]["value_inst"].PdvmDateTime
                print(f"[DEBUG] Nach Bearbeiten: value_inst id={id(self.controls[key]['value_inst'])} Wert={self.controls[key]['value_inst'].PdvmDateTime}")
            # Kein ab_inst mehr, ab_to_use ist direkt das Datum
            self.manager.set_value(key, new_val, ab_to_use)
            # Robustes Instanz-Update für viewtable (korrekte Tabelle/Gruppe aus Verweis holen)
            # Keine Spezialbehandlung für viewtable, alles wie Textfeld
            # Debug: Nach set_value
            if meta.type == "datetime" and "value_inst" in self.controls[key]:
                print(f"[DEBUG] Nach set_value: value_inst id={id(self.controls[key]['value_inst'])} Wert={self.controls[key]['value_inst'].PdvmDateTime}")
            self._load_values()
            print(f"[DEBUG] Nach _load_values: main_ctl={self.controls[key]['main_ctl'].text() if hasattr(self.controls[key]['main_ctl'], 'text') else self.controls[key]['main_ctl']}")

    def __init_ui__(self):
        # ...existing code...
        self._setup_dropdown()
        self._setup_helptext()
        # ...existing code...

    def _setup_dropdown(self):
        """Dropdown-Optionen direkt über Manager holen."""
        if self.meta.type == "dropdown":
            self.dropdown_options = self.manager.get_dropdown_options(self.meta)
            self.dropdown_keys = [o.get("key") for o in self.dropdown_options]
            self.dropdown_texts = [self.manager.translate_dropdown_value(self.meta, o.get("key")) for o in self.dropdown_options]
        else:
            self.dropdown_options = []
            self.dropdown_keys = []
            self.dropdown_texts = []

    def _setup_helptext(self):
        """Hilfetext direkt über Manager holen."""
        self.help_text = self.manager.get_help_text(self.meta)

    def _update_dropdown(self):
        """Dropdown-Optionen neu laden (z.B. nach Änderung)."""
        self._setup_dropdown()
        # ...bestehende Logik zur Aktualisierung der UI...

    def _update_helptext(self):
        self._setup_helptext()
        # ...bestehende Logik zur Aktualisierung der UI...

    def _save_stichtag_to_systemsteuerung(self):
        """
        Speichert den aktuellen Stichtag (self.st_inst.PdvmDateTime) in der Systemsteuerung.
        Dies stellt sicher, dass der Stichtag beim nächsten Programmstart wieder geladen wird.
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # user_guid aus call_data holen
            user_guid = self.call_data.get('user_guid')
            frame_guid = self.call_data.get('frame_guid')
            
            if not user_guid:
                logger.warning("[_save_stichtag_to_systemsteuerung] Keine user_guid in call_data gefunden!")
                return
                
            # Systemsteuerung-Datenbank öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=user_guid
            )
            
            # Aktuelle Daten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(user_guid, {})
            frame_data = raw_data.get(frame_guid, {}) if frame_guid else {}
            
            # Neuen Stichtag setzen
            new_stichtag = self.st_inst.PdvmDateTime
            user_data['stichtag'] = new_stichtag
            
            logger.info(f"🔹 Speichere neuen Stichtag {new_stichtag} ({self.st_inst.FormTimeStamp}) in Systemsteuerung für user_guid={user_guid}")
            
            # Daten zurückspeichern
            sys_db.speichern(user_guid, {
                user_guid: user_data,
                frame_guid: frame_data
            })
            
            logger.debug(f"🔹 Stichtag erfolgreich in Systemsteuerung gespeichert")
            
        except Exception as e:
            logger.error(f"[_save_stichtag_to_systemsteuerung] Fehler beim Speichern des Stichtags: {e}")

    def complete_rebuild_after_edit(self):
        """
        Vollständige Neuinitialisierung nach GUID-Änderungen über Edit.
        Macht dasselbe wie bei einem Neuaufruf des Dialogs.
        """
        logger.debug("[PdvmInputWidget] complete_rebuild_after_edit: Starte vollständige Neuinitialisierung")
        
        # Debug: Zeige aktuelle ViewTable-GUIDs vor dem Refresh
        self._debug_viewtable_guids("VOR Refresh")
        
        # Alle Instanzen neu laden
        if hasattr(self.manager, 'refresh_instances'):
            logger.debug("[PdvmInputWidget] complete_rebuild_after_edit: Rufe refresh_instances() auf")
            self.manager.refresh_instances()
        else:
            logger.warning("[PdvmInputWidget] complete_rebuild_after_edit: refresh_instances() nicht verfügbar!")
        
        # Debug: Zeige ViewTable-GUIDs nach Instanz-Refresh
        self._debug_viewtable_guids("NACH refresh_instances")
        
        # UI komplett neu aufbauen
        logger.debug("[PdvmInputWidget] complete_rebuild_after_edit: Rufe build_fields_and_values() auf")
        self.build_fields_and_values()
        
        # Debug: Zeige ViewTable-GUIDs nach UI-Neuaufbau
        self._debug_viewtable_guids("NACH build_fields_and_values")
        
        logger.debug("[PdvmInputWidget] complete_rebuild_after_edit: Vollständige Neuinitialisierung abgeschlossen")

    def _debug_viewtable_guids(self, phase):
        """Debug-Methode um ViewTable-GUIDs zu protokollieren"""
        try:
            logger.debug(f"[DEBUG ViewTable GUIDs {phase}]")
            for key, entry in getattr(self, 'controls', {}).items():
                if 'meta' in entry:
                    meta = entry['meta']
                    current_value, _ = self.manager.get_value(key)
                    data_instance = entry.get('data_instance')
                    instance_guid = getattr(data_instance, 'guid', 'keine Instanz') if data_instance else 'keine Instanz'
                    
                    # Debug für ALLE Felder, nicht nur ViewTable-Typ
                    if hasattr(meta, 'type'):
                        logger.debug(f"[DEBUG] {key} (Typ: {meta.type}): Wert={current_value}, Instanz-GUID={instance_guid}")
                    else:
                        logger.debug(f"[DEBUG] {key} (Kein Typ): Wert={current_value}, Instanz-GUID={instance_guid}")
        except Exception as e:
            logger.debug(f"[DEBUG] Fehler beim ViewTable-GUID-Debug: {e}")

class EditFieldDialog(QDialog):
    def __init__(self, parent, control):
        super().__init__(parent)
        self.control = control
        self.meta = control.meta
        self.current_value = control.display_value
        self.current_ab = control.abdatum_inst.PdvmDateTime if control.abdatum_inst else 1001.0
        self.value_inst = control.value_inst
        self.manager = parent.manager
        self.setWindowTitle(f"{self.meta.label} bearbeiten")
        self.setModal(True)
        form = QFormLayout(self)

        # Für ViewTable-Felder: Auswahl-Button über der Eingabezeile
        field_type = getattr(self.meta, 'type', 'text')
        if field_type == 'viewtable':
            # Auswahl-Button über die ganze Breite
            auswahl_btn = QPushButton("Auswahl")
            auswahl_btn.clicked.connect(self._on_auswahl_clicked)
            form.addRow(auswahl_btn)

        # — Hauptfeld je nach Typ erstellen —
        field_type = getattr(self.meta, 'type', 'text')
        
        if field_type == 'datetime':
            # Für DateTime-Felder: PdvmDateTimePicker verwenden
            display_val = getattr(self.meta, 'display_val', 'all')  # Aus Framedaten
            self.value_edit = PdvmDateTimePicker(
                self, 
                control.value_inst,  # Die DateTime-Instanz mit dem aktuellen Wert
                display=display_val
            )
            self.value_edit.setMinimumWidth(300)
            print(f"[DEBUG] DateTime-Feld '{self.meta.key}': display_val={display_val}, value_inst={control.value_inst}", flush=True)
        elif field_type == 'dropdown':
            # Für Dropdown-Felder: QComboBox mit Optionen befüllen
            from PyQt5.QtWidgets import QComboBox
            self.value_edit = QComboBox()
            self.value_edit.setMinimumWidth(300)
            
            # Dropdown-Optionen vom Manager holen
            options = self.manager.get_dropdown_options(self.meta)
            language = getattr(self.manager, 'language', 'de')
            
            print(f"[DEBUG] Dropdown-Feld '{self.meta.key}': Verfügbare Optionen:", flush=True)
            for i, option in enumerate(options):
                key = option.get('key', '')
                display_text = option.get(language, key) or key
                print(f"[DEBUG]   Option {i}: key='{key}', display='{display_text}'", flush=True)
                self.value_edit.addItem(display_text, key)  # Display-Text sichtbar, Key als Data
            
            # Debug: Alle verfügbaren Werte loggen
            print(f"[DEBUG] Dropdown '{self.meta.key}': control.value_inst='{control.value_inst}' (type={type(control.value_inst)})", flush=True)
            print(f"[DEBUG] Dropdown '{self.meta.key}': self.current_value='{self.current_value}' (type={type(self.current_value)})", flush=True)
            print(f"[DEBUG] Dropdown '{self.meta.key}': control.display_value='{control.display_value}' (type={type(control.display_value)})", flush=True)
            
            # Verschiedene Ansätze zum Finden des aktuellen Wertes
            current_key = None
            current_index = -1
            
            # Ansatz 1: control.value_inst verwenden (sollte der Raw-Key sein)
            if control.value_inst:
                current_key = str(control.value_inst)
                current_index = self.value_edit.findData(current_key)
                print(f"[DEBUG] Dropdown '{self.meta.key}': Ansatz 1 - Key='{current_key}', Index={current_index}", flush=True)
            
            # Ansatz 2: Falls nicht gefunden, versuche current_value als Key
            if current_index < 0 and self.current_value:
                current_key = str(self.current_value)
                current_index = self.value_edit.findData(current_key)
                print(f"[DEBUG] Dropdown '{self.meta.key}': Ansatz 2 - Key='{current_key}', Index={current_index}", flush=True)
            
            # Ansatz 3: Falls immer noch nicht gefunden, suche über Display-Text
            if current_index < 0 and self.current_value:
                current_index = self.value_edit.findText(str(self.current_value))
                print(f"[DEBUG] Dropdown '{self.meta.key}': Ansatz 3 - Display-Text='{self.current_value}', Index={current_index}", flush=True)
            
            # Auswahl setzen wenn gefunden
            if current_index >= 0:
                self.value_edit.setCurrentIndex(current_index)
                print(f"[DEBUG] Dropdown '{self.meta.key}': Index {current_index} ausgewählt", flush=True)
            else:
                print(f"[DEBUG] Dropdown '{self.meta.key}': Kein passender Wert gefunden!", flush=True)
            
            print(f"[DEBUG] Dropdown-Feld '{self.meta.key}': {len(options)} Optionen geladen, finaler Index={current_index}", flush=True)
        else:
            # Für alle anderen Felder: QLineEdit
            self.value_edit = QLineEdit()
            self.value_edit.setText(str(self.current_value) if self.current_value else "")
            self.value_edit.setMinimumWidth(300)
            if field_type == 'viewtable':
                self.value_edit.setPlaceholderText("GUID eingeben oder über 'Auswahl' wählen")
                
        form.addRow(self.meta.label + ":", self.value_edit)

        # — Ab-Datum-Widget - Korrigierte Logik —
        # Prüfen ob das Feld historical ist UND abdatum_inst existiert
        has_abdatum_inst = self.control.abdatum_inst is not None
        is_historical = getattr(self.meta, 'historical', False)
        has_abdatum_meta = getattr(self.meta, 'abdatum', False)
        
        # AbDatum anzeigen NUR wenn abdatum=true in Framedaten UND Instanz vorhanden
        show_abdatum = has_abdatum_meta and has_abdatum_inst
        
        # Debug-Ausgabe für Abdatum-Logik
        print(f"[DEBUG] Field '{self.meta.key}': has_abdatum_inst={has_abdatum_inst}, is_historical={is_historical}, has_abdatum_meta={has_abdatum_meta}, show_abdatum={show_abdatum}", flush=True)
        
        if show_abdatum:
            # Die AbDatum-Instanz direkt an den DateTimePicker übergeben
            self.ab_picker = PdvmDateTimePicker(self, self.control.abdatum_inst)
            self.ab_picker.update_display()
            form.addRow("Ab-Datum:", self.ab_picker)
        else:
            self.ab_picker = None

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        form.addRow(btn_box)
    
    def _on_auswahl_clicked(self):
        """Öffnet den Auswahl-Dialog für ViewTable-Felder."""
        try:
            from pdvm_search_list_widget_dialog import PdvmSearchListWidgetDialog
            
            # ViewTable-GUID aus den Metadaten holen
            viewtable_guid = getattr(self.meta, 'viewtable_guid', None)
            if not viewtable_guid:
                logger.warning(f"[EditFieldDialog] Keine ViewTable-GUID für Feld {self.meta.label}")
                return
            
            logger.debug(f"[EditFieldDialog] Öffne Auswahl-Dialog für ViewTable-GUID: {viewtable_guid}")
            
            # call_data für den Dialog vorbereiten
            manager = getattr(self.control, 'manager', None)
            call_data = getattr(manager, 'call_data', {}) if manager else {}
            
            # Such-Dialog öffnen - korrekte Parameter verwenden
            dlg = PdvmSearchListWidgetDialog(
                parent=self,
                view_guid=viewtable_guid,  # Korrekt: view_guid statt manager
                user_guid=call_data.get('user_guid'),
                frame_guid=call_data.get('frame_guid'),
                call_data=call_data
            )
            
            if dlg.exec_() == QDialog.Accepted:
                selected_guid = dlg.get_selected_guid()
                if selected_guid:
                    self.value_edit.setText(selected_guid)
                    logger.debug(f"[EditFieldDialog] Ausgewählte GUID: {selected_guid}")
                    
        except Exception as e:
            logger.exception(f"[EditFieldDialog] Fehler beim Öffnen des Auswahl-Dialogs: {e}")

    def get_results(self):
        # Wert extrahieren je nach Feldtyp
        field_type = getattr(self.meta, 'type', 'text')
        
        if field_type == 'datetime':
            # Für DateTime-Felder: PdvmDateTimePicker.save() aufrufen
            if hasattr(self.value_edit, 'save'):
                self.value_edit.save()  # Schreibt in die value_inst
                new_val = self.control.value_inst.PdvmDateTime  # Bereits als Float
                print(f"[DEBUG] DateTime get_results: new_val={new_val}", flush=True)
            else:
                new_val = self.current_value
        elif field_type == 'dropdown':
            # Für Dropdown-Felder: Key aus ComboBox extrahieren
            from PyQt5.QtWidgets import QComboBox
            if isinstance(self.value_edit, QComboBox):
                current_index = self.value_edit.currentIndex()
                new_val = self.value_edit.itemData(current_index)  # Key zurückgeben
                display_text = self.value_edit.currentText()
                print(f"[DEBUG] Dropdown get_results: key='{new_val}', display='{display_text}', index={current_index}", flush=True)
            else:
                new_val = self.value_edit.text()
        else:
            # Für andere Felder: Text aus QLineEdit
            new_val = self.value_edit.text()
            if self.value_inst:
                self.value_inst.Value = new_val
        
        # Ab-Datum verarbeiten wenn AbDatum-Picker vorhanden
        if hasattr(self, 'ab_picker') and self.ab_picker and self.control.abdatum_inst:
            # PdvmDateTimePicker.save() schreibt direkt in die übergebene Instanz
            self.ab_picker.save()
            # Verwende die PdvmDateTime Eigenschaft (bereits als Float)
            new_ab = self.control.abdatum_inst.PdvmDateTime
        else:
            # Fallback: current_ab ist bereits ein Float oder 1001.0
            new_ab = self.current_ab
        
        logger.debug(f"[EditFieldDialog.get_results] Rückgabe: new_val={new_val} (type={type(new_val)}), new_ab={new_ab} (type={type(new_ab)})")
        return new_val, new_ab

class HistoryDialog(QDialog):
    def __init__(self, parent, titel: str, meta: FieldMeta, values: list, field_widget=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.meta = meta
        self.key  = meta.key
        self.values = values  # Liste von (wert, ab)
        self.field_widget = field_widget  # Zentrale Referenz für Dropdown-Übersetzung

        if not values:
            QMessageBox.information(self, "Keine Historie", "Keine historischen Daten vorhanden.")
            self.reject()
            return

        self.setWindowTitle(f"{titel}: {meta.label}")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(QLabel("<b>Gültig-ab-Datum/Zeit</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Wert</b>"), 0, 1)
        grid.addWidget(QWidget(), 0, 2)

        # wenn es mehr als einen Eintrag gibt, darf jeder gelöscht werden
        deletable = len(values) > 1

        for row, (val, ab) in enumerate(values, start=1):
            dt = Pdvm_DateTime("DEU")
            dt.PdvmDateTime = float(ab)
            lbl_ab = QLabel(dt.FormTimeStamp)
            grid.addWidget(lbl_ab, row, 0)

            lbl_val = QLabel(self._format_value(val))
            grid.addWidget(lbl_val, row, 1)

            if deletable:
                btn_del = QPushButton("✕")
                btn_del.setFixedWidth(24)
                btn_del.setStyleSheet("color:red; font-weight:bold;")
                btn_del.clicked.connect(lambda _, a=ab: self._on_delete_entry(a))
                grid.addWidget(btn_del, row, 2)

        layout.addLayout(grid)

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def _format_value(self, val):
        # Dropdown-Übersetzung immer über FieldWidget, falls vorhanden
        if self.meta.type == "datetime":
            try:
                dt = Pdvm_DateTime("DEU")
                dt.PdvmDateTime = float(val)
                return dt.FormTimeStamp
            except:
                return str(val)
        if self.meta.type == "dropdown":
            if self.field_widget and hasattr(self.field_widget, '_get_dropdown_display'):
                return self.field_widget._get_dropdown_display(val)
            # Fallback: wie bisher
            key = str(val)
            for entry in self.meta.dropdown_options or []:
                if entry.get("key") == key:
                    return entry.get(self.parent_widget.manager.language) or key
            return key
        return str(val)

    def _on_delete_entry(self, ab: float):
        # Sicherheitsabfrage
        dt = Pdvm_DateTime("DEU")
        dt.PdvmDateTime = float(ab)
        stamp = dt.FormTimeStamp
        reply = QMessageBox.question(
            self,
            "Eintrag löschen?",
            f"Eintrag ab {stamp} wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Löschen im Manager
        self.parent_widget.manager.delete_value(self.key, ab)
        # Dialog schließen und UI neu laden
        self.accept()
        self.parent_widget._load_values()
