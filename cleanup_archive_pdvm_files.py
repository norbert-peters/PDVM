"""
V1 pdvm_* Archivierungs-Script (Phase 2)
=========================================
Verschiebt alle alten pdvm_* Dateien (ohne v2_ Präfix) ins archive_v1 Verzeichnis

Autor: PDVM V2.0
Datum: 06.11.2025
"""

import os
import shutil
from pathlib import Path

# Aktuelles Verzeichnis
ROOT_DIR = Path(__file__).parent

# Archive-Verzeichnis
ARCHIVE_DIR = ROOT_DIR / "archive_v1"


def archive_old_pdvm_files():
    """Archiviert alle alten pdvm_* Dateien (ohne v2_ Präfix)"""
    print("🗂️ V1 PDVM-DATEIEN ARCHIVIERUNG (PHASE 2)")
    print("=" * 70)
    
    # Sammle alte pdvm_* Dateien
    files_to_archive = []
    
    for file_path in ROOT_DIR.glob("pdvm_*.py"):
        # Überspringe V2-Dateien
        if file_path.name.startswith("v2_pdvm_"):
            continue
        
        files_to_archive.append(file_path)
    
    # Sammle auch andere alte Dateien
    other_patterns = [
        "PDVMManager.py",
        "pdvmdropdown.py",
        "analyze_*.py",
        "check_*.py",
        "debug_*.py",
        "diagnose_*.py",
        "examine_*.py",
        "find_*.py",
        "list_*.py",
        "show_*.py",
        "verify_*.py",
        "validate_*.py",
        "compare_*.py",
        "fix_*.py",
        "repair_*.py",
        "correct_*.py",
        "restore_*.py",
        "update_*.py",
        "set_*.py",
        "remove_*.py",
        "reset_*.py",
        "add_*.py",
        "create_*.py",
        "convert_*.py",
        "simple_*.py",
        "quick_*.py",
        "flexible_*.py",
        "grouped_*.py",
        "improved_*.py",
        "optimized_*.py",
        "robuste_*.py",
        "systematisches_*.py",
        "universal_*.py",
        "vollständige_*.py",
        "design_*.py",
        "framedaten_*.py",
    ]
    
    for pattern in other_patterns:
        for file_path in ROOT_DIR.glob(pattern):
            if file_path not in files_to_archive and not file_path.name.startswith("v2_"):
                files_to_archive.append(file_path)
    
    print(f"\n📊 Gefundene Dateien: {len(files_to_archive)}")
    
    if not files_to_archive:
        print("\n✅ Keine Dateien zu archivieren!")
        return
    
    # Zeige Übersicht (erste 50)
    print("\n📋 Folgende Dateien werden archiviert (erste 50):\n")
    for i, file_path in enumerate(sorted(files_to_archive)[:50], 1):
        print(f"   {i:3d}. {file_path.name}")
    
    if len(files_to_archive) > 50:
        print(f"\n   ... und {len(files_to_archive) - 50} weitere Dateien")
    
    # Bestätigung
    print(f"\n⚠️ {len(files_to_archive)} Dateien werden nach {ARCHIVE_DIR} verschoben!")
    response = input("   Fortfahren? (ja/nein): ").strip().lower()
    
    if response not in ["ja", "j", "yes", "y"]:
        print("\n❌ Abgebrochen!")
        return
    
    # Archiviere Dateien
    print("\n🚀 Archiviere Dateien...\n")
    archived_count = 0
    
    for file_path in files_to_archive:
        try:
            target_path = ARCHIVE_DIR / file_path.name
            
            # Wenn Datei bereits existiert, umbenennen
            if target_path.exists():
                base = target_path.stem
                ext = target_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = ARCHIVE_DIR / f"{base}_{counter}{ext}"
                    counter += 1
            
            shutil.move(str(file_path), str(target_path))
            archived_count += 1
            
            if archived_count % 10 == 0:
                print(f"   ... {archived_count}/{len(files_to_archive)} Dateien archiviert")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {file_path.name}: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ ARCHIVIERUNG ABGESCHLOSSEN!")
    print(f"   {archived_count}/{len(files_to_archive)} Dateien archiviert")
    print(f"   Ziel: {ARCHIVE_DIR}")
    print("=" * 70)
    
    # Zeige verbleibende Dateien
    print("\n📋 Verbleibende Python-Dateien im Hauptverzeichnis:\n")
    
    remaining_files = sorted([f for f in ROOT_DIR.glob("*.py") 
                             if not f.name.startswith("test_") 
                             and not f.name.startswith("cleanup_")])
    
    for i, file_path in enumerate(remaining_files, 1):
        prefix = "✅" if file_path.name.startswith("v2_") else "📄"
        print(f"   {i:2d}. {prefix} {file_path.name}")
    
    print(f"\n✅ {len(remaining_files)} Python-Dateien verbleiben im Hauptverzeichnis")
    
    # Zähle V2-Dateien
    v2_count = sum(1 for f in remaining_files if f.name.startswith("v2_"))
    print(f"   → davon {v2_count} V2-Dateien")


if __name__ == "__main__":
    archive_old_pdvm_files()
