# pdvm_view_daten_manager.py
"""
PDVM View Daten Manager - Zentrale Datenlogik
=============================================

Wird mit Widget initialisiert
Liefert Basistabelle von PdvmCentralDatenbank.get_value_view
"""

import logging
from typing import List, Dict, Tuple, Any
from pdvm_controls_manager import PdvmControlsManager

logger = logging.getLogger(__name__)

class PdvmViewDatenManager:
    """
    Zentrale Datenlogik für PDVM Views
    
    Initialisierung mit call_daten und Widget-Referenz
    """
    
    def __init__(self, call_daten, widget=None):
        self.call_daten = call_daten
        self.widget = widget
        
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.stichtag = call_daten.get("stichtag", 1001.0)
        self.mode = call_daten.get("mode", "user")  # admin oder user
        
        # Aktueller View-Mode (normal/expert)
        self.current_view_mode = "normal"  # Startet immer im Normal-Mode
        
        # NEUER EINFACHER CONTROLS MANAGER
        self.controls_manager = PdvmControlsManager()
        
        # Datenstrukturen
        self.view_config = None
        self.basis_data = []
        self.basis_columns = []
        
        # Cached Daten für beide Modi
        self.normal_mode_data = None
        self.normal_mode_controls = None
        self.expert_mode_data = None 
        self.expert_mode_controls = None
        
        # Provider für Spaltenparameter-Dialog
        self.provider = None
        
        # Initialisierung
        self._load_view_config()
        self._load_basis_data()
    
    def is_expert_mode(self):
        """Kompatibilitäts-Alias für Spaltenparameter-Dialog"""
        return self.current_view_mode == "expert"
    
    def _load_view_config(self):
        """View-Konfiguration laden"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # View-Config aus viewdaten laden
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            
            self.view_config = view_db.lesen()
            
            if self.view_config:
                logger.info(f"✅ View-Config geladen für: {self.view_guid}")
            else:
                logger.error(f"❌ Keine View-Config gefunden für: {self.view_guid}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Config: {e}")
            self.view_config = None
    
    def _load_basis_data(self):
        """Basisdaten über PdvmValueViewProvider laden für beide Modi"""
        try:
            if not self.view_config:
                logger.warning("⚠️ Keine View-Config - kann keine Daten laden")
                return
            
            # NEUE ARCHITEKTUR: PdvmValueViewProvider verwenden
            from pdvm_value_view_provider import PdvmValueViewProvider
            
            value_provider = PdvmValueViewProvider(db_name="PdvmManager.db")
            self.provider = value_provider  # Für Spaltenparameter-Dialog speichern
            
            # Normal-Mode Daten laden
            self.normal_mode_controls, self.normal_mode_data = value_provider.get_value_view(
                view_config=self.view_config, 
                stichtag=self.stichtag,
                mode="normal",
                user_guid=self.user_guid
            )
            
            # Expert-Mode Daten laden (nur wenn Admin-Modus)
            if self.mode == "admin":
                self.expert_mode_controls, self.expert_mode_data = value_provider.get_value_view(
                    view_config=self.view_config,
                    stichtag=self.stichtag, 
                    mode="expert",
                    user_guid=self.user_guid
                )
            else:
                # User-Mode: Expert-Mode nicht verfügbar
                self.expert_mode_controls = None
                self.expert_mode_data = None
            
            # Basis-Daten auf aktuellen Mode setzen
            self._update_current_mode_data()
            
            # CONTROLS MANAGER mit Daten laden
            if self.normal_mode_controls:
                self.controls_manager.load_from_provider_data(self.normal_mode_controls)
                self.controls_manager.set_mode(self.current_view_mode)
            
            logger.info(f"✅ Basisdaten geladen - Normal: {len(self.normal_mode_data) if self.normal_mode_data else 0} Zeilen")
            logger.info(f"✅ Controls Manager: {self.controls_manager.get_stats()}")
            if self.expert_mode_data:
                logger.info(f"✅ Expert-Mode: {len(self.expert_mode_data)} Zeilen")
            else:
                logger.info("🚫 Expert-Mode nicht verfügbar (User-Modus)")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Basisdaten über ValueViewProvider: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.basis_data = []
            self.basis_columns = []
    
    def switch_view_mode(self, new_mode: str):
        """
        Wechselt zwischen Normal-Mode und Expert-Mode
        
        Args:
            new_mode: "normal" oder "expert"
        """
        try:
            if new_mode not in ["normal", "expert"]:
                logger.warning(f"⚠️ Ungültiger View-Mode: {new_mode}")
                return False
            
            if new_mode == "expert" and self.mode != "admin":
                logger.warning("⚠️ Expert-Mode nicht verfügbar (kein Admin-Modus)")
                return False
            
            if new_mode == "expert" and not self.expert_mode_data:
                logger.warning("⚠️ Expert-Mode Daten nicht geladen")
                return False
            
            old_mode = self.current_view_mode
            self.current_view_mode = new_mode
            
            # Controls Manager über Mode-Wechsel informieren
            self.controls_manager.set_mode(new_mode)
            
            self._update_current_mode_data()
            
            logger.info(f"🔄 View-Mode gewechselt: {old_mode} → {new_mode}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Mode-Wechsel: {e}")
            return False
    
    def _update_current_mode_data(self):
        """Aktualisiert basis_data und basis_columns basierend auf current_view_mode"""
        try:
            if self.current_view_mode == "expert" and self.expert_mode_data:
                # Expert-Mode
                self.basis_data = self.expert_mode_data
                if hasattr(self.expert_mode_controls, 'columns'):
                    self.basis_columns = [col.get('name', f'col_{i}') for i, col in enumerate(self.expert_mode_controls.columns)]
                else:
                    self.basis_columns = list(self.basis_data[0].keys()) if self.basis_data else []
                
                logger.info(f"� Expert-Mode aktiv: {len(self.basis_columns)} Spalten")
                
            else:
                # Normal-Mode (default)
                self.basis_data = self.normal_mode_data or []
                if hasattr(self.normal_mode_controls, 'columns'):
                    self.basis_columns = [col.get('name', f'col_{i}') for i, col in enumerate(self.normal_mode_controls.columns)]
                else:
                    self.basis_columns = list(self.basis_data[0].keys()) if self.basis_data else []
                
                logger.info(f"📊 Normal-Mode aktiv: {len(self.basis_columns)} Spalten")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Mode-Daten: {e}")
            self.basis_data = []
            self.basis_columns = []
    
    def get_table_data(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Aktuelle Tabellendaten und Spalten zurückgeben
        
        Returns:
            Tuple[List[Dict], List[str]]: (Datenzeilen, Spaltennamen)
        """
        try:
            # Für erste Stufe: Einfach alle Basisdaten zurückgeben
            return self.basis_data, self.basis_columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Tabellendaten: {e}")
            return [], []
    
    def get_current_controls(self, for_dialog=False):
        """
        Aktuelle Control-Struktur je nach Mode zurückgeben
        EINFACH: Controls Manager liefert die korrekten Controls für den aktuellen Mode
        
        Args:
            for_dialog: Wenn True, bereitet Controls für Dialog vor (display_* Felder)
        
        Returns:
            Controls-Objekt mit Spalten-Definitionen
        """
        try:
            logger.info(f"🔍 get_current_controls - current_view_mode: {self.current_view_mode}")
            
            if for_dialog:
                # Dialog-Modus: Controls für Dialog vorbereiten
                self.controls_manager.prepare_for_dialog(self.current_view_mode)
                controls = self.controls_manager.get_dialog_controls(self.current_view_mode)
                logger.info(f"📋 {len(controls)} Controls für Dialog vorbereitet - Mode: {self.current_view_mode}")
            else:
                # Normaler Modus: Controls für Tabellen-Anzeige
                controls = self.controls_manager.get_controls_for_mode(self.current_view_mode)
                logger.info(f"🔍 Controls Manager liefert: {len(controls)} Controls für Mode '{self.current_view_mode}'")
            
            # Legacy-Format für bestehende UI (kann später weg)
            if for_dialog:
                # Dialog braucht Controls mit display_* Feldern
                legacy_format = [control.to_dict() for control in controls]
            else:
                legacy_format = self.controls_manager.to_legacy_format(self.current_view_mode)
            
            # Mock-Objekt mit columns Attribut für Legacy-Kompatibilität
            class ControlsResult:
                def __init__(self, columns):
                    self.columns = columns
            
            return ControlsResult(legacy_format)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der aktuellen Controls: {e}")
            return None
    
    def save_column_configuration(self, working_columns, mode):
        """
        EINFACHE Speicher-Methode: Dialog-Änderungen in Controls Manager übernehmen
        
        Args:
            working_columns: Liste der bearbeiteten Spalten vom Dialog (mit display_* Feldern)
            mode: "normal" oder "expert"
        
        Returns:
            bool: Erfolgreich gespeichert
        """
        try:
            logger.info(f"💾 save_column_configuration gestartet - Mode: {mode}")
            logger.info(f"💾 Zu speichern: {len(working_columns)} Spalten")
            
            # SCHRITT 1: Dialog-Änderungen in Controls Manager übernehmen
            self._update_controls_from_dialog_data(working_columns, mode)
            
            # SCHRITT 2: Controls Manager Änderungen in Mode-spezifische Felder übernehmen  
            self.controls_manager.apply_dialog_changes(mode)
            
            # SCHRITT 3: Transformierte Controls für Provider abrufen
            current_controls = self.controls_manager.get_controls_for_mode(mode)
            
            # SCHRITT 4: Über den Provider mit transformierten Controls speichern
            if self.provider and hasattr(self.provider, '_save_show_order_to_systemsteuerung'):
                success = self.provider._save_show_order_to_systemsteuerung(
                    self.user_guid, 
                    self.view_config, 
                    current_controls  # Verwende transformierte Controls statt working_columns
                )
                
                if success:
                    logger.info(f"✅ Spalten-Konfiguration erfolgreich gespeichert - Mode: {mode}")
                    # Nach dem Speichern: Daten neu laden
                    self._reload_data_after_save()
                    return True
                else:
                    logger.error(f"❌ Fehler beim Speichern über Provider")
                    return False
            else:
                logger.error(f"❌ Kein Provider oder Speicher-Methode verfügbar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spalten-Konfiguration: {e}")
            return False
    
    def _reload_data_after_save(self):
        """Nach dem Speichern: Daten neu laden um Änderungen zu übernehmen"""
        try:
            logger.info("🔄 Lade Daten nach Speichern neu...")
            self._load_basis_data()  # Basisdaten neu laden
            
            # Widget benachrichtigen um Tabelle zu aktualisieren
            if self.widget and hasattr(self.widget, 'load_data'):
                logger.info("🔄 Aktualisiere Widget-Tabelle nach Speichern...")
                self.widget.load_data()
            else:
                logger.warning("⚠️ Widget hat keine load_data Methode - Tabelle wird nicht aktualisiert")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuladen nach Speichern: {e}")

    def get_expert_mode_data(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Expert-Mode Daten (für spätere Erweiterung)
        
        Returns:
            Tuple[List[Dict], List[str]]: (Expert-Datenzeilen, Expert-Spaltennamen)
        """
        try:
            # Für erste Stufe: Gleiche Daten wie Normal-Mode
            return self.get_table_data()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Expert-Mode Daten: {e}")
            return [], []
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Filter-Optionen für Spalten (für spätere Erweiterung)
        
        Returns:
            Dict[str, List[str]]: {Spaltenname: [Eindeutige Werte]}
        """
        try:
            filter_options = {}
            
            for column in self.basis_columns:
                # Eindeutige Werte für jede Spalte sammeln
                unique_values = set()
                for row in self.basis_data:
                    value = row.get(column, '')
                    if value not in [None, '']:
                        unique_values.add(str(value))
                
                filter_options[column] = sorted(list(unique_values))[:10]  # Erste 10 Werte
            
            return filter_options
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Filter-Optionen: {e}")
            return {}
    
    def refresh_data(self):
        """Daten neu laden"""
        try:
            logger.info("🔄 Daten werden neu geladen...")
            self._load_basis_data()
            
            # Widget benachrichtigen (falls verfügbar)
            if self.widget and hasattr(self.widget, 'load_data'):
                self.widget.load_data()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuladen der Daten: {e}")
    
    def _update_controls_from_dialog_data(self, working_columns, mode):
        """
        Aktualisiert Controls Manager aus Dialog-Daten (working_columns mit display_* Feldern)
        
        Args:
            working_columns: Liste der bearbeiteten Spalten-Daten vom Dialog
            mode: "normal" oder "expert" - für welchen Mode wurden die Änderungen gemacht
        """
        try:
            logger.info(f"🔄 Aktualisiere Controls Manager mit {len(working_columns)} Dialog-Änderungen")
            
            for col_data in working_columns:
                column_name = col_data.get('name')
                if not column_name:
                    continue
                
                control = self.controls_manager.get_control(column_name)
                if not control:
                    continue
                
                # Dialog-Felder in Control aktualisieren
                if 'visible' in col_data:
                    control.display_show = col_data['visible']
                    logger.debug(f"🔄 Sichtbarkeit für '{column_name}': {col_data['visible']}")
                
                if 'order' in col_data:
                    control.display_order = col_data['order']
                    logger.debug(f"🔄 display_order für {column_name} auf {col_data['order']} gesetzt")
            
            logger.info(f"✅ display_order in {len(working_columns)} Controls aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Controls: {e}")
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Status-Informationen für Debugging
        
        Returns:
            Dict[str, Any]: Status-Informationen
        """
        return {
            "view_guid": self.view_guid,
            "user_guid": self.user_guid, 
            "stichtag": self.stichtag,
            "mode": self.mode,
            "current_view_mode": self.current_view_mode,
            "view_config_loaded": self.view_config is not None,
            "data_rows": len(self.basis_data),
            "data_columns": len(self.basis_columns),
            "columns": self.basis_columns[:5] if len(self.basis_columns) > 5 else self.basis_columns,
            "normal_mode_available": self.normal_mode_data is not None,
            "expert_mode_available": self.expert_mode_data is not None,
            "controls_manager": self.controls_manager.get_stats()
        }
    
    def is_expert_mode_available(self) -> bool:
        """Prüft ob Expert-Mode verfügbar ist"""
        return self.mode == "admin" and self.expert_mode_data is not None
    
    def get_current_mode(self) -> str:
        """Gibt den aktuellen View-Mode zurück"""
        return self.current_view_mode
    
    # ========================================
    # EINFACHE DIALOG API - wie User es wollte
    # ========================================
    
    def get_columns_for_mode(self, mode):
        """
        EINFACHE API für Dialog: Spalten für Mode holen
        Baut display_* Felder automatisch auf wenn nicht vorhanden
        """
        try:
            # Aktuell in dem Mode arbeiten
            current_mode = self.current_view_mode
            if mode != current_mode:
                # Temporär in den gewünschten Mode wechseln
                self.switch_view_mode(mode)
            
            # Controls für aktuellen Mode holen
            controls_result = self.get_current_controls(for_dialog=False)
            if not controls_result or not hasattr(controls_result, 'columns'):
                logger.warning(f"⚠️ Keine Spalten für Mode '{mode}' verfügbar")
                return []
            
            columns = []
            for col_data in controls_result.columns:
                # display_* Felder hinzufügen falls nicht vorhanden
                if 'display_show' not in col_data:
                    col_data['display_show'] = col_data.get('show', True)
                if 'display_order' not in col_data:
                    col_data['display_order'] = col_data.get('order', 999)
                if 'display_expert' not in col_data:
                    col_data['display_expert'] = col_data.get('expert', False)
                    
                columns.append(col_data)
            
            # Mode zurückwechseln falls gewechselt
            if mode != current_mode:
                self.switch_view_mode(current_mode)
            
            logger.info(f"✅ {len(columns)} Spalten für Mode '{mode}' bereitgestellt (display_* aufgebaut)")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler bei get_columns_for_mode: {e}")
            return []
    
    def save_columns_from_dialog(self, columns, mode):
        """
        EINFACHE API für Dialog: Spalten vom Dialog zurückspeichern
        Genau wie User es wollte - einfach und direkt
        """
        try:
            logger.info(f"💾 save_columns_from_dialog - Mode: {mode}, {len(columns)} Spalten")
            
            # Direkt über die bestehende save_column_configuration Methode
            success = self.save_column_configuration(columns, mode)
            
            if success:
                logger.info(f"✅ Dialog-Spalten erfolgreich gespeichert - Mode: {mode}")
                return True
            else:
                logger.error(f"❌ Fehler beim Speichern der Dialog-Spalten")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei save_columns_from_dialog: {e}")
            return False
