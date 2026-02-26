#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDVM Error Log Manager V6 - EINFACHE ARCHITEKTUR
=======================================================
Zentrales Error-Logging OHNE Pipeline-Komplexität

ARCHITEKTUR V6:
1. ✅ sys_error_log: Einfaches alle_lesen() + Schleife
2. ✅ Keine Pipeline (Overkill für < 100 Errors)
3. ✅ PdvmCentralDatenbank für Updates/Inserts
4. ✅ sys_error_acknowledgments zentral in GCS

WORKFLOW:
---------
1. add_error() wird aufgerufen
2. Alle Errors aus sys_error_log laden (alle_lesen)
3. In Schleife nach signature suchen
4. Update oder Insert via PdvmCentralDatenbank
5. Vorkommen in gcs._error_ack_db protokollieren
6. Flag setzen für Popup

VORTEILE:
- ✅ Einfach und robust
- ✅ Schnell für < 100 Einträge
- ✅ Keine Pipeline-Overhead
- ✅ Klare Error-Handling
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

# Controls für Error-Log
ERROR_LOG_CONTROLS = [
    'signature',           # Für Deduplication
    'error_type',
    'table_name',
    'record_guid',
    'user_guid',
    'timestamp',
    'last_occurrence',
    'occurrence_count',
    'error_message',
    'severity',
    'context_guid',
    'context_type',
]


