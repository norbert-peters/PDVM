#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 GLOBAL GCS - VEREINFACHTER ZUGRIFF AUF SYSTEMSTEUERUNG
========================================================

Kompatibilitätsmodul für bestehenden Code der global_gcs importiert.
Leitet alle Aufrufe an pdvm_central_systemsteuerung weiter.
"""

import logging
from pdvm_central_systemsteuerung import get_gcs, is_gcs_initialized, initialize_gcs

logger = logging.getLogger(__name__)

# Globale Variable für direkten Zugriff
gcs = None

def _update_gcs():
    """Aktualisiere globale gcs Variable"""
    global gcs
    try:
        if is_gcs_initialized():
            gcs = get_gcs()
            logger.debug("🔧 global_gcs.gcs aktualisiert")
        else:
            gcs = None
            logger.debug("🔧 global_gcs.gcs auf None gesetzt (nicht initialisiert)")
    except Exception as e:
        logger.warning(f"⚠️ Konnte gcs nicht aktualisieren: {e}")
        gcs = None

def get_global_gcs():
    """Hole globale Systemsteuerung (mit Auto-Update)"""
    _update_gcs()
    return gcs

# Auto-Update bei Import
_update_gcs()

# Exports für Kompatibilität
__all__ = ['gcs', 'get_global_gcs', 'get_gcs', 'is_gcs_initialized', 'initialize_gcs']