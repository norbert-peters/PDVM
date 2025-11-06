"""
V1 Archivierungs-Script
=======================
Verschiebt alle alten Dateien (ohne v2_ Präfix) ins archive_v1 Verzeichnis

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

# Dateien die BEHALTEN werden (nicht archiviert)
KEEP_FILES = {
    # V2-Dateien (Produktionsstand)
    "v2_*.py",
    
    # Kern-Module ohne v2_ die noch verwendet werden
    "pd_datetime.py",  # Pdvm_DateTime (Kernmodul)
    "pd_langtext.py",  # Langtext-System
    "pd_util.py",      # Utilities
    "global_gcs.py",   # Globale GCS-Instanz
    
    # V3-Menu-Handler (aktiv verwendet)
    "v3_menu_handler.py",
    "v3_menu_widgets.py",
    "v3_menu_system.py",
    
    # Handlers (aktiv verwendet)
    "handlers",  # Verzeichnis
    
    # Dokumentation & Tests
    "*.md",
    "test_*.py",
    "V3*.md",
    
    # Cleanup & Migrations-Scripts (für Referenz)
    "cleanup_*.py",
    "migrate_*.py",
    
    # Git & Config
    ".git",
    ".gitignore",
    ".github",
    "requirements.txt",
    "README.md",
    
    # Daten
    "Daten",
    "datasets",
    
    # Python-Umgebung
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    
    # Logs & Temp
    "*.log",
    ".v2_main_starts",
}

# Dateien/Verzeichnisse die ARCHIVIERT werden sollen
ARCHIVE_PATTERNS = [
    # Alte pdvm_* Dateien (ohne v2_ Präfix)
    "pdvm_*.py",
    
    # Analyse-Tools
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
    
    # Fix-Scripts
    "fix_*.py",
    "repair_*.py",
    "correct_*.py",
    "restore_*.py",
    "update_*.py",
    "set_*.py",
    "remove_*.py",
    "reset_*.py",
    
    # Add/Create-Scripts
    "add_*.py",
    "create_*.py",
    
    # Alte Hauptdateien
    "main.py",  # Alte Version
    "start_app.py",
    
    # Alte Struktur-Dateien
    "central_systemsteuerung.py",
    "datenbank.py",
    "global_gcs_backup.py",
    
    # Alte Dialog-Dateien
    "column_management_dialog.py",
    "column_management_dialog_backup.py",
    "field_search_detail_dialog.py",
    "field_search_detail_dialog_v2.py",
    "search_parameter_dialog.py",
    "search_parameter_dialog_simple.py",
    "simple_search_dialog.py",
    
    # Test & Beispiel-Dateien
    "Hallo_lernen.py",
    "Lerne_Class.py",
    "LernenDB.py",
    "PyQt5_Start.py",
    "Versuch_alle.py",
    "neue_methode.py",
    "FirstFile.py",
    
    # Alte Datenmodule
    "DatenHistAbfragenDic.py",
    "DatenLaden.py",
    "finanzdaten.py",
    "konto.py",
    "Personalstamm.py",
    "persondaten.py",
    "Pflegeperson.py",
    "Reports.py",
    
    # Design-Konzepte
    "design_konzept_*.py",
    "lupe_design_konzept.py",
    "extended_search_concept.py",
    "extended_search_ui_mockup.py",
    
    # Alte Manager
    "simple_*.py",
    "sort_manager.py",
    "projection_matrix.py",
    "column_projection_helper.py",
    
    # Alte Integration-Dateien
    "dialog_integration.py",
    "menu_integration_example.py",
    "open_view_from_db.py",
    
    # Backup-Dateien
    "*_backup.py",
    "*_BACKUP_*.py",
    
    # Diverse alte Dateien
    "allgemeines.py",
    "architecture_analysis.py",
    "architektur_dokumentation.py",
    "flexible_*.py",
    "grouped_*.py",
    "improved_*.py",
    "optimized_*.py",
    "robuste_*.py",
    "systematisches_*.py",
    "universal_*.py",
    "vollständige_*.py",
    
    # Spezifische alte Dateien
    "_get_visible_columns_from_gcs_KORRIGIERT.py",
    "EINHEITLICHE_STRUKTUR_KOMPLETT.py",
    "UI_VERBESSERUNGEN_ERFOLGREICH_IMPLEMENTIERT.py",
    "json_repair_*.py",
    "matrix_3_ebenen_example.py",
    "shuffle_and_split_data.py",
    "spalten_analyse.py",
    
    # Zusammenfassungen (als .md archiviert)
    "stichtag_problem_gelöst.py",
    "stichtagbar_lösung_zusammenfassung.py",
    "zusatzmenu_korrekturen_zusammenfassung.py",
]


def should_keep(file_path: Path) -> bool:
    """Prüft ob Datei behalten werden soll"""
    name = file_path.name
    
    # V2-Dateien behalten
    if name.startswith("v2_"):
        return True
    
    # Test-Dateien behalten
    if name.startswith("test_"):
        return True
    
    # Kern-Module behalten
    if name in ["pd_datetime.py", "pd_langtext.py", "pd_util.py", "global_gcs.py"]:
        return True
    
    # V3-Menu-Handler behalten
    if name.startswith("v3_menu_"):
        return True
    
    # Handlers-Verzeichnis behalten
    if file_path.is_dir() and name == "handlers":
        return True
    
    # Dokumentation behalten
    if name.endswith(".md"):
        return True
    
    # Git/Config behalten
    if name in [".git", ".gitignore", ".github", "requirements.txt", "README.md"]:
        return True
    
    # Daten behalten
    if name in ["Daten", "datasets"]:
        return True
    
    # Python-Umgebung behalten
    if name in [".venv", "venv", "env", "__pycache__"]:
        return True
    
    # Logs behalten
    if name.endswith(".log") or name == ".v2_main_starts":
        return True
    
    # Cleanup/Migrate-Scripts behalten
    if name.startswith("cleanup_") or name.startswith("migrate_") and name != "migrate_v2_to_v3.py":
        return True
    
    return False


def should_archive(file_path: Path) -> bool:
    """Prüft ob Datei archiviert werden soll"""
    name = file_path.name
    
    # Nur Python-Dateien archivieren
    if not name.endswith(".py"):
        return False
    
    # Dieses Script nicht archivieren
    if name == "cleanup_archive_v1.py":
        return False
    
    # Prüfe gegen Archive-Patterns
    for pattern in ARCHIVE_PATTERNS:
        if "*" in pattern:
            # Wildcard-Match
            prefix = pattern.replace("*", "")
            if pattern.startswith("*"):
                if name.endswith(prefix):
                    return True
            elif pattern.endswith("*"):
                if name.startswith(prefix):
                    return True
        else:
            # Exakter Match
            if name == pattern:
                return True
    
    return False


def archive_files():
    """Archiviert alle alten Dateien"""
    print("🗂️ V1 ARCHIVIERUNGS-SCRIPT")
    print("=" * 70)
    
    # Erstelle Archive-Verzeichnis
    if not ARCHIVE_DIR.exists():
        ARCHIVE_DIR.mkdir(parents=True)
        print(f"✅ Archive-Verzeichnis erstellt: {ARCHIVE_DIR}")
    else:
        print(f"📁 Archive-Verzeichnis existiert: {ARCHIVE_DIR}")
    
    # Sammle zu archivierende Dateien
    files_to_archive = []
    
    for file_path in ROOT_DIR.iterdir():
        # Überspringe Verzeichnisse (außer handlers)
        if file_path.is_dir():
            continue
        
        # Überspringe Dateien die behalten werden sollen
        if should_keep(file_path):
            continue
        
        # Prüfe ob Datei archiviert werden soll
        if should_archive(file_path):
            files_to_archive.append(file_path)
    
    print(f"\n📊 Gefundene Dateien: {len(files_to_archive)}")
    
    if not files_to_archive:
        print("\n✅ Keine Dateien zu archivieren!")
        return
    
    # Zeige Übersicht
    print("\n📋 Folgende Dateien werden archiviert:\n")
    for i, file_path in enumerate(sorted(files_to_archive), 1):
        print(f"   {i:3d}. {file_path.name}")
    
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
            print(f"   ✅ {file_path.name} → {target_path.name}")
            archived_count += 1
            
        except Exception as e:
            print(f"   ❌ Fehler bei {file_path.name}: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ ARCHIVIERUNG ABGESCHLOSSEN!")
    print(f"   {archived_count}/{len(files_to_archive)} Dateien archiviert")
    print(f"   Ziel: {ARCHIVE_DIR}")
    print("=" * 70)
    
    # Zeige verbleibende V2-Dateien
    print("\n📋 Verbleibende V2-Dateien:\n")
    v2_files = sorted(ROOT_DIR.glob("v2_*.py"))
    for i, file_path in enumerate(v2_files, 1):
        print(f"   {i:2d}. {file_path.name}")
    
    print(f"\n✅ {len(v2_files)} V2-Dateien verbleiben im Hauptverzeichnis")


if __name__ == "__main__":
    archive_files()
