"""
V2 → PDVM Umbenennung
=====================
Benennt alle v2_* Dateien in pdvm_* um und aktualisiert alle Imports

Autor: PDVM V2.0
Datum: 06.11.2025
"""

import os
import re
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent

# Mapping: v2_name → pdvm_name
RENAME_MAPPING = {
    # Haupt-Dateien
    "v2_main.py": "pdvm_main.py",
    "v2_systemstart.py": "pdvm_systemstart.py",
    "v2_login_dialog.py": "pdvm_login_dialog.py",
    "v2_mandanten_dialog.py": "pdvm_mandanten_dialog.py",
    
    # GCS & Systemsteuerung
    "v2_gcs.py": "pdvm_gcs.py",
    "v2_central_systemsteuerung.py": "pdvm_central_systemsteuerung.py",
    
    # Datenbank
    "v2_pdvm_datenbank.py": "pdvm_datenbank.py",
    "v2_pdvm_central_datenbank.py": "pdvm_central_datenbank.py",
    
    # Menü-System
    "v2_menu_handler.py": "pdvm_menu_handler.py",
    "v2_menu_builder.py": "pdvm_menu_builder.py",
    "v2_menu_storage.py": "pdvm_menu_storage.py",
    "v2_menu_schema.py": "pdvm_menu_schema.py",
    "v2_command_handler.py": "pdvm_command_handler.py",
    
    # View-System
    "v2_pdvm_view_controller.py": "pdvm_view_controller.py",
    "v2_pdvm_view_dialog.py": "pdvm_view_dialog.py",
    "v2_pdvm_view_ui.py": "pdvm_view_ui.py",
    "v2_pdvm_view_matrix_manager.py": "pdvm_view_matrix_manager.py",
    
    # Pipeline
    "v2_pdvm_pipeline.py": "pdvm_pipeline.py",
    "v2_pdvm_matrix_constants.py": "pdvm_matrix_constants.py",
    
    # Filter & Suche
    "v2_pdvm_einfach_filter_dialog.py": "pdvm_einfach_filter_dialog.py",
    "v2_pdvm_einfach_filter_manager.py": "pdvm_einfach_filter_manager.py",
    "v2_pdvm_komplex_filter_dialog.py": "pdvm_komplex_filter_dialog.py",
    "v2_pdvm_komplex_filter_manager.py": "pdvm_komplex_filter_manager.py",
    "v2_pdvm_filter_reset_manager.py": "pdvm_filter_reset_manager.py",
    "v2_pdvm_schnellsuche_manager.py": "pdvm_schnellsuche_manager.py",
    
    # Dialoge
    "v2_pdvm_dialog_widget.py": "pdvm_dialog_widget.py",
    "v2_pdvm_genereller_dialog.py": "pdvm_genereller_dialog.py",
    "v2_pdvm_sort_summen_dialog.py": "pdvm_sort_summen_dialog.py",
    "v2_column_management_dialog.py": "pdvm_column_management_dialog.py",
    
    # Input Controls
    "v2_pdvm_input_control.py": "pdvm_input_control.py",
    "v2_pdvm_input_controls_manager.py": "pdvm_input_controls_manager.py",
    "v2_pdvm_input_type_base.py": "pdvm_input_type_base.py",
    "v2_pdvm_input_type_text.py": "pdvm_input_type_text.py",
    "v2_pdvm_input_type_datetime.py": "pdvm_input_type_datetime.py",
    "v2_pdvm_input_type_dropdown.py": "pdvm_input_type_dropdown.py",
    "v2_pdvm_input_type_viewtable.py": "pdvm_input_type_viewtable.py",
    
    # Utilities
    "v2_pdvm_search_string_parser.py": "pdvm_search_string_parser_v2.py",  # Konflikt vermeiden
    
    # Init & Verify
    "v2_init_auth_database.py": "pdvm_init_auth_database.py",
    "v2_init_mandanten_databases.py": "pdvm_init_mandanten_databases.py",
    "v2_verify_auth_database.py": "pdvm_verify_auth_database.py",
    "v2_migrate_pdvm_data.py": "pdvm_migrate_data.py",
    
    # Test
    "v2_test_with_menu.py": "pdvm_test_with_menu.py",
}


