# filter_helper_methods.py
# Hilfsmethoden für vereinfachten Filter-Dialog

import logging

logger = logging.getLogger(__name__)

def save_persistent_filters_unified(view_guid, collected_filters):
    """Speichere alle Filter einheitlich in APP-DB"""
    logger.info(f"💾 Speichere {len(collected_filters)} Filter persistent...")
    
    try:
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs or not hasattr(gcs, '_app_db'):
            logger.warning("⚠️ GCS._app_db nicht verfügbar")
            return False
            
        success_count = 0
        for field_key, filter_data in collected_filters.items():
            try:
                if filter_data['type'] == 'complex':
                    # Komplexer Filter
                    persist_data = {
                        'field_key': field_key,
                        'conditions': filter_data['conditions'],
                        'created_at': '2025-10-05'
                    }
                else:
                    # Einfacher Filter
                    persist_data = {
                        'field_key': field_key,
                        'simple_search': filter_data['simple_value'],
                        'created_at': '2025-10-05'
                    }
                
                success = gcs._app_db.set_value(view_guid, field_key, persist_data)
                if success:
                    success_count += 1
                    logger.info(f"💾 {field_key}: gespeichert")
                else:
                    logger.warning(f"⚠️ {field_key}: Speichern fehlgeschlagen")
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Speichern von {field_key}: {e}")
                
        logger.info(f"✅ {success_count}/{len(collected_filters)} Filter erfolgreich gespeichert")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Fehler beim persistenten Speichern: {e}")
        return False

def generate_filter_string(collected_filters):
    """Generiere Filterstring aus gesammelten Filtern"""
    logger.info(f"🎯 Generiere Filterstring aus {len(collected_filters)} Filtern...")
    
    try:
        if not collected_filters:
            return ""
            
        filter_parts = []
        
        for field_key, filter_data in collected_filters.items():
            if filter_data['type'] == 'complex':
                # Komplexer Filter: Bedingungen verarbeiten
                conditions = filter_data['conditions']
                for condition in conditions:
                    value = condition.get('value', '')
                    operator = condition.get('operator_type', 'enthält')
                    negation = condition.get('negation', 'IS')
                    
                    if value:
                        # Konvertiere zu SQL-ähnlichem Format
                        if operator == 'beginnt mit':
                            filter_part = f"{field_key} LIKE '{value}%'"
                        elif operator == 'endet mit':
                            filter_part = f"{field_key} LIKE '%{value}'"
                        elif operator == 'enthält':
                            filter_part = f"{field_key} LIKE '%{value}%'"
                        elif operator == 'ist gleich':
                            filter_part = f"{field_key} = '{value}'"
                        else:
                            filter_part = f"{field_key} LIKE '%{value}%'"  # Fallback
                            
                        if negation == 'NOT':
                            filter_part = f"NOT ({filter_part})"
                            
                        filter_parts.append(filter_part)
                        
            else:
                # Einfacher Filter
                value = filter_data['simple_value']
                if value:
                    filter_parts.append(f"{field_key} LIKE '%{value}%'")
        
        filter_string = " AND ".join(filter_parts)
        logger.info(f"🎯 Filterstring: {filter_string}")
        return filter_string
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Generieren des Filterstrings: {e}")
        return ""

def apply_filter_to_matrix_manager(view_guid, filter_string, collected_filters):
    """Wende Filter auf MatrixManager an"""
    logger.info(f"🎯 Wende Filter auf MatrixManager an...")
    
    try:
        from pdvm_matrix_manager import get_matrix_manager
        matrix_manager = get_matrix_manager(view_guid)
        
        if not matrix_manager:
            logger.error("❌ MatrixManager nicht verfügbar")
            return False
            
        if not filter_string:
            # Leerer Filter = alle Daten anzeigen
            success = matrix_manager.apply_filter(None, None)
            logger.info("🔵 Leerer Filter - alle Daten angezeigt")
        else:
            # Filter anwenden
            has_complex = any(f.get('type') == 'complex' for f in collected_filters.values())
            filter_type = 'komplex' if has_complex else 'einfach'
            
            success = matrix_manager.apply_filter(filter_type, {
                'filter_string': filter_string,
                'collected_filters': collected_filters
            })
            
            if success:
                logger.info(f"✅ {filter_type.title()} Filter erfolgreich angewendet")
            else:
                logger.warning(f"⚠️ {filter_type.title()} Filter-Anwendung fehlgeschlagen")
                
        return success
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Anwenden des Filters: {e}")
        return False