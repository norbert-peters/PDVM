"""
PDVM Value View Provider

Extrahiert die get_value_view Logik aus PdvmCentralDatenbank
und macht daraus eine spezialisierte Klasse.

Diese Klasse ist verantwortlich für:
- Controls und Basisdaten-Tabelle erstellen
- Komplexe View-Logik mit _original/_show Spalten
- Verwendung der PdvmCentralDatenbank nur für Basis-CRUD Operationen
"""

import logging
import json
from typing import Optional, Dict, List, Tuple, Any
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmValueViewProvider:
    """
    Spezialisierte Klasse für komplexe Value-View Operationen
    
    Verwendet intern PdvmCentralDatenbank für Basis-Operationen,
    aber stellt komplexe get_value_view Funktionalität bereit.
    
    Unterstützt Normal-Mode und Expert-Mode mit unterschiedlichen Spalten-Logiken.
    """
    
    def __init__(self, db_name: str = "PdvmManager.db"):
        """
        Initialisiert den ValueViewProvider
        
        Args:
            db_name: Name der Datenbank
            
        Raises:
            RuntimeError: Wenn zentrale Systemsteuerung nicht gefunden wird
        """
        self.db_name = db_name
        
        # Erstelle temporäre PdvmCentralDatenbank Instanz für die komplexe Logik
        # Diese wird nur für get_value_view verwendet
        self._temp_central_db = PdvmCentralDatenbank(db_name=db_name)
        
        # Zentrale Systemsteuerung finden - MUSS existieren!
        self._systemsteuerung_db = self._get_central_systemsteuerung(db_name)
        
        logger.info(f"🏭 PdvmValueViewProvider initialisiert für DB: {db_name}")
    
    def _get_central_systemsteuerung(self, db_name):
        """
        Findet die zentrale Systemsteuerung-Instanz über QApplication
        
        Wirft Exception wenn nicht gefunden - das ist ein Systemfehler!
        """
        try:
            # Über QApplication die MainApp finden
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                raise RuntimeError("❌ Keine QApplication-Instanz gefunden - System nicht ordnungsgemäß initialisiert")
            
            # Suche nach MainWindow mit central_systemsteuerung
            for widget in app.allWidgets():
                if hasattr(widget, 'central_systemsteuerung'):
                    logger.info(f"🏭 PdvmValueViewProvider verwendet zentrale Systemsteuerung von MainApp")
                    return widget.central_systemsteuerung
            
            # Wenn hier angekommen: Systemfehler!
            raise RuntimeError("❌ Zentrale Systemsteuerung nicht gefunden - MainApp nicht ordnungsgemäß initialisiert")
            
        except ImportError as e:
            raise RuntimeError(f"❌ Qt-Framework nicht verfügbar: {e}")
        except Exception as e:
            raise RuntimeError(f"❌ Fehler beim Zugriff auf zentrale Systemsteuerung: {e}")
    
    def get_value_view(self, view_config: dict, stichtag: Optional[float] = None, 
                       mode: str = "normal", user_guid: Optional[str] = None) -> Tuple[Any, List[Dict]]:
        """
        Zentrale View-Methode: Gibt (controls, daten)-Tuple zurück.
        
        Args:
            view_config: View-Konfiguration mit metadata und ROOT
            stichtag: Optional - Stichtag für historische Daten
            mode: "normal" oder "expert" - bestimmt welche Spalten angezeigt werden
            user_guid: Benutzer-GUID für Systemsteuerung-Speicherung
            
        Returns:
            Tuple: (controls, daten)
            - controls: ColumnControl-Objekt mit Spaltenstruktur  
            - daten: Liste von Dicts mit optimaler Spaltenstruktur
        """
        try:
            logger.info(f"🏭 PdvmValueViewProvider.get_value_view gestartet - Mode: {mode}")
            
            # Delegiere vorerst an die bestehende Implementierung
            raw_controls, raw_data = self._temp_central_db.get_value_view(view_config, stichtag)
            
            if not raw_controls or not raw_data:
                logger.warning("⚠️ Keine Basis-Daten vom Central-DB erhalten")
                return None, []
            
            # Lade gespeicherte Systemsteuerung-Konfiguration falls vorhanden
            saved_config = None
            if user_guid:
                saved_config = self._load_show_order_from_systemsteuerung(user_guid, view_config)
            
            # Mode-spezifische Verarbeitung
            if mode == "normal":
                filtered_controls, filtered_data = self._process_normal_mode(
                    raw_controls, raw_data, user_guid, view_config, saved_config
                )
            elif mode == "expert":
                filtered_controls, filtered_data = self._process_expert_mode(
                    raw_controls, raw_data, user_guid, view_config, saved_config
                )
            else:
                logger.warning(f"⚠️ Unbekannter Mode: {mode}, verwende Normal-Mode")
                filtered_controls, filtered_data = self._process_normal_mode(
                    raw_controls, raw_data, user_guid, view_config, saved_config
                )
            
            logger.info(f"✅ PdvmValueViewProvider.get_value_view erfolgreich - Mode: {mode}")
            return filtered_controls, filtered_data
            
        except Exception as e:
            logger.error(f"❌ Fehler in PdvmValueViewProvider.get_value_view: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, []
    
    def get_view_config(self, view_guid: str) -> Dict:
        """Lädt View-Konfiguration für gegebene view_guid"""
        try:
            viewdaten_db = PdvmCentralDatenbank(
                db_name=self.db_name,
                table_name="viewdaten",
                guid=view_guid
            )
            return viewdaten_db.lesen()
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Config für {view_guid}: {e}")
            return {}
    
    def create_control_structure_for_felder(self, felder_config: Dict) -> Any:
        """Erstellt Control-Struktur für gegebene Felder-Konfiguration"""
        return self._temp_central_db.create_control_structure_for_felder(felder_config)
    
    def _process_normal_mode(self, raw_controls, raw_data, user_guid, view_config, saved_config=None):
        """
        Verarbeitet Daten für Normal-Mode
        
        Normal-Mode: Nur Spalten mit expert=false, in show_order Reihenfolge
        1. Zuerst Spalten mit show=true 
        2. Dann der Rest
        3. show_order wird neu erstellt und in Systemsteuerung gespeichert
        Berücksichtigt gespeicherte Systemsteuerung-Konfiguration falls vorhanden
        """
        try:
            logger.info("🔧 Normal-Mode Verarbeitung gestartet")
            
            # 1. Gespeicherte Konfiguration prüfen und anwenden
            if saved_config and saved_config.get('columns'):
                logger.info("📖 Verwende gespeicherte Systemsteuerung-Konfiguration")
                # Spalten aus gespeicherter Konfiguration wiederherstellen
                saved_columns_dict = {col['name']: col for col in saved_config['columns']}
                
                # Original-Spalten mit gespeicherten Werten aktualisieren
                for column in raw_controls.columns:
                    column_name = column.get('name', '')
                    if column_name in saved_columns_dict:
                        saved_col = saved_columns_dict[column_name]
                        column['show'] = saved_col.get('show', False)
                        column['show_order'] = saved_col.get('show_order', 0)
                        logger.debug(f"🔄 Spalte {column_name}: show={column['show']}, order={column['show_order']}")
            
            # 2. Spalten filtern: nur expert=false, aber dummy ausschließen
            normal_columns = []
            show_columns = []
            hide_columns = []
            
            for column in raw_controls.columns:
                expert_flag = column.get('expert', False)
                show_flag = column.get('show', False)
                column_name = column.get('name', '')
                
                # Dummy-Spalte überspringen (ist nur Fallback, normalerweise nicht angezeigt)
                if column_name == 'dummy':
                    continue
                
                if not expert_flag:  # Nur non-expert Spalten
                    normal_columns.append(column)
                    if show_flag:
                        show_columns.append(column)
                    else:
                        hide_columns.append(column)
            
            # 3. Reihenfolge: Wenn gespeicherte Config vorhanden, nach show_order sortieren
            # Ansonsten: erst show=true, dann show=false
            if saved_config and saved_config.get('columns'):
                # Nach gespeicherter show_order sortieren
                sorted_columns = sorted(normal_columns, key=lambda x: x.get('show_order', 0))
            else:
                # Standard-Sortierung: erst show=true, dann show=false
                sorted_columns = show_columns + hide_columns
            
            # 4. display_order für die Anzeige im Dialog setzen (immer neu berechnen)
            for i, column in enumerate(sorted_columns):
                column['show_order'] = i + 1
                column['display_order'] = i + 1  # Temporäre Eigenschaft für Dialog-Anzeige
            
            # 4. Neue Control-Struktur erstellen
            filtered_controls = self._create_filtered_controls(raw_controls, sorted_columns)
            
            # 5. Daten entsprechend filtern
            normal_column_names = [col['name'] for col in sorted_columns]
            filtered_data = self._filter_data_columns(raw_data, normal_column_names)
            
            # 6. In Systemsteuerung speichern (falls user_guid vorhanden)
            if user_guid:
                self._save_show_order_to_systemsteuerung(user_guid, view_config, sorted_columns)
            
            logger.info(f"✅ Normal-Mode: {len(sorted_columns)} Spalten, {len(show_columns)} sichtbar")
            return filtered_controls, filtered_data
            
        except Exception as e:
            logger.error(f"❌ Fehler in Normal-Mode Verarbeitung: {e}")
            return raw_controls, raw_data
    
    def _process_expert_mode(self, raw_controls, raw_data, user_guid, view_config, saved_config=None):
        """
        Verarbeitet Daten für Expert-Mode
        
        Expert-Mode: Alle Spalten, Reihenfolge nach order und show
        Berücksichtigt gespeicherte Systemsteuerung-Konfiguration falls vorhanden
        """
        try:
            logger.info("🔧 Expert-Mode Verarbeitung gestartet")
            
            # 1. Alle Spalten verwenden
            all_columns = raw_controls.columns.copy()
            
            # 2. Sortieren nach order, dann nach show
            sorted_columns = sorted(all_columns, key=lambda x: (x.get('order', 0), not x.get('show', False)))
            
            # 3. display_order für Expert-Mode setzen (basierend auf aktueller Position)
            for i, column in enumerate(sorted_columns):
                column['display_order'] = i + 1  # Temporäre Eigenschaft für Dialog-Anzeige
            
            # 4. Control-Struktur und Daten unverändert lassen (alle Spalten)
            expert_column_names = [col['name'] for col in sorted_columns]
            filtered_data = self._filter_data_columns(raw_data, expert_column_names)
            
            logger.info(f"✅ Expert-Mode: {len(sorted_columns)} Spalten (alle verfügbar)")
            return raw_controls, filtered_data
            
        except Exception as e:
            logger.error(f"❌ Fehler in Expert-Mode Verarbeitung: {e}")
            return raw_controls, raw_data
    
    def _create_filtered_controls(self, original_controls, filtered_columns):
        """Erstellt neue Control-Struktur mit gefilterten Spalten"""
        try:
            # Erstelle eine Kopie der Control-Struktur mit nur den gefilterten Spalten
            filtered_controls = type(original_controls)()  # Neue Instanz derselben Klasse
            filtered_controls.columns = filtered_columns
            return filtered_controls
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der gefilterten Controls: {e}")
            return original_controls
    
    def _filter_data_columns(self, raw_data, column_names):
        """Filtert Datenzeilen auf die angegebenen Spalten"""
        try:
            filtered_data = []
            for row in raw_data:
                filtered_row = {col_name: row.get(col_name, '') for col_name in column_names}
                filtered_data.append(filtered_row)
            return filtered_data
        except Exception as e:
            logger.error(f"❌ Fehler beim Filtern der Daten: {e}")
            return raw_data
    
    def _load_show_order_from_systemsteuerung(self, user_guid, view_config):
        """Lädt die gespeicherte show_order aus der Systemsteuerung über PdvmCentralDatenbank"""
        try:
            # Verwende die EINE Systemsteuerung-Instanz
            # Gruppe ist user_guid, Feld ist 'complete_controls'
            saved_controls_data = self._systemsteuerung_db.get_value(
                gruppe=user_guid, 
                feld='complete_controls'
            )
            
            if saved_controls_data:
                # get_value() gibt bereits ein Dictionary zurück, nicht JSON
                if isinstance(saved_controls_data, str):
                    import json
                    config_data = json.loads(saved_controls_data)
                else:
                    config_data = saved_controls_data  # Bereits Dictionary
                
                # Timestamp ist bereits im PDVM-Format (float), keine Konvertierung nötig
                logger.info(f"📖 Gespeicherte Config für User {user_guid} geladen: {len(config_data.get('columns', []))} Spalten")
                return config_data
            else:
                logger.info(f"📖 Keine gespeicherte Config für User {user_guid} gefunden")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Config: {e}")
            return None

    def _save_show_order_to_systemsteuerung(self, user_guid, view_config, controls_data):
        """Speichert die show_order in der Systemsteuerung über PdvmCentralDatenbank"""
        try:
            # Import für PDVM DateTime Format
            from pdvm_datetime import PdvmDateTimeUtils
            
            # Controls können sowohl Dictionary als auch Control-Objekte sein
            show_order_data = {
                'columns': [],
                'mode': 'normal',
                'timestamp': PdvmDateTimeUtils.PdvmDateTimeNow()  # Aktueller PDVM-Zeitstempel
            }
            
            logger.debug(f"📊 Speichere {len(controls_data)} Controls in Systemsteuerung")
            
            for i, item in enumerate(controls_data):
                if hasattr(item, 'name'):  # Control-Objekt
                    show_value = getattr(item, 'show_show', getattr(item, 'show', False))
                    col_data = {
                        'name': item.name,
                        'show_order': getattr(item, 'show_order', 0),
                        'show': show_value
                    }
                    logger.debug(f"📊 Control-Objekt {i}: {item.name} - show_show={getattr(item, 'show_show', 'N/A')}, show={getattr(item, 'show', 'N/A')} → {show_value}")
                else:  # Dictionary
                    show_value = item.get('show_show', item.get('show', False))
                    col_data = {
                        'name': item['name'], 
                        'show_order': item.get('display_order', item.get('show_order', 0)),  # display_order hat Vorrang
                        'show': show_value
                    }
                    logger.debug(f"📊 Dictionary {i}: {item['name']} - show_show={item.get('show_show', 'N/A')}, show={item.get('show', 'N/A')} → {show_value}")
                
                show_order_data['columns'].append(col_data)
            
            # Verwende die EINE Systemsteuerung-Instanz
            # Speichere als Dictionary (nicht JSON), da PdvmCentralDatenbank das automatisch handhabt
            logger.debug(f"📊 Zu speichernde Daten: {show_order_data}")
            
            success = self._systemsteuerung_db.set_value(
                gruppe=user_guid,
                feld='complete_controls',
                wert=show_order_data  # Dictionary direkt übergeben
            )
            
            logger.debug(f"📊 set_value Erfolg: {success}")
            
            # WICHTIG: Verwende save_values() für PdvmCentralDatenbank-Persistierung
            # Das speichert alle Dirty-Data der aktuellen Instanz
            try:
                self._systemsteuerung_db.save_values()
                logger.info(f"💾 show_order für User {user_guid} in Systemsteuerung gespeichert: {len(controls_data)} Spalten")
                return True
            except Exception as save_error:
                logger.error(f"❌ Fehler beim Schreiben in Systemsteuerung-Datenbank für User {user_guid}: {save_error}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der show_order: {e}")
            return False