def create_import_mapping():
    """Erstellt Mapping für Import-Replacements"""
    import_mapping = {}
    
    for old_name, new_name in RENAME_MAPPING.items():
        # Module-Namen (ohne .py)
        old_module = old_name.replace(".py", "")
        new_module = new_name.replace(".py", "")
        
        import_mapping[old_module] = new_module
    
    return import_mapping


def update_imports_in_file(file_path, import_mapping):
    """Aktualisiert Imports in einer Datei"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Pattern für Imports
        for old_module, new_module in import_mapping.items():
            # import v2_xxx
            pattern1 = rf'\bimport\s+{re.escape(old_module)}\b'
            if re.search(pattern1, content):
                content = re.sub(pattern1, f'import {new_module}', content)
                changes.append(f"import {old_module} → import {new_module}")
            
            # from v2_xxx import
            pattern2 = rf'\bfrom\s+{re.escape(old_module)}\s+import\b'
            if re.search(pattern2, content):
                content = re.sub(pattern2, f'from {new_module} import', content)
                changes.append(f"from {old_module} → from {new_module}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes
        
        return []
        
    except Exception as e:
        print(f"   ❌ Fehler bei {file_path.name}: {e}")
        return []


def rename_files():
    """Benennt v2_* Dateien in pdvm_* um"""
    print("🔄 V2 → PDVM UMBENENNUNG")
    print("=" * 70)
    
    print(f"\n📋 {len(RENAME_MAPPING)} Dateien werden umbenannt:\n")
    
    # Zeige Mapping
    for i, (old_name, new_name) in enumerate(sorted(RENAME_MAPPING.items()), 1):
        print(f"   {i:2d}. {old_name:45s} → {new_name}")
    
    # Bestätigung
    print(f"\n⚠️ Dateien werden umbenannt!")
    response = input("   Fortfahren? (ja/nein): ").strip().lower()
    
    if response not in ["ja", "j", "yes", "y"]:
        print("\n❌ Abgebrochen!")
        return
    
    # Erstelle Import-Mapping
    import_mapping = create_import_mapping()
    
    # Phase 1: Dateien umbenennen
    print("\n🚀 PHASE 1: Dateien umbenennen...\n")
    renamed_count = 0
    
    for old_name, new_name in RENAME_MAPPING.items():
        old_path = ROOT_DIR / old_name
        new_path = ROOT_DIR / new_name
        
        if old_path.exists():
            try:
                shutil.move(str(old_path), str(new_path))
                print(f"   ✅ {old_name} → {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"   ❌ Fehler bei {old_name}: {e}")
        else:
            print(f"   ⚠️ {old_name} nicht gefunden")
    
    print(f"\n✅ {renamed_count}/{len(RENAME_MAPPING)} Dateien umbenannt")
    
    # Phase 2: Imports aktualisieren
    print("\n🔄 PHASE 2: Imports aktualisieren...\n")
    
    all_py_files = list(ROOT_DIR.glob("*.py"))
    all_py_files.extend(ROOT_DIR.glob("handlers/*.py"))
    
    total_changes = 0
    files_changed = 0
    
    for file_path in all_py_files:
        changes = update_imports_in_file(file_path, import_mapping)
        if changes:
            print(f"   📝 {file_path.name}:")
            for change in changes:
                print(f"      → {change}")
            total_changes += len(changes)
            files_changed += 1
    
    print(f"\n✅ {total_changes} Imports aktualisiert in {files_changed} Dateien")
    
    print("\n" + "=" * 70)
    print("✅ UMBENENNUNG ABGESCHLOSSEN!")
    print("=" * 70)
    
    # Zeige verbleibende v2_* Dateien
    remaining_v2 = list(ROOT_DIR.glob("v2_*.py"))
    if remaining_v2:
        print(f"\n⚠️ {len(remaining_v2)} v2_* Dateien verbleiben:\n")
        for file_path in sorted(remaining_v2):
            print(f"   - {file_path.name}")
    else:
        print("\n✅ Alle v2_* Dateien umbenannt!")


if __name__ == "__main__":
    rename_files()
