"""
Neue _create_controls_from_view_config Methode für einheitliche Struktur
"""

def _create_controls_from_view_config(self):
    """
    FIRST_CALL: Erstelle Controls basierend auf view_config
    NEUE STRUKTUR: Einheitliche Schlüssel-Logik
    """
    try:
        if not hasattr(self, 'view_config') or not self.view_config:
            logger.warning("⚠️ Keine view_config verfügbar für Control-Erstellung")
            return
            
        # NEUE STRUKTUR: Direkte Schlüssel statt Array
        # Filtere System-Felder heraus, suche nach Spalten-Schlüsseln
        system_keys = {'tabelle', 'expertenmodus', 'last_modified', 'spalten', 'ROOT'}
        column_keys = [k for k in self.view_config.keys() if k not in system_keys]
        
        # FALLBACK: Alte Array-Struktur unterstützen
        if not column_keys and 'spalten' in self.view_config:
            columns = self.view_config.get('spalten', [])
            logger.info(f"🔄 Fallback: Konvertiere alte Array-Struktur ({len(columns)} Spalten)")
            
            for column in columns:
                # Alte Struktur: {feld, name, type, ui: {width}}
                field_name = column.get('feld') or column.get('name')
                if not field_name:
                    continue
                    
                title = column.get('name') or column.get('title', field_name)
                width = 100
                if 'ui' in column and isinstance(column['ui'], dict):
                    ui_width = column['ui'].get('width', '100')
                    if isinstance(ui_width, str) and ui_width.endswith('%'):
                        percent = float(ui_width.rstrip('%'))
                        width = int(percent * 8)
                    else:
                        width = int(ui_width) if str(ui_width).isdigit() else 100
                
                control_state = {
                    'field_name': field_name,
                    'spaltenueberschrift': title,
                    'datentyp': column.get('type', 'string'),
                    'spaltenbreite': width,
                    'sichtbar': True
                }
                
                self.controls_data[field_name] = control_state
                logger.debug(f"   📋 Control erstellt (Fallback): {field_name} → {title}")
        
        # NEUE STRUKTUR: Direkte Schlüssel
        elif column_keys:
            logger.info(f"🔨 Erstelle Controls für {len(column_keys)} Spalten (neue Struktur)")
            
            for field_name in column_keys:
                column = self.view_config[field_name]
                if not isinstance(column, dict):
                    continue
                
                control_state = {
                    'field_name': field_name,
                    'spaltenueberschrift': column.get('name', field_name),
                    'datentyp': column.get('typ', 'string'),
                    'spaltenbreite': column.get('breite', 100),
                    'sichtbar': column.get('sichtbar', True)
                }
                
                self.controls_data[field_name] = control_state
                logger.debug(f"   📋 Control erstellt: {field_name} → {control_state['spaltenueberschrift']}")
        else:
            logger.warning("⚠️ Keine Spalten in view_config gefunden")
            return
            
        self._convert_controls_to_columns_data()
        logger.info(f"✅ {len(self.controls_data)} Controls aus view_config erstellt")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Controls: {e}")
