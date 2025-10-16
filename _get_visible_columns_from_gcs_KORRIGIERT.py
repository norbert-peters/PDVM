    def _get_visible_columns_from_gcs(self):
        """
        🎯 SPALTEN-PROJEKTION: Verwendet die vorberechneten Projektions-Tabellen aus GCS
        
        KORREKTE ARCHITEKTUR:
        - Verwendet get_projection_table() aus GCS
        - StandardMode: 'table_standard' Projektion (nur show=true)
        - ExpertMode: 'table_expert' Projektion (alle außer dummy)
        - Reihenfolge und Auswahl kommen aus den Projektions-Tabellen
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar für Spalten-Projektion")
                return []
            
            # KRITISCH: Verwende die vorberechneten Projektions-Tabellen!
            # Diese werden bei rebuild_projection_tables() aus den Controls erstellt
            if gcs.expert_mode:
                projection = gcs.get_projection_table(self.view_guid, 'table_expert')
                mode_info = "ExpertMode"
            else:
                projection = gcs.get_projection_table(self.view_guid, 'table_standard')
                mode_info = "StandardMode"
            
            if not projection:
                logger.warning(f"⚠️ Keine Projektion verfügbar für {mode_info}")
                # Fallback: Projektions-Tabellen neu aufbauen
                logger.info(f"🔄 Baue Projektions-Tabellen neu auf...")
                gcs.rebuild_projection_tables(self.view_guid)
                
                # Erneut versuchen
                if gcs.expert_mode:
                    projection = gcs.get_projection_table(self.view_guid, 'table_expert')
                else:
                    projection = gcs.get_projection_table(self.view_guid, 'table_standard')
                
                if not projection:
                    logger.error(f"❌ Auch nach rebuild keine Projektion verfügbar!")
                    return []
            
            logger.info(f"✅ {mode_info} Projektion: {len(projection)} Spalten in Reihenfolge")
            logger.debug(f"📋 Spalten: {projection[:5]}..." if len(projection) > 5 else f"📋 Spalten: {projection}")
            
            return projection
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Projektion: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
