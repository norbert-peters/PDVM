#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PdvmCentralStichtagManager - Zentrale Stichtag-Verwaltung
Verwaltet eine einzige PdvmDateTime-Instanz für den Stichtag system-weit.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)

class PdvmCentralStichtagManager(QObject):
    """
    Zentrale Stichtag-Manager-Klasse
    
    - Verwaltet EINE PdvmDateTime-Instanz für den Stichtag
    - Synchronisiert automatisch mit central_systemsteuerung
    - Sendet Signals bei Änderungen
    - Kann direkt vom PdvmDatetimePicker verwendet werden
    
    Architektur:
    - Singleton-Pattern: nur eine Instanz pro Anwendung
    - Signal/Slot-System für Updates
    - Automatische Persistierung in Systemsteuerung
    """
    
    # Signals für Stichtag-Änderungen
    stichtag_changed = pyqtSignal(float)  # Neuer Stichtag als float
    stichtag_formatted_changed = pyqtSignal(str)  # Formatierter Stichtag als String
    
    def __init__(self, central_systemsteuerung, user_guid, initial_stichtag="2025216"):
        """
        Initialisiert den zentralen Stichtag-Manager
        
        Args:
            central_systemsteuerung: Instanz der PdvmCentralDatenbank (systemsteuerung)
            user_guid: GUID des aktuellen Benutzers
            initial_stichtag: Standard-Stichtag falls keiner in DB vorhanden
        """
        super().__init__()
        
        self.central_systemsteuerung = central_systemsteuerung
        self.user_guid = user_guid
        self.initial_stichtag = initial_stichtag
        
        # ZENTRALE PdvmDateTime-Instanz erstellen
        self.pdvm_datetime = Pdvm_DateTime("DEU")
        
        # Stichtag aus Systemsteuerung laden oder Standard setzen
        self._load_stichtag_from_db()
        
        logger.info(f"🗓️ Zentraler Stichtag-Manager initialisiert: {self.get_formatted_stichtag()}")
    
    def _load_stichtag_from_db(self):
        """Lädt den Stichtag aus der Systemsteuerung oder setzt Standard-Wert"""
        try:
            if self.central_systemsteuerung:
                stichtag_data = self.central_systemsteuerung.get_value(
                    gruppe=self.user_guid,
                    feld="stichtag",
                    ab_zeit=None
                )
                
                if stichtag_data:
                    stichtag_str = str(stichtag_data.get("wert", self.initial_stichtag))
                    self.pdvm_datetime.PdvmDateTime = float(stichtag_str)
                    logger.debug(f"📥 Stichtag aus DB geladen: {stichtag_str}")
                else:
                    # Standard-Wert setzen und in DB speichern
                    self.pdvm_datetime.PdvmDateTime = float(self.initial_stichtag)
                    self._save_to_db()
                    logger.info(f"📝 Standard-Stichtag gesetzt und gespeichert: {self.initial_stichtag}")
            else:
                # Fallback wenn keine Systemsteuerung verfügbar
                self.pdvm_datetime.PdvmDateTime = float(self.initial_stichtag)
                logger.warning("⚠️ Keine Systemsteuerung verfügbar - verwende Standard-Stichtag")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Stichtags: {e}")
            # Fallback auf Standard
            self.pdvm_datetime.PdvmDateTime = float(self.initial_stichtag)
    
    def _save_to_db(self):
        """Speichert den aktuellen Stichtag in die Systemsteuerung"""
        try:
            if self.central_systemsteuerung:
                # KORRIGIERT: Speichere mit korrekten Nachkommastellen
                stichtag_value = self.get_stichtag_string_pdvm_format()
                
                self.central_systemsteuerung.set_value(
                    gruppe=self.user_guid,
                    feld="stichtag",
                    wert=stichtag_value,
                    ab_zeit=1001.0
                )
                
                self.central_systemsteuerung.save_values()
                logger.debug(f"💾 Stichtag in DB gespeichert: {stichtag_value}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Stichtags: {e}")
    
    def get_pdvm_datetime(self):
        """
        Gibt die zentrale PdvmDateTime-Instanz zurück
        
        Returns:
            Pdvm_DateTime: Die zentrale Stichtag-Instanz
        """
        return self.pdvm_datetime
    
    def get_stichtag_float(self):
        """
        Gibt den Stichtag als float zurück
        
        Returns:
            float: Stichtag im PdvmDateTime-Format
        """
        return self.pdvm_datetime.PdvmDateTime
    
    @property
    def akt_stichtag(self):
        """
        ZENTRALE STICHTAG-PROPERTY
        
        Gibt den aktuellen Stichtag als float zurück.
        Diese Property ist die EINZIGE Quelle für Stichtag-Daten im System.
        
        Returns:
            float: Aktueller Stichtag im PdvmDateTime-Format
        """
        return self.pdvm_datetime.PdvmDateTime
    
    def get_stichtag_string(self):
        """
        Gibt den Stichtag als String zurück (für DB-Speicherung)
        KORRIGIERT: Behält Nachkommastellen bei
        
        Returns:
            str: Stichtag als String im PdvmFormat mit Nachkommastellen
        """
        return str(self.pdvm_datetime.PdvmDateTime)
    
    def get_stichtag_string_pdvm_format(self):
        """
        Gibt den Stichtag im korrekten PdvmFormat zurück
        VERWENDET JETZT ZENTRALE PdvmDateTimeStr Property!
        
        Returns:
            str: Stichtag im PdvmFormat mit zentraler Formatierung
        """
        try:
            return self.pdvm_datetime.PdvmDateTimeStr
        except Exception as e:
            logger.error(f"❌ Fehler beim Formatieren des Stichtags: {e}")
            # Fallback mit zentralen PdvmDateTimeUtils
            try:
                from pdvm_datetime import PdvmDateTimeUtils
                return PdvmDateTimeUtils.PdvmDateTimeNowStr
            except Exception as fallback_error:
                logger.error(f"❌ Auch Fallback-Formatierung fehlgeschlagen: {fallback_error}")
                return str(self.pdvm_datetime.PdvmDateTime)
    
    def get_formatted_stichtag(self):
        """
        Gibt den Stichtag formatiert zurück (dd.mm.yyyy)
        
        Returns:
            str: Formatierter Stichtag
        """
        try:
            return f"{self.pdvm_datetime.Day:02d}.{self.pdvm_datetime.Month:02d}.{self.pdvm_datetime.Year}"
        except:
            return "Ungültiges Datum"
    
    def set_stichtag(self, new_stichtag):
        """
        Setzt einen neuen Stichtag und speichert ihn
        
        Args:
            new_stichtag: Neuer Stichtag als float, int oder string
        """
        try:
            old_stichtag = self.pdvm_datetime.PdvmDateTime
            
            # Neuen Stichtag setzen
            if isinstance(new_stichtag, str):
                new_stichtag = float(new_stichtag)
            elif isinstance(new_stichtag, int):
                new_stichtag = float(new_stichtag)
            
            self.pdvm_datetime.PdvmDateTime = new_stichtag
            
            # In DB speichern
            self._save_to_db()
            
            # Signals senden
            self.stichtag_changed.emit(new_stichtag)
            self.stichtag_formatted_changed.emit(self.get_formatted_stichtag())
            
            logger.info(f"🗓️ Stichtag geändert: {self.get_formatted_stichtag()} (vorher: {old_stichtag})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Stichtags: {e}")
    
    def set_stichtag_from_components(self, day, month, year):
        """
        Setzt den Stichtag aus Tag, Monat, Jahr-Komponenten
        
        Args:
            day (int): Tag (1-31)
            month (int): Monat (1-12)  
            year (int): Jahr (4-stellig)
        """
        try:
            # Temporäre PdvmDateTime-Instanz für Berechnung
            temp_dt = Pdvm_DateTime("DEU")
            temp_dt.Day = day
            temp_dt.Month = month
            temp_dt.Year = year
            
            # Neuen Stichtag setzen
            self.set_stichtag(temp_dt.PdvmDateTime)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Stichtags aus Komponenten: {e}")

    def set_stichtag_with_time(self, day, month, year, hour=0, minute=0, second=0):
        """
        Setzt den Stichtag mit expliziter Zeitangabe
        
        Args:
            day (int): Tag (1-31)
            month (int): Monat (1-12)  
            year (int): Jahr (4-stellig)
            hour (int): Stunde (0-23, optional, default: 0)
            minute (int): Minute (0-59, optional, default: 0)
            second (int): Sekunde (0-59, optional, default: 0)
        """
        try:
            # Temporäre PdvmDateTime-Instanz für Berechnung
            temp_dt = Pdvm_DateTime("DEU")
            temp_dt.Day = day
            temp_dt.Month = month
            temp_dt.Year = year
            temp_dt.Hour = hour
            temp_dt.Minute = minute
            temp_dt.Second = second
            
            # Neuen Stichtag mit Zeit setzen
            self.set_stichtag(temp_dt.PdvmDateTime)
            
            logger.info(f"🕐 Stichtag mit Zeit gesetzt: {self.get_formatted_stichtag()} {hour:02d}:{minute:02d}:{second:02d}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Stichtags mit Zeit: {e}")

    def get_time_components(self):
        """
        Gibt die Zeitkomponenten des aktuellen Stichtags zurück
        
        Returns:
            dict: Dictionary mit hour, minute, second
        """
        try:
            return {
                "hour": self.pdvm_datetime.Hour,
                "minute": self.pdvm_datetime.Minute, 
                "second": self.pdvm_datetime.Second
            }
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Zeitkomponenten: {e}")
            return {"hour": 0, "minute": 0, "second": 0}
    
    def connect_datetime_picker(self, datetime_picker):
        """
        Verbindet einen PdvmDatetimePicker direkt mit diesem Manager
        
        Args:
            datetime_picker: PdvmDatetimePicker-Instanz
        """
        try:
            # PdvmDateTime-Instanz an Picker übergeben
            datetime_picker.set_pdvm_datetime_instance(self.pdvm_datetime)
            
            # Signal-Verbindungen einrichten (falls der Picker Signals hat)
            if hasattr(datetime_picker, 'datetime_changed'):
                datetime_picker.datetime_changed.connect(self._on_picker_changed)
            
            logger.info(f"🔗 DatetimePicker mit zentralem Stichtag-Manager verbunden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verbinden des DatetimePickers: {e}")
    
    def _on_picker_changed(self):
        """Callback wenn der DatetimePicker den Stichtag ändert"""
        try:
            # Da der Picker direkt auf unserer PdvmDateTime-Instanz arbeitet,
            # müssen wir nur speichern und Signals senden
            self._save_to_db()
            
            current_stichtag = self.pdvm_datetime.PdvmDateTime
            self.stichtag_changed.emit(current_stichtag)
            self.stichtag_formatted_changed.emit(self.get_formatted_stichtag())
            
            logger.info(f"🔄 Stichtag über DatetimePicker geändert: {self.get_formatted_stichtag()}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei DatetimePicker-Callback: {e}")
    
    def refresh_from_db(self):
        """Lädt den Stichtag neu aus der Datenbank (für externe Änderungen)"""
        old_stichtag = self.pdvm_datetime.PdvmDateTime
        self._load_stichtag_from_db()
        
        # Prüfen ob sich etwas geändert hat
        if abs(old_stichtag - self.pdvm_datetime.PdvmDateTime) > 0.1:
            self.stichtag_changed.emit(self.pdvm_datetime.PdvmDateTime)
            self.stichtag_formatted_changed.emit(self.get_formatted_stichtag())
            logger.info(f"🔄 Stichtag aus DB aktualisiert: {self.get_formatted_stichtag()}")
    
    def get_info_dict(self):
        """
        Gibt Debug-Informationen zurück
        
        Returns:
            dict: Info-Dictionary mit allen relevanten Daten
        """
        return {
            "stichtag_float": self.get_stichtag_float(),
            "stichtag_string": self.get_stichtag_string(),
            "stichtag_pdvm_format": self.get_stichtag_string_pdvm_format(),
            "formatted": self.get_formatted_stichtag(),
            "year": self.pdvm_datetime.Year,
            "month": self.pdvm_datetime.Month,
            "day": self.pdvm_datetime.Day,
            "user_guid": self.user_guid,
            "has_systemsteuerung": self.central_systemsteuerung is not None
        }
