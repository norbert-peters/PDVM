"""
Prüft Template-Struktur (55555...) in sys_viewdaten
"""
import sys
import os

# Pfad anpassen
sys.path.insert(0, os.path.dirname(__file__))

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

# Minimales GCS Setup
os.chdir(os.path.dirname(__file__))

# Datenbank direkt öffnen
from pdvm_datenbank_manager import PdvmDatenbankManager

manager = PdvmDatenbankManager()
manager.set_system_db_path('Daten/pdvm_system.db')

# Template laden
db = PdvmCentralDatenbank('sys_viewdaten', '55555555-5555-5555-5555-555555555555')

print("=" * 60)
print("TEMPLATE-STRUKTUR (55555555-5555-5555-5555-555555555555)")
print("=" * 60)

gruppen = db.get_groups()
print(f"\n✅ Gruppen ({len(gruppen)}):")
for g in gruppen:
    print(f"  - {g}")

# ROOT prüfen
print("\n📋 ROOT:")
root = db.get_value_by_group('ROOT')
if root:
    for key, val in root.items():
        print(f"  {key}: {val}")
else:
    print("  ❌ Nicht vorhanden")

# ROOT_CONTROLS prüfen
print("\n📋 ROOT_CONTROLS:")
root_controls = db.get_value_by_group('ROOT_CONTROLS')
if root_controls:
    for key, val in root_controls.items():
        print(f"  {key}: {type(val).__name__}")
        if isinstance(val, dict):
            for k2, v2 in val.items():
                print(f"    {k2}: {v2}")
else:
    print("  ❌ Nicht vorhanden")

print("\n" + "=" * 60)
