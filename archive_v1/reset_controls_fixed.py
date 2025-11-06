    def reset_controls_to_default(self):
        """
        Controls auf Standard zurücksetzen
        
        WORKFLOW:
        1. Reset-Flag temporär setzen
        2. Controls NEU generieren (OHNE Abgleich)
        3. Projektions-Tabellen NEU berechnen
        4. Kompletter View-Reload
        """
        logger.info("=== CONTROLS RESET TO DEFAULT ===")
        
        try:
            # SCHRITT 1: Reset-Flag temporär setzen
            logger.info("  Setze Reset-Flag temporär...")
            old_reset = self.reset
            self.reset = True
            
            # SCHRITT 2: Controls NEU generieren (OHNE Abgleich)
            logger.info("  Generiere Controls NEU (OHNE Abgleich)...")
            self._generate_and_save_controls()
            
            # Reset-Flag zurücksetzen
            self.reset = old_reset
            logger.info("  Controls neu generiert und persistent gemacht")
            
            # SCHRITT 3: Projektions-Tabellen NEU berechnen (KEY!)
            logger.info("  Berechne Projektions-Tabellen NEU...")
            self._build_projection_tables()
            logger.info("  Projektions-Tabellen neu berechnet")
            
            # SCHRITT 4: Kompletter Reload (BasisMatrix -> Pipeline -> UI)
            logger.info("  Kompletter View-Reload...")
            
            # BasisMatrix neu (da Controls möglicherweise neue Felder haben)
            self._build_basis_matrix()
            
            # Pipeline durchlaufen
            self._run_matrix_pipeline()
            
            # UI aktualisieren
            self.refresh_ui_from_matrix()
            
            logger.info("Controls erfolgreich auf Standard zurückgesetzt")
            
        except Exception as e:
            logger.error(f"Controls-Reset fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # Exception weiterreichen für UI-Fehlerbehandlung
