"""
V2.0 Initialisierungs-Script für Auth-Datenbank

ZWECK:
- Erstellt auth.db mit sys_benutzer und sys_mandanten
- Legt Test-User an (admin@super.de, user@super.de)
- Übernimmt Daten aus alter PdvmManager.db
- Erstellt 2 Test-Mandanten

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 1.0
"""

import sqlite3
import json
import bcrypt
import uuid
import os
from datetime import datetime
from typing import Dict, Optional

class V2AuthDatabaseInit:
    """Initialisierung der V2.0 Auth-Datenbank"""
    
    def __init__(self):
        self.auth_db_path = "Daten/auth.db"
        self.old_db_path = "Daten/PdvmManager.db"
        
        # Timestamp für created_at / modified_at
        self.timestamp = datetime.now().strftime('%Y%j.%H%M%S')
        
        print("=" * 70)
        print("🚀 V2.0 AUTH-DATENBANK INITIALISIERUNG")
        print("=" * 70)
    
    def run(self):
        """Hauptablauf"""
        try:
            # 1. Verzeichnis sicherstellen
            self._ensure_data_directory()
            
            # 2. Auth-DB erstellen
            self._create_auth_database()
            
            # 3. sys_benutzer Tabelle erstellen
            self._create_sys_benutzer_table()
            
            # 4. sys_mandanten Tabelle erstellen
            self._create_sys_mandanten_table()
            
            # 5. Test-User anlegen
            self._create_test_users()
            
            # 6. Test-Mandanten anlegen
            self._create_test_mandanten()
            
            # 7. Zusammenfassung
            self._print_summary()
            
            print("\n✅ INITIALISIERUNG ERFOLGREICH ABGESCHLOSSEN!")
            return True
            
        except Exception as e:
            print(f"\n❌ FEHLER bei Initialisierung: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _ensure_data_directory(self):
        """Stellt sicher dass Daten/ Verzeichnis existiert"""
        if not os.path.exists("Daten"):
            os.makedirs("Daten")
            print("✅ Daten/ Verzeichnis erstellt")
        else:
            print("✅ Daten/ Verzeichnis vorhanden")
    
    def _create_auth_database(self):
        """Erstellt auth.db (oder öffnet bestehende)"""
        if os.path.exists(self.auth_db_path):
            print(f"⚠️  {self.auth_db_path} existiert bereits - wird überschrieben!")
            os.remove(self.auth_db_path)
        
        conn = sqlite3.connect(self.auth_db_path)
        conn.close()
        print(f"✅ {self.auth_db_path} erstellt")
    
    def _create_sys_benutzer_table(self):
        """Erstellt sys_benutzer Tabelle"""
        conn = sqlite3.connect(self.auth_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sys_benutzer (
                benutzer TEXT PRIMARY KEY,
                passwort TEXT NOT NULL,
                uid TEXT NOT NULL,
                daten TEXT NOT NULL,
                name TEXT,
                historisch INTEGER DEFAULT 0,
                source_hash TEXT,
                sec_id TEXT,
                gilt_bis TEXT DEFAULT '999365.00000',
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ sys_benutzer Tabelle erstellt")
    
    def _create_sys_mandanten_table(self):
        """Erstellt sys_mandanten Tabelle (generischer Container)"""
        conn = sqlite3.connect(self.auth_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sys_mandanten (
                uid TEXT PRIMARY KEY,
                daten TEXT NOT NULL,
                name TEXT,
                historisch INTEGER DEFAULT 0,
                source_hash TEXT,
                sec_id TEXT,
                gilt_bis TEXT DEFAULT '999365.00000',
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ sys_mandanten Tabelle erstellt")
    
    def _create_test_users(self):
        """Erstellt Test-User (admin + user)"""
        print("\n📋 ERSTELLE TEST-USER")
        print("-" * 70)
        
        # User-Daten aus alter DB laden (falls vorhanden)
        old_user_data = self._load_old_user_data()
        
        # Admin-User
        admin_data = old_user_data.get('admin@super.de', {})
        self._create_user(
            email='admin@super.de',
            password='admin',
            name='Administrator',
            roles=['admin'],
            sec_profiles=['sec-admin-full'],
            mandanten=['mandant_001', 'mandant_002'],
            default_mandant='mandant_001',
            old_data=admin_data
        )
        
        # Work-User
        user_data = old_user_data.get('user@super.de', {})
        self._create_user(
            email='user@super.de',
            password='user',
            name='Test User',
            roles=['user', 'vertrieb'],
            sec_profiles=['sec-public-read', 'sec-vertrieb'],
            mandanten=['mandant_001'],
            default_mandant='mandant_001',
            old_data=user_data
        )
    
    def _load_old_user_data(self) -> Dict:
        """Lädt User-Daten aus alter PdvmManager.db"""
        if not os.path.exists(self.old_db_path):
            print(f"⚠️  Alte DB nicht gefunden: {self.old_db_path}")
            return {}
        
        try:
            conn = sqlite3.connect(self.old_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM benutzerstamm")
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                benutzer = row['benutzer']
                daten = row['daten']
                
                # JSON parsen
                try:
                    daten_dict = json.loads(daten)
                    result[benutzer] = daten_dict
                    print(f"   ✅ Alte Daten geladen: {benutzer}")
                except:
                    print(f"   ⚠️  JSON-Fehler bei: {benutzer}")
            
            conn.close()
            return result
            
        except Exception as e:
            print(f"⚠️  Fehler beim Laden alter User-Daten: {e}")
            return {}
    
    def _create_user(self, email: str, password: str, name: str, 
                     roles: list, sec_profiles: list, mandanten: list,
                     default_mandant: str, old_data: Dict = None):
        """
        Erstellt einen User in sys_benutzer
        
        Args:
            email: Email-Adresse (PRIMARY KEY)
            password: Klartext-Passwort (wird gehasht)
            name: Anzeigename
            roles: Liste von Rollen ['admin', 'user', 'vertrieb']
            sec_profiles: Liste von Security-Profilen
            mandanten: Liste von Mandanten-IDs
            default_mandant: Default Mandant
            old_data: Optionale alte Daten aus PdvmManager.db
        """
        # Passwort hashen (bcrypt)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # UID generieren
        uid = str(uuid.uuid4())
        
        # Daten-Dict aufbauen
        daten_dict = {
            "USER": old_data.get('USER', {}) if old_data else {
                "NAME": name,
                "EMAIL": email,
                "TELEFON": ""
            },
            "SETTINGS": old_data.get('SETTINGS', {}) if old_data else {
                "THEME": "light",
                "LANGUAGE": "DEU",
                "FONT_SIZE": 10,
                "STICHTAG": self.timestamp
            },
            "MANDANTEN": {
                "LIST": mandanten,
                "DEFAULT": default_mandant
            },
            "PERMISSIONS": {
                "ROLES": roles,
                "SEC_PROFILES": sec_profiles
            }
        }
        
        # In DB einfügen
        conn = sqlite3.connect(self.auth_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sys_benutzer
            (benutzer, passwort, uid, daten, name, historisch, 
             gilt_bis, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email,
            password_hash,
            uid,
            json.dumps(daten_dict, ensure_ascii=False, indent=2),
            name,
            0,
            '999365.00000',
            self.timestamp,
            self.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ User erstellt: {email} ({name})")
        print(f"      Rollen: {roles}")
        print(f"      Mandanten: {mandanten}")
    
    def _create_test_mandanten(self):
        """Erstellt Test-Mandanten"""
        print("\n📋 ERSTELLE TEST-MANDANTEN")
        print("-" * 70)
        
        # Mandant 1
        self._create_mandant(
            mandant_id='mandant_001',
            db_name='Mandant1',
            bezeichnung='Hauptverwaltung',
            status='aktiv'
        )
        
        # Mandant 2
        self._create_mandant(
            mandant_id='mandant_002',
            db_name='Mandant2',
            bezeichnung='Filiale Hampeldorf',
            status='aktiv'
        )
    
    def _create_mandant(self, mandant_id: str, db_name: str, 
                        bezeichnung: str, status: str = 'aktiv'):
        """
        Erstellt einen Mandanten in sys_mandanten
        
        Args:
            mandant_id: z.B. "mandant_001"
            db_name: z.B. "Mandant1"
            bezeichnung: z.B. "Hauptverwaltung"
            status: "aktiv" / "inaktiv" / "test"
        """
        # UID = mandant_id
        uid = mandant_id
        
        # Daten-Dict aufbauen (GRUPPE/FELD-Struktur)
        daten_dict = {
            "ROOT": {
                "DB_NAME": db_name,
                "BEZEICHNUNG": bezeichnung
            },
            "METADATEN": {
                "MANDANT_ID": mandant_id,
                "STATUS": status,
                "ERSTELLT_AM": self.timestamp,
                "ERSTELLT_VON": "system",
                "LOGO_PATH": f"{mandant_id}/logo.png",
                "COUNTRY": "DEU"
            }
        }
        
        # In DB einfügen
        conn = sqlite3.connect(self.auth_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sys_mandanten
            (uid, daten, name, historisch, sec_id,
             gilt_bis, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            uid,
            json.dumps(daten_dict, ensure_ascii=False, indent=2),
            bezeichnung,
            0,
            'sec-admin-full',  # Nur Admin darf Mandanten bearbeiten
            '999365.00000',
            self.timestamp,
            self.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Mandant erstellt: {mandant_id} ({bezeichnung})")
        print(f"      DB-Name: {db_name}")
        print(f"      Status: {status}")
    
    def _print_summary(self):
        """Zeigt Zusammenfassung der erstellten Daten"""
        print("\n" + "=" * 70)
        print("📊 ZUSAMMENFASSUNG")
        print("=" * 70)
        
        conn = sqlite3.connect(self.auth_db_path)
        cursor = conn.cursor()
        
        # User zählen
        cursor.execute("SELECT COUNT(*) FROM sys_benutzer")
        user_count = cursor.fetchone()[0]
        print(f"\n👤 BENUTZER: {user_count}")
        
        cursor.execute("SELECT benutzer, name FROM sys_benutzer")
        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]})")
        
        # Mandanten zählen
        cursor.execute("SELECT COUNT(*) FROM sys_mandanten")
        mandant_count = cursor.fetchone()[0]
        print(f"\n🏢 MANDANTEN: {mandant_count}")
        
        cursor.execute("SELECT uid, name FROM sys_mandanten")
        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]})")
        
        conn.close()
        
        print("\n📂 DATENBANK: " + self.auth_db_path)
        print(f"📊 GRÖSSE: {os.path.getsize(self.auth_db_path)} Bytes")


def main():
    """Hauptfunktion"""
    print("\n")
    
    # Initialisierung durchführen
    init = V2AuthDatabaseInit()
    success = init.run()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 INITIALISIERUNG ABGESCHLOSSEN!")
        print("=" * 70)
        print("\n📋 NÄCHSTE SCHRITTE:")
        print("   1. Login-Dialog implementieren (v2_login_dialog.py)")
        print("   2. Mandanten-Auswahl implementieren (v2_mandanten_dialog.py)")
        print("   3. Hauptanwendung anpassen (v2_main.py)")
        print("\n🔐 TEST-ZUGÄNGE:")
        print("   Admin: admin@super.de / admin")
        print("   User:  user@super.de  / user")
        print("")
    else:
        print("\n❌ INITIALISIERUNG FEHLGESCHLAGEN!")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
