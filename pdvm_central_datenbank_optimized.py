# Optimierte get_value_view Methode mit getrennter Spalten-Erstellung und Daten-Befüllung

def get_value_view(self, view_config: dict, stichtag: Optional[float] = None) -> list:
    """
    Zentrale View-Methode: Erstellt eine saubere, konsistente Tabellenstruktur.
    
    OPTIMIERTE ARCHITEKTUR mit getrennter Spalten-Erstellung und Daten-Befüllung:
    1. Alle Spaltennamen in Kleinbuchstaben
    2. System-Spalten: uid_original, uid_show
    3. Nur _original und _show Spalten erlaubt
    4. Automatische Original-Spalten für Datum-Felder: alter_original, jahr_original, monat_original, tag_original
    5. Aufbereitete Show-Spalten für alle Felder
    6. Ein einziger Durchlauf für alle Daten-Operationen
    
    Args:
        view_config: View-Konfiguration mit metadata und Feldliste
        stichtag: Optionaler Stichtag für historische Daten
        
    Returns:
        Liste von Dicts mit optimaler Spaltenstruktur
    """
    try:
        if stichtag is None:
            from pd_datetime import Pdvm_DateTime
            dt_inst = Pdvm_DateTime("DEU")
            stichtag = dt_inst.PdvmDateTimeNow()
        
        # DateTime-Instanz für Datumsübersetzungen
        dt_formatter = Pdvm_DateTime("DEU")
        
        # 1. View-Konfiguration extrahieren
        if not view_config or "metadata" not in view_config:
            logger.error("❌ Ungültige view_config - metadata fehlt")
            return []
        
        table_name = view_config["ROOT"]["view_table"]
        felder = view_config["metadata"][table_name]["felder"]
        
        # 2. Alle Datensätze der VIEW-TABELLE laden (EINMAL!)
        from pdvm_datenbank import PdvmDatenbank
        data_db = PdvmDatenbank(db_name=self.db_name, table_name=table_name)
        alle_datensaetze = data_db.lesen_alle()
        
        if not alle_datensaetze:
            logger.warning(f"📊 Keine Datensätze in Tabelle {table_name} gefunden")
            return []
        
        # WICHTIG: historisch-Flag für View-Tabelle ermitteln
        if alle_datensaetze and len(alle_datensaetze) > 0:
            first_row = alle_datensaetze[0]
            self.historisch = bool(first_row.get("historisch", False))
        else:
            self.historisch = False
        
        logger.info(f"📊 get_value_view: Verarbeite {len(alle_datensaetze)} Datensätze für {len(felder)} Felder")
        logger.info("🔧 OPTIMIERTE ARCHITEKTUR: Getrennte Spalten-Erstellung, automatische Original-Spalten für Datum")
        
        # 3. SCHRITT 1: Spalten-Struktur definieren (ohne Doppelungen)
        column_structure = self._create_column_structure(felder)
        
        # 4. SCHRITT 2: Datensätze verarbeiten (ein Durchlauf)
        result = []
        for row_data in alle_datensaetze:
            guid = row_data.get("uid")
            if not guid:
                continue
            
            # JSON-Daten laden
            raw_data = row_data.get("daten", {})
            if isinstance(raw_data, str):
                try:
                    self.data = json.loads(raw_data)
                except:
                    self.data = {}
            else:
                self.data = raw_data
            
            # Datensatz mit definierter Spalten-Struktur erstellen
            record = self._create_record_with_structure(
                guid, felder, column_structure, dt_formatter, stichtag
            )
            
            result.append(record)
        
        logger.info(f"✅ {len(result)} Datensätze verarbeitet - {len(column_structure)} Spalten total")
        logger.info("📊 KEINE DOPPELUNGEN: Saubere Spalten-Struktur mit automatischen Original-Spalten")
        logger.info("⚡ OPTIMIERT: Ein Durchlauf für alle Daten-Operationen")
        return result
        
    except Exception as e:
        logger.error(f"❌ Fehler in get_value_view: {e}")
        return []

