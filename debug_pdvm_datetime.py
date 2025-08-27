#!/usr/bin/env python3
"""
DEBUG: PdvmDateTime Interpretation
"""

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from pd_datetime import Pdvm_DateTime
    
    # Test PdvmDateTime Format
    test_wert = 950803.0  # sollte 05.08.1972 sein
    
    dt = Pdvm_DateTime("DEU")
    dt.PdvmDateTime = test_wert
    
    logger.info(f"🔍 PdvmDateTime Test: {test_wert}")
    logger.info(f"   Date: {dt.Date}")
    logger.info(f"   Year: {dt.Year}")
    logger.info(f"   Month: {dt.Month}")
    logger.info(f"   Day: {dt.Day}")
    
    # Test mit bekanntem Datum
    dt2 = Pdvm_DateTime("DEU")
    dt2.Date = "05.08.1972"
    logger.info(f"🔍 Rückkonvertierung von '05.08.1972':")
    logger.info(f"   PdvmDateTime: {dt2.PdvmDateTime}")
    logger.info(f"   Year: {dt2.Year}")
    logger.info(f"   Month: {dt2.Month}")
    logger.info(f"   Day: {dt2.Day}")
    
except Exception as e:
    logger.error(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
