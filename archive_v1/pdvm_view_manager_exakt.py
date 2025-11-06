#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PdvmViewManager - EXAKTE IMPLEMENTIERUNG nach USER-SPEZIFIKATION
Implementiert den linearen 6-Schritte-Ablauf in der ge                           else:
                    # Keine Daten gefunden - Basis-Struktur übernehmen
                    logger.info(f"ℹ️ Keine Daten in PdvmCentralDatenbank (Gruppe: {self.view_guid}) - übernehme Basis-Struktur")
                    self.display_view_control = deepcopy(self.basis_view_control)
                    
                    # Fehlende Attribute ergänzen
                    self._ergaenge_fehlende_attribute()
                    
                    # In PdvmCentralDatenbank speichern
                    self._display_control_in_systemsteuerung_ablegen()
                    logger.info("✅ Basis-Struktur mit ergänzten Attributen in PdvmCentralDatenbank gespeichert")
                    break                 # Keine Daten gefunden - Basis-Struktur übernehmen
                    logger.info(f"ℹ️ Keine Daten in PdvmCentralDatenbank (Gruppe: {self.view_guid}) - übernehme Basis-Struktur")
                    self.display_view_control = deepcopy(self.basis_view_control)
                    
                    # Fehlende Attribute ergänzen
                    self._ergaenze_fehlende_attribute()
                    
                    # In PdvmCentralDatenbank speichern
                    self._display_control_in_systemsteuerung_ablegen()
                    logger.info("✅ Basis-Struktur mit ergänzten Attributen in PdvmCentralDatenbank gespeichert")
                    breaknfolge
