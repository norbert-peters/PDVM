# Neue get_value_view Implementierung nach deiner strukturierten Architektur

def get_value_view(self, view_config: dict, stichtag: Optional[float] = None) -> tuple:
    """
    NEUE STRUKTURIERTE ARCHITEKTUR mit ColumnControl.
    Implementiert deine 4-Schritte-Methode:
    
    1. Control-Struktur über alle Spalten mit order-Eigenschaft
    2. Lese Original-Spalten aus viewdaten mit spaltenname_original 
    3. Füge type:date _original Sonderspalten und Show-Spalten hinzu
    4. Lineares Befüllen nach Control-Struktur
    
    Returns:
        tuple: (table_data: list, column_control: ColumnControl) für ViewWidget-Verwendung
    """
    try:
        if stichtag is None:
            from pd_datetime import Pdvm_DateTime
            dt_inst = Pdvm_DateTime("DEU")
            stichtag = dt_inst.PdvmDateTimeNow()
        
        logger.info("🏗️ NEUE CONTROL-ARCHITEKTUR: Strukturierte Spalten-Verarbeitung")
        
        # 1. View-Konfiguration validieren
        if not view_config or "metadata" not in view_config:
            logger.error("❌ Ungültige view_config - metadata fehlt")
            return [], ColumnControl()
        
        table_name = view_config["ROOT"]["view_table"]
        felder = view_config["metadata"][table_name]["felder"]
        
        # 2. Alle Datensätze laden
        from pdvm_datenbank import PdvmDatenbank
        data_db = PdvmDatenbank(db_name=self.db_name, table_name=table_name)
        alle_datensaetze = data_db.lesen_alle()
        
        if not alle_datensaetze:
            logger.warning(f"📊 Keine Datensätze in Tabelle {table_name} gefunden")
            return [], ColumnControl()
        
        logger.info(f"📊 Verarbeite {len(alle_datensaetze)} Datensätze für {len(felder)} Felder")
        
        # SCHRITT 1: Control-Struktur erstellen mit order
        column_control = self._create_column_control(felder)
        
        # SCHRITT 4: Lineares Befüllen der Tabelle nach Control
        table_data = []
        dropdown_cache = {}  # Dropdown-Daten nur einmal pro GUID laden
        
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
            
            # Record nach Control-Struktur erstellen
            record = self._create_record_by_control(
                guid=guid,
                column_control=column_control,
                stichtag=stichtag,
                dropdown_cache=dropdown_cache
            )
            
            table_data.append(record)
        
        logger.info(f"✅ {len(table_data)} Datensätze verarbeitet")
        logger.info(f"📊 {len(column_control.columns)} Spalten in Control-Struktur")
        logger.info("🎯 Control-Daten verfügbar für ViewWidget-Darstellung")
        
        return table_data, column_control
        
    except Exception as e:
        logger.error(f"❌ Fehler in get_value_view: {e}")
        return [], ColumnControl()

def _create_column_control(self, felder: list) -> ColumnControl:
    """
    SCHRITT 1: Erstellt die Control-Struktur über alle Spalten.
    Definiert Order und Eigenschaften für jede Spalte.
    """
    control = ColumnControl()
    order = 0
    
    # System-Spalten zuerst
    control.add_column("uid_original", "system", order)
    order += 1
    control.add_column("uid_show", "system", order)
    order += 1
    
    # SCHRITT 2: Original-Spalten aus Feldkonfiguration
    for feld_config in felder:
        feld_name = feld_config["feld"].lower()
        feld_type = feld_config.get("type", "string")
        
        # Original-Spalte
        control.add_column(
            f"{feld_name}_original", 
            "original", 
            order,
            original_field=feld_name,
            field_config=feld_config
        )
        order += 1
        
        # SCHRITT 2.1: Bei type:date -> _original Sonderspalten hinzufügen
        if feld_type == "date":
            date_original_cols = [
                f"{feld_name}_alter_original",
                f"{feld_name}_jahr_original", 
                f"{feld_name}_monat_original",
                f"{feld_name}_tag_original"
            ]
            for col in date_original_cols:
                control.add_column(
                    col, 
                    "date_plus", 
                    order,
                    original_field=feld_name,
                    field_config=feld_config,
                    is_auto_generated=True
                )
                order += 1
    
    # SCHRITT 3: Show-Spalten hinzufügen
    for feld_config in felder:
        feld_name = feld_config["feld"].lower()
        feld_type = feld_config.get("type", "string")
        
        # Show-Spalte (Name aus Original-Spalte übernommen)
        control.add_column(
            f"{feld_name}_show", 
            "show", 
            order,
            original_field=feld_name,
            field_config=feld_config
        )
        order += 1
        
        # Bei type:date -> Show-Sonderspalten
        if feld_type == "date":
            date_show_cols = [
                f"{feld_name}_alter_show",
                f"{feld_name}_jahr_show", 
                f"{feld_name}_monat_show",
                f"{feld_name}_tag_show"
            ]
            for col in date_show_cols:
                control.add_column(
                    col, 
                    "date_plus", 
                    order,
                    original_field=feld_name,
                    field_config=feld_config,
                    is_auto_generated=True
                )
                order += 1
    
    # Control sortieren
    control.sort_columns()
    
    logger.info(f"🏗️ Control-Struktur erstellt: {len(control.columns)} Spalten")
    logger.info("📋 Reihenfolge: System → Original → Auto-Original → Show → Auto-Show")
    
    return control

