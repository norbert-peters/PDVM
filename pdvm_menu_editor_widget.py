"""
🎯 PDVM Menu-Editor Widget - WRAPPER für einfache Version
=========================================================

DIESER FILE IST NUR NOCH EIN WRAPPER!

Die echte Implementation ist in:
    pdvm_menu_editor_simple.py

Grund: Komplette Vereinfachung nach User-Feedback
    - EINE DB-Instanz statt 3
    - Matrix-Ansatz statt komplexe Tabs
    - Orange Rahmen für Änderungen
    - save_all_values() für alles
"""

import logging
from pdvm_menu_editor_simple import PdvmMenuEditorSimple

logger = logging.getLogger(__name__)


# ============================================================================
# WRAPPER-Klasse für Kompatibilität mit bestehendem Code
# ============================================================================

class PdvmMenuEditorWidget(PdvmMenuEditorSimple):
    """Wrapper für alte Aufrufe - leitet zu neuer einfacher Version weiter"""
    pass


def create_menu_editor_widget(menu_guid: str, parent=None):
    """Factory-Funktion (kompatibel mit altem Code)"""
    logger.info(f"🎯 Menu-Editor erstellt für: {menu_guid}")
    return PdvmMenuEditorWidget(menu_guid, parent)
