"""
V2 Dependencies Checker
=======================
Analysiert welche Module von V2 benötigt werden und holt sie aus dem Archiv zurück

Autor: PDVM V2.0
Datum: 06.11.2025
"""

import subprocess
import re
from pathlib import Path
import shutil

ROOT_DIR = Path(__file__).parent
ARCHIVE_DIR = ROOT_DIR / "archive_v1"

# Liste der bekannten fehlenden Module
REQUIRED_MODULES = [
    "pdvm_datetime.py",
    "pdvm_date_time_picker.py",
    "pdvm_search_string_parser.py",
    "pdvm_dropdown_value.py",
    "pdvm_benutzer.py",
    "pdvm_dropdown_picker.py",
    "pdvm_dropdown.py",
    "pdvm_user_db.py",
    "allgemeines.py",
]

def restore_module(module_name):
    """Holt Modul aus Archiv zurück"""
    source = ARCHIVE_DIR / module_name
    target = ROOT_DIR / module_name
    
    if source.exists() and not target.exists():
        shutil.copy(str(source), str(target))
        print(f"   ✅ {module_name} wiederhergestellt")
        return True
    elif target.exists():
        print(f"   ℹ️  {module_name} bereits vorhanden")
        return False
    else:
        print(f"   ❌ {module_name} nicht im Archiv gefunden")
        return False

def find_missing_modules():
    """Führt v2_main.py aus und findet fehlende Module"""
    print("🔍 Suche fehlende Module...\n")
    
    try:
        result = subprocess.run(
            ["python", "v2_main.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse ModuleNotFoundError
        errors = re.findall(r"ModuleNotFoundError: No module named '([^']+)'", result.stderr)
        return list(set(errors))  # Unique
        
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        print(f"❌ Fehler beim Ausführen: {e}")
        return []

def main():
    print("🔧 V2 DEPENDENCIES CHECKER")
    print("=" * 70)
    
    # Finde fehlende Module
    missing = find_missing_modules()
    
    if missing:
        print(f"\n📋 Gefundene fehlende Module: {len(missing)}\n")
        for module in missing:
            print(f"   - {module}")
    
    # Erweitere Liste mit bekannten Modulen
    all_required = set(REQUIRED_MODULES)
    for module in missing:
        all_required.add(f"{module}.py")
    
    print(f"\n🔄 Stelle {len(all_required)} Module wieder her...\n")
    
    restored = 0
    for module in sorted(all_required):
        if restore_module(module):
            restored += 1
    
    print(f"\n" + "=" * 70)
    print(f"✅ {restored} Module wiederhergestellt")
    print("=" * 70)
    
    # Teste erneut
    print("\n🧪 Teste V2-Start...\n")
    missing_after = find_missing_modules()
    
    if missing_after:
        print(f"⚠️ Noch {len(missing_after)} Module fehlen:\n")
        for module in missing_after:
            print(f"   - {module}")
    else:
        print("✅ Alle Module gefunden!")

if __name__ == "__main__":
    main()
