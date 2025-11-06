#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Dropdown Manager
====================

Zentrale Klasse für alle Dropdown-Funktionalitäten.
Verwaltet Dropdown-Optionen, Übersetzungen und Display-Werte.
"""

import logging
from typing import Dict, Any, List, Optional
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class PdvmDropdownManager:
    """
    Manager für alle Dropdown-Funktionalitäten.
    Behandelt Dropdown-Optionen, Übersetzungen und Display-Werte.
    """
    
    def __init__(self, db_name: str = "PdvmManager.db"):
        self.db_name = db_name
        logger.info(f"🔧 DropdownManager initialisiert für DB: {db_name}")
    
    def get_dropdown_options_from_data(self, table_name: str, field_name: str, dropdown_config: dict) -> Dict[str, str]:
        """
        Zentrale Methode: Erzeugt Dropdown-Optionen basierend auf tatsächlich in der Tabelle vorhandenen Werten.
        
        Args:
            table_name: Name der Tabelle (z.B. "persondaten")
            field_name: Name des Feldes (z.B. "ANREDE") 
            dropdown_config: Konfiguration mit "table", "key", "value" für Übersetzungen
            
        Returns:
            Dict[str, str]: {key: display_text} Mapping aller in den Daten vorkommenden Werte
        """
        options = {}
        
        try:
            # 1. Alle tatsächlich vorhandenen Werte aus der Tabelle sammeln
            unique_values = self._collect_unique_values_from_table(table_name, field_name)
            logger.info(f"🔍 Gefundene eindeutige Werte in {table_name}.{field_name}: {unique_values}")
            
            if not unique_values:
                logger.warning(f"⚠️ Keine Werte für {field_name} in {table_name} gefunden")
                return {}
            
            # 2. Für jeden gefundenen Wert den Display-Text ermitteln
            for value in unique_values:
                if value and str(value).strip():  # Leere Werte überspringen
                    display_text = self.get_dropdown_display_value(str(value), field_name, dropdown_config)
                    options[str(value)] = display_text
            
            logger.info(f"✅ Dropdown-Optionen für {field_name}: {len(options)} Optionen")
            return options
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dropdown-Optionen für {field_name}: {e}")
            return {}
    
    def get_dropdown_display_value(self, raw_value: str, field_name: str, dropdown_config: dict) -> str:
        """
        Übersetzt einen Raw-Wert zu seinem Display-Text für Dropdown-Felder.
        
        Args:
            raw_value: Der rohe Wert aus der Datenbank
            field_name: Name des Feldes
            dropdown_config: Dropdown-Konfiguration
            
        Returns:
            str: Übersetzter Display-Text oder Raw-Wert als Fallback
        """
        if not raw_value:
            return ""
        
        try:
            dropdown_table = dropdown_config.get("table", "dropdowndaten")
            dropdown_key = dropdown_config.get("key")
            dropdown_group = dropdown_config.get("value", "ANREDE")
            
            if not dropdown_key:
                return str(raw_value)
            
            # Dropdown-Daten laden
            dropdown_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=dropdown_table,
                guid=dropdown_key
            )
            
            dropdown_data = dropdown_db.lesen()
            if not dropdown_data or "ROOT" not in dropdown_data:
                return str(raw_value)
            
            # Werte-Gruppe finden
            value_group = dropdown_data["ROOT"].get(dropdown_group, {})
            if not value_group or "werte" not in value_group:
                return str(raw_value)
            
            # Passenden Eintrag suchen
            for entry in value_group["werte"]:
                if str(entry.get("key", "")) == str(raw_value):
                    # Priorität: de > en > key
                    display_text = entry.get("de") or entry.get("en") or str(raw_value)
                    return display_text
            
            # Fallback: Raw-Wert
            return str(raw_value)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Übersetzen des Dropdown-Werts {raw_value}: {e}")
            return str(raw_value) if raw_value else ""
    
    def _collect_unique_values_from_table(self, table_name: str, field_name: str) -> List[Any]:
        """
        Sammelt alle eindeutigen Werte für ein Feld aus einer Tabelle.
        
        Args:
            table_name: Tabellenname
            field_name: Feldname
            
        Returns:
            List[Any]: Liste der eindeutigen Werte
        """
        unique_values = set()
        
        try:
            # Alle Datensätze aus der Tabelle laden
            table_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=table_name,
                guid=None  # Alle Datensätze
            )
            
            all_records = table_db.lesen_alle()
            if not all_records:
                return []
            
            # Durch alle Datensätze iterieren und Werte sammeln
            for record in all_records:
                try:
                    # Daten aus JSON-Spalte extrahieren
                    data_json = record.get("daten", "{}")
                    if isinstance(data_json, str):
                        import json
                        data = json.loads(data_json)
                    else:
                        data = data_json
                    
                    # Wert für das Feld sammeln
                    if "ROOT" in data:
                        field_value = data["ROOT"].get(field_name)
                        if field_value and str(field_value).strip():
                            unique_values.add(field_value)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Verarbeiten von Datensatz: {e}")
                    continue
            
            return sorted(list(unique_values))
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sammeln der Werte aus {table_name}.{field_name}: {e}")
            return []
    
    def get_dropdown_options_for_field(self, field_config: dict, table_name: str) -> Dict[str, str]:
        """
        Holt Dropdown-Optionen für ein spezifisches Feld basierend auf der Konfiguration.
        
        Args:
            field_config: Feld-Konfiguration mit Dropdown-Informationen
            table_name: Tabellenname für die Datenbasis
            
        Returns:
            Dict[str, str]: Dropdown-Optionen {key: display_text}
        """
        try:
            field_name = field_config.get("feld", "")
            dropdown_config = field_config.get("dropdown_config", {})
            
            if not dropdown_config:
                # Fallback: dropdown direkt aus field_config
                dropdown_config = field_config.get("dropdown", {})
            
            if not dropdown_config:
                logger.warning(f"⚠️ Keine Dropdown-Konfiguration für {field_name}")
                return {}
            
            return self.get_dropdown_options_from_data(table_name, field_name, dropdown_config)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dropdown-Optionen für Feld: {e}")
            return {}
    
    def translate_value(self, value: Any, field_config: dict) -> str:
        """
        Übersetzt einen Wert basierend auf der Feld-Konfiguration.
        
        Args:
            value: Zu übersetzender Wert
            field_config: Feld-Konfiguration mit Dropdown-Informationen
            
        Returns:
            str: Übersetzter Wert oder Original-Wert als Fallback
        """
        if not value:
            return ""
        
        try:
            field_type = field_config.get("type", "")
            if field_type != "dropdown":
                return str(value)
            
            field_name = field_config.get("feld", "")
            dropdown_config = field_config.get("dropdown_config", {})
            
            if not dropdown_config:
                dropdown_config = field_config.get("dropdown", {})
            
            if not dropdown_config:
                return str(value)
            
            return self.get_dropdown_display_value(str(value), field_name, dropdown_config)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Übersetzen des Werts: {e}")
            return str(value) if value else ""
