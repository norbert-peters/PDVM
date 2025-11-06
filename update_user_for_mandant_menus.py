"""
Aktualisiert User-Daten für Migration zu V2-Menüs aus Mandanten-DB
"""
import sqlite3
import json

USER_GUID = "4886ad26-061b-4662-a762-c8c83f36692d"
STARTMENU_GUID = "5ca6674e-b9ce-4581-9756-64e742883f80"  # Admin-Startmenü

print("🔧 Aktualisiere User-Daten für V2-Menü-System")
print("="*80)

# Verbinde zur auth.db
conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

# Lade aktuelle User-Daten
cursor.execute("SELECT daten FROM sys_benutzer WHERE uid = ?", (USER_GUID,))
row = cursor.fetchone()

if not row:
    print(f"❌ User {USER_GUID} nicht gefunden!")
    conn.close()
    exit(1)

user_data = json.loads(row[0])

# Aktualisiere MEINEAPPS
if 'MEINEAPPS' not in user_data:
    user_data['MEINEAPPS'] = {}

user_data['MEINEAPPS']['START'] = STARTMENU_GUID

# Liste der erlaubten Menüs
available_menus = [
    "5ca6674e-b9ce-4581-9756-64e742883f80",  # Admin-Startmenü
    "3424b00f-bb4d-4759-9689-e9e08249117b",  # Admin-Menü
    "113c6a2c-af9a-4022-929b-6544799e8954",  # Admin-Testmenü
    "e1e77039-d1b5-46ff-b12b-cced0ae0da7c",  # Admin-Benutzermenü
    "1a653694-3132-48d9-bc3e-a512962ae8e6",  # Basis-Menü
]

if 'LIST' not in user_data['MEINEAPPS']:
    user_data['MEINEAPPS']['LIST'] = []

# Füge alle Menüs zur Liste hinzu
for menu_guid in available_menus:
    if menu_guid not in user_data['MEINEAPPS']['LIST']:
        user_data['MEINEAPPS']['LIST'].append(menu_guid)

# Speichere zurück
user_data_json = json.dumps(user_data, ensure_ascii=False)
cursor.execute(
    "UPDATE sys_benutzer SET daten = ? WHERE uid = ?",
    (user_data_json, USER_GUID)
)

conn.commit()
conn.close()

print(f"✅ User-Daten aktualisiert!")
print(f"   START: {STARTMENU_GUID}")
print(f"   LIST: {len(user_data['MEINEAPPS']['LIST'])} Menüs")
print()
print("📝 Konfigurierte Menüs:")
for menu_guid in user_data['MEINEAPPS']['LIST']:
    print(f"   • {menu_guid}")
