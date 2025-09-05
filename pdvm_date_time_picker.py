# pdvm_date_time_picker.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDateEdit, QTimeEdit, QAbstractSpinBox
from PyQt5.QtCore import QDate, QTime
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils

import logging
logger = logging.getLogger(__name__)


class PdvmDateTimePicker(QWidget):
    def refresh_from_instance(self):
        """
        Synchronisiert self.initial mit dem aktuellen Wert der Instanz und aktualisiert die Anzeige.
        """
        self.initial.PdvmDateTime = self.pdvm_datetime.PdvmDateTime
        self.update_display()
    """
    PyQt5-Widget zum Editieren eines Pdvm_DateTime:
      - display == "all": Datum + Zeit
      - display == "only_date": nur Datum
      - display == "only_time": nur Zeit
      - display_time_short: wenn False, zusätzlich Sekunden

    Ablauf:
      - default_date: Float (z.B. 20250605.000000) oder None
      - Wenn self.pdvm_datetime aktuell ein Sentinel (1001.0 / 9999365.0) ist:
          • default_date != None → self.initial.PdvmDateTime = default_date
          • sonst             → self.initial.PdvmDateTime = PdvmDateTimeNow()
      - Wenn kein Sentinel         → self.initial.PdvmDateTime = self.pdvm_datetime.PdvmDateTime
      - Alle Änderungen (Datum/Zeit) landen in self.initial; erst save() schreibt
        self.initial.PdvmDateTime endgültig zurück in self.pdvm_datetime.
    """
    def __init__(self, parent, pdvm_datetime: Pdvm_DateTime,
                 display="all", display_time_short=False,
                 default_date: float = None,
                 *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pdvm_datetime = pdvm_datetime
        self.display = display
        self.display_time_short = display_time_short
        self.default_date = default_date

        # ─── 1) temporäre Instanz: "self.initial" ──────────────────────────────
        self.initial = Pdvm_DateTime("DEU")

        # prüfen, ob pdvm_datetime gerade ein Sentinel ist
        try:
            raw_val = float(self.pdvm_datetime.PdvmDateTime)
        except Exception:
            raw_val = None
        is_sentinel = (raw_val in (1001.0, 9999365.0))

        if is_sentinel:
            if default_date is not None:
                # default_date ist ein Float → ins temporäre Pdvm_DateTime schreiben
                self.initial.PdvmDateTime = float(default_date)
                logger.debug(f"🔹 Sentinel erkannt, verwende default_date {self.initial.FormTimeStamp} zur Initialisierung")
            else:
                # kein default_date → PdvmDateTimeNow()
                now_val = PdvmDateTimeUtils.PdvmDateTimeNow()
                self.initial.PdvmDateTime = now_val
                logger.debug(f"🔹 Sentinel erkannt, verwende PdvmDateTimeNow() = {self.initial.FormTimeStamp} zur Initialisierung")
        else:
            # kein Sentinel → sofort aus dem existierenden Wert befüllen
            self.initial.PdvmDateTime = raw_val
            logger.debug(f"🔹 Kein Sentinel, initialisiere aus pdvm_datetime = {self.initial.FormTimeStamp}")

        # ─── 2) Read-Only-Status speichern (anfangs False) ───────────────────────
        self._readonly = False

        # ─── 3) UI aufbauen ─────────────────────────────────────────────────────
        lo = QHBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)

        # Datumsteil (falls gewünscht)
        if self.display in ("all", "only_date"):
            date_edit = QDateEdit(self)
            date_edit.setDisplayFormat("dd.MM.yyyy")
            date_edit.setDate(QDate(self.initial.Year, self.initial.Month, self.initial.Day))
            date_edit.setCalendarPopup(True)
            date_edit.dateChanged.connect(self._on_date_changed)
            lo.addWidget(date_edit)
            self._date_edit = date_edit

        # Zeitteil (falls gewünscht)
        if self.display in ("all", "only_time"):
            t = (self.initial.Hour, self.initial.Minute,
                 0 if self.display_time_short else self.initial.Second)
            time_edit = QTimeEdit(self)
            fmt = "HH:mm" + ("" if self.display_time_short else ":ss")
            time_edit.setDisplayFormat(fmt)
            time_edit.setTime(QTime(*t))
            time_edit.setKeyboardTracking(False)
            time_edit.timeChanged.connect(self._on_time_changed)
            lo.addWidget(time_edit)
            self._time_edit = time_edit

    def _on_date_changed(self, qdate: QDate):
        """
        Speichert das neue Datum in self.initial (Tag/Monat/Jahr).
        """
        self.initial.PdvmDateT = (qdate.year(), qdate.month(), qdate.day())
        logger.debug(f"🔹 _on_date_changed → initial jetzt: {self.initial.FormTimeStamp}")

    def _on_time_changed(self, qtime: QTime):
        """
        Speichert die neue Zeit in self.initial (Stunde/Minute/Sekunde).
        """
        self.initial.PdvmTimeT = (
            qtime.hour(),
            qtime.minute(),
            0 if self.display_time_short else qtime.second(),
            0
        )
        logger.debug(f"🔹 _on_time_changed → initial jetzt: {self.initial.FormTimeStamp}")

    def get_pdvm_datetime(self) -> Pdvm_DateTime:
        """
        Gibt die zugrunde liegende Pdvm_DateTime-Instanz zurück.
        Änderungen liegen bis save() nur in self.initial.
        """
        return self.pdvm_datetime

    def save(self):
        """
        Überträgt self.initial.PdvmDateTime endgültig in self.pdvm_datetime.
        """
        logger.debug("🔹 PdvmDateTimePicker.save() aufgerufen")
        self.pdvm_datetime.PdvmDateTime = self.initial.PdvmDateTime
        logger.info(
            "🔹 PdvmDateTimePicker.save(): In pdvm_datetime geschrieben → "
            f"{self.pdvm_datetime.FormTimeStamp}"
        )

    def update_display(self):
        """
        Zeichnet die Widgets basierend auf self.initial und self._readonly neu.
        """
        # Prüfe, ob das zugrundeliegende pdvm_datetime immer noch ein Sentinel ist
        try:
            raw_val = float(self.pdvm_datetime.PdvmDateTime)
        except Exception:
            raw_val = None
        is_sentinel = (raw_val in (1001.0, 9999365.0))

        # ─── Datumsteil ─────────────────────────────────────────────────────────
        if hasattr(self, "_date_edit"):
            # (Optional könnte man hier, wenn self._readonly und is_sentinel, hide() aufrufen.)
            self._date_edit.show()
            self._date_edit.setDisplayFormat("dd.MM.yyyy")
            self._date_edit.setDate(QDate(self.initial.Year, self.initial.Month, self.initial.Day))
            self._date_edit.setCalendarPopup(not self._readonly)
            self._date_edit.setButtonSymbols(
                QAbstractSpinBox.NoButtons if self._readonly else QAbstractSpinBox.UpDownArrows
            )
            if self._readonly:
                self._date_edit.setStyleSheet("background-color: #fafafa; color: black;")
            else:
                self._date_edit.setStyleSheet("")

        # ─── Zeitteil ────────────────────────────────────────────────────────────
        if hasattr(self, "_time_edit"):
            self._time_edit.show()
            fmt = "HH:mm" + ("" if self.display_time_short else ":ss")
            self._time_edit.setDisplayFormat(fmt)
            self._time_edit.setTime(QTime(self.initial.Hour, self.initial.Minute, self.initial.Second))
            self._time_edit.setButtonSymbols(
                QAbstractSpinBox.NoButtons if self._readonly else QAbstractSpinBox.UpDownArrows
            )
            if self._readonly:
                self._time_edit.setStyleSheet("background-color: #f0f0f0; color: black;")
            else:
                self._time_edit.setStyleSheet("")

        # ─── Gesamtes Widget aktivieren/deaktivieren ────────────────────────────
        self.setEnabled(not self._readonly)

    def setReadOnly(self, readonly: bool):
        """
        Setzt nur den Read-Only-Status und updatet die UI.
        """
        logger.debug(f"🔹 PdvmDateTimePicker.setReadOnly({readonly})")
        self._readonly = readonly
        self.update_display()

    def update_with_new_instance(self, new_pdvm_datetime: Pdvm_DateTime):
        """
        Aktualisiert das Widget mit einer neuen PdvmDateTime-Instanz.
        Diese Methode wird verwendet, wenn sich die zugrunde liegende Instanz geändert hat.
        """
        logger.debug(f"🔹 PdvmDateTimePicker.update_with_new_instance aufgerufen - neuer Wert: {new_pdvm_datetime.PdvmDateTime}")
        
        # Die neue Instanz übernehmen
        self.pdvm_datetime = new_pdvm_datetime
        
        # Initial-Werte aus der neuen Instanz setzen
        try:
            raw_val = float(self.pdvm_datetime.PdvmDateTime)
        except Exception:
            raw_val = 1001.0  # Fallback auf Sentinel
            
        # Prüfen, ob es ein Sentinel ist
        if raw_val in (1001.0, 9999365.0):
            # Sentinel → verwende aktuelles Datum als Default
            if hasattr(self, 'default_date') and self.default_date is not None:
                if isinstance(self.default_date, (int, float)):
                    self.initial.PdvmDateTime = float(self.default_date)
                else:
                    now_val = PdvmDateTimeUtils.PdvmDateTimeNow()
                    self.initial.PdvmDateTime = now_val
            else:
                now_val = PdvmDateTimeUtils.PdvmDateTimeNow()
                self.initial.PdvmDateTime = now_val
        else:
            # Kein Sentinel → aus der neuen Instanz übernehmen
            self.initial.PdvmDateTime = raw_val
            
        # UI aktualisieren
        self.update_display()
        logger.debug(f"🔹 PdvmDateTimePicker.update_with_new_instance abgeschlossen - initial jetzt: {self.initial.FormTimeStamp}")
