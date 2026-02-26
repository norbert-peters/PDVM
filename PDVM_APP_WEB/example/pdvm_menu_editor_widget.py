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

# Neuer Wrapper: Leitet Aufrufe an die optimierte Implementierung weiter
from pdvm_menu_editor_optimized import (
    PdvmMenuEditorOptimized,
    create_menu_editor_widget as create_optimized_widget,
    create_menu_editor_dialog as create_optimized_dialog,
)

logger = logging.getLogger(__name__)


# Backward-compatible wrapper class
class PdvmMenuEditorWidget(PdvmMenuEditorOptimized):
    """Kompatibler Wrapper: Erweitert die optimierte Implementierung."""
    pass


def create_menu_editor_widget(menu_guid: str, parent=None):
    """Factory-Funktion (kompatibel mit altem Code)

    Leitet zur optimierten Implementierung weiter.
    """
    logger.info(f"🎯 Menü-Editor (wrapper) erstellt für: {menu_guid}")
    return PdvmMenuEditorWidget(menu_guid, parent)


def create_menu_editor_dialog(menu_guid: str, parent=None):
    """Kompatibler Dialog Factory (optional)"""
    return create_optimized_dialog(menu_guid, parent)
