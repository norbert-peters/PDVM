"""
Wrapper module for backward compatibility.

This file used to contain the "simple" editor implementation. To avoid
multiple different modules providing different editor classes (and to make
the editor used everywhere consistent), this module now delegates to the
optimized implementation in `pdvm_menu_editor_optimized.py`.

The original implementation has been backed up under
`pdvm_menu_editor_backup_20251112_120000/__pdvm_menu_editor_simple.py.bak`.
"""

import logging

from pdvm_menu_editor_optimized import (
    PdvmMenuEditorOptimized,
    create_menu_editor_widget as create_optimized_widget,
    create_menu_editor_dialog as create_optimized_dialog,
)

logger = logging.getLogger(__name__)


class PdvmMenuEditorSimple(PdvmMenuEditorOptimized):
    """Compatibility wrapper exposing the old class name."""
    pass


def create_menu_editor_widget(menu_guid: str, parent=None):
    logger.info(f"Delegating create_menu_editor_widget to optimized for {menu_guid}")
    return create_optimized_widget(menu_guid, parent)


def create_menu_editor_dialog(menu_guid: str, parent=None):
    return create_optimized_dialog(menu_guid, parent)
    
