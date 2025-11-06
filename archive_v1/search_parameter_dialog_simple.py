# search_parameter_dialog_simple.py
# VEREINFACHTE accept_changes Methode - ersetzt die komplexe Version

def accept_changes_simple(self):
    """
    EINFACHER 3-SCHRITT ABLAUF wie vom Benutzer gewünscht:
    1. Alle Filterparameter werden geladen (persistent aus APP-DB) 
    2. Dialog wird angezeigt mit den geladenen Daten (oder leer wenn keine vorhanden)
    3. Bei OK: Alle Parameter werden persistent gespeichert UND ein fertiger Filterstring wird zurückgegeben
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🎯 === VEREINFACHTER 3-SCHRITT ABLAUF ===")
        
        # SCHRITT 1: Sammle alle aktuellen Filter-Werte aus UI
        collected_filters = {}
        
        for field_key, widget_dict in self.filter_widgets.items():
            # Einfacher Wert aus Widget
            simple_value = self._get_widget_value(widget_dict).strip() if self._get_widget_value(widget_dict) else ""
            
            # Extended Conditions (falls vorhanden)
            extended_conditions = self.extended_filter_conditions.get(field_key, [])
            
            if extended_conditions:
                # Komplexer Filter
                collected_filters[field_key] = {
                    'type': 'complex',
                    'conditions': [c.to_dict() if hasattr(c, 'to_dict') else c for c in extended_conditions],
                    'simple_value': simple_value
                }
                logger.info(f"🔧 Komplexer Filter: {field_key} = {len(extended_conditions)} Bedingungen")
                
            elif simple_value:
                # Einfacher Filter
                collected_filters[field_key] = {
                    'type': 'simple', 
                    'value': simple_value
                }
                logger.info(f"🔧 Einfacher Filter: {field_key} = '{simple_value}'")
        
        logger.info(f"📊 Gesammelt: {len(collected_filters)} Filter")
        
        # SCHRITT 2: Persistent speichern (ALLE auf einmal)
        self._save_filters_persistent(collected_filters)
        
        # SCHRITT 3: Filterstring generieren und an Hauptfilter weiterleiten
        filter_success = self._execute_collected_filters(collected_filters)
        
        if filter_success:
            logger.info("✅ Filter erfolgreich angewendet")
            self.accept()  # Dialog schließen
        else:
            logger.warning("⚠️ Filter-Anwendung fehlgeschlagen")
            
    except Exception as e:
        logger.error(f"❌ Fehler im vereinfachten accept_changes: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def _save_filters_persistent(self, collected_filters):
    """Speichere alle Filter persistent - EINHEITLICH"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs or not hasattr(gcs, '_app_db'):
            logger.warning("⚠️ GCS._app_db nicht verfügbar")
            return False
            
        for field_key, filter_data in collected_filters.items():
            try:
                # Einheitliches Datenformat
                persist_data = {
                    'field_key': field_key,
                    'created_at': '2025-10-05'
                }
                
                if filter_data['type'] == 'complex':
                    persist_data['conditions'] = filter_data['conditions']
                    if 'simple_value' in filter_data and filter_data['simple_value']:
                        persist_data['simple_search'] = filter_data['simple_value']
                else:
                    persist_data['simple_search'] = filter_data['value']
                
                success = gcs._app_db.set_value(self.view_guid, field_key, persist_data)
                if success:
                    logger.info(f"💾 {field_key}: gespeichert")
                else:
                    logger.warning(f"⚠️ {field_key}: Speichern fehlgeschlagen")
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Speichern von {field_key}: {e}")
                
        logger.info("✅ Persistente Speicherung abgeschlossen")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim persistenten Speichern: {e}")
        return False

def _execute_collected_filters(self, collected_filters):
    """Führe gesammelte Filter über LinearFilterExecutionManager aus"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not self.linear_filter_manager:
            logger.warning("⚠️ LinearFilterExecutionManager nicht verfügbar")
            return False
            
        if not collected_filters:
            # Leere Filter = Reset auf Basis-Matrix
            success = self.linear_filter_manager.execute_filter_linear('einfach', {})
            logger.info("🔵 Leerer Filter - Reset auf Basis-Matrix")
            return success
            
        # Bestimme Filter-Typ automatisch
        has_complex = any(f.get('type') == 'complex' for f in collected_filters.values())
        filter_type = 'komplex' if has_complex else 'einfach'
        
        # Führe Filter aus
        success = self.linear_filter_manager.execute_filter_linear(filter_type, {
            'collected_filters': collected_filters,
            'filter_type': f'parameter_{filter_type}'
        })
        
        if success:
            logger.info(f"✅ {filter_type.title()} Filter erfolgreich ausgeführt")
        else:
            logger.warning(f"⚠️ {filter_type.title()} Filter-Ausführung fehlgeschlagen")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Filter-Ausführung: {e}")
        return False


# Diese Methoden können direkt in SearchParameterDialog integriert werden
# durch monkey-patching oder direktes Ersetzen der accept_changes Methode