class PdvmErrorLogManager:
    """
    EINFACHER Error-Manager V6 (OHNE Pipeline)
    
    FEATURES V6:
    - ✅ Einfaches alle_lesen() statt Pipeline
    - ✅ Robuste Error-Behandlung
    - ✅ Schnell für < 100 Errors
    """
    
    def __init__(self, gcs):
        """
        Initialisiert Error-Log Manager V6 - EINFACH
        
        Args:
            gcs: Globale Systemsteuerung
        """
        self.gcs = gcs
        logger.info("✅ Error-Log Manager V6 (EINFACH - ohne Pipeline) initialisiert")
    
    
    def start_collection(self):
        """Dummy-Methode für Kompatibilität"""
        logger.info("📥 Error-Sammlung gestartet (Dummy - Popup via finish_collection)")
    
    def add_error(
        self,
        table_name: str,
        record_guid: str,
        error_type: str,
        error_message: str,
        severity: str = "error",
        context_guid: Optional[str] = None,
        context_type: str = "table"
    ):
        """
        ✅ V6: EINFACHE Lösung ohne Pipeline (robuster!)
        
        WORKFLOW:
        1. Alle Errors aus sys_error_log laden (via alle_lesen)
        2. In Schleife nach signature suchen
        3. Update oder Insert via PdvmCentralDatenbank
        
        Args:
            table_name: Name der betroffenen Tabelle
            record_guid: GUID des fehlerhaften Datensatzes
            error_type: Fehlertyp (json_parse, attribute, type, etc.)
            error_message: Detaillierte Fehlermeldung
            severity: Schweregrad (warning, error, critical)
            context_guid: Optionale Kontext-GUID
            context_type: Kontext-Typ (table, view, dialog)
        
        Returns:
            str: Error-GUID
        """
        try:
            from pdvm_datetime import Pdvm_DateTime
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from pdvm_datenbank import PdvmDatenbank
            
            dt_inst = Pdvm_DateTime(self.gcs.country)
            timestamp = dt_inst.PdvmDateTimeNow()
            
            # Signature für Deduplication
            signature = f"{table_name}|{record_guid}|{error_type}"
            
            # ✅ EINFACH: Alle Errors laden
            errors_db = PdvmDatenbank('sys_error_log')
            all_errors = errors_db.alle_lesen()
            
            # ✅ EINFACH: Nach Signature suchen
            existing_guid = None
            for error_row in all_errors:
                error_guid = error_row['uid']
                # Prüfe signature im daten-Dict
                error_data = error_row.get('daten', {})
                if error_data.get('ROOT', {}).get('signature') == signature:
                    existing_guid = error_guid
                    break
            
            if existing_guid:
                # Error existiert bereits → Update
                error_db = PdvmCentralDatenbank('sys_error_log', existing_guid)
                
                # Hole aktuellen Count
                current_count = error_db.get_static_value('ROOT', 'occurrence_count') or 1
                new_count = current_count + 1
                
                # Update
                error_db.set_value('ROOT', 'occurrence_count', new_count, timestamp)
                error_db.set_value('ROOT', 'last_occurrence', timestamp, timestamp)
                error_db.save_all_values()
                
                # Vorkommen protokollieren
                self._add_vorkommen(existing_guid, timestamp)
                
                logger.info(f"🔄 Error existiert (Signature): {signature} → Count={new_count}")
                
                # Flag setzen
                self.gcs.set_property('pending_error_popup', True)
                self.gcs._db.save_all_values()
                
                return existing_guid
            
            else:
                # Neuer Error → Insert
                error_db = PdvmCentralDatenbank('sys_error_log')  # Ohne GUID
                
                # Alle Felder befüllen
                error_db.set_value('ROOT', 'timestamp', timestamp, timestamp)
                error_db.set_value('ROOT', 'last_occurrence', timestamp, timestamp)
                error_db.set_value('ROOT', 'occurrence_count', 1, timestamp)
                error_db.set_value('ROOT', 'error_type', error_type, timestamp)
                error_db.set_value('ROOT', 'error_message', error_message, timestamp)
                error_db.set_value('ROOT', 'table_name', table_name, timestamp)
                error_db.set_value('ROOT', 'record_guid', record_guid, timestamp)
                error_db.set_value('ROOT', 'severity', severity, timestamp)
                error_db.set_value('ROOT', 'context_guid', context_guid or table_name, timestamp)
                error_db.set_value('ROOT', 'context_type', context_type, timestamp)
                error_db.set_value('ROOT', 'user_guid', self.gcs.user_guid, timestamp)
                error_db.set_value('ROOT', 'signature', signature, timestamp)
                
                # Speichern (generiert automatisch GUID)
                error_guid = error_db.save_all_values()
                
                logger.info(f"✅ Neuer Error: {error_guid[:8]}... → {signature}")
                
                # Vorkommen protokollieren
                self._add_vorkommen(error_guid, timestamp)
                
                # Flag setzen
                self.gcs.set_property('pending_error_popup', True)
                self.gcs._db.save_all_values()
                
                return error_guid
        
        except Exception as e:
            logger.error(f"❌ Fehler in add_error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        
        # ✅ GCS-FLAG SETZEN: Popup muss angezeigt werden
        self.gcs.set_property('pending_error_popup', True)
        self.gcs._db.save_all_values()  # Persistent machen!
        logger.info("🚩 GCS-Flag gesetzt: pending_error_popup = True")
        
        # ✅ Punkt 10: Keine RAM-Sammlung mehr - direkt aus DB lesen beim Popup
        
        return error_guid
    
    def _add_vorkommen(self, error_guid: str, timestamp: float):
        """
        Protokolliert Vorkommen eines Errors in sys_error_acknowledgments
        
        Struktur:
          uid: user_guid
          daten: {
            "error_guid_1": {
              "VORKOMMEN": [timestamp1, timestamp2, timestamp3],  # Liste!
              "LAST_SHOW": timestamp  # Letztes Popup
            }
          }
        
        Args:
            error_guid: GUID des Errors aus sys_error_log
            timestamp: PdvmDateTime Timestamp des Vorkommens
        """
        try:
            import json
            
            # ✅ ZENTRALE INSTANZ: sys_error_acknowledgments (MIT user_guid)
            ack_db = self.gcs._error_ack_db
            
            # Lese bisherige Vorkommen-Liste
            vorkommen_json = ack_db.get_static_value(error_guid, 'VORKOMMEN')
            if vorkommen_json:
                try:
                    vorkommen_list = json.loads(vorkommen_json)
                    if not isinstance(vorkommen_list, list):
                        vorkommen_list = []
                except:
                    vorkommen_list = []
            else:
                vorkommen_list = []
            
            # Neues Vorkommen hinzufügen
            vorkommen_list.append(timestamp)
            
            # Zurück als JSON-String speichern
            ack_db.set_value(error_guid, 'VORKOMMEN', json.dumps(vorkommen_list), timestamp)
            
            # LAST_SHOW initialisieren (falls erstes Vorkommen)
            if len(vorkommen_list) == 1:
                ack_db.set_value(error_guid, 'LAST_SHOW', 0.0, timestamp)  # 0 = noch nie gezeigt
            
            ack_db.save_all_values()
            
            logger.info(f"📝 Vorkommen protokolliert: Error {error_guid[:8]}... → {len(vorkommen_list)} Vorkommen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Protokollieren von Vorkommen: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _find_existing_error_in_db(self, signature, table_name, record_guid, error_type):
        """
        Sucht existierenden Error in sys_error_log über Signature
        
        Returns:
            str: Error-GUID oder None
        """
        try:
            # ✅ ZENTRALE INSTANZ: Durchsuche gcs._error_log_db
            error_db = self.gcs._error_log_db
            
            # Durchsuche alle Gruppen (jede Gruppe = ein Error)
            for error_guid in error_db.data.keys():
                if error_guid == 'ROOT':  # ROOT überspringen
                    continue
                    
                stored_signature = error_db.get_static_value(error_guid, 'signature')
                if stored_signature == signature:
                    return error_guid
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Error-Suche: {e}")
            return None
    
    def acknowledge_errors(self, error_guids):
        """
        Bestätigt Errors (wird beim Popup-OK aufgerufen)
        
        Setzt LAST_SHOW auf aktuellen Timestamp → 24h Timer startet
        
        Args:
            error_guids (List[str]): Liste der Error-GUIDs zum Bestätigen
        """
        try:
            from pd_datetime import Pdvm_DateTime
            
            # Aktuelle Zeit
            dt_inst = Pdvm_DateTime(self.gcs.country)
            now = dt_inst.PdvmDateTimeNow()
            
            # ✅ ZENTRALE INSTANZ: sys_error_acknowledgments
            ack_db = self.gcs._error_ack_db
            
            for error_guid in error_guids:
                # Setze LAST_SHOW auf jetzt → 24h Timer startet
                ack_db.set_value(error_guid, 'LAST_SHOW', now, now)
                logger.info(f"✅ Error bestätigt: {error_guid[:8]}... → LAST_SHOW={now:.5f}")
            
            ack_db.save_all_values()
            logger.info(f"✅ {len(error_guids)} Errors bestätigt, 24h Timer gestartet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Bestätigen von Errors: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def finish_collection(self):
        """
        ✅ V3: Prüft GCS-Flag und zeigt Popup falls pending
        
        WORKFLOW:
        1. GCS-Flag prüfen: pending_error_popup?
        2. Falls True: Alle unbestätigten Errors aus DB laden
        3. Popup anzeigen
        4. Flag zurücksetzen
        """
        # ✅ GCS-FLAG PRÜFEN (persistent!)
        pending = self.gcs.get_property('pending_error_popup', 's')
        
        if not pending:
            logger.info("✅ Kein pending_error_popup Flag - kein Popup nötig")
            return
        
        logger.info("🚩 GCS-Flag gefunden: pending_error_popup = True")
        
        # ⚠️ KRITISCH: Flag SOFORT zurücksetzen BEVOR Popup (verhindert Loop!)
        self.gcs.set_property('pending_error_popup', False)
        self.gcs._db.save_all_values()  # Persistent machen!
        logger.info("🔒 Flag zurückgesetzt BEVOR Popup (Loop-Prevention)")
        
        # Lade ALLE unbestätigten Errors aus DB
        unacknowledged_errors = self._load_unacknowledged_errors()
        
        if not unacknowledged_errors:
            logger.warning("⚠️ Flag gesetzt aber keine Errors gefunden")
            return
        
        logger.info(f"📢 Zeige Popup mit {len(unacknowledged_errors)} unbestätigten Error(s)...")
        
        # Popup anzeigen (Flag bereits zurückgesetzt!)
        self._show_error_popup_from_db(unacknowledged_errors)
        
        logger.info("✅ Error-Popup angezeigt")
    
    def _load_unacknowledged_errors(self):
        """
        ✅ V6: EINFACH - Lädt Errors die angezeigt werden müssen (24h-Logik)
        
        Logik:
        - Error zeigen wenn: (jetzt - LAST_SHOW) > 24h ODER LAST_SHOW == 0
        
        Returns:
            List[Dict]: Error-Dicts für Popup
        """
        try:
            from pdvm_datetime import Pdvm_DateTime
            from pdvm_datenbank import PdvmDatenbank
            import json
            
            # Aktuelle Zeit
            dt_inst = Pdvm_DateTime(self.gcs.country)
            now = dt_inst.PdvmDateTimeNow()
            
            # 24 Stunden in PdvmDateTime Format (1 Tag = 1.0)
            ONE_DAY = 1.0
            
            # ✅ EINFACH: Alle Errors laden
            errors_db = PdvmDatenbank('sys_error_log')
            all_errors = errors_db.alle_lesen()
            
            # ✅ Hole Acknowledgments DB
            ack_db = self.gcs._error_ack_db
            
            error_list = []
            
            # ✅ EINFACH: Durch alle Errors iterieren
            for error_row in all_errors:
                error_guid = error_row['uid']
                error_data = error_row.get('daten', {}).get('ROOT', {})
                
                # Nur eigene Errors (user_guid prüfen)
                if error_data.get('user_guid') != self.gcs.user_guid:
                    continue
                
                # ✅ 24h-LOGIK: Prüfe LAST_SHOW
                last_show = ack_db.get_static_value(error_guid, 'LAST_SHOW') or 0.0
                
                # Zeige Error wenn:
                # 1. Noch nie gezeigt (LAST_SHOW == 0) ODER
                # 2. Mehr als 24h her ((now - LAST_SHOW) > 1.0)
                if last_show == 0.0 or (now - last_show) > ONE_DAY:
                    # Lade Vorkommen-Liste
                    vorkommen_json = ack_db.get_static_value(error_guid, 'VORKOMMEN')
                    vorkommen_list = []
                    if vorkommen_json:
                        try:
                            vorkommen_list = json.loads(vorkommen_json)
                        except:
                            pass
                    
                    error_list.append({
                        'guid': error_guid,
                        'table_name': error_data.get('table_name'),
                        'record_guid': error_data.get('record_guid'),
                        'error_type': error_data.get('error_type'),
                        'error_message': error_data.get('error_message'),
                        'severity': error_data.get('severity'),
                        'context_type': error_data.get('context_type'),
                        'timestamp': error_data.get('timestamp'),
                        'last_occurrence': error_data.get('last_occurrence'),
                        'occurrence_count': error_data.get('occurrence_count'),
                        'user_guid': error_data.get('user_guid'),
                        'vorkommen': vorkommen_list,  # ✅ Alle Vorkommen
                        'last_show': last_show  # ✅ Wann zuletzt gezeigt
                    })
            
            logger.info(f"📥 {len(error_list)} Errors müssen angezeigt werden (24h-Logik)")
            return error_list
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Errors aus DB: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _show_error_popup_from_db(self, errors: List[Dict[str, Any]]):
        """
        Zeigt formatiertes Popup mit Errors aus DB
        
        Args:
            errors: Liste von Error-Dicts aus sys_error_log
        """
        if not errors:
            return
        
        dialog = ErrorLogDialog(errors, self.gcs, parent=None)
        result = dialog.exec_()
        
        # ✅ Bei BESTÄTIGUNG: acknowledge_errors() aufrufen → 24h Timer startet
        if result == QDialog.Accepted:
            error_guids = [err['guid'] for err in errors]
            self.acknowledge_errors(error_guids)
            logger.info(f"✅ {len(error_guids)} Errors wurden bestätigt → 24h Timer gestartet")
        
        # ✅ Bei ABBRECHEN: Nichts tun → Errors werden beim nächsten alle_lesen() wieder angezeigt
        elif result == QDialog.Rejected:
            logger.info(f"🔄 User hat Popup abgebrochen → {len(errors)} Errors bleiben aktiv")


class ErrorLogDialog(QDialog):
    """
    ✅ V6: Formatiertes Popup für Error-Anzeige mit 3 Aktionen:
    
    1. 24h bestätigen → LAST_SHOW wird gesetzt, 24h keine Anzeige
    2. Kopieren → Text in Zwischenablage für Admin
    3. Abbrechen → Popup schließen, Errors bleiben aktiv
    """
    
    def __init__(self, errors: List[Dict[str, Any]], gcs, parent=None):
        """
        Args:
            errors: Liste von Error-Dicts aus sys_error_log
            gcs: Globale Systemsteuerung (für Formatierung)
            parent: Parent-Widget
        """
        super().__init__(parent)
        self.errors = errors
        self.gcs = gcs
        
        self.setWindowTitle(f"⚠️ Datenbankfehler gefunden ({len(errors)} Fehler)")
        self.setModal(True)
        self.resize(900, 650)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt UI mit formatiertem Text und 3 Buttons"""
        layout = QVBoxLayout()
        
        # Textfeld mit formatiertem Error-Output
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(self.gcs.layout.get_monospace_font())
        
        # Errors formatieren
        formatted_text = self._format_errors()
        self.text_edit.setPlainText(formatted_text)
        
        layout.addWidget(self.text_edit)
        
        # ✅ Buttons: 24h bestätigen, Kopieren, Abbrechen
        button_layout = QHBoxLayout()
        
        # Button 1: 24h bestätigen (QDialog.Accepted)
        btn_acknowledge = QPushButton("⏰ 24h bestätigen")
        btn_acknowledge.setToolTip("Fehler werden 24 Stunden lang nicht mehr angezeigt")
        btn_acknowledge.clicked.connect(self.accept)
        button_layout.addWidget(btn_acknowledge)
        
        # Button 2: Kopieren (für Admin)
        btn_copy = QPushButton("📋 Kopieren")
        btn_copy.setToolTip("Text in Zwischenablage kopieren zum Senden an Admin")
        btn_copy.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(btn_copy)
        
        # Button 3: Abbrechen (QDialog.Rejected)
        btn_cancel = QPushButton("❌ Abbrechen")
        btn_cancel.setToolTip("Popup schließen, Fehler bleiben aktiv und werden beim nächsten Laden wieder angezeigt")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _format_errors(self) -> str:
        """
        Formatiert alle Errors im gewünschten Format
        
        Returns:
            str: Formatierter Multi-Line-String
        """
        from pdvm_datetime import Pdvm_DateTime
        
        lines = []
        
        for i, error in enumerate(self.errors, start=1):
            # Zeitstempel formatieren
            dt_inst = Pdvm_DateTime(self.gcs.country)
            dt_inst.PdvmDateTime = error['timestamp']
            formatted_time = dt_inst.FormTimeStamp
            
            # Severity in Großbuchstaben
            severity_upper = error['severity'].upper()
            
            # Error-Block Header
            lines.append("=" * 70)
            lines.append(f"FEHLER #{i} [{severity_upper}]")
            lines.append("=" * 70)
            lines.append(f"Typ:       {error['error_type']}")
            
            # Häufigkeit + Zeitpunkt (wie User gewünscht)
            if error['occurrence_count'] > 1:
                # Bei mehrfachen: "Häufigkeit + Zuletzt"
                dt_inst_last = Pdvm_DateTime(self.gcs.country)
                dt_inst_last.PdvmDateTime = error['last_occurrence']
                formatted_last = dt_inst_last.FormTimeStamp
                
                lines.append(f"Häufigkeit: {error['occurrence_count']}x aufgetreten")
                lines.append(f"Zuletzt:   {formatted_last}")
            else:
                # Bei einmalig: "Zeitpunkt"
                lines.append(f"Zeitpunkt: {formatted_time}")
            
            lines.append(f"Tabelle:   {error['table_name']}")
            lines.append(f"Datensatz: {error['record_guid']}")
            lines.append("")
            lines.append("Fehlermeldung:")
            lines.append(error['error_message'])
            lines.append("")
            lines.append("")
        
        return "\n".join(lines)
    
    def _copy_to_clipboard(self):
        """Kopiert formatierten Text in Zwischenablage"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        logger.info("📋 Error-Log in Zwischenablage kopiert")


# ========================================
# GLOBALE FUNKTIONEN (Kompatibilität)
# ========================================

def log_error(*args, **kwargs):
    """
    Legacy-Funktion für direktes Error-Logging
    
    ⚠️ DEPRECATED: Verwende stattdessen gcs.error_log_manager.add_error()
    """
    from pdvm_central_systemsteuerung import get_gcs
    gcs = get_gcs()
    if gcs and hasattr(gcs, 'error_log_manager'):
        return gcs.error_log_manager.add_error(*args, **kwargs)
    else:
        logger.error("❌ GCS nicht verfügbar für log_error()")
        return None


def check_new_errors():
    """
    Legacy-Funktion für Error-Check
    
    ⚠️ DEPRECATED: Wird nicht mehr benötigt (Popup kommt automatisch nach finish_collection())
    """
    logger.info("ℹ️ check_new_errors() aufgerufen - wird nicht mehr benötigt (V2 Pipeline)")
    pass
