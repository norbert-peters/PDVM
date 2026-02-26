# -*- coding: utf-8 -*-
"""
Modified Tracking System - Multi-User Synchronisation

ZWECK:
- Erkennt Änderungen an Tabellen
- Ermöglicht automatische View-Aktualisierung
- User-spezifisches Caching für Performance
- Funktioniert mandantenübergreifend

ARCHITEKTUR:
┌─────────────────────────────────────────────────────────────┐
│ sys_systemsteuerung (System-GUID: 0000...)                  │
│                                                              │
│  gruppe=tabellenname                                         │
│  feld=MODIFIED_AT                                            │
│  value=PdvmDateTime (z.B. 2024312.123456)                   │
│                                                              │
│  ✅ SINGLE SOURCE OF TRUTH für Tabellen-Änderungen         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ sys_systemsteuerung (User-GUID: z.B. 4886ad26...)          │
│                                                              │
│  gruppe=USER                                                 │
│  untergruppe=000...                                          │
│  feld=tabellenname                                           │
│  value=last_read_timestamp                                   │
│                                                              │
│  ✅ Jeder User cached seine letzte Leseoperation           │
└─────────────────────────────────────────────────────────────┘

AUTOR: Norbert Peters
DATUM: 06.12.2025
"""
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


def update_modified_tracking(table_name):
    """
    Aktualisiert MODIFIED_AT Timestamp für eine Tabelle (nach Speicherung)
    
    VERWENDUNG:
    - In save_all_values() nach erfolgreicher Speicherung
    - In db.speichern() nach UPDATE/INSERT
    
    Args:
        table_name (str): Name der geänderten Tabelle
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # PdvmDateTime für aktuellen Timestamp holen
        from pd_datetime import Pdvm_DateTime
        temp_dt = Pdvm_DateTime()
        current_timestamp = temp_dt.PdvmDateTime
        
        # System-Satz in sys_systemsteuerung aktualisieren
        system_guid = "00000000-0000-0000-0000-000000000000"
        sys_db = PdvmCentralDatenbank('sys_systemsteuerung', system_guid)
        
        # MODIFIED_AT für diese Tabelle setzen
        sys_db.set_value(table_name, 'MODIFIED_AT', current_timestamp)
        sys_db.save_all_values()
        
        logger.info(f"🔄 Modified Tracking aktualisiert für '{table_name}' (Timestamp: {current_timestamp})")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Modified Tracking Update fehlgeschlagen für '{table_name}': {e}")
        return False


def check_modified_and_should_refresh(table_name):
    """
    Prüft ob Tabelle seit letztem User-Zugriff geändert wurde
    
    VERWENDUNG:
    - In View-Controller vor View-Anzeige
    - Gibt True zurück wenn View neu geladen werden sollte
    
    Args:
        table_name (str): Name der zu prüfenden Tabelle
        
    Returns:
        bool: True wenn View neu geladen werden sollte, False wenn Cache verwendet werden kann
    """
    try:
        # GCS holen
        gcs = get_gcs()
        if not gcs:
            logger.warning("⚠️ GCS nicht verfügbar - lade View sicher neu")
            return True
        
        # System-MODIFIED_AT holen
        system_guid = "00000000-0000-0000-0000-000000000000"
        sys_db = PdvmCentralDatenbank('sys_systemsteuerung', system_guid)
        system_modified, _ = sys_db.get_value(table_name, 'MODIFIED_AT')
        
        if not system_modified:
            # Keine Tracking-Daten vorhanden = erste Verwendung oder alte Tabelle
            logger.debug(f"ℹ️ Kein Modified Tracking für '{table_name}' - lade View neu")
            return True
        
        # User-last_read holen
        user_guid = gcs.user_guid
        user_db = PdvmCentralDatenbank('sys_systemsteuerung', user_guid)
        user_last_read, _ = user_db.get_value('USER/000', table_name)
        
        if not user_last_read:
            # User hat diese Tabelle noch nie geladen
            logger.info(f"🆕 Erster Zugriff von User auf '{table_name}' - lade View neu")
            
            # User-last_read initialisieren
            user_db.set_value('USER/000', table_name, system_modified)
            user_db.save_all_values()
            return True
        
        # Vergleich: System vs User
        system_time = float(system_modified)
        user_time = float(user_last_read)
        
        if system_time > user_time:
            # Tabelle wurde geändert seit letztem User-Zugriff
            logger.info(f"🔄 Tabelle '{table_name}' wurde geändert - lade View neu")
            logger.debug(f"   System: {system_time}, User: {user_time}")
            
            # User-last_read aktualisieren
            user_db.set_value('USER/000', table_name, system_modified)
            user_db.save_all_values()
            return True
        else:
            # Tabelle unverändert - Cache verwenden
            logger.info(f"✅ Tabelle '{table_name}' unverändert - verwende Cache")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Modified-Check fehlgeschlagen für '{table_name}': {e}")
        # Im Fehlerfall: sicher neu laden
        return True


def initialize_user_tracking(table_name):
    """
    Initialisiert User-Tracking für eine Tabelle (nach erstem Load)
    
    VERWENDUNG:
    - Optional nach View-Load, falls check_modified_and_should_refresh() nicht verwendet wird
    
    Args:
        table_name (str): Name der geladenen Tabelle
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # GCS holen
        gcs = get_gcs()
        if not gcs:
            logger.warning("⚠️ GCS nicht verfügbar - überspringe User-Tracking Init")
            return False
        
        # System-MODIFIED_AT holen
        system_guid = "00000000-0000-0000-0000-000000000000"
        sys_db = PdvmCentralDatenbank('sys_systemsteuerung', system_guid)
        system_modified, _ = sys_db.get_value(table_name, 'MODIFIED_AT')
        
        if not system_modified:
            # Keine System-Daten = nichts zu initialisieren
            return False
        
        # User-last_read setzen
        user_guid = gcs.user_guid
        user_db = PdvmCentralDatenbank('sys_systemsteuerung', user_guid)
        user_db.set_value('USER/000', table_name, system_modified)
        user_db.save_all_values()
        
        logger.debug(f"✅ User-Tracking initialisiert für '{table_name}'")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ User-Tracking Init fehlgeschlagen für '{table_name}': {e}")
        return False
