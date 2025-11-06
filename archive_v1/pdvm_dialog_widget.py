 # pdvm_dialog_widget.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QGroupBox, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt
from pdvm_input_widget import PdvmInputWidget
# from pdvm_search_list_widget import PdvmSearchListWidget  # ENTFERNT - nicht mehr benötigt
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils
# from pdvm_view_manager import PdvmViewManager  # ENTFERNT - nicht mehr benötigt
import logging

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
TEMPLATE_GUID = "00000000-0000-0000-0000-000000000000"


class PdvmDialogManager:
    def __init__(self, base_call: dict):
        logger.info("🔹 PdvmDialogManager gestartet")
        # Basis-Call-Daten
        self.base_call  = base_call.copy()
        self.user_guid  = self.base_call['user_guid']
        self.frame_guid = self.base_call['frame_guid']
        self.mode       = self.base_call.get('mode', 0)
        # Stichtag-Instanz erstellen und aus Systemsteuerung laden
        self.st_inst = Pdvm_DateTime("DEU")
        # -------------------------------------------------------------
        #  Systemsteuerung laden und user_data / frame_data extrahieren
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=self.user_guid
        )
        raw_data = sys_db.lesen() or {}
        self.user_data  = raw_data.get(self.user_guid, {})
        self.frame_data = raw_data.get(self.frame_guid, {})

        # 4) Defaults in user_data setzen – nur speichern, wenn noch kein Eintrag da war
        now = PdvmDateTimeUtils.PdvmDateTimeNow()
        if 'stichtag' not in self.user_data:
            # Erster Lauf: lege Tagesdatum als Stichtag fest
            self.st_inst.PdvmDateTime = now
            self.user_data['stichtag'] = now
            # Persistiere hier das neue Feld
            sys_db.speichern(self.user_guid, {
                self.user_guid: self.user_data,
                self.frame_guid: self.frame_data
            })
        else:
            # Bereits ein Stichtag gespeichert → lade ihn
            self.st_inst.PdvmDateTime = float(self.user_data['stichtag'])

        # Sprache defaulten, ohne sofort zu speichern
        self.user_data.setdefault('language', self.base_call.get('language','de'))

        # Frame-Daten defaults (ohne Speichern)
        self.frame_data.setdefault('last_root_guid', SYSTEM_USER_ID)

        # Persistieren
        sys_db.speichern(self.user_guid, {
            self.user_guid: self.user_data,
            self.frame_guid: self.frame_data
        })

        # view_guid aus framedaten
        frm = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="framedaten",
            guid=self.frame_guid
        )
        # view_guid holen und ggf. Dict bereinigen
        vg = frm.get_value('ROOT', 'view_guid')
        if isinstance(vg, dict):
            self.view_guid = vg.get('wert')
        else:
            self.view_guid = vg
        logger.debug(f"🔹 im PdvmDialogManager view_guid = {self.view_guid}" )
        if not self.view_guid:
            raise ValueError("🔴 view_guid in framedaten fehlt")

        # Entfernt: Kein zentraler InputManager mehr! Das InputWidget erzeugt seinen eigenen Manager.

    def get_call(self, root_guid=None, stichtag_inst=None):
        # Wenn neue Inst übergeben, speichere sie
        if stichtag_inst:
            self.save(stichtag_inst=stichtag_inst)

        return {
            'user_guid':     self.user_guid,
            'view_guid':     self.view_guid,
            'frame_guid':    self.frame_guid,
            'mode':          self.mode,
            'root_guid':     root_guid or self.frame_data.get('last_root_guid'),
            'stichtag_inst': self.st_inst,
            'language':      self.user_data['language'],
        }

    def save(self, root_guid=None, stichtag_inst=None, language=None):
        # Frame GUID aktualisieren
        if root_guid is not None:
            self.frame_data['last_root_guid'] = root_guid
        # Stichtag-Inst aktualisieren
        if stichtag_inst:
            self.st_inst = stichtag_inst
            self.user_data['stichtag'] = self.st_inst.PdvmDateTime
        # Sprache aktualisieren
        if language:
            self.user_data['language'] = language

        # Persistiere beides
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=self.user_guid
        )
        db.speichern(self.user_guid, {
            self.user_guid: self.user_data,
            self.frame_guid: self.frame_data
        })
        logger.debug(f"🔹 Nach save(): systemsteuerung[{self.user_guid}] = {db.lesen().get(self.user_guid)}")

    def clear(self):
        self.frame_data.clear()
        PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=self.user_guid
        ).speichern(self.user_guid, {
            self.user_guid: self.user_data
        })


