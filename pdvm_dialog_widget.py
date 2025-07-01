# pdvm_dialog_widget.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QPushButton,
    QHBoxLayout, QGroupBox
)
from pdvm_input_widget import PdvmInputWidget
from pdvm_search_list_widget import PdvmSearchListWidget
from pdvm_central_datenbank import PdvmCentralDatenbank
from pd_datetime import Pdvm_DateTime, PdvmDateTimeUtils
from pdvm_view_manager import PdvmViewManager
import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmDialogWidget gestartet")

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
TEMPLATE_GUID = "00000000-0000-0000-0000-000000000000"


class PdvmDialogManager:
    def __init__(self, base_call: dict):
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
        logger.debug(f"🔹 74 framedaten[{self.frame_guid}] = {frm.lesen()}")
        self.view_guid = frm.get_value('ROOT', 'view_guid')
        logger.debug(f"🔹 76 view_guid = {self.view_guid}" )
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
    def __init__(self, call_data: dict, parent=None):
        super().__init__(parent)
        self.manager      = PdvmDialogManager(call_data)
        self.layout       = QVBoxLayout(self)
        self.search       = None
        self.view_mgr     = None
        self.input_widget = None
        self._init_ui()

    def _init_ui(self):
        # Clear layout
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Aktionstasten
        frame_data = self.manager.frame_data
        btn_frame = QGroupBox("Aktionen")
        btn_layout = QHBoxLayout(btn_frame)
        btn_select = QPushButton("Auswahl übernehmen")
        btn_select.clicked.connect(self._trigger_selection)
        btn_layout.addWidget(btn_select)
        btn_new = QPushButton("Neuanlage")
        btn_new.clicked.connect(self._on_create_new)
        btn_layout.addWidget(btn_new)
        self.layout.addWidget(btn_frame)

        # Entscheide, ob Search oder Input
        lr = frame_data.get('last_root_guid', SYSTEM_USER_ID)
        if lr == SYSTEM_USER_ID:
            cd = self.manager.get_call()
            vm = PdvmViewManager(cd)
            self.view_mgr = vm
            w = PdvmSearchListWidget(vm, vm.view_table)
            w.selectionChanged.connect(self._on_search_selected)
            self.layout.addWidget(w)
            self.search = w
        else:
            cd = self.manager.get_call(root_guid=lr)
            self._show_input(cd, show_back=True)

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
        if show_back:
            btn = QPushButton("Auswahl")
            btn.clicked.connect(lambda: (self.manager.clear(), self._init_ui()))
            self.layout.addWidget(btn)
        # Input-Widget: KEIN Manager mehr übergeben, nur call_data und parent!
        iw = PdvmInputWidget(call_data, parent=self)
        for btn in iw.findChildren(QPushButton):
            if btn.text() == "Refresh":
                btn.clicked.disconnect()
                # statt iw._on_refresh, rufe hier dialog._on_refresh
                btn.clicked.connect(self._on_refresh)
                break
        self.layout.addWidget(iw)
        self.input_widget = iw
        # Refresh-Handler umleiten
        for btn in iw.findChildren(QPushButton):
            if btn.text() == "Refresh":
                btn.clicked.disconnect()
                btn.clicked.connect(self._on_refresh)
                break

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
