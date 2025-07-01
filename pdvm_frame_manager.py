# pdvm_frame_manager.py

import logging
from pdvm_datenbank import PdvmDatenbank as PdvmDB
from pdvm_view_manager import PdvmViewManager
from pdvm_search_list_widget import SearchListWidget
from pdvm_input_control import PdvmInputFrame

logger = logging.getLogger(__name__)

class PdvmFrameManager:
    def __init__(self, call_daten: dict):
        """
        call_daten muss mindestens enthalten:
          - user_guid
          - framedaten: { GUID: <GUID der framedaten>, HIST: <bool> }
        Optional: view_guid in framedaten selbst
        """
        self.call_daten   = call_daten
        self.user_guid    = call_daten["user_guid"]
        self.frame_guid   = call_daten["framedaten"]["GUID"]
        self.stichtag     = float(call_daten.get("stichtag", "1001.0"))
        self.mode         = call_daten.get("mode", 0)

        # 1) lade framedaten
        self.frame_db     = PdvmDB("PdvmManager.db", "framedaten", hist=False)
        frame_meta        = self.frame_db.lesen(self.frame_guid) or {}
        self.root_table   = frame_meta["root_table"]
        self.view_guid    = frame_meta.get("view_guid")

        # 2) Steuerungsdaten (letzte Auswahl) für den User
        self.ctrl_db      = PdvmDB("PdvmManager.db", "systemsteuerung", hist=False)
        self.ctrl_user    = self.ctrl_db.lesen(self.user_guid) or {}

    def get_last_selection(self):
        return self.ctrl_user.get(self.root_table, {}).get("last_guid")

    def get_last_stichtag(self):
        return self.ctrl_user.get(self.root_table, {}).get("stichtag", self.stichtag)

    def save_selection(self, guid, stichtag):
        self.ctrl_user.setdefault(self.root_table, {})["last_guid"] = guid
        self.ctrl_user[self.root_table]["stichtag"] = stichtag
        self.ctrl_db.speichern(self.user_guid, self.ctrl_user)
        logger.info(f"gespeichert: {self.root_table} → {guid} @ {stichtag}")

    def widget_for_input_frame(self):
        """
        Gibt ein QWidget zurück – entweder die Such-Liste (falls noch keine GUID bekannt)
        oder direkt das InputFrame, wenn wir schon eine GUID im Steuerungs-DB haben.
        """
        last_guid   = self.get_last_selection()
        last_sticht = self.get_last_stichtag()

        # Wenn schon eine GUID existiert, direkt den InputFrame bauen:
        if last_guid:
            return self._build_input_frame(last_guid, last_sticht)

        # Sonst: zeige zuerst die Auswahl-View:
        return self._build_selection_widget(last_sticht)

    def _build_selection_widget(self, stichtag):
        if not self.view_guid:
            raise RuntimeError("view_guid fehlt in den framedaten!")

        # 1) Baue call_daten für die View:
        view_call = {
            "user_guid": self.user_guid,
            "view_guid": self.view_guid,
            "stichtag":  stichtag,
            "mode":      self.mode
        }
        vm = PdvmViewManager(view_call)

        # 2) Such-Widget
        selector = SearchListWidget(vm, table_name=self.root_table)
        selector.selectionChanged.connect(self._on_user_selected)
        return selector

    def _on_user_selected(self, guids):
        """
        Wenn der User sich in der Liste entschieden hat:
        erste GUID nehmen, speichern und dann InputFrame zeigen.
        """
        if not guids:
            return
        chosen = guids[0]
        st     = self.get_last_stichtag()
        self.save_selection(chosen, st)
        # und nun das InputFrame bauen:
        self._current_widget = self._build_input_frame(chosen, st)
        # ... hier müsstest Du es noch in Dein Main-Window einsetzen ...

    def _build_input_frame(self, guid, stichtag):
        """
        Erzeugt das PdvmInputFrame, indem wir ihm **nur** die nötigen call_daten
        übergeben (GUIDs, Sprache, Header-Text, …)
        """
        # Wir nehmen einfach die Original-call_daten und ergänzen
        call = {
            **self.call_daten,
            "stichtag":          str(stichtag),
            "header_text":       "Detail-Maske",
            # framedaten-GUID bleibt erhalten
            # evtl. Dropdown- oder pdvmperson-GUIDs aus self.call_daten übernehmen
        }
        # wichtig: framedaten bleibt drin, dort steckt die GUID der Frame-Definition:
        # call["framedaten"] == {"GUID": ..., "HIST": ...}

        return PdvmInputFrame(parent=None, config=call)