def _create_column_structure(self, felder: list) -> dict:
    """
    Erstellt die komplette Spalten-Struktur ohne Doppelungen.
    
    Args:
        felder: Liste der Feld-Konfigurationen
        
    Returns:
        dict: Spalten-Struktur mit allen benötigten Spalten
    """
    structure = {}
    
    # System-Spalten (immer vorhanden)
    structure["uid_original"] = {"type": "system", "order": 0}
    structure["uid_show"] = {"type": "system", "order": 1}
    
    order_counter = 2
    
    # Benutzer-Felder verarbeiten
    for feld_config in felder:
        feld_name = feld_config["feld"].lower()
        feld_type = feld_config.get("type", "string")
        
        # Original-Spalte (immer)
        original_col = f"{feld_name}_original"
        if original_col not in structure:
            structure[original_col] = {
                "type": "original", 
                "field_type": feld_type,
                "field_config": feld_config,
                "order": order_counter
            }
            order_counter += 1
        
        # Show-Spalte (immer)
        show_col = f"{feld_name}_show"
        if show_col not in structure:
            structure[show_col] = {
                "type": "show", 
                "field_type": feld_type,
                "field_config": feld_config,
                "order": order_counter
            }
            order_counter += 1
        
        # NEUE: Automatische Original-Spalten für Datum-Felder
        if feld_type == "date":
            date_original_cols = [
                f"{feld_name}_alter_original",
                f"{feld_name}_jahr_original", 
                f"{feld_name}_monat_original",
                f"{feld_name}_tag_original"
            ]
            
            for col in date_original_cols:
                if col not in structure:
                    structure[col] = {
                        "type": "date_original",
                        "field_type": "integer",
                        "parent_field": feld_name,
                        "field_config": feld_config,
                        "order": order_counter
                    }
                    order_counter += 1
            
            # Entsprechende Show-Spalten für Datum
            date_show_cols = [
                f"{feld_name}_alter_show",
                f"{feld_name}_jahr_show", 
                f"{feld_name}_monat_show",
                f"{feld_name}_tag_show"
            ]
            
            for col in date_show_cols:
                if col not in structure:
                    structure[col] = {
                        "type": "date_show",
                        "field_type": "string",
                        "parent_field": feld_name,
                        "field_config": feld_config,
                        "order": order_counter
                    }
                    order_counter += 1
    
    logger.info(f"🏗️ Spalten-Struktur erstellt: {len(structure)} Spalten definiert")
    return structure

def _create_record_with_structure(self, guid: str, felder: list, column_structure: dict, 
                                dt_formatter, stichtag: float) -> dict:
    """
    Erstellt einen Datensatz basierend auf der definierten Spalten-Struktur.
    EIN DURCHLAUF für alle Daten-Operationen.
    
    Args:
        guid: GUID des Datensatzes
        felder: Liste der Feld-Konfigurationen  
        column_structure: Definierte Spalten-Struktur
        dt_formatter: PdvmDateTime-Instanz
        stichtag: Aktueller Stichtag
        
    Returns:
        dict: Vollständig befüllter Datensatz
    """
    # Datensatz mit allen Spalten initialisieren
    record = {}
    
    # Alle Spalten in korrekter Reihenfolge initialisieren
    sorted_columns = sorted(column_structure.items(), key=lambda x: x[1]["order"])
    for col_name, col_info in sorted_columns:
        record[col_name] = None  # Initialer Wert
    
    # System-Spalten befüllen
    record["uid_original"] = guid
    record["uid_show"] = guid[:8] + "..."
    
    # Felder-Daten sammeln (ein Durchlauf durch alle Felder)
    field_data = {}
    for feld_config in felder:
        feld_name = feld_config["feld"].lower()
        feld_gruppe = feld_config.get("gruppe", "ROOT")
        feld_type = feld_config.get("type", "string")
        
        # DB-Zugriff
        feld_gruppe_upper = feld_gruppe.upper()
        feld_name_upper = feld_config["feld"].upper()
        
        result_dict = self.get_value(feld_gruppe_upper, feld_name_upper, stichtag)
        original_wert = result_dict.get("wert") if result_dict else None
        
        field_data[feld_name] = {
            "original": original_wert,
            "config": feld_config,
            "type": feld_type
        }
    
    # ALLE Spalten in einem Durchlauf befüllen
    for feld_name, data in field_data.items():
        original_wert = data["original"]
        feld_config = data["config"]
        feld_type = data["type"]
        
        # Original-Spalte befüllen
        record[f"{feld_name}_original"] = original_wert
        
        # Show-Spalte befüllen
        show_wert = self._create_show_value(original_wert, feld_config, dt_formatter, stichtag)
        record[f"{feld_name}_show"] = show_wert
        
        # Datum-Felder: Automatische Original- und Show-Spalten
        if feld_type == "date":
            self._add_complete_date_columns(record, feld_name, original_wert, dt_formatter, stichtag)
    
    return record