def _create_record_by_control(self, guid: str, column_control: ColumnControl, 
                            stichtag: float, dropdown_cache: dict) -> dict:
    """
    SCHRITT 4: Erstellt einen Record basierend auf der Control-Struktur.
    Lineares Abarbeiten ohne Duplikate oder falsche Reihenfolge.
    """
    record = {}
    dt_formatter = Pdvm_DateTime("DEU")
    
    for column_info in column_control.columns:
        col_name = column_info['name']
        col_type = column_info['type']
        original_field = column_info.get('original_field')
        field_config = column_info.get('field_config', {})
        
        if col_type == "system":
            # System-Spalten
            if col_name == "uid_original":
                record[col_name] = guid
            elif col_name == "uid_show":
                record[col_name] = guid[:8] + "..."  # Verkürzte Anzeige
                
        elif col_type == "original":
            # Original-Spalte: Wert aus DB mit spaltenname_original
            if original_field:
                # SCHRITT 2: Lese Wert mit spaltenname_original
                gruppe = field_config.get("gruppe", "PERSDATEN")
                wert = self.get_value(gruppe, original_field.upper(), stichtag)
                # Nur Skalar-Werte verwenden (nicht dict)
                if isinstance(wert, dict) and "wert" in wert:
                    record[col_name] = wert["wert"]
                else:
                    record[col_name] = wert
                    
        elif col_type == "show":
            # Show-Spalte: Übersetzung von Original-Wert
            if original_field:
                original_col = f"{original_field}_original"
                original_wert = record.get(original_col)
                
                # type:text -> einfach übernehmen
                if field_config.get("type") == "text":
                    record[col_name] = str(original_wert) if original_wert else ""
                # dropdown -> übersetzen (mit Cache!)
                elif field_config.get("type") == "dropdown":
                    record[col_name] = self._translate_dropdown_cached(
                        original_wert, field_config, dropdown_cache, guid
                    )
                # type:date -> PdvmDateTime.Date
                elif field_config.get("type") == "date":
                    if isinstance(original_wert, (int, float)) and original_wert > 0:
                        dt_formatter.PdvmDateTime = original_wert
                        record[col_name] = dt_formatter.Date
                    else:
                        record[col_name] = ""
                else:
                    record[col_name] = str(original_wert) if original_wert else ""
                    
        elif col_type == "date_plus":
            # Automatische Datum-Spalten
            if original_field and "_" in col_name:
                # Extrahiere was berechnet werden soll: alter, jahr, monat, tag
                parts = col_name.split("_")
                calc_type = parts[-2]  # z.B. "alter", "jahr", "monat", "tag"
                is_show = parts[-1] == "show"
                
                original_col = f"{original_field}_original"
                original_wert = record.get(original_col)
                
                if isinstance(original_wert, (int, float)) and original_wert > 0:
                    dt_formatter.PdvmDateTime = original_wert
                    
                    if calc_type == "alter":
                        # Alter zum Stichtag berechnen
                        dt_stichtag = Pdvm_DateTime("DEU")
                        dt_stichtag.PdvmDateTime = stichtag
                        # Differenz in Jahren berechnen
                        diff_days = int(stichtag) - int(original_wert)
                        alter_jahre = diff_days // 365  # Vereinfachte Berechnung
                        record[col_name] = alter_jahre if not is_show else str(alter_jahre)
                        
                    elif calc_type == "jahr":
                        record[col_name] = dt_formatter.Year if not is_show else str(dt_formatter.Year)
                        
                    elif calc_type == "monat":
                        if is_show:
                            # Deutscher Monatsname für Show
                            monate = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
                                     "Juli", "August", "September", "Oktober", "November", "Dezember"]
                            record[col_name] = monate[dt_formatter.Month] if dt_formatter.Month <= 12 else ""
                        else:
                            record[col_name] = dt_formatter.Month
                            
                    elif calc_type == "tag":
                        record[col_name] = dt_formatter.Day if not is_show else str(dt_formatter.Day)
                else:
                    record[col_name] = "" if is_show else 0
    
    return record

def _translate_dropdown_cached(self, wert: Any, field_config: dict, 
                             dropdown_cache: dict, guid: str) -> str:
    """
    Übersetzt Dropdown-Werte mit Cache (nur einmal pro GUID laden).
    """
    if not wert:
        return ""
    
    dropdown_config = field_config.get("dropdown_config", {})
    if not dropdown_config:
        return str(wert)
    
    # Cache-Key erstellen
    cache_key = f"{guid}_{dropdown_config.get('table', '')}_{dropdown_config.get('gruppe', '')}"
    
    if cache_key not in dropdown_cache:
        # Dropdown-Daten laden und cachen
        dropdown_cache[cache_key] = self._load_dropdown_data(dropdown_config, guid)
    
    # Übersetzen
    dropdown_data = dropdown_cache[cache_key]
    return dropdown_data.get(str(wert), str(wert))

def _load_dropdown_data(self, dropdown_config: dict, guid: str) -> dict:
    """
    Lädt Dropdown-Daten für Übersetzungen.
    """
    try:
        # Hier würde die echte Dropdown-Daten-Logik stehen
        # Für jetzt Return ein leeres Dict
        return {}
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Dropdown-Daten: {e}")
        return {}
