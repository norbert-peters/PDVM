# pdvm_date_time_picker.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDateEdit, QTimeEdit, QAbstractSpinBox, QPushButton
from PyQt5.QtCore import QDate, QTime, pyqtSignal
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils

import logging
logger = logging.getLogger(__name__)


class PdvmDateTimePicker(QWidget):
    """
    🔹 SIGNAL: valueChanged wird bei Änderungen emittiert (für Dirty-Visualisierung)
    """
    valueChanged = pyqtSignal()  # Signal für Input Control
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

        # WICHTIG: default_date hat IMMER Vorrang, wenn übergeben!
        # Das ermöglicht explizites Setzen von Werten (auch Sentinels wie 1001.0)
        if default_date is not None:
            # Expliziter default_date übergeben → verwenden (auch wenn Sentinel!)
            self.initial.PdvmDateTime = float(default_date)
            logger.debug(f"🔹 Verwende expliziten default_date: {self.initial.FormTimeStamp} (Wert: {default_date})")
        else:
            # Kein default_date → Wert aus pdvm_datetime übernehmen
            try:
                raw_val = float(self.pdvm_datetime.PdvmDateTime)
            except Exception:
                raw_val = None
            
            is_sentinel = (raw_val in (1001.0, 9999365.0))
            
            if is_sentinel:
                # Sentinel ohne default_date → PdvmDateTimeNow als Fallback
                now_val = PdvmDateTimeUtils.PdvmDateTimeNow
                self.initial.PdvmDateTime = now_val
                logger.debug(f"🔹 Sentinel erkannt (kein default_date), verwende PdvmDateTimeNow = {self.initial.FormTimeStamp}")
            else:
                # Normaler Wert → übernehmen
                self.initial.PdvmDateTime = raw_val
                logger.debug(f"🔹 Kein Sentinel, initialisiere aus pdvm_datetime = {self.initial.FormTimeStamp}")

        # ─── 2) Read-Only-Status speichern (anfangs False) ───────────────────────
        self._readonly = False

        # ─── 2b) DIRTY-TRACKING: Original-Wert speichern ──────────────────────────
        self._original_value = self.initial.PdvmDateTime  # Float speichern
        self._is_dirty = False  # Anfangs nicht dirty

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
        
        # ─── 4) "JETZT" Button hinzufügen ─────────────────────────────────────
        jetzt_button = QPushButton("Jetzt", self)
        jetzt_button.setToolTip("Setzt aktuellen Timestamp")
        jetzt_button.setMaximumWidth(60)
        jetzt_button.clicked.connect(self._set_current_timestamp)
        lo.addWidget(jetzt_button)
        self._jetzt_button = jetzt_button
        
        # ─── 5) "00:00" Button hinzufügen (nur bei Zeitanzeige) ──────────────
        if self.display in ("all", "only_time"):
            midnight_button = QPushButton("00:00", self)
            midnight_button.setToolTip("Setzt Uhrzeit auf 00:00:00")
            midnight_button.setMaximumWidth(60)
            midnight_button.clicked.connect(self._set_midnight)
            lo.addWidget(midnight_button)
            self._midnight_button = midnight_button
    
    def _set_current_timestamp(self):
        """Setzt aktuellen Timestamp in den DateTimePicker"""
        now_val = PdvmDateTimeUtils.PdvmDateTimeNow
        self.initial.PdvmDateTime = now_val
        self.update_display()
        logger.debug(f"🔹 Jetzt-Button geklickt → {self.initial.FormTimeStamp}")
    
    def _set_midnight(self):
        """Setzt Uhrzeit auf 00:00:00 (Mitternacht)"""
        # Aktuelles Datum behalten, nur Zeit auf 00:00:00 setzen
        current_date = (self.initial.Year, self.initial.Month, self.initial.Day)
        
        # Datum setzen (behält das aktuelle Datum)
        self.initial.PdvmDateT = current_date
        
        # Zeit auf 00:00:00 setzen
        self.initial.PdvmTimeT = (0, 0, 0, 0)  # Stunde, Minute, Sekunde, Mikrosekunde
        
        self.update_display()
        logger.debug(f"🔹 00:00-Button geklickt → {self.initial.FormTimeStamp}")

    def refresh_from_instance(self):
        """
        Synchronisiert self.initial mit dem aktuellen Wert der Instanz und aktualisiert die Anzeige.
        """
        self.initial.PdvmDateTime = self.pdvm_datetime.PdvmDateTime
        self.update_display()

    def _on_date_changed(self, qdate: QDate):
        """
        Speichert das neue Datum in self.initial (Tag/Monat/Jahr).
        """
        self.initial.PdvmDateT = (qdate.year(), qdate.month(), qdate.day())
        self._is_dirty = True  # 🔹 DIRTY-TRACKING: Änderung erkannt!
        self.set_dirty_style(True)  # 🔹 ORANGE RAHMEN setzen!
        self.valueChanged.emit()  # 🔹 SIGNAL: Input Control benachrichtigen!
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
        self._is_dirty = True  # 🔹 DIRTY-TRACKING: Änderung erkannt!
        self.set_dirty_style(True)  # 🔹 ORANGE RAHMEN setzen!
        self.valueChanged.emit()  # 🔹 SIGNAL: Input Control benachrichtigen!
        logger.debug(f"🔹 _on_time_changed → initial jetzt: {self.initial.FormTimeStamp}")

    def get_pdvm_datetime(self) -> Pdvm_DateTime:
        """
        Gibt die zugrunde liegende Pdvm_DateTime-Instanz zurück.
        Änderungen liegen bis save() nur in self.initial.
        """
        return self.pdvm_datetime

    def is_dirty(self) -> bool:
        """
        🔹 DIRTY-TRACKING: Gibt True zurück, wenn Änderungen vorliegen.
        Prüft, ob aktueller Wert vom Original abweicht.
        """
        return self._is_dirty
    
    def set_dirty_style(self, dirty: bool):
        """
        🔹 DIRTY-VISUALISIERUNG: Setzt orange Rahmen für geänderte Werte
        """
        if dirty:
            # Orange Rahmen für dirty
            style = """
                QDateEdit, QTimeEdit {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 3px;
                }
            """
        else:
            # Normal Rahmen
            style = """
                QDateEdit, QTimeEdit {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 3px;
                }
            """
        
        # Style auf interne Widgets anwenden
        if hasattr(self, '_date_edit'):
            self._date_edit.setStyleSheet(style)
        if hasattr(self, '_time_edit'):
            self._time_edit.setStyleSheet(style)

    def save(self):
        """
        Überträgt self.initial.PdvmDateTime endgültig in self.pdvm_datetime.
        
        KRITISCH: Zuerst aktuelle Werte aus Widgets in self.initial übertragen!
        Events (_on_date_changed, _on_time_changed) werden NUR bei User-Interaktion gefeuert.
        Beim programmatischen Refresh (z.B. Stichtag Apply-Button) müssen wir manuell auslesen.
        """
        logger.info(f"🔹 PdvmDateTimePicker.save() AUFGERUFEN")
        logger.info(f"    VORHER: pdvm_datetime={self.pdvm_datetime.PdvmDateTime}, initial={self.initial.PdvmDateTime}")
        
        # ─── SCHRITT 1: Aktuelle Widget-Werte in self.initial übertragen ────────
        # WICHTIG: Wir müssen Datum UND Zeit ZUSAMMEN setzen, nicht einzeln!
        # Wenn nur Datum gesetzt wird, wird Zeit auf 00:00:00 zurückgesetzt!
        
        # Standardwerte aus self.initial (falls Widgets nicht vorhanden)
        year, month, day = self.initial.Year, self.initial.Month, self.initial.Day
        hour, minute, second = self.initial.Hour, self.initial.Minute, self.initial.Second
        
        # Datum aus Widget übernehmen (falls vorhanden)
        if hasattr(self, '_date_edit'):
            qdate = self._date_edit.date()
            year, month, day = qdate.year(), qdate.month(), qdate.day()
            logger.debug(f"    📅 Datum aus Widget übernommen: {year}-{month}-{day}")
        
        # Zeit aus Widget übernehmen (falls vorhanden)
        if hasattr(self, '_time_edit'):
            qtime = self._time_edit.time()
            hour = qtime.hour()
            minute = qtime.minute()
            second = 0 if self.display_time_short else qtime.second()
            logger.debug(f"    ⏰ Zeit aus Widget übernommen: {hour}:{minute}:{second}")
        
        # ZUSAMMEN setzen mit PdvmDateTimeT (verhindert Korruption!)
        self.initial.PdvmDateTimeT = (year, month, day, hour, minute, second, 0)
        logger.info(f"    NACH Widget-Transfer: initial={self.initial.PdvmDateTime}")
        
        # ─── SCHRITT 2: Transfer zu pdvm_datetime ────────────────────────────────
        self.pdvm_datetime.PdvmDateTime = self.initial.PdvmDateTime
        self._is_dirty = False
        self._original_value = self.initial.PdvmDateTime
        self.set_dirty_style(False)
        
        logger.info(f"    NACHHER: pdvm_datetime={self.pdvm_datetime.PdvmDateTime}")
        logger.info(f"    FORMATIERT: {self.pdvm_datetime.FormTimeStamp}")

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
                    now_val = PdvmDateTimeUtils.PdvmDateTimeNow
                    self.initial.PdvmDateTime = now_val
            else:
                now_val = PdvmDateTimeUtils.PdvmDateTimeNow
                self.initial.PdvmDateTime = now_val
        else:
            # Kein Sentinel → aus der neuen Instanz übernehmen
            self.initial.PdvmDateTime = raw_val
            
        # UI aktualisieren
        self.update_display()
        logger.debug(f"🔹 PdvmDateTimePicker.update_with_new_instance abgeschlossen - initial jetzt: {self.initial.FormTimeStamp}")
