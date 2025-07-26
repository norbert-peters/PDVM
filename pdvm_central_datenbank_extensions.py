# pdvm_central_datenbank_extensions.py
"""
Erweiterungen für PdvmCentralDatenbank für Original/Show-Spalten-Architektur
"""

import logging
from typing import Dict, List, Any, Optional

# Import der Basis-Klasse
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmCentralDatenbankExtensions:
    """
    Erweiterungen für die zentrale Datenbank-Klasse
    Implementiert die Original/Show-Spalten-Logik
    """
    
    def get_value_view_with_columns(self, view_config: Dict, stichtag: float, 
                                   show_YMD: bool = False, show_alter: bool = False) -> List[Dict[str, Any]]:
        """
        Zentrale Methode zur Datenaufbereitung mit Original/Show-Spalten-Struktur
        
        Architektur:
        1. Für jedes Feld: field_original und field_show
        2. type:string -> original = show = raw_value
        3. type:dropdown -> original = raw_key, show = translated_value
        4. type:date -> original = pdvm_datetime, show = formatted_date
        5. Zusatzspalten: Alter, Jahr, Monat, Tag (IMMER erstellt)
        
        Args:
            view_config: View-Konfiguration
            stichtag: Stichtag für historische Daten
            show_YMD: Sichtbarkeit der YMD-Spalten (Struktur wird immer erstellt)
            show_alter: Sichtbarkeit der Alter-Spalten (Struktur wird immer erstellt)
            
        Returns:
            List[Dict]: Daten mit Original/Show-Spalten-Struktur
        """
        try:
            # Basis-Konfiguration extrahieren
            root_config = view_config.get("ROOT", {})
            table_name = root_config.get("view_table")
            
            if not table_name:
                raise ValueError("Kein view_table in ROOT-Konfiguration")
            
            # Feld-Konfigurationen
            metadata = view_config.get("metadata", {})
            table_metadata = metadata.get(table_name, {})
            fields_config = table_metadata.get("felder", [])
            
            # Rohdaten aus Datenbank laden
            raw_data = self._load_raw_table_data(table_name, stichtag)
            
            # Daten mit Original/Show-Spalten aufbereiten
            processed_data = []
            
            for record in raw_data:
                processed_record = {}
                
                # Standard-Felder mit Original/Show-Spalten
                for field_config in fields_config:
                    field_name = field_config.get("feld")
                    field_type = field_config.get("type", "string")
                    
                    if not field_name:
                        continue
                    
                    raw_value = record.get(field_name)
                    
                    # Original-Spalte (immer Rohdaten)
                    processed_record[f"{field_name}_original"] = raw_value
                    
                    # Show-Spalte (abhängig vom Typ)
                    if field_type == "string":
                        # String: Original = Show
                        processed_record[f"{field_name}_show"] = raw_value or ""
                        
                    elif field_type == "dropdown":
                        # Dropdown: Original = Key, Show = übersetzter Wert
                        dropdown_config = field_config.get("dropdown", {})
                        translated_value = self.get_dropdown_display_value(
                            raw_value=str(raw_value) if raw_value else "",
                            field_name=field_name,
                            dropdown_config=dropdown_config
                        )
                        processed_record[f"{field_name}_show"] = translated_value
                        
                    elif field_type == "date":
                        # Datum: Original = PdvmDateTime, Show = formatiertes Datum
                        if raw_value and str(raw_value).strip():
                            try:
                                from pd_datetime import Pdvm_DateTime
                                pdvm_dt = Pdvm_DateTime("DEU")
                                pdvm_dt.PdvmDateTime = float(raw_value)
                                
                                # Show-Spalte: Formatiertes Datum
                                processed_record[f"{field_name}_show"] = pdvm_dt.Date
                                
                                # ZUSATZSPALTEN (immer erstellt, unabhängig von show_YMD/show_alter)
                                
                                # Jahr/Monat/Tag-Spalten
                                processed_record[f"{field_name}_Jahr"] = pdvm_dt.Year
                                processed_record[f"{field_name}_Monat"] = pdvm_dt.Month
                                processed_record[f"{field_name}_Tag"] = pdvm_dt.Day
                                
                                # Interne Filter-Spalten (für Jahr/Monat/Tag-Filter)
                                processed_record[f"_{field_name}_year"] = pdvm_dt.Year
                                processed_record[f"_{field_name}_month"] = pdvm_dt.Month
                                processed_record[f"_{field_name}_day"] = pdvm_dt.Day
                                
                                # Alter-Spalte (bei Geburtsdatum)
                                if field_name.lower() in ['geburtsdatum', 'geburtstag']:
                                    alter = self._calculate_age(pdvm_dt)
                                    processed_record[f"{field_name}_Alter"] = alter
                                    
                            except Exception as e:
                                logger.warning(f"⚠️ Fehler bei Datumsverarbeitung {field_name}={raw_value}: {e}")
                                # Fallback: Leere Werte
                                processed_record[f"{field_name}_show"] = ""
                                processed_record[f"{field_name}_Jahr"] = None
                                processed_record[f"{field_name}_Monat"] = None
                                processed_record[f"{field_name}_Tag"] = None
                                processed_record[f"_{field_name}_year"] = None
                                processed_record[f"_{field_name}_month"] = None
                                processed_record[f"_{field_name}_day"] = None
                                
                                if field_name.lower() in ['geburtsdatum', 'geburtstag']:
                                    processed_record[f"{field_name}_Alter"] = None
                        else:
                            # Leeres Datum
                            processed_record[f"{field_name}_show"] = ""
                            processed_record[f"{field_name}_Jahr"] = None
                            processed_record[f"{field_name}_Monat"] = None
                            processed_record[f"{field_name}_Tag"] = None
                            processed_record[f"_{field_name}_year"] = None
                            processed_record[f"_{field_name}_month"] = None
                            processed_record[f"_{field_name}_day"] = None
                            
                            if field_name.lower() in ['geburtsdatum', 'geburtstag']:
                                processed_record[f"{field_name}_Alter"] = None
                    
                    else:
                        # Unbekannter Typ: Wie String behandeln
                        processed_record[f"{field_name}_show"] = str(raw_value) if raw_value else ""
                
                # GUID für Referenzierung
                processed_record["_guid"] = record.get("_guid", "")
                
                processed_data.append(processed_record)
            
            logger.info(f"✅ Daten aufbereitet: {len(processed_data)} Datensätze mit Original/Show-Spalten")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenaufbereitung mit Original/Show-Spalten: {e}")
            raise
    
    def _load_raw_table_data(self, table_name: str, stichtag: float) -> List[Dict[str, Any]]:
        """
        Lädt Rohdaten aus der Tabelle
        
        Args:
            table_name: Name der Tabelle
            stichtag: Stichtag für historische Daten
            
        Returns:
            List[Dict]: Rohdaten aus der Datenbank
        """
        try:
            # Datenbank-Manager für die Tabelle
            table_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=table_name
            )
            
            # Alle Datensätze laden
            raw_data = table_db.load_all_records()
            
            logger.info(f"✅ Rohdaten geladen: {len(raw_data)} Datensätze aus {table_name}")
            
            return raw_data
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Rohdaten aus {table_name}: {e}")
            return []
    
    def _calculate_age(self, geburtsdatum_dt) -> Optional[int]:
        """
        Berechnet das Alter zum aktuellen Tagesdatum
        
        Args:
            geburtsdatum_dt: PdvmDateTime-Instanz des Geburtsdatums
            
        Returns:
            int: Alter in Jahren oder None bei Fehler
        """
        try:
            from pd_datetime import Pdvm_DateTime, PdvmDateTimeUtils
            
            # Heutiges Datum
            heute_dt = Pdvm_DateTime("DEU")
            heute_dt.PdvmDateTime = PdvmDateTimeUtils.PdvmDateTimeNow()
            
            # Grundalter: Differenz der Jahre
            alter = heute_dt.Year - geburtsdatum_dt.Year
            
            # Korrektur: Hat die Person schon Geburtstag gehabt?
            if (heute_dt.Month < geburtsdatum_dt.Month or 
                (heute_dt.Month == geburtsdatum_dt.Month and heute_dt.Day < geburtsdatum_dt.Day)):
                alter -= 1
            
            return max(0, alter)  # Negative Alter vermeiden
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Altersberechnung: {e}")
            return None


# Monkey-Patch für PdvmCentralDatenbank
def install_extensions():
    """Installiert die Erweiterungen in PdvmCentralDatenbank"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Erweiterungen hinzufügen
        extensions = PdvmCentralDatenbankExtensions()
        PdvmCentralDatenbank.get_value_view_with_columns = extensions.get_value_view_with_columns
        PdvmCentralDatenbank._load_raw_table_data = extensions._load_raw_table_data
        PdvmCentralDatenbank._calculate_age = extensions._calculate_age
        
        logger.info("✅ PdvmCentralDatenbank-Erweiterungen installiert")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Installieren der Erweiterungen: {e}")


# Auto-Installation beim Import
install_extensions()
