
#!/usr/bin/env python3
"""
NEUER PdvmViewDatenManager - Vollständig linear aufgebaut
Alle Methoden neu erstellt basierend auf der linearen Architektur
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

# Logging Setup
logger = logging.getLogger(__name__)

import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung


class ColumnControl:
    """Vereinfachte Column Control Klasse"""
    
    def __init__(self):
        self.columns = []
        self.row_guids = []
        self.column_data = {}
        
    def add_column(self, name: str, col_type: str, order: int, **kwargs):
        """Fügt eine Spalte hinzu"""
        column = {
            'name': name,
            'type': col_type,
            'order': order,
            **kwargs
        }
        self.columns.append(column)
        
    def set_row_data(self, guid: str, row_dict: dict):
        """Setzt alle Spaltenwerte für eine GUID"""
        if guid not in self.row_guids:
            self.row_guids.append(guid)
        
        for column_name, value in row_dict.items():
            if column_name not in self.column_data:
                self.column_data[column_name] = {}
            self.column_data[column_name][guid] = value
            
    def get_row_data(self, guid: str):
        """Holt alle Spaltenwerte für eine GUID"""
        row_data = {}
        for column_name in self.column_data.keys():
            row_data[column_name] = self.column_data[column_name].get(guid, "")
        return row_data


class PdvmViewDatenManager:
    """
    NEUER LINEAR AUFGEBAUTER Daten Manager mit Widget-Kontrolle
    Komplett neu erstellt mit linearer Architektur
    
    NEUE ARCHITEKTUR: DatenManager (persistent) kontrolliert Widget (disposable)
    """
    
    def __init__(self, call_daten, widget=None, parent_app=None):
        self.call_daten = call_daten
        self.widget = widget  # Aktuelles kontrolliertes Widget (kann None sein)
        self._parent_app = parent_app

        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.first_call = call_daten.get("first_call", True)

        # Column Control System - PERSISTENT!
        self.column_control = None
        self.basis_columns = []
        self.basis_data = []

        logger.info(f"🔧 NEUER LINEAR aufgebauter DatenManager gestartet (PERSISTENT)")
        logger.info(f"📋 View: {self.view_guid}, First Call: {self.first_call}")

        # Daten laden
        self._build_system()
    
    def update_call_daten(self, new_call_daten: dict):
        """Aktualisiert call_daten für bestehenden Manager (ohne Neuaufbau)."""
        self.call_daten.update(new_call_daten)
        logger.info(f"📝 Call-Daten für persistenten Manager aktualisiert: {self.view_guid}")
    
    def create_controlled_widget(self, parent=None, reload_callback=None):
        """
        KORREKTE ARCHITEKTUR: DatenManager erstellt bewährtes Widget mit allen Features.
        Verwendet das bewährte, funktionierende Widget - nur Architektur umgekehrt.
        """
        try:
            # Das BEWÄHRTE Widget mit allen Features verwenden
            from pdvm_view_widget_corrected_architecture import PdvmViewWidget
            
            # Widget erstellen und persistenten DatenManager übergeben
            widget = PdvmViewWidget(
                call_daten=self.call_daten,
                persistent_view_manager=self,  # Persistenter Manager wird übergeben
                parent=parent,
                reload_callback=reload_callback
            )
            
            # Widget-Referenz für refresh_controlled_widget
            self.widget = widget
            
            logger.info(f"✅ Bewährtes Widget mit allen Features erfolgreich erstellt")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des bewährten Widgets: {e}")
            traceback.print_exc()
            raise
    
    def refresh_controlled_widget(self):
        """
        KORREKTE ARCHITEKTUR: Refresht das bewährte Widget über die persistenten Daten.
        Verwendet die bewährten Refresh-Methoden.
        """
        if self.widget is None:
            logger.warning("⚠️ Kein Widget zum Refreshen vorhanden")
            return None
            
        try:
            logger.info("🔄 Refreshe bewährtes Widget über persistenten DatenManager")
            
            # Persistente Daten aktualisieren (wie original)
            if hasattr(self, 'refresh_controls_and_projection'):
                self.refresh_controls_and_projection()
            
            # Widget über bewährte _load_table_data Methode aktualisieren
            if hasattr(self.widget, '_load_table_data'):
                self.widget._load_table_data()
                
            # Header aktualisieren
            if hasattr(self.widget, 'update_header_text'):
                self.widget.update_header_text()
            
            logger.info(f"✅ Widget erfolgreich über persistenten DatenManager refresht")
            return self.widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Widget-Refresh: {e}")
            traceback.print_exc()
            return None
    
    def _populate_widget(self, widget):
        """Füllt das Widget mit den aktuellen Daten vom persistenten DatenManager."""
        try:
            if not widget:
                return
                
            # Widget-interne _load_table_data Methode aufrufen wenn vorhanden
            if hasattr(widget, '_load_table_data'):
                widget._load_table_data()
            
            # Header aktualisieren wenn vorhanden  
            if hasattr(widget, 'update_header_text'):
                widget.update_header_text()
                
            logger.info("✅ Widget mit persistenten DatenManager-Daten befüllt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen des Widgets: {e}")
            traceback.print_exc()

    def _build_system(self):
        """
        SCHRITT-FÜR-SCHRITT AUFBAU:
        1. ViewDaten laden
        2. Controls aufbauen
        3. Daten laden (nur bei first_call oder Stichtagswechsel)
        """
        try:
            logger.info("🔧 SCHRITT 1: ViewDaten laden")
            view_felder = self._load_view_felder()

            logger.info("🔧 SCHRITT 2: Column Controls aufbauen")
            if self.first_call:
                # Neuaufruf: Controls neu aufbauen
                self.column_control = self._build_column_controls(view_felder)
            else:
                # Refresh: Controls aus Systemsteuerung laden
                logger.info("📊 Refresh-Modus: Lade Controls aus Systemsteuerung")
                self.column_control = self._build_column_controls_from_systemsteuerung()

            logger.info("🔧 SCHRITT 3: Basis-Spalten ableiten")
            if self.first_call:
                # Neuaufruf: Basis-Spalten neu ableiten
                self.basis_columns = self._get_columns_from_controls()
            else:
                # Refresh: Basis-Spalten immer neu ableiten (weil Controls geladen wurden)
                logger.info("📊 Refresh-Modus: Basis-Spalten aus geladenen Controls ableiten")
                self.basis_columns = self._get_columns_from_controls()

            logger.info("🔧 SCHRITT 4: Daten laden (nur falls first_call)")
            if self.first_call:
                records_loaded = self._load_records_data(limit=100)
                logger.info(f"✅ {records_loaded} Datensätze geladen")
            else:
                logger.info("📊 SKIP: Datenladen übersprungen (first_call=False)")

        except Exception as e:
            logger.error(f"❌ Fehler beim System-Aufbau: {e}")
            traceback.print_exc()
            raise
        finally:
            # Nach dem ersten Aufruf ist first_call immer False
            if self.first_call:
                self.first_call = False
                logger.info("🔧 first_call auf False gesetzt nach erstem System-Aufbau")

    def refresh_controls_and_projection(self):
        """
        Aktualisiert nur die Parameter in den bestehenden Controls (show, order) aus der Systemsteuerung
        und baut dann die Projektion neu auf. Die Controls selbst bleiben erhalten - nur die Projektions-Parameter ändern sich.
        """
        try:
            logger.info("🔄 Control-Parameter aus Systemsteuerung laden und Projektion neu aufbauen")
            
            # Lade die aktuellen ColumnControl-Parameter aus der Systemsteuerung
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            column_attributes = cc_data.get("wert", {}) if cc_data and "wert" in cc_data else {}
            
            if column_attributes and hasattr(self, 'basis_columns'):
                logger.info(f"📥 Aktualisiere Parameter für {len(self.basis_columns)} bestehende Controls")
                
                # Aktualisiere nur die Parameter in den bestehenden basis_columns
                for col in self.basis_columns:
                    col_name = col['name']
                    if col_name in column_attributes:
                        new_attrs = column_attributes[col_name]
                        # Nur die Projektions-Parameter aktualisieren
                        col['show'] = new_attrs.get('show', col.get('show', False))
                        col['expertOrder'] = new_attrs.get('expertOrder', col.get('expertOrder', 999))
                        col['displayOrder'] = new_attrs.get('displayOrder', col.get('displayOrder', 999))
                        logger.debug(f"  {col_name}: show={col['show']}, eO={col['expertOrder']}, dO={col['displayOrder']}")
                
                logger.info("✅ Control-Parameter aktualisiert - Projektion wird neu aufgebaut")
                logger.info(f"   Aktuelle Modus-Einstellung: ExpertMode={gcs.global_expert_mode}")
            else:
                logger.warning("⚠️ Keine ColumnControls in Systemsteuerung gefunden oder keine basis_columns vorhanden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh der Control-Parameter: {e}")
            traceback.print_exc()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh der Controls/Projektion: {e}")
            traceback.print_exc()

    def _refresh_control_parameters_only(self):
        """
        NUR-PARAMETER-REFRESH: Aktualisiert nur die show/order Parameter ohne neue Controls zu erstellen.
        Wird bei Refresh verwendet wenn keine bestehenden Controls vorhanden sind (Notfall).
        """
        try:
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            gcs = PdvmCentralSystemsteuerung()
            
            # Lade gespeicherte Attribute aus Systemsteuerung
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"🔄 Parameter-Refresh: {len(attr_map)} gespeicherte Control-Attribute geladen")
                
                # Erstelle minimale Controls nur aus gespeicherten Daten (ohne neue hinzuzufügen)
                columns = []
                for col_name, attrs in attr_map.items():
                    col = {
                        'name': col_name,
                        'show': attrs.get('show', False),
                        'expertOrder': attrs.get('expertOrder', 0),
                        'displayOrder': attrs.get('displayOrder', 0),
                        'type': 'unknown',  # Typ ist für Refresh nicht wichtig
                        'spaltenueberschrift': col_name.replace('_', ' ').title()
                    }
                    columns.append(col)
                
                # Simuliere die Controls-Struktur für Refresh
                self.column_control = {'columns': columns}
                logger.info(f"🔄 Parameter-Refresh: {len(columns)} minimale Controls erstellt")
                
            else:
                logger.error("❌ Keine gespeicherten Control-Parameter für Refresh gefunden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Parameter-Refresh: {e}")
            traceback.print_exc()

    def _build_column_controls_from_systemsteuerung(self):
        """
        REFRESH-MODUS: Baut Column Controls aus gespeicherten Systemsteuerung-Daten auf.
        Wird nur bei Refresh (first_call=False) verwendet.
        """
        try:
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            gcs = PdvmCentralSystemsteuerung()
            
            # Lade gespeicherte Attribute aus Systemsteuerung
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"🔄 Refresh-Modus: {len(attr_map)} Control-Attribute aus Systemsteuerung geladen")
                
                # Erstelle Controls aus gespeicherten Daten
                columns = []
                for col_name, attrs in attr_map.items():
                    col = {
                        'name': col_name,
                        'show': attrs.get('show', False),
                        'expertOrder': attrs.get('expertOrder', 0),
                        'displayOrder': attrs.get('displayOrder', 0),
                        'type': self._guess_column_type(col_name),
                        'spaltenueberschrift': self._create_column_header(col_name),
                        'field_config': {}  # Minimale Config für Refresh
                    }
                    columns.append(col)
                
                logger.info(f"✅ Refresh-Modus: {len(columns)} Controls aus Systemsteuerung aufgebaut")
                return {'columns': columns}
                
            else:
                logger.error("❌ Refresh-Modus: Keine ColumnControls in Systemsteuerung gefunden!")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der Controls aus Systemsteuerung: {e}")
            traceback.print_exc()
            return None

    def _guess_column_type(self, col_name):
        """Errät den Spaltentyp aus dem Namen (für Refresh-Modus)."""
        if 'geburtsdatum' in col_name:
            if 'alter' in col_name:
                return 'date_alter'
            elif 'jahr' in col_name:
                return 'date_jahr'
            elif 'monat' in col_name:
                return 'date_monat'
            elif 'tag' in col_name:
                return 'date_tag'
            else:
                return 'date'
        elif col_name == 'dummy':
            return 'dummy'
        elif col_name.startswith('uid'):
            return 'string'
        else:
            return 'string'

    def _create_column_header(self, col_name):
        """Erstellt eine Spaltenüberschrift aus dem Control-Namen (für Refresh-Modus)."""
        if col_name == 'uid_original':
            return 'UID (orig.)'
        elif col_name == 'uid_show':
            return 'UID'
        elif col_name == 'dummy':
            return ''
        elif col_name.endswith('_original'):
            base_name = col_name.replace('_original', '').replace('_', ' ').title()
            return f"{base_name} (orig.)"
        elif col_name.endswith('_show'):
            base_name = col_name.replace('_show', '').replace('_', ' ').title()
            return base_name
        else:
            return col_name.replace('_', ' ').title()


    def get_abdatum_matrix(self, show_only=True):
        """Gibt die Abdatum-Matrix für die aktuelle Projektion zurück (wie im Matrix-Prototyp)."""
        if not hasattr(self, '_abdatum_matrix') or self._abdatum_matrix is None:
            return None
            
        # Projektion wie bei get_table_data_for_display
        if show_only:
            columns = sorted([col for col in self.basis_columns if col.get('show', False)], key=lambda c: c.get('displayOrder', 999))
        else:
            columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
            
        col_names = [col['name'] for col in columns]
        abdatum_matrix = []
        
        # LINEARE LÖSUNG: Abdatum-Werte sind bereits für alle Spalten (inkl. _show) vorhanden
        for ab_row in self._abdatum_matrix:
            projected_row = [ab_row.get(col_name, None) for col_name in col_names]
            abdatum_matrix.append(projected_row)
            
        return abdatum_matrix
    
    def _load_or_init_column_controls(self, view_felder):
        """
        LINEARES VORGEHEN für ColumnControls (vereinfacht):
        
        1. Baue IMMER Standard-Controls mit Standard-Sortierung auf (0, 1, 2, ...)
        2. Synchronisiere Attribute aus Systemsteuerung in bestehende Controls
        3. Fehlende Controls (nicht in Systemsteuerung) bekommen Order +1000 und show=true (_show)
        4. Bei Order >1000 gefunden: Alle neu nummerieren (0, 1, 2, ...) und in Systemsteuerung speichern
        
        Control-Namen:
        - _original-Spalten als feldname_original, uid_original (System).
        - _show-Spalten als feldname_show, Dummy als 'dummy'.
        - Spaltenüberschrift: _original → name (aus Viewdaten) + ' (orig.)', _show → name (aus Viewdaten), Dummy → ''.
        """
        # SCHRITT 1: Lade gespeicherte Attribute aus Systemsteuerung
        try:
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                logger.info(f"✅ ColumnControl-Attribute aus Systemsteuerung geladen für {self.view_guid}")
                attr_map = cc_data["wert"]
                logger.info(f"🔍 Geladene Attribute: {len(attr_map)} Controls")
            else:
                logger.info(f"ℹ️ Keine ColumnControl-Attribute gefunden")
                attr_map = {}
        except Exception as e:
            logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht aus Systemsteuerung laden: {e}")
            attr_map = {}

        # SCHRITT 2: Baue IMMER Standard-Controls mit Standard-Sortierung auf
        columns = []
        order_counter = 0  # Beginne bei 0 für Standard-Sortierung

        # SYSTEM-SPALTEN: uid_original
        uid_orig_col = {
            'name': 'uid_original',
            'type': 'string',
            'gruppe': 'SYSTEM',
            'feld': 'UID',
            'show': False,  # Standard: unsichtbar
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {'feld': 'UID', 'name': 'UID', 'type': 'string'},
            'spaltenueberschrift': 'UID (orig.)'
        }
        columns.append(uid_orig_col)
        order_counter += 1

        # VIEW-FELDER: _original Controls erstellen
        for feld_config in view_felder:
            feldname_gross = feld_config["feld"]
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "PERSDATEN")
            spaltenname = feld_config.get("name", feld_name)

            # _original Control
            name_orig = f"{feld_name}_original"
            col = {
                'name': name_orig,
                'type': feld_type,
                'gruppe': gruppe,
                'feld': feldname_gross,
                'show': False,  # Standard: unsichtbar
                'expertOrder': order_counter,
                'displayOrder': order_counter,
                'field_config': feld_config,
                'spaltenueberschrift': f"{spaltenname} (orig.)"
            }
            columns.append(col)
            order_counter += 1

            # Zusatzfelder für date
            if feld_type == "date":
                zusatz_namen = {
                    "alter": "Alter",
                    "jahr": "Jahr", 
                    "monat": "Monat",
                    "tag": "Tag"
                }
                
                for zusatz in ["alter", "jahr", "monat", "tag"]:
                    zusatz_field_config = feld_config.copy()
                    zusatz_field_config["type"] = f"date_{zusatz}"
                    name_zusatz = f"{feld_name}_{zusatz}_original"
                    zusatz_anzeige = zusatz_namen[zusatz]
                    
                    col = {
                        'name': name_zusatz,
                        'type': f"date_{zusatz}",
                        'gruppe': gruppe,
                        'feld': feldname_gross,
                        'show': False,  # Standard: unsichtbar
                        'expertOrder': order_counter,
                        'displayOrder': order_counter,
                        'field_config': zusatz_field_config,
                        'spaltenueberschrift': f"{spaltenname} {zusatz_anzeige} (orig.)"
                    }
                    columns.append(col)
                    order_counter += 1

        # _show Controls für alle _original (außer dummy)
        for col in columns[:]:
            if col['name'].endswith('_original'):
                show_name = col['name'].replace('_original', '_show')
                
                # Überschrift: Gleich wie Original-Spalte, aber ohne "(orig.)"
                original_ueberschrift = col.get('spaltenueberschrift', '')
                show_ueberschrift = original_ueberschrift.replace(' (orig.)', '') if original_ueberschrift else show_name
                
                show_col = {
                    'name': show_name,
                    'type': col['type'],
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'show': True,  # Standard: _show Spalten sind sichtbar
                    'expertOrder': order_counter,
                    'displayOrder': order_counter,
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': show_ueberschrift
                }
                columns.append(show_col)
                order_counter += 1

        # Dummy Control
        dummy_col = {
            'name': 'dummy',
            'type': 'dummy',
            'show': False,  # Standard: unsichtbar
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {},
            'spaltenueberschrift': ''
        }
        columns.append(dummy_col)
        order_counter += 1

        logger.info(f"🔧 {len(columns)} Standard-Controls mit Standard-Sortierung erstellt")

        # SCHRITT 3: Synchronisation - Attribute aus Systemsteuerung in bestehende Controls übernehmen
        found_new_controls = False
        
        for col in columns:
            col_name = col['name']
            if col_name in attr_map:
                # Bestehende Einstellungen übernehmen
                saved_attrs = attr_map[col_name]
                col['show'] = saved_attrs.get('show', col['show'])
                col['expertOrder'] = saved_attrs.get('expertOrder', col['expertOrder'])
                col['displayOrder'] = saved_attrs.get('displayOrder', col['displayOrder'])
            else:
                # NEUES Control nicht in Systemsteuerung gefunden
                logger.debug(f"🆕 Neues Control gefunden: {col_name}")
                col['expertOrder'] += 1000  # Markierung als "neu"
                col['displayOrder'] += 1000  # Markierung als "neu"
                # _show Controls: show=True, andere: show bleibt
                if col_name.endswith('_show'):
                    col['show'] = True
                found_new_controls = True

        logger.info(f"✅ Synchronisation abgeschlossen - {len(columns)} Controls, neue gefunden: {found_new_controls}")

        # SCHRITT 4: Bei neuen Controls (Order >1000): Alle neu nummerieren
        if found_new_controls:
            logger.info(f"🔧 Neue Controls gefunden - nummeriere alle Order-Werte neu")
            
            # ExpertOrder neu nummerieren
            expert_sorted = sorted(columns, key=lambda x: x['expertOrder'])
            for i, col in enumerate(expert_sorted):
                col['expertOrder'] = i
                
            # DisplayOrder neu nummerieren
            display_sorted = sorted(columns, key=lambda x: x['displayOrder'])
            for i, col in enumerate(display_sorted):
                col['displayOrder'] = i
                
            logger.info(f"✅ Order-Werte neu nummeriert: {len(columns)} Controls")

        # SCHRITT 5: Persistierung nur bei neuen Controls UND first_call
        # Bei Refresh (first_call=False) niemals speichern!
        if found_new_controls and self.first_call:
            persist_map = {col['name']: {
                'show': col['show'],
                'expertOrder': col['expertOrder'],
                'displayOrder': col['displayOrder']
            } for col in columns}
            
            try:
                gcs.set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
                gcs.save_values()
                logger.info(f"💾 Neue Controls in Systemsteuerung gespeichert für {self.view_guid} (first_call=True)")
            except Exception as e:
                logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht speichern: {e}")
        elif found_new_controls and not self.first_call:
            logger.info(f"🔄 Neue Controls erkannt aber NICHT gespeichert (Refresh-Modus, first_call=False)")
        else:
            logger.info(f"ℹ️ Keine neuen Controls - keine Persistierung erforderlich")

        return columns
    
    def _load_view_felder(self):
        """SCHRITT 1: ViewDaten-Felder laden"""
        try:
            if not self.first_call:
                logger.info("📊 SKIP: ViewDaten bereits geladen")
                return []
            
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten", 
                guid=self.view_guid
            )
            
            view_table = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not view_table:
                raise ValueError("VIEW_TABLE nicht gefunden")
            
            view_metadaten = view_db.get_static_value(gruppe='METADATEN', feld=view_table.upper())
            if not view_metadaten or 'felder' not in view_metadaten:
                raise ValueError("ViewDaten-Felder nicht gefunden")
                
            felder = view_metadaten['felder']
            logger.info(f"📋 {len(felder)} ViewDaten-Felder geladen für Tabelle '{view_table}'")
            
            # Tabelle für spätere Verwendung speichern
            self.view_table = view_table
            
            return felder
            
        except Exception as e:
            logger.error(f"❌ Fehler beim ViewDaten-Laden: {e}")
            raise
    
    def _build_column_controls(self, view_felder):
        """
        SCHRITT 2: Column Controls linear aufbauen oder aus Systemsteuerung laden
        """
        try:
            columns = self._load_or_init_column_controls(view_felder)
            
            # displayOrder-Vergabe nur für neu erstellte Controls ohne displayOrder
            show_counter = 0
            for col in columns:
                if 'displayOrder' not in col or col.get('displayOrder', None) is None:
                    if col.get('show', False):
                        col['displayOrder'] = show_counter
                        show_counter += 1
                    else:
                        col['displayOrder'] = col.get('expertOrder', 0) + 1000
                elif col.get('show', False):
                    show_counter += 1

            # ColumnControl-Objekt für interne Nutzung
            column_control = ColumnControl()
            for col in columns:
                # WICHTIG: Alle relevanten Felder übertragen, aber Namenskonflikte vermeiden
                col_kwargs = {
                    'show': col.get('show', True),
                    'expertOrder': col.get('expertOrder', 999),
                    'displayOrder': col.get('displayOrder', 999),
                    'expert': col.get('expert', False),
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': col.get('spaltenueberschrift', col['name']),
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'anzeige': col.get('spaltenueberschrift', col['name'])  # Für ColumnControl
                }
                
                column_control.add_column(
                    col['name'],
                    col.get('type', 'string'),
                    col.get('expertOrder', 999),  # Verwende expertOrder als order
                    **col_kwargs
                )
                
            logger.info(f"✅ {len(columns)} Column Controls aufgebaut")
            return column_control
        except Exception as e:
            logger.error(f"❌ Fehler beim Column Control Aufbau: {e}")
            traceback.print_exc()
            raise
    
    def _get_columns_from_controls(self):
        """SCHRITT 3: Basis-Spalten aus Controls ableiten mit korrekter Struktur für Dialog"""
        try:
            columns = []
            for col_dict in self.column_control.columns:
                # WICHTIG: Alle Felder korrekt mappen und sicherstellen dass sie existieren
                simple_col = {
                    'name': col_dict['name'],
                    'label': col_dict.get('anzeige', col_dict['name']),
                    'type': col_dict.get('type', 'string'),
                    'show': col_dict.get('show', True),
                    'expertOrder': col_dict.get('expertOrder', col_dict.get('order', 999)),  
                    'displayOrder': col_dict.get('displayOrder', col_dict.get('order', 999)),  
                    'expert': col_dict.get('expert', False),  
                    'field_config': col_dict.get('field_config', {}),
                    'spaltenueberschrift': col_dict.get('spaltenueberschrift', col_dict.get('anzeige', col_dict['name'])),
                    'gruppe': col_dict.get('gruppe'),
                    'feld': col_dict.get('feld')
                }
                
                # Sicherheitscheck: Alle Order-Felder müssen valide Zahlen sein
                if not isinstance(simple_col['expertOrder'], (int, float)):
                    simple_col['expertOrder'] = 999
                if not isinstance(simple_col['displayOrder'], (int, float)):
                    simple_col['displayOrder'] = simple_col['expertOrder']
                    
                columns.append(simple_col)
                
            logger.info(f"✅ {len(columns)} Basis-Spalten aufgebaut (mit korrekten Order-Feldern)")
            
            # Debug-Output
            for col in columns[:3]:  # Erste 3 Spalten zur Kontrolle
                logger.debug(f"  {col['name']}: expertOrder={col['expertOrder']}, displayOrder={col['displayOrder']}, show={col['show']}")
                
            return columns
        except Exception as e:
            logger.error(f"❌ Fehler beim Basis-Spalten-Aufbau: {e}")
            traceback.print_exc()
            return []
    
    def _load_records_data(self, limit=100):
        """
        SCHRITT 4: Daten laden
        3. set_data pro Zeile 
        4. get_value pro Feld mit Zusatzspalten-Logik
        """
        try:
            if not hasattr(self, 'view_table') or not self.view_table:
                raise ValueError("view_table nicht verfügbar")

            from pdvm_central_datenbank import PdvmCentralDatenbank

            # Alle Datensätze laden
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None
            )

            all_records = data_db.lesen_alle_ohne_system(limit=limit)
            logger.info(f"📊 {len(all_records)} Datensätze geladen")

            # Datetime-Formatter
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")

            # Pro Datensatz verarbeiten
            successful_records = 0
            working_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None
            )

            abdatum_matrix = []

            for i, record_info in enumerate(all_records):
                try:
                    data_guid = record_info["uid"]
                    data_dict = record_info["daten_dict"]

                    # 3. set_data pro Zeile
                    working_db.set_data(data_dict, data_guid)

                    # Row-Record erstellen
                    row_record = {'uid_original': data_guid}

                    # 4. get_value pro _original Feld
                    abdatum_row = self._fill_original_columns(row_record, working_db, dt_formatter, collect_abdatum=True)

                    # 5. _show Spalten aus _original übertragen (erstmal 1:1)
                    # WICHTIG: Auch Abdatum für _show Spalten übertragen
                    self._fill_show_columns(row_record, abdatum_row)

                    # In Column Control speichern
                    self.column_control.set_row_data(data_guid, row_record)
                    abdatum_matrix.append(abdatum_row)
                    successful_records += 1

                    if (i + 1) % 20 == 0:
                        logger.info(f"   📊 {i+1}/{len(all_records)} Datensätze verarbeitet...")

                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Datensatz {record_info.get('uid', 'unbekannt')}: {e}")
                    continue

            self._abdatum_matrix = abdatum_matrix
            logger.info(f"✅ {successful_records} Datensätze erfolgreich geladen")
            return successful_records

        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-Laden: {e}")
            traceback.print_exc()
            return 0
    
    def _fill_original_columns(self, row_record: dict, working_db, dt_formatter, collect_abdatum=False):
        """
        SCHRITT 4: _original Spalten befüllen
        Linear durch alle _original Spalten, mit get_value + Zusatzspalten-Logik
        Wenn collect_abdatum=True, wird eine dict-Liste mit ab_zeit pro Spalte zurückgegeben.
        """
        import copy
        abdatum_row = {} if 'collect_abdatum' in locals() or 'collect_abdatum' in globals() else None
        import inspect
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        collect_abdatum = values.get('collect_abdatum', False)
        try:
            # SPEZIELL: uid_original behandeln
            if 'uid_original' in row_record and collect_abdatum:
                # uid_original hat kein echtes ab_zeit (es ist die GUID selbst)
                abdatum_row['uid_original'] = None
                
            for col in self.basis_columns:
                col_name = col['name']
                if not col_name.endswith('_original') or col_name == 'uid_original':
                    continue  # uid_original bereits oben behandelt
                col_type = col.get('type', '')
                gruppe = col.get('gruppe', 'PERSDATEN')
                feld = col.get('feld')
                if gruppe:
                    gruppe = str(gruppe).upper()
                if feld:
                    feld = str(feld).upper()
                if not col_type.startswith("date_"):
                    if feld and gruppe:
                        try:
                            wert = working_db.get_value(gruppe, feld, ab_zeit=gcs.global_stichtag)
                            ab_zeit = None
                            if isinstance(wert, dict):
                                ab_zeit = wert.get('ab_zeit', None)
                                wert_inhalt = wert.get('wert', "")
                                if wert_inhalt is None or wert_inhalt == "":
                                    row_record[col_name] = ""
                                else:
                                    row_record[col_name] = wert_inhalt
                            else:
                                row_record[col_name] = wert if wert is not None else ""
                            if collect_abdatum:
                                abdatum_row[col_name] = ab_zeit
                            logger.debug(f"✅ {col_name} = {row_record[col_name]} (get_value {gruppe}, {feld}) ab_zeit={ab_zeit}")
                        except Exception as e:
                            logger.debug(f"⚠️ get_value Fehler für {col_name} ({gruppe}, {feld}): {e}")
                            row_record[col_name] = ""
                            if collect_abdatum:
                                abdatum_row[col_name] = None
                    else:
                        row_record[col_name] = ""
                        if collect_abdatum:
                            abdatum_row[col_name] = None
                else:
                    zusatz_typ = col_type.replace("date_", "")
                    basis_col_name = col_name.replace(f"_{zusatz_typ}_original", "_original")
                    if basis_col_name in row_record:
                        basis_wert_raw = row_record[basis_col_name]
                        if isinstance(basis_wert_raw, dict) and 'wert' in basis_wert_raw:
                            basis_wert = basis_wert_raw['wert']
                        else:
                            basis_wert = basis_wert_raw
                        if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                            zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                            row_record[col_name] = zusatz_wert
                        else:
                            row_record[col_name] = ""
                        if collect_abdatum:
                            # KORREKTUR: Abdatum der Basis-Spalte verwenden, nicht None
                            abdatum_row[col_name] = abdatum_row.get(basis_col_name, None)
                    else:
                        if feld and gruppe:
                            try:
                                basis_wert_raw = working_db.get_value(gruppe, feld, ab_zeit=gcs.global_stichtag)
                                ab_zeit = basis_wert_raw.get('ab_zeit', None) if isinstance(basis_wert_raw, dict) else None
                                basis_wert = basis_wert_raw['wert'] if isinstance(basis_wert_raw, dict) else basis_wert_raw
                                if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                                    zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                                    row_record[col_name] = zusatz_wert
                                else:
                                    row_record[col_name] = ""
                                if collect_abdatum:
                                    abdatum_row[col_name] = ab_zeit
                            except Exception as e:
                                logger.debug(f"⚠️ get_value Fehler für Zusatzspalte {col_name}: {e}")
                                row_record[col_name] = ""
                                if collect_abdatum:
                                    abdatum_row[col_name] = None
                        else:
                            row_record[col_name] = ""
                            if collect_abdatum:
                                abdatum_row[col_name] = None
            if collect_abdatum:
                return abdatum_row
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _original Spalten: {e}")
            if collect_abdatum:
                return abdatum_row
    
    def _berechne_datum_zusatz(self, original_datum: float, zusatz_typ: str, dt_formatter):
        """Berechnet Datum-Zusatzwerte"""
        try:
            dt_formatter.PdvmDateTime = original_datum
            
            if zusatz_typ == "alter":
                # PRÄZISE TAGESEXAKTE ALTERSBERECHNUNG
                return self._berechne_alter(gcs.global_stichtag, original_datum)
            elif zusatz_typ == "jahr":
                return dt_formatter.Year
            elif zusatz_typ == "monat":
                return dt_formatter.Month
            elif zusatz_typ == "tag":
                return dt_formatter.Day
            else:
                return ""
        except Exception as e:
            logger.debug(f"❌ Datum-Zusatz-Berechnung Fehler ({zusatz_typ}): {e}")
            return ""
    
    def _berechne_alter(self, stichtag, datum):
        stdiff = int(stichtag) - int(datum)
        strest = stdiff % 1000
        return int((stdiff - strest) / 1000)

    def _fill_show_columns(self, row_record: dict, abdatum_row: dict = None):
        """
        SCHRITT 5: _show Spalten befüllen
        Erstmal einfach: 1:1 aus _original übertragen mit besserer Behandlung
        ERWEITERT: Auch Abdatum für _show Spalten von _original übertragen
        """
        try:
            # System uid_show
            if 'uid_original' in row_record:
                guid = row_record['uid_original']
                row_record['uid_show'] = guid[:8] + "..." if guid else ""
                
                # Abdatum auch für uid_show setzen (falls vorhanden)
                if abdatum_row and 'uid_original' in abdatum_row:
                    abdatum_row['uid_show'] = abdatum_row['uid_original']
            
            # Alle anderen _show Spalten
            for col in self.basis_columns:
                col_name = col['name']
                col_type = col['type']
                
                if not col_name.endswith('_show') or col_name == 'uid_show':
                    continue
                
                # Entsprechende _original Spalte finden
                original_col_name = col_name.replace('_show', '_original')
                
                if original_col_name in row_record:
                    original_wert = row_record[original_col_name]
                    
                    # LINEARES ABDATUM ÜBERTRAGEN: _show bekommt dasselbe Abdatum wie _original
                    if abdatum_row and original_col_name in abdatum_row:
                        abdatum_row[col_name] = abdatum_row[original_col_name]
                    
                    # Bei normalen Feldern: Historische Dictionaries zu lesbaren Werten
                    if not col_type.startswith("date_") and isinstance(original_wert, dict) and 'wert' in original_wert:
                        # Für Datum: PdvmDateTime Formatierung
                        if col_type == "date" and isinstance(original_wert['wert'], (int, float)):
                            try:
                                from pdvm_datetime import Pdvm_DateTime
                                dt_formatter = Pdvm_DateTime("DEU")
                                dt_formatter.PdvmDateTime = original_wert['wert']
                                formatted_value = dt_formatter.Date_formatted
                                row_record[col_name] = formatted_value
                                logger.debug(f"✅ {col_name} = {formatted_value} (formatiert aus {original_wert['wert']})")
                            except Exception as e:
                                row_record[col_name] = str(original_wert['wert'])
                                logger.debug(f"⚠️ {col_name} = {original_wert['wert']} (Fallback: {e})")
                        else:
                            # Normaler Wert aus dict
                            row_record[col_name] = str(original_wert['wert']) if original_wert['wert'] is not None else ""
                    else:
                        # Bei date_* types: 1:1 übertragen (bereits berechnet)
                        row_record[col_name] = original_wert if original_wert is not None else ""
                        logger.debug(f"✅ {col_name} = {original_wert} (1:1 aus {original_col_name})")
                else:
                    row_record[col_name] = ""
                    logger.debug(f"⚠️ {col_name} = '' (keine _original Spalte)")
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _show Spalten: {e}")
    
    # ===========================================
    # API METHODEN für Widget-Integration
    # ===========================================
    
    def get_table_data_for_display(self):
        """Gibt die Tabellendaten und Spaltennamen für den aktuellen Modus zurück.
        Verwendet die ZENTRALE PROJEKTION - dieselbe wie der Dialog
        """
        try:
            if not self.column_control:
                return {'headers': [], 'rows': []}

            # ZENTRALE PROJEKTION: Verwende dieselbe Logik wie der Dialog
            from column_projection_helper import get_projected_columns
            columns = get_projected_columns(self.basis_columns)
            display_columns = [col['name'] for col in columns]
            # Schöne Header-Namen für die Anzeige verwenden
            display_headers = [col.get('spaltenueberschrift', col['name']) for col in columns]

            display_data = []
            guids_to_remove = []
            for guid in list(self.column_control.row_guids):
                row_data = self.column_control.get_row_data(guid)
                # Prüfe, ob alle Felder leer sind (außer uid_original und uid_show)
                all_empty = True
                for col in display_columns:
                    if col in ('uid_original', 'uid_show'):
                        continue
                    if str(row_data.get(col, "")).strip() != "":
                        all_empty = False
                        break
                if all_empty:
                    guids_to_remove.append(guid)
                    continue
                display_row = [row_data.get(col, "") for col in display_columns]
                display_data.append(display_row)

            # Entferne leere Zeilen aus Controls
            for guid in guids_to_remove:
                if guid in self.column_control.row_guids:
                    self.column_control.row_guids.remove(guid)
                for col_data in self.column_control.column_data.values():
                    if guid in col_data:
                        del col_data[guid]

            # NEUE ARCHITEKTUR: Rückgabe als Dict für Widget-Kompatibilität
            # ✅ WICHTIG: Abdatum-Matrix für Tooltips mitliefern (3. Dimension)
            result_data = {
                'headers': display_headers,  # Schöne Namen verwenden
                'rows': display_data
            }
            
            # Abdatum-Matrix hinzufügen, falls vorhanden
            try:
                abdatum_matrix = self.get_abdatum_matrix(show_only=True)
                if abdatum_matrix:
                    result_data['abdatum_matrix'] = abdatum_matrix
                    logger.info(f"✅ Abdatum-Matrix für Tooltips hinzugefügt: {len(abdatum_matrix)} Zeilen")
                else:
                    logger.info("ℹ️ Keine Abdatum-Matrix verfügbar")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Laden der Abdatum-Matrix: {e}")
                result_data['abdatum_matrix'] = None
            
            return result_data
            
        except Exception as e:
            logger.error(f"❌ Fehler in get_table_data_for_display: {e}")
            import traceback
            traceback.print_exc()
            return {'headers': [], 'rows': []}

    def save_column_settings(self, updated_columns):
        """
        NEUE ARCHITEKTUR: Speichert Column Settings vom Dialog.
        Wird vom Widget aufgerufen wenn der ColumnSettingsDialog Änderungen hat.
        DatenManager bleibt persistent und behält alle Einstellungen!
        """
        try:
            logger.info(f"💾 Speichere Column Settings in persistentem DatenManager")
            
            # Aktualisiere die basis_columns mit den neuen Einstellungen
            if updated_columns and hasattr(self, 'basis_columns'):
                self.basis_columns = updated_columns
                logger.info(f"✅ {len(updated_columns)} Column Controls in persistentem DatenManager aktualisiert")
            
            # Speichere mit der bestehenden save_column_configuration Methode
            self.save_column_configuration(working_columns=updated_columns)
            
            logger.info(f"✅ Column Settings erfolgreich in persistentem DatenManager gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Column Settings im persistenten DatenManager: {e}")
            traceback.print_exc()

    def save_column_configuration(self, working_columns=None, mode=None):
        """
        Speichert Spalten-Konfiguration in der Systemsteuerung
        
        Args:
            working_columns: Geänderte Spalten-Konfiguration (Dialog-Format)
            mode: Aktueller Modus (wird ignoriert - linear)
            
        Returns:
            bool: True wenn erfolgreich gespeichert
        """
        try:
            logger.info(f"💾 save_column_configuration aufgerufen")
            
            # Falls working_columns übergeben wurde, diese in basis_columns übernehmen
            if working_columns:
                logger.info(f"💾 Übernehme {len(working_columns)} geänderte Spalten")
                
                # Dialog gibt bereits das richtige Format zurück: show, expertOrder, displayOrder
                # Aber sicherheitshalber prüfen wir das Format
                for working_col in working_columns:
                    col_name = working_col.get('name')
                    if not col_name:
                        continue
                    
                    # Entsprechende Basis-Spalte finden und aktualisieren
                    for basis_col in self.basis_columns:
                        if basis_col['name'] == col_name:
                            # Direkte Übernahme aus Dialog (bereits im richtigen Format)
                            basis_col['show'] = working_col.get('show', basis_col.get('show', False))
                            basis_col['expertOrder'] = working_col.get('expertOrder', basis_col.get('expertOrder', 999))
                            basis_col['displayOrder'] = working_col.get('displayOrder', basis_col.get('displayOrder', 999))
                            
                            # Fallback für alte Dialog-Formate (falls vorhanden)
                            if 'visible' in working_col:
                                basis_col['show'] = working_col['visible']
                            if 'order' in working_col:
                                basis_col['displayOrder'] = working_col['order']
                            if 'expert_order' in working_col:
                                basis_col['expertOrder'] = working_col['expert_order']
                            break
            
            # Persistiere alle Spalten-Attribute in der Systemsteuerung
            persist_map = {col['name']: {
                'show': col['show'],
                'expertOrder': col['expertOrder'], 
                'displayOrder': col['displayOrder']
            } for col in self.basis_columns}
            
            gcs.set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
            gcs.save_values()
            
            logger.info(f"✅ ColumnControl-Attribute erfolgreich in Systemsteuerung gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spalten-Konfiguration: {e}")
            return False

#        except Exception as e:
#            logger.error(f"❌ Fehler bei get_table_data_for_display: {e}")
#            return [], []
    
