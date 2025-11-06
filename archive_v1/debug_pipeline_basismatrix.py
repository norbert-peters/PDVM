#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Script: Pipeline BasisMatrix Analyse
===========================================

Testet die neue Pipeline-Integration und analysiert die BasisMatrix 
auf verfügbare Spalten, insbesondere _original Spalten.
"""

import sys
import os
import logging

# Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline_basismatrix():
    """Testet die BasisMatrix der Pipeline in einem echten ViewDialog"""
    
    try:
        # Simuliere minimale GCS-Umgebung
        from pdvm_central_systemsteuerung import initialize_gcs, get_gcs
        
        # Test-User für GCS
        test_user_guid = "test-pipeline-user"
        test_user_json = """{
            "country": "DE",
            "mode": "ExpertMode",
            "timestamp": "2024-01-01"
        }"""
        
        # GCS initialisieren
        gcs = initialize_gcs(test_user_guid, test_user_json)
        logger.info(f"✅ GCS initialisiert: {gcs.user_guid}")
        
        # ViewDialog erstellen (minimal)
        from pdvm_view_dialog import PdvmViewDialog
        
        # Test Controls Config mit sortByOriginal
        test_controls_config = {
            'geburtsdatum_show': {
                'name': 'Geburtsdatum',
                'sortByOriginal': True,
                'sequence': 1,
                'visible': True
            },
            'familienname_show': {
                'name': 'Familienname', 
                'sortByOriginal': True,
                'sequence': 2,
                'visible': True
            }
        }
        
        # Test-Matrix mit _original Spalten
        test_display_matrix = [
            ['uid_original', 'geburtsdatum_original', 'familienname_original', 'geburtsdatum_show', 'familienname_show'],
            ['1', '1990-01-15', 'Mustermann_ORIG', '15.01.1990', 'Mustermann'],
            ['2', '1985-12-03', 'Schmidt_ORIG', '03.12.1985', 'Schmidt'],
            ['3', '1992-06-21', 'Weber_ORIG', '21.06.1992', 'Weber']
        ]
        
        # Test call_daten für ViewDialog
        test_call_daten = {
            'view_guid': 'test-pipeline-view',
            'title': 'Pipeline BasisMatrix Test',
            'first_call': True,
            'reset': False
        }
        
        # ViewDialog mit Test-Daten erstellen
        dialog = PdvmViewDialog(call_daten=test_call_daten)
        
        logger.info("✅ ViewDialog mit Test-Daten erstellt")
        
        # 🎯 KERNTEST: Prüfe Pipeline Integration
        logger.info("🔧 Analysiere Pipeline-Integration...")
        
        # Prüfe Pipeline Manager
        if hasattr(dialog.view_display, 'pipeline_manager'):
            pipeline_manager = dialog.view_display.pipeline_manager
            logger.info(f"✅ Pipeline Manager vorhanden: {type(pipeline_manager)}")
            
            # Prüfe Pipeline
            if hasattr(pipeline_manager, 'pipeline'):
                pipeline = pipeline_manager.pipeline
                logger.info(f"✅ Pipeline vorhanden: {type(pipeline)}")
                
                # Prüfe BasisMatrix
                if hasattr(pipeline, 'basis_matrix'):
                    basis_matrix = pipeline.basis_matrix
                    if basis_matrix:
                        logger.info(f"✅ BasisMatrix geladen: {len(basis_matrix)} Zeilen")
                        
                        # Header analysieren
                        header = basis_matrix[0] if basis_matrix else []
                        logger.info(f"🔍 BasisMatrix Header: {header}")
                        
                        # Prüfe auf _original Spalten
                        original_columns = [col for col in header if col.endswith('_original')]
                        logger.info(f"🎯 _original Spalten gefunden: {original_columns}")
                        
                        # Test sortByOriginal Detection
                        from pdvm_data_processing_pipeline import ProcessingOptions
                        
                        # Test-Optionen mit sortByOriginal
                        options = ProcessingOptions(
                            sort_column='geburtsdatum_show',
                            sort_direction='asc',
                            sort_by_original=True
                        )
                        
                        # Pipeline-Verarbeitung testen
                        logger.info("🧪 Teste Pipeline-Verarbeitung mit sortByOriginal...")
                        processed_data = pipeline.apply_processing(options)
                        
                        if processed_data:
                            logger.info(f"✅ Pipeline-Verarbeitung erfolgreich: {len(processed_data)} Zeilen")
                            logger.info(f"📊 Verarbeitete Header: {processed_data[0] if processed_data else 'Keine'}")
                        else:
                            logger.error("❌ Pipeline-Verarbeitung fehlgeschlagen")
                        
                        # Test _get_actual_sort_column
                        actual_sort_col = pipeline._get_actual_sort_column('geburtsdatum_show', options)
                        logger.info(f"🎯 Tatsächliche Sortier-Spalte: '{actual_sort_col}'")
                        
                        if actual_sort_col == 'geburtsdatum_original':
                            logger.info("🎉 sortByOriginal Detection funktioniert korrekt!")
                        else:
                            logger.error(f"❌ sortByOriginal Problem: Erwartet 'geburtsdatum_original', erhalten '{actual_sort_col}'")
                    
                    else:
                        logger.error("❌ BasisMatrix ist leer")
                else:
                    logger.error("❌ Keine BasisMatrix in Pipeline")
            else:
                logger.error("❌ Keine Pipeline im Manager")
        else:
            logger.error("❌ Kein Pipeline Manager im ViewDialog")
        
        logger.info("🏁 BasisMatrix-Analyse abgeschlossen")
        
    except Exception as e:
        logger.error(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔧 Pipeline BasisMatrix Debug-Analyse")
    test_pipeline_basismatrix()