#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Error Log Manager
======================
Zentrales System für Fehlerprotokollierung mit Pop-up Warnung

ARCHITEKTUR:
- Tabelle sys_error_log in Mandanten-DB
- Automatisches Logging bei kritischen Fehlern
- Pop-up bei neuen unbestätigten Fehlern
- View-Integration für Fehlerübersicht

VERWENDUNG:
    from pdvm_error_log_manager import log_error, check_new_errors
    
    # Fehler loggen
    log_error(
        context_guid="view-guid",
        context_type="view",
        error_type="json_parse",
        error_message="JSON corrupt",
        record_guid="datensatz-guid",
        table_name="persondaten",
        severity="error"
    )
    
    # Bei App-Start prüfen
    check_new_errors()  # Zeigt Pop-up wenn neue Fehler
"""

import logging
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class PdvmErrorLogManager:
    """
    Manager für zentrale Fehlerprotokollierung
    
    FEATURES:
    - Automatisches Logging in sys_error_log
    - Schweregrad-basierte Filterung
    - Pop-up Warnung bei kritischen Fehlern
    - Bestätigungs-Tracking (acknowledged)
    """
    
    def __init__(self, gcs):
        """
        Initialisiert Error-Log Manager
        
        Args:
            gcs: Globale Systemsteuerung (für DB-Zugriff)
        """
        self.gcs = gcs
        self._ensure_error_log_table()
        
        logger.info("✅ Error-Log Manager initialisiert")
    
    def _ensure_error_log_table(self):
        """
        Stellt sicher dass sys_error_log und sys_error_acknowledgments Tabellen existieren
        
        ✅ SYSTEMTABELLEN: Verwenden PdvmCentralDatenbank mit Gruppe/Feld-Struktur
        
        STRUKTUR sys_error_log (Gruppen/Felder):
        - ROOT/timestamp: Zeitpunkt des ersten Auftretens
        - ROOT/last_occurrence: Zeitpunkt des letzten Auftretens
        - ROOT/occurrence_count: Anzahl Auftreten
        - ROOT/context_guid: GUID des betroffenen Objekts
        - ROOT/context_type: Typ (view/table/dialog)
        - ROOT/error_type: Fehlertyp (json_parse/attribute/type)
        - ROOT/error_message: Fehlermeldung
        - ROOT/record_guid: Betroffener Datensatz
        - ROOT/table_name: Betroffene Tabelle
        - ROOT/severity: Schweregrad (warning/error/critical)
        
        STRUKTUR sys_error_acknowledgments (Gruppen/Felder):
        - ROOT/error_guid: Referenz auf sys_error_log
        - ROOT/user_guid: User der bestätigt hat
        - ROOT/acknowledged_at: Zeitpunkt der Bestätigung
        - ROOT/expires_at: Ablaufdatum (24h später)
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Tabellen werden automatisch bei erster Verwendung erstellt
        logger.info(f"📋 Error-Log Systemtabellen bereit (PdvmCentralDatenbank)")
    
    def log_error(
        self,
        context_guid: str,
        context_type: str,
        error_type: str,
        error_message: str,
        record_guid: Optional[str] = None,
        table_name: Optional[str] = None,
        severity: str = "error",
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Loggt Fehler in sys_error_log mit DEDUPLIZIERUNG
        
        DEDUPLIZIERUNG:
        - Prüft ob Fehler bereits existiert (table_name, record_guid, error_type)
        - Falls JA: Update timestamp + occurrence_count hochzählen
        - Falls NEIN: Neuer Eintrag
        
        Args:
            context_guid: GUID des betroffenen Objekts (View/Dialog/Frame)
            context_type: Typ (view/dialog/frame/menu/table)
            error_type: Fehlertyp (json_parse/attribute/type/database)
            error_message: Vollständige Fehlermeldung
            record_guid: Betroffener Datensatz (optional)
            table_name: Betroffene Tabelle (optional)
            severity: Schweregrad (warning/error/critical)
            additional_info: Zusätzliche Infos (optional)
            
        Returns:
            str: GUID des Log-Eintrags (bestehend oder neu)
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        import allgemeines as all
        
        # Timestamp generieren
        timestamp = self.gcs.st_inst.PdvmDateTime
        
        # ✅ DEDUPLIZIERUNG: Prüfe ob Fehler bereits existiert
        existing_error = self._find_existing_error(table_name, record_guid, error_type)
        
        if existing_error:
            # Update bestehenden Fehler
            log_guid = existing_error['uid']
            error_db = PdvmCentralDatenbank('sys_error_log', log_guid)
            
            # Occurrence count hochzählen
            result = error_db.get_value('ROOT', 'occurrence_count')
            current_count = result[0] if isinstance(result, tuple) else (result or 1)
            
            error_db.set_value('ROOT', 'occurrence_count', current_count + 1, timestamp)
            error_db.set_value('ROOT', 'last_occurrence', timestamp, timestamp)
            error_db.save_all_values()
            
            logger.warning(f"⚠️ Fehler aktualisiert: {log_guid} (#{current_count + 1})")
            return log_guid
        
        # Neuer Fehler - mit PdvmCentralDatenbank erstellen (OHNE GUID)
        error_db = PdvmCentralDatenbank('sys_error_log')  # ✅ Keine GUID beim Init
        
        # Alle Felder setzen (Gruppe/Feld-Struktur, nicht-historisch)
        error_db.set_value('ROOT', 'timestamp', timestamp, timestamp)
        error_db.set_value('ROOT', 'last_occurrence', timestamp, timestamp)
        error_db.set_value('ROOT', 'occurrence_count', 1, timestamp)
        error_db.set_value('ROOT', 'context_guid', context_guid, timestamp)
        error_db.set_value('ROOT', 'context_type', context_type, timestamp)
        error_db.set_value('ROOT', 'error_type', error_type, timestamp)
        error_db.set_value('ROOT', 'error_message', error_message, timestamp)
        error_db.set_value('ROOT', 'record_guid', record_guid or "", timestamp)
        error_db.set_value('ROOT', 'table_name', table_name or "", timestamp)
        error_db.set_value('ROOT', 'severity', severity, timestamp)
        
        # Speichern (generiert automatisch neue GUID)
        log_guid = error_db.save_all_values()
        
        # Name-Spalte setzen (NACH save, jetzt hat error_db eine GUID)
        name_text = f"{severity.upper()}: {error_type} in {table_name or context_type}"
        error_db.set_name(name_text)
        
        logger.warning(f"⚠️ Fehler geloggt: {log_guid} ({severity})")
        logger.debug(f"   Context: {context_type}/{context_guid}")
        logger.debug(f"   Fehler: {error_message}")
        
        return log_guid
    
    def _find_existing_error(self, table_name: Optional[str], record_guid: Optional[str], error_type: str) -> Optional[Dict[str, Any]]:
        """
        Sucht bestehenden Fehler mit gleicher Signatur
        
        DEDUPLIZIERUNGS-KEY: (table_name, record_guid, error_type)
        
        Args:
            table_name: Tabellenname
            record_guid: Datensatz-GUID
            error_type: Fehlertyp
            
        Returns:
            Dict|None: Bestehender Fehler oder None
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        if not table_name or not record_guid:
            return None
        
        # Alle Fehler laden (über PdvmDatenbank)
        from pdvm_datenbank import PdvmDatenbank
        errors_db = PdvmDatenbank('sys_error_log')
        all_errors = errors_db.alle_lesen()
        
        for error in all_errors:
            guid = error['uid']
            error_db = PdvmCentralDatenbank('sys_error_log', guid)
            
            # ✅ Verwende get_static_value für nicht-historische Daten
            error_table = error_db.get_static_value('ROOT', 'table_name')
            error_record = error_db.get_static_value('ROOT', 'record_guid')
            error_error_type = error_db.get_static_value('ROOT', 'error_type')
            
            if (error_table == table_name and 
                error_record == record_guid and 
                error_error_type == error_type):
                return {'uid': guid}
        
        return None
    
    def get_unacknowledged_errors(self, severity_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Holt alle unbestätigten Fehler (USER-SPEZIFISCH mit ABLAUFDATUM)
        
        LOGIK:
        - Prüft sys_error_acknowledgments Tabelle für aktuellen User
        - Fehler ist unbestätigt WENN:
          * Keine Bestätigung existiert ODER
          * Bestätigung ist abgelaufen (> 24 Stunden)
        
        Args:
            severity_filter: Liste von Schweregraden (z.B. ['error', 'critical'])
            
        Returns:
            List[Dict]: Liste aller unbestätigten Fehler
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        current_user = self.gcs.user_guid
        current_time = self.gcs.st_inst.PdvmDateTime
        
        # Alle Fehler laden (über PdvmDatenbank)
        from pdvm_datenbank import PdvmDatenbank
        errors_db = PdvmDatenbank('sys_error_log')
        all_errors = errors_db.alle_lesen()
        all_error_guids = [e['uid'] for e in all_errors]
        
        # Lade alle Bestätigungen (über PdvmDatenbank)
        acks_db = PdvmDatenbank('sys_error_acknowledgments')
        all_acks = acks_db.alle_lesen()
        all_ack_guids = [a['uid'] for a in all_acks]
        
        # Erstelle Lookup: error_guid → expires_at (nur für aktuellen User)
        acknowledged_errors = {}
        for ack_guid in all_ack_guids:
            ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', ack_guid)
            
            # ✅ Verwende get_static_value für nicht-historische Daten
            ack_user = ack_db.get_static_value('ROOT', 'user_guid')
            
            if ack_user == current_user:
                error_guid = ack_db.get_static_value('ROOT', 'error_guid')
                expires_at = ack_db.get_static_value('ROOT', 'expires_at')
                
                acknowledged_errors[error_guid] = expires_at
        
        unack_errors = []
        for error_guid in all_error_guids:
            error_db = PdvmCentralDatenbank('sys_error_log', error_guid)
            
            # ✅ Prüfe ob Bestätigung existiert und noch gültig
            if error_guid in acknowledged_errors:
                expires_at = acknowledged_errors[error_guid]
                if expires_at > current_time:
                    # Bestätigung noch gültig → überspringen
                    continue
            
            # ✅ Verwende get_static_value für nicht-historische Daten (sys_error_log ist historisch=0)
            severity = error_db.get_static_value('ROOT', 'severity')
            
            # Schweregrad-Filter
            if severity_filter and severity not in severity_filter:
                continue
            
            # Hole alle weiteren Felder (statisch)
            timestamp = error_db.get_static_value('ROOT', 'timestamp')
            last_occ = error_db.get_static_value('ROOT', 'last_occurrence')
            count = error_db.get_static_value('ROOT', 'occurrence_count') or 1
            context = error_db.get_static_value('ROOT', 'context_type')
            error_type = error_db.get_static_value('ROOT', 'error_type')
            message = error_db.get_static_value('ROOT', 'error_message')
            record_guid = error_db.get_static_value('ROOT', 'record_guid')
            table_name = error_db.get_static_value('ROOT', 'table_name')
            
            error_dict = {
                'uid': error_guid,
                'name': error_db.get_name(),
                'timestamp': timestamp,
                'last_occurrence': last_occ,
                'occurrence_count': count,
                'context_type': context,
                'error_type': error_type,
                'error_message': message,
                'severity': severity,
                'record_guid': record_guid,
                'table_name': table_name
            }
            
            # 🔍 DEBUG: Zeige was wir tatsächlich zurückgeben
            logger.debug(f"🔍 Fehler #{len(unack_errors)+1}:")
            logger.debug(f"   occurrence_count: {count} (type: {type(count)})")
            logger.debug(f"   last_occurrence: {last_occ} (type: {type(last_occ)})")
            logger.debug(f"   timestamp: {timestamp}")
            
            unack_errors.append(error_dict)
        
        logger.info(f"✅ {len(unack_errors)} unbestätigte Fehler gefunden")
        return unack_errors
    
    def acknowledge_error(self, log_guid: str, hours_until_expiry: int = 24):
        """
        Markiert Fehler als bestätigt (USER-SPEZIFISCH mit ABLAUFDATUM)
        
        ABLAUF:
        1. Erstellt Eintrag in sys_error_acknowledgments
        2. Setzt expires_at = jetzt + hours_until_expiry
        3. Nach Ablauf erscheint Fehler wieder
        
        Args:
            log_guid: GUID des Log-Eintrags
            hours_until_expiry: Stunden bis Bestätigung abläuft (Standard: 24h)
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        import allgemeines as all
        
        current_user = self.gcs.user_guid
        current_time = self.gcs.st_inst.PdvmDateTime
        
        # Berechne Ablaufdatum (PdvmDateTime + Stunden)
        # PdvmDateTime Format: YYYYDDD.FFFFFF (Jahr + Tag im Jahr + Tagesbruch)
        hours_fraction = hours_until_expiry / 24.0  # Bruch eines Tages
        expires_at = current_time + hours_fraction
        
        # Prüfe ob Bestätigung bereits existiert (über PdvmDatenbank)
        from pdvm_datenbank import PdvmDatenbank
        acks_db = PdvmDatenbank('sys_error_acknowledgments')
        all_acks = acks_db.alle_lesen()
        
        existing_ack_guid = None
        for ack in all_acks:
            ack_guid = ack['uid']
            ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', ack_guid)
            
            # ✅ Verwende get_static_value für nicht-historische Daten
            ack_error_guid = ack_db.get_static_value('ROOT', 'error_guid')
            ack_user_guid = ack_db.get_static_value('ROOT', 'user_guid')
            
            if ack_error_guid == log_guid and ack_user_guid == current_user:
                existing_ack_guid = ack_guid
                break
        
        if existing_ack_guid:
            # Update bestehende Bestätigung
            ack_db = PdvmCentralDatenbank('sys_error_acknowledgments', existing_ack_guid)
            ack_db.set_value('ROOT', 'acknowledged_at', current_time, current_time)
            ack_db.set_value('ROOT', 'expires_at', expires_at, current_time)
            ack_db.save_all_values()
            logger.info(f"✅ Bestätigung aktualisiert: {log_guid} (gültig bis {expires_at})")
        else:
            # Neue Bestätigung erstellen (mit PdvmCentralDatenbank OHNE GUID)
            ack_db = PdvmCentralDatenbank('sys_error_acknowledgments')  # ✅ Keine GUID beim Init
            
            # Alle Felder setzen
            ack_db.set_value('ROOT', 'error_guid', log_guid, current_time)
            ack_db.set_value('ROOT', 'user_guid', current_user, current_time)
            ack_db.set_value('ROOT', 'acknowledged_at', current_time, current_time)
            ack_db.set_value('ROOT', 'expires_at', expires_at, current_time)
            
            # Speichern (generiert automatisch neue GUID)
            ack_guid = ack_db.save_all_values()
            
            # Name setzen (NACH save, jetzt hat ack_db eine GUID)
            ack_db.set_name(f"{log_guid[:8]}|{current_user[:8]}")
            
            logger.info(f"✅ Fehler bestätigt: {log_guid} für User {current_user} (gültig bis {expires_at})")
    
    def acknowledge_all_errors(self, hours_until_expiry: int = 24):
        """
        Markiert alle Fehler als bestätigt
        
        Args:
            hours_until_expiry: Stunden bis Bestätigung abläuft (Standard: 24h)
        """
        unack = self.get_unacknowledged_errors()
        for error in unack:
            self.acknowledge_error(error['uid'], hours_until_expiry)
        
        logger.info(f"✅ {len(unack)} Fehler bestätigt (gültig für {hours_until_expiry}h)")


class ErrorLogDialog(QDialog):
    """
    Pop-up Dialog für unbestätigte Fehler
    
    Zeigt alle kritischen Fehler und ermöglicht Bestätigung
    """
    
    def __init__(self, errors: List[Dict[str, Any]], manager: PdvmErrorLogManager, parent=None):
        """
        Initialisiert Dialog
        
        Args:
            errors: Liste unbestätigter Fehler
            manager: Error-Log Manager für Bestätigung
            parent: Parent-Widget
        """
        super().__init__(parent)
        self.errors = errors
        self.manager = manager
        
        self.setWindowTitle("⚠️ PDVM Fehlerprotokoll")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h2>⚠️ {len(self.errors)} Fehler protokolliert</h2>")
        header.setStyleSheet("color: #d32f2f; padding: 10px;")
        layout.addWidget(header)
        
        info = QLabel(
            "Die folgenden Fehler sind während der Datenverarbeitung aufgetreten.\n"
            "Betroffene Datensätze wurden übersprungen und sind möglicherweise nicht sichtbar."
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 5px 10px; background-color: #fff3cd; border-radius: 5px;")
        layout.addWidget(info)
        
        # Fehler-Liste
        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setStyleSheet("font-family: 'Courier New'; font-size: 9pt;")
        
        # Formatierte Fehler-Ausgabe
        formatted_errors = []
        for i, error in enumerate(self.errors, 1):
            # Occurrence Info
            occurrence_info = ""
            if error.get('occurrence_count', 1) > 1:
                occurrence_info = f"Häufigkeit: {error['occurrence_count']}x aufgetreten\n"
                if error.get('last_occurrence'):
                    occurrence_info += f"Zuletzt:    {self._format_timestamp(error['last_occurrence'])}\n"
            
            formatted_errors.append(
                f"{'='*70}\n"
                f"FEHLER #{i} [{error['severity'].upper()}]\n"
                f"{'='*70}\n"
                f"Typ:       {error['error_type']}\n"
                f"Kontext:   {error['context_type']}\n"
                f"Zeitpunkt: {self._format_timestamp(error['timestamp'])}\n"
                f"{occurrence_info}"
                f"Tabelle:   {error['table_name']}\n"
                f"Datensatz: {error['record_guid']}\n"
                f"\nFehlermeldung:\n{error['error_message']}\n\n"
            )
        
        error_text.setText("\n".join(formatted_errors))
        layout.addWidget(error_text)
        
        # Buttons
        btn_acknowledge = QPushButton("✅ Alle Fehler bestätigen und schließen")
        btn_acknowledge.setStyleSheet(
            "background-color: #4caf50; color: white; padding: 10px; "
            "font-weight: bold; border-radius: 5px;"
        )
        btn_acknowledge.clicked.connect(self._acknowledge_and_close)
        layout.addWidget(btn_acknowledge)
        
        btn_close = QPushButton("Schließen (ohne Bestätigung)")
        btn_close.setStyleSheet("padding: 8px;")
        btn_close.clicked.connect(self.reject)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Formatiert Timestamp lesbar"""
        if not timestamp:
            return "Unbekannt"
        
        # Nutze GCS DateTime für Formatierung
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if gcs:
            dt = gcs.temp_dt_inst
            dt.PdvmDateTime = timestamp
            return dt.FormTimeStamp
        
        return str(timestamp)
    
    def _acknowledge_and_close(self):
        """Bestätigt alle Fehler und schließt Dialog"""
        self.manager.acknowledge_all_errors()
        self.accept()


# =============================================================================
# GLOBALE FUNKTIONEN (für einfache Verwendung)
# =============================================================================

_global_error_log_manager: Optional[PdvmErrorLogManager] = None


def get_error_log_manager() -> Optional[PdvmErrorLogManager]:
    """Holt globale Error-Log Manager Instanz"""
    return _global_error_log_manager


def initialize_error_log_manager(gcs) -> PdvmErrorLogManager:
    """
    Initialisiert globalen Error-Log Manager
    
    Args:
        gcs: Globale Systemsteuerung
        
    Returns:
        PdvmErrorLogManager: Manager-Instanz
    """
    global _global_error_log_manager
    _global_error_log_manager = PdvmErrorLogManager(gcs)
    return _global_error_log_manager


def log_error(
    context_guid: str,
    context_type: str,
    error_type: str,
    error_message: str,
    record_guid: Optional[str] = None,
    table_name: Optional[str] = None,
    severity: str = "error",
    additional_info: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Loggt Fehler (Wrapper für globalen Manager)
    
    Returns:
        str|None: GUID des Log-Eintrags oder None wenn Manager nicht initialisiert
    """
    manager = get_error_log_manager()
    if manager:
        return manager.log_error(
            context_guid=context_guid,
            context_type=context_type,
            error_type=error_type,
            error_message=error_message,
            record_guid=record_guid,
            table_name=table_name,
            severity=severity,
            additional_info=additional_info
        )
    else:
        logger.warning("⚠️ Error-Log Manager nicht initialisiert - Fehler nicht geloggt")
        return None


def check_new_errors(parent=None) -> bool:
    """
    Prüft auf neue unbestätigte Fehler und zeigt Pop-up
    
    Args:
        parent: Parent-Widget für Dialog
        
    Returns:
        bool: True wenn Fehler vorhanden waren
    """
    manager = get_error_log_manager()
    if not manager:
        return False
    
    # Hole kritische und normale Fehler (keine Warnings)
    errors = manager.get_unacknowledged_errors(severity_filter=['error', 'critical'])
    
    if errors:
        logger.warning(f"⚠️ {len(errors)} unbestätigte Fehler gefunden")
        dialog = ErrorLogDialog(errors, manager, parent)
        dialog.exec_()
        return True
    
    return False