class PdvmDialogWidget(QWidget):
    def on_field_edited(self, meta, new_val, new_ab):
        """
        Wird von PdvmInputWidget oder PdvmFieldWidget aufgerufen, wenn ein Feld editiert oder ein History-Eintrag gelöscht wurde.
        Führt einen vollständigen Refresh durch (wie Refresh-Button).
        """
        logger.info(f"[PdvmDialogWidget] on_field_edited: meta={getattr(meta, 'key', meta)}, new_val={new_val}, new_ab={new_ab}")
        self._on_refresh()
    def __init__(self, call_data: dict, parent=None):
        super().__init__(parent)
        logger.info("🔹 PdvmDialogWidget gestartet")
        self.manager      = PdvmDialogManager(call_data)
        self.layout       = QVBoxLayout(self)
        self.search       = None
        self.view_mgr     = None
        self.input_widget = None
        self.input_frame  = None
        self.view_frame   = None
        self._init_ui()

    def _init_ui(self):
        # Clear layout
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Aktionstasten NUR für die View (Suchliste)
        frame_data = self.manager.frame_data
        self.btn_frame = QGroupBox("Aktionen")
        self.btn_layout = QHBoxLayout(self.btn_frame)
        self.btn_select = QPushButton("Auswahl übernehmen")
        self.btn_select.clicked.connect(self._trigger_selection)
        self.btn_layout.addWidget(self.btn_select)
        self.btn_new = QPushButton("Neuanlage")
        self.btn_new.clicked.connect(self._on_create_new)
        self.btn_layout.addWidget(self.btn_new)

        # Entscheide, ob Search oder Input
        lr = frame_data.get('last_root_guid', SYSTEM_USER_ID)
        if lr == SYSTEM_USER_ID:
            # DEAKTIVIERT - ViewManager und SearchListWidget nicht mehr verfügbar
            logger.warning("Search-Funktionalität temporär deaktiviert - verwende Input-Widget")
            self._create_input_widget()
            # cd = self.manager.get_call()
            # vm = PdvmViewManager(cd)
            # self.view_mgr = vm
            # w = PdvmSearchListWidget(vm, vm.view_table)
            # w.selectionChanged.connect(self._on_search_selected)
            # self.view_frame = w
            # self.layout.addWidget(self.btn_frame)
            # self.layout.addWidget(self.view_frame)
            self.search = w
            self.input_frame = None
        else:
            cd = self.manager.get_call(root_guid=lr)
            mode = cd.get('mode', 0)
            if mode == 0:
                self.input_frame = PdvmInputWidget(cd, parent=self)
                self.layout.addWidget(self.input_frame)
                self.input_frame.backToSelection.connect(self._on_back_to_view)
                self.view_frame = None
            else:
                placeholder = QWidget(self)
                vbox = QVBoxLayout(placeholder)
                vbox.setContentsMargins(20, 20, 20, 20)
                vbox.setSpacing(20)
                btn_back = QPushButton("Zur Auswahl")
                btn_back.setMinimumWidth(0)
                btn_back.setMaximumWidth(600)
                btn_back.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn_back.setStyleSheet("font-size: 15px; font-weight: bold; padding: 8px 0;")
                btn_back.clicked.connect(self._on_back_to_view)
                vbox.addWidget(btn_back, alignment=Qt.AlignHCenter)
                guid = cd.get('root_guid', '-')
                label = QLabel(f"Für den Mode {mode} ist noch kein Frame vorhanden.\nAktuelle GUID: {guid}")
                label.setStyleSheet("font-size: 16px; color: #888; padding: 20px;")
                vbox.addWidget(label, alignment=Qt.AlignHCenter)
                self.layout.addWidget(placeholder)
                self.input_frame = placeholder
                self.view_frame = None

    def _on_search_selected(self, guids: list):
        if not guids:
            return
        gid = guids[0]
        self.manager.save(root_guid=gid)
        cd = self.manager.get_call(root_guid=gid)
        self._show_input(cd, show_back=True)

    def _show_input(self, call_data: dict, show_back: bool = False):
        # Clear layout
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        # Back-Button
        # Kein zusätzlicher Auswahl-Button mehr – Umschalten erfolgt nur noch über den Button im InputWidget
        # Immer ein vollständiges call_data mit root_guid aus dem Manager holen!
        root_guid = call_data.get('root_guid')
        if not root_guid:
            raise ValueError("PdvmDialogWidget: call_data muss ein gültiges 'root_guid' enthalten, bevor das InputWidget erzeugt wird!")
        mode = call_data.get('mode', 0)
        if mode == 0:
            # Wenn das InputFrame schon existiert, nur reload, sonst neu anlegen
            if self.input_frame is not None and isinstance(self.input_frame, PdvmInputWidget):
                self.input_frame.reload_with_root_guid(root_guid)
                self.layout.addWidget(self.input_frame)
                self.view_frame = None
            else:
                full_call_data = self.manager.get_call(root_guid=root_guid)
                self.input_frame = PdvmInputWidget(full_call_data, parent=self)
                self.layout.addWidget(self.input_frame)
                self.input_frame.backToSelection.connect(self._on_back_to_view)
                self.view_frame = None
        else:
            placeholder = QWidget(self)
            vbox = QVBoxLayout(placeholder)
            vbox.setContentsMargins(20, 20, 20, 20)
            vbox.setSpacing(20)
            btn_back = QPushButton("Zur Auswahl")
            btn_back.setMinimumWidth(0)
            btn_back.setMaximumWidth(600)
            btn_back.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_back.setStyleSheet("font-size: 15px; font-weight: bold; padding: 8px 0;")
            btn_back.clicked.connect(self._on_back_to_view)
            vbox.addWidget(btn_back, alignment=Qt.AlignHCenter)
            guid = call_data.get('root_guid', '-')
            label = QLabel(f"Für den Mode {mode} ist noch kein Frame vorhanden.\nAktuelle GUID: {guid}")
            label.setStyleSheet("font-size: 16px; color: #888; padding: 20px;")
            vbox.addWidget(label, alignment=Qt.AlignHCenter)
            self.layout.addWidget(placeholder)
            self.input_frame = placeholder
            self.view_frame = None

    def _on_back_to_view(self):
        # Setze last_root_guid in der Systemsteuerung auf SYSTEM_USER_ID (keine Auswahl)
        self.manager.save(root_guid=SYSTEM_USER_ID)
        self._init_ui()
        self.view_frame = None

    def _on_refresh(self):
        logger.debug("🔹 Refresh im Dialog-Knopf gedrückt")
        # 1) Speichere aktuellen Picker-Wert in st_inst
        self.input_widget.st_picker.save()
        # 2) Hole die zentrale Instanz mit dem nun aktuellen Datum
        new_inst = self.input_widget.st_inst
        logger.debug(f"🔹 _on_refresh: speichere neuen Stichtag: {new_inst.PdvmDateTime}")
        # 3) Persistiere ihn in der Systemsteuerung
        self.manager.save(stichtag_inst=new_inst)
        # 4) Mirror in InputWidget-Manager (für Dropdowns, etc.)
        iw_mgr = self.input_widget.manager
        iw_mgr.stichtag = new_inst.PdvmDateTime
        iw_mgr.st_inst.PdvmDateTime = new_inst.PdvmDateTime
        # 4a) Stichtagsgenaue Instanzen neu laden
        if hasattr(iw_mgr, 'refresh_instances_for_stichtag'):
            iw_mgr.refresh_instances_for_stichtag()
        # 5) UI neu aufbauen
        self.input_widget._on_refresh()
        self.input_widget.ts_display.setText(new_inst.FormTimeStamp)

    def _on_create_new(self):
        self.manager.save(root_guid=TEMPLATE_GUID)
        cd = self.manager.get_call(root_guid=TEMPLATE_GUID)
        self._show_input(cd, show_back=True)

    def _trigger_selection(self):
        if self.search:
            self.search.emit_selection()