def _add_complete_date_columns(self, record: dict, feld_name: str, original_wert: Any, 
                              dt_formatter, stichtag: float):
    """
    Fügt ALLE Datums-Spalten hinzu: Original UND Show-Versionen.
    
    Args:
        record: Der Datensatz-Record (wird modifiziert)
        feld_name: Name des Datums-Feldes (kleinbuchstaben)
        original_wert: Der Original-Datumswert
        dt_formatter: PdvmDateTime-Instanz
        stichtag: Aktueller Stichtag
    """
    try:
        if not isinstance(original_wert, (int, float)) or original_wert <= 0:
            # ALLE Spalten mit leeren Werten initialisieren
            date_cols = [
                f"{feld_name}_alter_original", f"{feld_name}_alter_show",
                f"{feld_name}_jahr_original", f"{feld_name}_jahr_show",
                f"{feld_name}_monat_original", f"{feld_name}_monat_show",
                f"{feld_name}_tag_original", f"{feld_name}_tag_show"
            ]
            for col in date_cols:
                record[col] = ""
            return
        
        # Datum setzen
        dt_formatter.PdvmDateTimeSet(original_wert)
        
        # Alter berechnen (basierend auf Stichtag)
        dt_stichtag = Pdvm_DateTime("DEU")
        dt_stichtag.PdvmDateTimeSet(stichtag)
        alter = dt_stichtag.PdvmDateTimeGetAlter(original_wert)
        
        # Jahr, Monat, Tag extrahieren
        jahr = dt_formatter.PdvmDateTimeGetJahr()
        monat = dt_formatter.PdvmDateTimeGetMonat()
        tag = dt_formatter.PdvmDateTimeGetTag()
        monat_name = dt_formatter.PdvmDateTimeGetMonatName()  # Deutscher Monatsname
        
        # ORIGINAL-Spalten (Zahlen-Werte)
        record[f"{feld_name}_alter_original"] = alter if alter is not None else 0
        record[f"{feld_name}_jahr_original"] = jahr
        record[f"{feld_name}_monat_original"] = monat
        record[f"{feld_name}_tag_original"] = tag
        
        # SHOW-Spalten (Formatierte Anzeige)
        record[f"{feld_name}_alter_show"] = str(alter) if alter is not None else ""
        record[f"{feld_name}_jahr_show"] = str(jahr)
        record[f"{feld_name}_monat_show"] = monat_name  # z.B. "Januar"
        record[f"{feld_name}_tag_show"] = str(tag)
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Datums-Spalten für {feld_name}: {e}")
        # Fallback: Alle Spalten leer
        date_cols = [
            f"{feld_name}_alter_original", f"{feld_name}_alter_show",
            f"{feld_name}_jahr_original", f"{feld_name}_jahr_show",
            f"{feld_name}_monat_original", f"{feld_name}_monat_show",
            f"{feld_name}_tag_original", f"{feld_name}_tag_show"
        ]
        for col in date_cols:
            record[col] = ""