"""

import sys
import json
import logging
from typing import Any, Dict, List, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class PdvmViewManager:
    """
    EXAKTER ViewManager - implementiert exakt die vom User spezifizierte Reihenfolge:
    
    1. Initialisierung: PdvmCentralDatenbank für Viewdaten → get_value_view() 
       → Vollständige Basistabelle + Basis_View_Control_Struktur
    
    2. Systemsteuerung: Daten aus Gruppe=view_guid lesen → Display_View_Control_Struktur
    3. View-Control-Aufbau: display_view_control über basis_view_control → EXAKTE Reihenfolge
    4. Spalten-Filterung: Nur sichtbare Spalten (show=True) → get_sichtbare_spalten()
    5. Daten-Anwendung: display_view_control auf aktuelle_tabelle → get_aktuelle_tabelle()
    6. Fortgeschrittene Funktionen: get_alle_spalten_info(), Expert-Modus-Integration
    """
    
    def get_alle_spalten_info(self) -> List[Dict[str, Any]]:
        """Gibt detaillierte Informationen zu allen Spalten zurück"""
        if not self.display_view_control:
            return []
        
        spalten_info = []
        for col in self.display_view_control.columns:
            info = {
                'name': col['name'],
                'show': col.get('show', False),
                'expert': col.get('expert', False),
                'order': col.get('order', 0),
                'type': col.get('type', 'unknown'),
                'anzeige': col.get('anzeige', col['name'])
            }
            spalten_info.append(info)
        
        return spalten_info
    
    def get_spalten_info(self) -> List[Dict[str, Any]]:
        """Alias für get_alle_spalten_info für Kompatibilität"""
        return self.get_alle_spalten_info()

    def __init__(
        self,
        view_guid: str,
        view_config: dict,
        central_systemsteuerung,
        db_name: str = "PdvmManager.db",
        stichtag: Optional[float] = None
    ):
        """
        Initialisierung nach USER-SPEZIFIKATION
        """
        self.view_guid = view_guid
        self.view_config = view_config
        self.central_systemsteuerung = central_systemsteuerung
        self.db_name = db_name
        self.stichtag = stichtag
        
        # Datenstrukturen nach Spezifikation
        self.basis_view_control = None       # Unveränderliche Basis-Struktur
        self.display_view_control = None     # Display-Control-Struktur (änderbar)
        self.vollstaendige_basistabelle = [] # Vollständige Basisdaten (alle Spalten)
        self.aktuelle_tabelle = []           # Aktuelle Tabelle nach Display-Control
        
        logger.info(f"🔹 PdvmViewManager initialisiert für view_guid: {view_guid}")
        
        # SCHRITT 1: Basis-Daten laden (EXAKT nach Spezifikation)
        self._schritt1_basis_daten_laden()
        
        # SCHRITT 2: Display-Control aus Systemsteuerung (EXAKT nach Spezifikation)
        self._schritt2_display_control_aus_systemsteuerung()
        
        # SCHRITT 3: Tabelle aufbauen (EXAKT nach Spezifikation)
        self._schritt3_tabelle_aufbauen()
    
    def _schritt1_basis_daten_laden(self):
        """
        SCHRITT 1: In der Initialisierung von PdvmViewManager erstellen wir für die Viewdaten 
        eine Instanz von PdvmCentralDatenbank. Hier erhalten wir mit der Funktion get_value_view 
        die vollständig Basistabelle mit allen Spalten (_original, _show und dummy). 
        Dazu wird die vollständige Basis_View_Control Struktur übergeben.
        """
        logger.info("🔧 SCHRITT 1: Basis-Daten laden")
        
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # View-Tabelle ermitteln
            table_name = self.view_config["ROOT"]["view_table"]
            
            # PdvmCentralDatenbank-Instanz für Viewdaten erstellen
            view_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name=table_name,
                guid=None  # Keine spezifische GUID - alle Daten laden
            )
            
            # get_value_view() aufrufen → vollständige Basistabelle + Basis_View_Control_Struktur
            result = view_db.get_value_view(self.view_config, self.stichtag)
            
            if isinstance(result, tuple) and len(result) == 2:
                self.basis_view_control, self.vollstaendige_basistabelle = result
                logger.info(f"✅ Vollständige Basistabelle geladen: {len(self.vollstaendige_basistabelle)} Datensätze")
                logger.info(f"✅ Basis_View_Control_Struktur: {len(self.basis_view_control.columns)} Spalten")
                
                # Alle Spalten loggen
                alle_spalten = [col['name'] for col in self.basis_view_control.columns]
                logger.info(f"📋 Alle Spalten (_original, _show, dummy): {alle_spalten}")
            else:
                logger.error("❌ get_value_view() lieferte nicht das erwartete Tuple-Format")
                self.vollstaendige_basistabelle = []
                self.basis_view_control = None
            
        except Exception as e:
            logger.error(f"❌ Fehler in SCHRITT 1: {e}")
            self.vollstaendige_basistabelle = []
            self.basis_view_control = None
    
    def _schritt2_display_control_aus_systemsteuerung(self):
        """
        SCHRITT 2: Display_View_Control_Struktur aus zentraler Systemsteuerung laden.
        Automatische Datenkorrektur: Falls Attribute fehlen → ergänzen → speichern → neu laden.
        Arbeitet so lange, bis alle Daten vollständig und korrekt sind.
        """
        logger.info("🔧 SCHRITT 2: Display-Control aus Systemsteuerung")
        
        if not self.basis_view_control:
            logger.error("❌ Keine Basis_View_Control_Struktur verfügbar")
            return
        
        # Endlos-Schleife bis Daten vollständig und korrekt sind
        while True:
            try:
                # 1. Daten aus PdvmCentralDatenbank lesen (NICHT CentralSystemsteuerung!)
                display_control_data = self.daten_laden.central_datenbank.get_value(
                    gruppe=self.view_guid,
                    feld="display_view_control"
                )
                
                if display_control_data and display_control_data.get("wert"):
                    # Daten gefunden - in Control-Struktur umwandeln
                    control_dict = display_control_data.get("wert")
                    self.display_view_control = self._dict_zu_control_struktur(control_dict)
                    logger.info(f"✅ Display_View_Control aus PdvmCentralDatenbank geladen (Gruppe: {self.view_guid})")
                    
                    # 2. Prüfen, ob alle erforderlichen Attribute vorhanden sind
                    if self._sind_alle_attribute_vollstaendig():
                        # Alles vollständig - weiterarbeiten
                        logger.info("✅ Alle Attribute vollständig - arbeite mit diesen Daten")
                        break
                    else:
                        # 3. Attribute fehlen - automatisch ergänzen
                        logger.info("⚠️ Attribute unvollständig - ergänze automatisch")
                        self._ergaenze_fehlende_attribute()
                        
                        # Ergänzte Daten in PdvmCentralDatenbank speichern
                        self._display_control_in_systemsteuerung_ablegen()
                        logger.info("✅ Ergänzte Daten in PdvmCentralDatenbank gespeichert")
                        
                        # 4. Neu laden (nächster Schleifendurchlauf)
                        continue
                        
                else:
                    # Keine Daten gefunden - Basis-Struktur übernehmen
                    logger.info(f"ℹ️ Keine Daten in Systemsteuerung (Gruppe: {self.view_guid}) - übernehme Basis-Struktur")
                    self.display_view_control = deepcopy(self.basis_view_control)
                    
                    # Fehlende Attribute ergänzen
                    self._ergaenze_fehlende_attribute()
                    
                    # In Systemsteuerung speichern
                    self._display_control_in_systemsteuerung_ablegen()
                    self.central_systemsteuerung.save_values()
                    logger.info("✅ Basis-Struktur mit allen Attributen in Systemsteuerung gespeichert")
                    
                    # Neu laden (nächster Schleifendurchlauf)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Fehler in SCHRITT 2: {e}")
                # Fallback: Basis-Control mit vollständigen Attributen
                self.display_view_control = deepcopy(self.basis_view_control)
                self._ergaenze_fehlende_attribute()
                break
    
    def _schritt3_tabelle_aufbauen(self):
        """
        SCHRITT 3: Anhand der Display_View_Control_Struktur wird die Tabelle mit allen Eigenschaften aufgebaut.
        KOMPLETT GETRENNTE MODI:
        - Expert-Mode: Verwendet 'show' und 'order'
        - Normal-Mode: Verwendet 'show_show' und 'show_order' (völlig unabhängig!)
        """
        logger.info("🔧 SCHRITT 3: Tabelle mit GETRENNTEN Modi aufbauen")
        
        if not self.display_view_control or not self.vollstaendige_basistabelle:
            logger.error("❌ Display_View_Control_Struktur oder vollständige Basistabelle fehlt")
            self.aktuelle_tabelle = []
            return
        
        try:
            # Expert-Modus Status ermitteln
            expert_mode_active = self.is_expert_mode_active()
            logger.info(f"🎯 Aktueller Modus: {'Expert' if expert_mode_active else 'Normal'}")
            
            # KOMPLETT GETRENNTE LOGIK PRO MODUS
            if expert_mode_active:
                # === EXPERT-MODE: Verwendet 'show' und 'order' ===
                logger.info("🔧 Expert-Mode: Verwende 'show' und 'order' Attribute")
                sichtbare_spalten = []
                
                for col in self.display_view_control.columns:
                    show_val = col.get('show', False)
                    col_name = col.get('name', '?')
                    
                    if show_val:
                        sichtbare_spalten.append(col_name)
                        logger.debug(f"   Expert-Mode: '{col_name}' hinzugefügt (show={show_val})")
                    else:
                        logger.debug(f"   Expert-Mode: '{col_name}' übersprungen (show={show_val})")
                
                # Sortierung nach 'order'
                sortierte_spalten = sorted(
                    sichtbare_spalten,
                    key=lambda col_name: self._get_expert_order(col_name)
                )
                logger.info(f"🔧 Expert-Mode: {len(sortierte_spalten)} Spalten nach 'order' sortiert")
                
            else:
                # === NORMAL-MODE: Verwendet 'show_show' und 'show_order' ===
                logger.info("👤 Normal-Mode: Verwende 'show_show' und 'show_order' Attribute")
                sichtbare_spalten = []
                
                for col in self.display_view_control.columns:
                    show_show_val = col.get('show_show', False)
                    col_name = col.get('name', '?')
                    
                    # WICHTIG: Normal-Mode ignoriert 'expert' und 'show' komplett!
                    # Nur 'show_show' entscheidet über Sichtbarkeit
                    if show_show_val:
                        sichtbare_spalten.append(col_name)
                        logger.debug(f"   Normal-Mode: '{col_name}' hinzugefügt (show_show={show_show_val})")
                    else:
                        logger.debug(f"   Normal-Mode: '{col_name}' übersprungen (show_show={show_show_val})")
                
                # Sortierung nach 'show_order'
                sortierte_spalten = sorted(
                    sichtbare_spalten,
                    key=lambda col_name: self._get_normal_order(col_name)
                )
                logger.info(f"👤 Normal-Mode: {len(sortierte_spalten)} Spalten nach 'show_order' sortiert")
            
            # Aktuelle Tabelle mit gefilterten Spalten aufbauen
            self.aktuelle_tabelle = []
            for row in self.vollstaendige_basistabelle:
                # Nur sichtbare Spalten in richtiger Reihenfolge
                gefilterte_row = {col: row.get(col, "") for col in sortierte_spalten}
                self.aktuelle_tabelle.append(gefilterte_row)
            
            logger.info(f"✅ Tabelle aufgebaut: {len(self.aktuelle_tabelle)} Zeilen, {len(sortierte_spalten)} Spalten")
            logger.info(f"📋 Sichtbare Spalten in Reihenfolge: {sortierte_spalten}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tabellenaufbau: {e}")
            self.aktuelle_tabelle = []

    def _get_expert_order(self, column_name: str) -> int:
        """Ermittelt die Expert-Mode Order-Position einer Spalte (verwendet 'order')"""
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                return col.get('order', 9999)
        return 9999

    def _get_normal_order(self, column_name: str) -> int:
        """Ermittelt die Normal-Mode Order-Position einer Spalte (verwendet 'show_order')"""
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                return col.get('show_order', 9999)
        return 9999
    
    def _get_spalten_order(self, column_name: str) -> int:
        """Ermittelt die Order-Position einer Spalte (bevorzugt show_order wenn vorhanden)"""
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                # WICHTIG: show_order hat Vorrang für Normal-Modus Spalten-Verschiebung
                # Wenn show_order vorhanden ist, verwende es (Normal-Modus Reihenfolge)
                if 'show_order' in col and col['show_order'] is not None:
                    return col['show_order']
                # Sonst verwende order (Expert-Modus oder Fallback)
                return col.get('order', 9999)
        return 9999

    def _get_order_for_mode(self, column_name: str, expert_mode: bool) -> int:
        """Ermittelt die Order-Position einer Spalte basierend auf dem aktuellen Modus"""
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                if expert_mode:
                    # Expert-Mode: Verwende immer 'order' (alle Spalten)
                    return col.get('order', 9999)
                else:
                    # Normal-Mode: Verwende 'show_order' für Normal-Spalten, 
                    # aber diese Funktion wird nur für Normal-Spalten aufgerufen
                    if 'show_order' in col and col['show_order'] is not None:
                        return col['show_order']
                    # Fallback für Normal-Spalten ohne show_order
                    return col.get('order', 9999)
        return 9999
    
    def _dict_zu_control_struktur(self, control_data):
        """Konvertiert Dict/List zurück zu Control-Struktur"""
        if not control_data:
            return None
        
        try:
            from pdvm_central_datenbank import ColumnControl
            
            control = ColumnControl()
            
            # Handle both dict and list formats
            if isinstance(control_data, dict):
                # Dict-Format (neu): {"columns": [...], "metadata": {...}}
                columns_data = control_data.get("columns", [])
                control.metadata = control_data.get("metadata", {})
                logger.info("📋 Lade Control-Struktur aus Dict-Format")
            elif isinstance(control_data, list):
                # List-Format (alt): [column1, column2, ...]
                columns_data = control_data
                control.metadata = {}
                logger.info("📋 Lade Control-Struktur aus List-Format (Legacy)")
            else:
                logger.error(f"❌ Unbekanntes Control-Data Format: {type(control_data)}")
                return None
            
            # Spalten wiederherstellen
            for col_data in columns_data:
                if isinstance(col_data, dict):
                    control.columns.append(col_data)
                else:
                    logger.warning(f"⚠️ Überspringe ungültigen Spalten-Eintrag: {col_data}")
            
            logger.info(f"✅ Control-Struktur geladen: {len(control.columns)} Spalten")
            return control
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Konvertieren Data → Control-Struktur: {e}")
            logger.error(f"   Data-Typ: {type(control_data)}")
            logger.error(f"   Data-Inhalt (erste 200 Zeichen): {str(control_data)[:200]}")
            return None
    
    def _control_struktur_zu_dict(self, control_structure) -> dict:
        """Konvertiert Control-Struktur zu Dict für Systemsteuerung"""
        if not control_structure:
            return {}
        
        return {
            "columns": [dict(col) for col in control_structure.columns],
            "metadata": getattr(control_structure, 'metadata', {})
        }
    
    def _display_control_in_systemsteuerung_ablegen(self):
        """
        Legt Display_View_Control_Struktur korrekt in die PdvmCentralDatenbank ab.
        Verwendet die richtige Struktur: Gruppe=view_guid, Feld="display_view_control"
        """
        try:
            if not self.display_view_control:
                logger.error("❌ Keine Display_View_Control_Struktur zum Speichern")
                return
                
            # Control-Struktur zu Dict konvertieren
            control_dict = self._control_struktur_zu_dict(self.display_view_control)
            
            # WICHTIG: Verwende PdvmCentralDatenbank (daten_laden) statt CentralSystemsteuerung
            # Speichere unter Gruppe=view_guid, Feld="display_view_control"
            result = self.daten_laden.central_datenbank.set_value(
                gruppe=self.view_guid,
                feld="display_view_control", 
                wert=control_dict
            )
            
            if result:
                logger.info(f"✅ Display_View_Control korrekt in PdvmCentralDatenbank gespeichert (Gruppe: {self.view_guid})")
            else:
                logger.error(f"❌ Fehler beim Speichern in PdvmCentralDatenbank (Gruppe: {self.view_guid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ablegen in PdvmCentralDatenbank: {e}")
    
    # PUBLIC API METHODS nach Spezifikation
    
    def get_aktuelle_tabelle(self) -> List[Dict[str, Any]]:
        """Gibt die aktuelle Tabelle zurück (nach Display_View_Control_Struktur)"""
        return self.aktuelle_tabelle
    
    def get_sichtbare_spalten(self) -> List[str]:
        """Gibt die aktuell sichtbaren Spalten in richtiger Reihenfolge zurück"""
        if not self.display_view_control:
            return []
        
        sichtbare_spalten = []
        for col in self.display_view_control.columns:
            if col.get('show', False):
                sichtbare_spalten.append(col['name'])
        
        # Nach Order sortieren
        return sorted(sichtbare_spalten, key=lambda col: self._get_spalten_order(col))
    
    def aenderung_spalten_auswahl(self, column_name: str, sichtbar: bool):
        """
        SCHRITT 4: Jede Änderung an der Auswahl, Sortierung, Reihenfolge etc. wird in die 
        Display_Control_Struktur eingetragen und in der Instanz_Systemsteuerung abgelegt. 
        Dieses wird persistent gemacht. Und mit der Struktur die Tabelle entsprechende verändert oder neu gebaut.
        """
        logger.info(f"🔧 SCHRITT 4: Änderung Spalten-Auswahl - {column_name} → sichtbar={sichtbar}")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display_View_Control_Struktur verfügbar")
            return
        
        # Änderung in Display_Control_Struktur eintragen
        spalte_gefunden = False
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                col['show'] = sichtbar
                spalte_gefunden = True
                break
        
        if spalte_gefunden:
            # In Instanz_Systemsteuerung ablegen
            self._display_control_in_systemsteuerung_ablegen()
            
            # Persistent machen
            self.central_systemsteuerung.save_values()
            logger.info("✅ Änderung persistent in Systemsteuerung gespeichert")
            
            # Tabelle entsprechend verändert/neu gebaut
            self._schritt3_tabelle_aufbauen()
            logger.info("✅ Tabelle entsprechend neu aufgebaut")
        else:
            logger.error(f"❌ Spalte {column_name} nicht gefunden")
    
    def aenderung_spalten_reihenfolge(self, column_name: str, neue_order: int):
        """
        SCHRITT 4: Änderung der Reihenfolge wird in Display_Control_Struktur eingetragen
        """
        logger.info(f"🔧 SCHRITT 4: Änderung Spalten-Reihenfolge - {column_name} → Order={neue_order}")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display_View_Control_Struktur verfügbar")
            return
        
        # Änderung in Display_Control_Struktur eintragen
        for col in self.display_view_control.columns:
            if col['name'] == column_name:
                col['order'] = neue_order
                break
        
        # In Instanz_Systemsteuerung ablegen → persistent → Tabelle aktualisiert
        self._display_control_in_systemsteuerung_ablegen()
        self.central_systemsteuerung.save_values()
        self._schritt3_tabelle_aufbauen()
        
        logger.info("✅ Reihenfolge-Änderung abgeschlossen")
    
    def expert_modus_spalte_abwaehlen(self, column_name: str):
        """
        SCHRITT 5: Wenn der Expert Modus aktiv ist, kann man auch die die Expert Spalten abwählen. 
        In diesem Falle werde bei diesen Spalten der Expert Modus auf False gesetzt und show auf true. 
        Damit können dann Spalten, die im Expert Mode waren als ganz normale Spalten verwaltet werden.
        """
        logger.info(f"🔧 SCHRITT 5: Expert-Spalte abwählen - {column_name} → Expert=False, Show=True")
        
        if not self.display_view_control:
            logger.error("❌ Keine Display_View_Control_Struktur verfügbar")
            return
        
        # Expert-Spalte zu normaler Spalte umwandeln
        for col in self.display_view_control.columns:
            if col['name'] == column_name and col.get('expert', False):
                col['expert'] = False  # Expert Modus auf False
                col['show'] = True     # show auf true
                logger.info(f"✅ Expert-Spalte {column_name} zu normaler Spalte umgewandelt")
                break
        
        # In Systemsteuerung ablegen → persistent → Tabelle aktualisiert
        self._display_control_in_systemsteuerung_ablegen()
        self.central_systemsteuerung.save_values()
        self._schritt3_tabelle_aufbauen()
        
        logger.info("✅ Expert-Spalte kann jetzt als normale Spalte verwaltet werden")
    
    def reset_auf_basis(self):
        """
        SCHRITT 6: Beim Reset wird einfach die Basis_Control_Struktur in die Display_Control_Struktur 
        übernommen und wie eine sonstige Änderung in der Systemsteuerung gespeichert und aktualisiert.
        """
        logger.info("🔧 SCHRITT 6: Reset - Basis_Control_Struktur → Display_Control_Struktur")
        
        if not self.basis_view_control:
            logger.error("❌ Keine Basis_Control_Struktur verfügbar")
            return
        
        # Basis_Control_Struktur in Display_Control_Struktur übernehmen
        self.display_view_control = deepcopy(self.basis_view_control)
        logger.info("✅ Basis_Control_Struktur in Display_Control_Struktur übernommen")
        
        # Wie sonstige Änderung: in Systemsteuerung speichern und aktualisieren
        self._display_control_in_systemsteuerung_ablegen()
        self.central_systemsteuerung.save_values()
        self._schritt3_tabelle_aufbauen()
        
        logger.info("✅ Reset abgeschlossen - Display_Control_Struktur zurückgesetzt")
    
    def get_alle_spalten_info(self) -> List[Dict[str, Any]]:
        """Gibt Informationen über alle verfügbaren Spalten zurück"""
        if not self.display_view_control:
            return []
        
        spalten_info = []
        for col in self.display_view_control.columns:
            info = {
                'name': col['name'],
                'show': col.get('show', False),
                'expert': col.get('expert', False),
                'order': col.get('order', 0),
                'type': col.get('type', 'unknown'),
                'anzeige': col.get('anzeige', col['name'])
            }
            spalten_info.append(info)
        
        return spalten_info
    
    def get_spalten_info(self) -> List[Dict[str, Any]]:
        """Alias für get_alle_spalten_info für Kompatibilität"""
        return self.get_alle_spalten_info()
    
    def get_expert_spalten(self) -> List[str]:
        """Gibt alle Expert-Spalten zurück"""
        if not self.display_view_control:
            return []
        
        expert_spalten = []
        for col in self.display_view_control.columns:
            if col.get('expert', False):
                expert_spalten.append(col['name'])
        
        return expert_spalten

    def _sind_alle_attribute_vollstaendig(self) -> bool:
        """
        Prüft, ob alle erforderlichen Attribute in der Display-Control-Struktur vorhanden sind.
        Erforderliche Attribute für GETRENNTE Modi:
        - Expert-Mode: name, show, order, expert
        - Normal-Mode: name, show_show, show_order, expert
        """
        if not self.display_view_control or not self.display_view_control.columns:
            return False
        
        # Alle Spalten müssen diese Attribute haben
        basis_attribute = ['name', 'expert']
        expert_mode_attribute = ['show', 'order']  # Für Expert-Mode
        normal_mode_attribute = ['show_show', 'show_order']  # Für Normal-Mode
        
        for col in self.display_view_control.columns:
            # Basis-Attribute prüfen
            for attr in basis_attribute:
                if attr not in col or col.get(attr) is None:
                    logger.debug(f"⚠️ Basis-Attribut '{attr}' fehlt in Spalte '{col.get('name', '?')}'")
                    return False
            
            # Expert-Mode Attribute prüfen
            for attr in expert_mode_attribute:
                if attr not in col:
                    logger.debug(f"⚠️ Expert-Mode Attribut '{attr}' fehlt in Spalte '{col.get('name', '?')}'")
                    return False
            
            # Normal-Mode Attribute prüfen
            for attr in normal_mode_attribute:
                if attr not in col:
                    logger.debug(f"⚠️ Normal-Mode Attribut '{attr}' fehlt in Spalte '{col.get('name', '?')}'")
                    return False
        
        logger.debug("✅ Alle erforderlichen Attribute für beide Modi sind vollständig vorhanden")
        return True

    def _ergaenze_fehlende_attribute(self):
        """
        Ergänzt fehlende Attribute in der Display-Control-Struktur.
        KOMPLETT GETRENNTE MODI:
        - Expert-Mode: show, order 
        - Normal-Mode: show_show, show_order (völlig unabhängig!)
        """
        if not self.display_view_control or not self.display_view_control.columns:
            logger.warning("⚠️ Keine Display-Control-Struktur für Attribut-Ergänzung")
            return
        
        logger.info("🔧 Ergänze fehlende Attribute für GETRENNTE Expert/Normal-Modi...")
        
        # 1. Standardwerte für ALLE Spalten setzen
        for col in self.display_view_control.columns:
            # Expert-Mode Attribute (bestehend)
            if 'show' not in col:
                col['show'] = True  # Expert-Mode Sichtbarkeit
            if 'expert' not in col:
                col['expert'] = False  # Spalten-Typ (nur für Info)
            if 'order' not in col:
                col['order'] = 999  # Expert-Mode Reihenfolge
            
            # Normal-Mode Attribute (NEU - komplett getrennt!)
            if 'show_show' not in col:
                # Normal-Mode Sichtbarkeit: Standardmäßig alle Spalten sichtbar
                # (User kann dann individuell ein-/ausschalten)
                col['show_show'] = True
            if 'show_order' not in col:
                col['show_order'] = None  # Wird unten gesetzt
        
        # 2. show_order für ALLE Spalten generieren (Normal-Mode ist unabhängig von expert!)
        all_columns = list(self.display_view_control.columns)
        
        # Nach Expert-Mode order sortieren (als Basis für Normal-Mode Reihenfolge)
        all_columns.sort(key=lambda x: x.get('order', 999))
        
        # show_order Werte vergeben - durchnummeriert 1, 2, 3, ... für ALLE Spalten
        for i, col in enumerate(all_columns, 1):
            col['show_order'] = i
            logger.debug(f"✅ Normal-Mode: show_order={i} für Spalte '{col.get('name', '?')}'")
        
        logger.info("✅ Getrennte Modi-Attribute erfolgreich ergänzt!")
        logger.info(f"   Expert-Mode: Verwendet 'show' und 'order' für alle Spalten")
        logger.info(f"   Normal-Mode: Verwendet 'show_show' und 'show_order' für alle Spalten")
        
        logger.info("✅ Fehlende Attribute automatisch ergänzt")

    def _ensure_show_order_values(self):
        """
        VERALTET: Wird durch _ergaenze_fehlende_attribute ersetzt.
        Diese Methode bleibt für Kompatibilität erhalten.
        """
        logger.debug("ℹ️ _ensure_show_order_values aufgerufen - verwende _ergaenze_fehlende_attribute")
        self._ergaenze_fehlende_attribute()

    def is_expert_mode_active(self) -> bool:
        """
        Prüft, ob Expert-Modus aktuell aktiv ist.
        Expert-Modus ist aktiv wenn mindestens eine Expert-Spalte in Expert-Mode sichtbar ist (show=True).
        """
        if not self.display_view_control or not self.display_view_control.columns:
            return False
        
        # Expert-Modus ist aktiv, wenn mindestens eine Expert-Spalte sichtbar ist (show=True)
        for col in self.display_view_control.columns:
            if col.get('expert', False) and col.get('show', False):
                return True
        
        return False

    def aenderung_expert_umschalten(self) -> bool:
        """
        Schaltet zwischen Normal- und Expert-Modus um.
        GETRENNTE MODI: Funktioniert nur auf Expert-Mode 'show' Attribut.
        Normal-Mode 'show_show' bleibt unverändert!
        """
        try:
            if not self.display_view_control or not self.display_view_control.columns:
                print("   ⚠️ Keine Display-Control Struktur für Expert-Umschaltung")
                return False
            
            # Expert-Modus Status ermitteln (sind Expert-Spalten in Expert-Mode sichtbar?)
            expert_mode_active = self.is_expert_mode_active()
            
            # Expert-Modus umschalten (nur Expert-Mode 'show' Attribut ändern)
            if expert_mode_active:
                # Expert-Modus AUS: Expert-Spalten in Expert-Mode verstecken
                for col in self.display_view_control.columns:
                    if col.get('expert', False):
                        col['show'] = False  # Nur Expert-Mode Sichtbarkeit ändern
                print("   🔧 Expert-Modus AUS: Expert-Spalten versteckt (show=False)")
            else:
                # Expert-Modus EIN: Expert-Spalten in Expert-Mode anzeigen
                for col in self.display_view_control.columns:
                    if col.get('expert', False):
                        col['show'] = True  # Nur Expert-Mode Sichtbarkeit ändern
                print("   🔧 Expert-Modus EIN: Expert-Spalten angezeigt (show=True)")
            
            # Control-Struktur in PdvmCentralDatenbank speichern
            self._display_control_in_systemsteuerung_ablegen()
            print(f"   ✅ Expert-Modus Änderung in PdvmCentralDatenbank gespeichert")
            
            # Tabelle neu aufbauen
            self._schritt3_tabelle_aufbauen()
            return True
                
        except Exception as e:
            print(f"❌ Fehler beim Expert-Modus umschalten: {e}")
            return False

    def aenderung_reset(self) -> bool:
        """Setzt Display-Control auf Basis-Control zurück mit korrekten Standard-Werten"""
        try:
            if not self.basis_view_control:
                print("   ❌ Keine Basis-Control Struktur für Reset verfügbar")
                return False
            
            # Schritt 1: Display Control von Basis Control erstellen mit KORREKTEN Standard-Werten
            print("   🔄 Reset: Display-Control von Basis-Control erstellen...")
            self.display_view_control = deepcopy(self.basis_view_control)
            
            # WICHTIG: Standard-Werte für show korrekt setzen (nur _show Spalten sichtbar)
            for col in self.display_view_control.columns:
                col_name = col['name']
                if col_name.endswith('_show') or col_name == 'uid_show':
                    # Show-Spalten: sichtbar
                    col['show'] = True
                    col['expert'] = False
                elif col_name.endswith('_original') or col_name == 'uid_original':
                    # Original-Spalten: nicht sichtbar, nur im Expert-Modus
                    col['show'] = False
                    col['expert'] = True
                elif col_name == 'dummy':
                    # Dummy-Spalte: nicht sichtbar
                    col['show'] = False
                    col['expert'] = False
                else:
                    # System-Spalten: Standard-Verhalten beibehalten
                    pass
            
            # Schritt 2: In Systemsteuerung speichern
            if self.central_systemsteuerung:
                control_dict = self._control_struktur_zu_dict(self.display_view_control)
                self.central_systemsteuerung.set_value(
                    gruppe=self.view_guid,
                    feld="display_view_control",
                    wert=control_dict
                )
                self.central_systemsteuerung.save_values()
                print(f"   ✅ Reset: Display-Control in Systemsteuerung zurückgesetzt")
                # Tabelle neu aufbauen
                self._schritt3_tabelle_aufbauen()
                return True
            else:
                print("   ⚠️ Reset: Keine Systemsteuerung verfügbar")
                return False
                
        except Exception as e:
            print(f"❌ Fehler beim Zurücksetzen der View: {e}")
            return False


if __name__ == "__main__":
    print("🎯 PdvmViewManager - EXAKTE IMPLEMENTIERUNG nach USER-SPEZIFIKATION")
    print("=" * 70)
    print("1. Basis-Daten laden: PdvmCentralDatenbank → get_value_view() → vollständige Basistabelle")
    print("2. Display-Control: Systemsteuerung Gruppe=view_guid → Display_View_Control_Struktur")
    print("3. Tabelle aufbauen: Display_View_Control_Struktur → Tabelle mit allen Eigenschaften")
    print("4. Änderungen: Display_Control → Systemsteuerung → persistent → Tabelle aktualisiert") 
    print("5. Expert-Modus: Expert-Spalten → expert=False, show=True → normale Verwaltung")
    print("6. Reset: Basis_Control → Display_Control → Systemsteuerung → aktualisiert")
    print("=" * 70)
