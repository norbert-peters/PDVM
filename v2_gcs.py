"""
V2.0 Global Central System (GCS)

Zentrale Systemsteuerung für V2.0:
- User-Daten (aus auth.db übernommen, NICHT erneut laden!)
- Mandanten-Daten (aus auth.db übernommen)
- Mandanten-Datenbank (Daten/mandant_XXX/datenbank.db)
- PdvmDatenbank & PdvmCentralDatenbank Integration

WICHTIG: Nach Login KEINE Verbindung mehr zu auth.db!

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 2.0
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from v2_pdvm_datenbank import PdvmDatenbank
from v2_pdvm_central_datenbank import PdvmCentralDatenbank


# Globale GCS-Instanz (Singleton)
_gcs_instance = None


class V2GlobalCentralSystem:
    """
    V2.0 Globale Systemsteuerung
    
    Wird EINMALIG nach Login/Mandanten-Auswahl initialisiert.
    Keine weitere Verbindung zu auth.db!
    """
    
    def __init__(self, user_data: Dict, mandant_guid: str, mandant_data: Dict):
        """
        Args:
            user_data: Komplette User-Daten aus auth.db (EINMALIG!)
            mandant_guid: Mandanten-GUID aus sys_mandanten.uid
            mandant_data: Komplette Mandanten-Daten aus auth.db
        """
        # ⭐ User-Informationen (aus auth.db)
        self.user_guid = user_data['uid']
        self.user_email = user_data['email']
        self.user_name = user_data['name']
        self.user_daten = user_data['daten']  # Komplettes JSON
        
        # ⭐ Mandanten-Informationen (aus auth.db)
        self.mandant_guid = mandant_guid  # GUID aus sys_mandanten
        self.mandant_id = mandant_data['METADATEN']['MANDANT_ID']  # ⭐ mandant_001, mandant_002
        self.mandant_data = mandant_data  # Komplettes JSON
        
        # ⭐ Mandanten-Datenbank-Pfad
        self.mandant_db_path = self._get_mandant_db_path(self.mandant_id)
        
        # ⭐ PdvmInit.json für alte Datenbank-Klassen aktualisieren
        self._update_pdvm_init_json()
        
        # Benutzer-Einstellungen (Shortcuts)
        self.country = self.user_daten['SETTINGS']['COUNTRY']
        self.language = self.user_daten['SETTINGS']['LANGUAGE']
        self.theme = self.user_daten['SETTINGS']['THEME']
        self.mode = self.user_daten['SETTINGS']['MODE']
        self.stichtag = self.user_daten['SETTINGS']['STICHTAG']
        
        # Security
        self.user_roles = self.user_daten['PERMISSIONS']['ROLES']
        self.user_sec_profiles = self.user_daten['PERMISSIONS']['SEC_PROFILES']
        
        # MeineApps
        self.start_menu_guid = self.user_daten.get('MEINEAPPS', {}).get('START')
        self.anwendungen = self.user_daten.get('ANWENDUNGEN', {})
        
        # Mandanten-Info
        self.mandant_name = mandant_data['ROOT']['BEZEICHNUNG']
        self.mandant_db_name = mandant_data['ROOT']['DB_NAME']
        self.mandant_country = mandant_data['METADATEN']['COUNTRY']
        self.mandant_status = mandant_data['METADATEN']['STATUS']
        
        # System-GUID für Anwendungsdaten (0000...)
        self.system_guid = "00000000-0000-0000-0000-000000000000"
        
        # ⭐ 4 Datenbank-Instanzen initialisieren
        self._init_database_instances()
        
        # ⭐ Mandanten-Daten in man_db abgleichen
        self._sync_mandant_data_to_man_db()
        
        print("\n" + "="*70)
        print("✅ GCS V2.0 INITIALISIERT")
        print("="*70)
        print(f"   User: {self.user_name} ({self.user_email})")
        print(f"   User-GUID: {self.user_guid}")
        print(f"   Mandant: {self.mandant_name} ({self.mandant_id})")
        print(f"   DB-Pfad: {self.mandant_db_path}")
        print(f"   Rollen: {', '.join(self.user_roles)}")
        print(f"   Security: {', '.join(self.user_sec_profiles)}")
        print(f"   Country: {self.country}")
        print(f"   Mode: {self.mode}")
        print(f"   Stichtag: {self.stichtag}")
        print("="*70 + "\n")
    
    def _init_database_instances(self):
        """
        Initialisiert die 4 Datenbank-Instanzen für GCS
        
        1. u_db = Benutzerstamm (OHNE GUID) - Fiktive Tabelle, nur Login-Daten
        2. app_db = sys_anwendungsdaten (user_guid) - User-Settings
        3. db = sys_systemsteuerung (user_guid) - Systemsteuerung
        4. man_db = sys_anwendungsdaten (mandant_guid) - Mandanten-Daten
        """
        try:
            # 1. Benutzerstamm (fiktiv - OHNE GUID!)
            self.u_db = PdvmCentralDatenbank('benutzerstamm')
            self.u_db.set_data(self.user_daten)
            
            # 2. User-Anwendungsdaten
            self.app_db = PdvmCentralDatenbank('sys_anwendungsdaten', self.user_guid)
            
            # 3. Systemsteuerung
            self.db = PdvmCentralDatenbank('sys_systemsteuerung', self.user_guid)
            
            # 4. Mandanten-Anwendungsdaten
            self.man_db = PdvmCentralDatenbank('sys_anwendungsdaten', self.mandant_guid)
            
            print(f"✅ 4 Datenbank-Instanzen initialisiert")
            print(f"   u_db: benutzerstamm [fiktiv, OHNE GUID]")
            print(f"   app_db: sys_anwendungsdaten[{self.user_guid}]")
            print(f"   db: sys_systemsteuerung[{self.user_guid}]")
            print(f"   man_db: sys_anwendungsdaten[{self.mandant_guid}]")
            
        except Exception as e:
            print(f"⚠️ Fehler bei Datenbank-Initialisierung: {e}")
            import traceback
            traceback.print_exc()
    
    def _sync_mandant_data_to_man_db(self):
        """
        Gleicht Mandanten-Daten aus auth.db mit man_db ab
        
        LINEAR:
        1. set_data(mandant_data) → Überschreibt alle Daten
        2. set_value() für Zusatz-Felder (DB_PATH, LETZTER_LOGIN)
        3. save_all_values() → Fertig!
        """
        try:
            from pdvm_datetime import Pdvm_DateTime
            dt = Pdvm_DateTime("DEU")
            letzter_login = dt.PdvmDateTimeNow()
            
            # 1. Mandanten-Daten aus auth.db überschreiben
            self.man_db.set_data(self.mandant_data, self.mandant_guid)
            
            # 2. Zusätzliche Felder setzen
            self.man_db.set_value('ROOT', 'DB_PATH', self.mandant_db_path, 1001.0)
            self.man_db.set_value('METADATEN', 'LETZTER_LOGIN', letzter_login, letzter_login)
            
            # 3. Speichern
            self.man_db.save_all_values()
            
            print(f"💾 Mandanten-Daten abgeglichen in man_db")
            print(f"   DB-Pfad: {self.mandant_db_path}")
            print(f"   Letzter Login: {letzter_login}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Abgleich der Mandanten-Daten: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_mandant_db_path(self, mandant_id: str) -> str:
        """
        Ermittelt Pfad zur Mandanten-Datenbank
        
        Returns:
            Absoluter Pfad zu datenbank.db
        """
        base_path = Path(__file__).parent / "Daten" / mandant_id
        db_path = base_path / "datenbank.db"
        
        if not db_path.exists():
            raise FileNotFoundError(
                f"Mandanten-Datenbank nicht gefunden: {db_path}"
            )
        
        return str(db_path)
    
    def _update_pdvm_init_json(self):
        """
        Aktualisiert PdvmInit.json mit aktuellem Datenbank-Pfad
        
        Die alten pdvm_datenbank/pdvm_central_datenbank Klassen lesen
        den DB-Pfad aus PdvmInit.json. In V2.0 setzen wir diesen Pfad
        beim Login, damit alte und neue Klassen gemeinsam funktionieren.
        """
        try:
            init_file_path = Path(__file__).parent / "PdvmInit.json"
            
            # PdvmInit.json laden oder neu erstellen
            if init_file_path.exists():
                with open(init_file_path, 'r', encoding='utf-8') as f:
                    init_data = json.load(f)
            else:
                init_data = {"ROOT": {}}
            
            # Datenbank-Pfad setzen (nur Dateiname, nicht vollständiger Pfad!)
            init_data["ROOT"]["datenbank"] = str(Path(self.mandant_db_path).name)
            
            # Zusätzlich: Vollständigen Pfad als Backup speichern
            init_data["ROOT"]["datenbank_pfad"] = str(self.mandant_db_path)
            
            # Speichern
            with open(init_file_path, 'w', encoding='utf-8') as f:
                json.dump(init_data, f, ensure_ascii=False, indent=4)
            
            print(f"📝 PdvmInit.json aktualisiert: {init_data['ROOT']['datenbank']}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Aktualisieren von PdvmInit.json: {e}")
            # Nicht kritisch
    
    def get_user_setting(self, key: str) -> Any:
        """
        Holt User-Einstellung
        
        Args:
            key: Setting-Key (z.B. 'THEME', 'LANGUAGE')
        
        Returns:
            Setting-Wert oder None
        """
        return self.user_daten.get('SETTINGS', {}).get(key)
    
    def get_menu_guid(self, bereich: str, menu_name: str) -> Optional[str]:
        """
        Holt Menü-GUID aus Anwendungen
        
        Args:
            bereich: Bereich (z.B. 'PERSONALWESEN', 'FINANZWESEN')
            menu_name: Menü-Name (z.B. 'MENU', 'SUBMENU_1')
        
        Returns:
            GUID oder None
        """
        return self.anwendungen.get(bereich, {}).get(menu_name)
    
    def has_role(self, role: str) -> bool:
        """Prüft ob User Rolle hat"""
        return role in self.user_roles
    
    def has_sec_profile(self, profile: str) -> bool:
        """Prüft ob User Security-Profile hat"""
        return profile in self.user_sec_profiles
    
    def get_mandant_info(self) -> Dict:
        """
        Gibt Mandanten-Info zurück
        
        Returns:
            {
                'guid': 'b9eb1c2e-...',
                'id': 'mandant_001',
                'name': 'Hauptverwaltung',
                'db_name': 'Mandant1',
                'country': 'DEU',
                'status': 'aktiv',
                'db_path': '.../datenbank.db'
            }
        """
        return {
            'guid': self.mandant_guid,  # GUID aus sys_mandanten
            'id': self.mandant_id,      # mandant_001, mandant_002
            'name': self.mandant_name,
            'db_name': self.mandant_db_name,
            'country': self.mandant_country,
            'status': self.mandant_status,
            'db_path': self.mandant_db_path
        }
    
    def get_user_info(self) -> Dict:
        """
        Gibt User-Info zurück
        
        Returns:
            {
                'guid': '...',
                'email': '...',
                'name': '...',
                'roles': [...],
                'sec_profiles': [...],
                'country': 'DEU',
                'mode': 'expert'
            }
        """
        return {
            'guid': self.user_guid,
            'email': self.user_email,
            'name': self.user_name,
            'roles': self.user_roles,
            'sec_profiles': self.user_sec_profiles,
            'country': self.country,
            'mode': self.mode,
            'stichtag': self.stichtag
        }
    



def init_gcs(user_data: Dict, mandant_guid: str, mandant_data: Dict) -> V2GlobalCentralSystem:
    """
    Initialisiert GCS EINMALIG nach Login
    
    Args:
        user_data: Komplette User-Daten aus auth.db
        mandant_guid: Gewählte Mandanten-GUID (sys_mandanten.uid)
        mandant_data: Komplette Mandanten-Daten aus auth.db
    
    Returns:
        GCS-Instanz
    """
    global _gcs_instance
    
    if _gcs_instance is not None:
        print("⚠️ GCS bereits initialisiert - wird überschrieben!")
    
    _gcs_instance = V2GlobalCentralSystem(user_data, mandant_guid, mandant_data)
    return _gcs_instance


def get_gcs() -> Optional[V2GlobalCentralSystem]:
    """
    Holt globale GCS-Instanz
    
    Returns:
        GCS oder None (wenn noch nicht initialisiert)
    """
    return _gcs_instance


def reset_gcs():
    """Setzt GCS zurück (z.B. bei Logout)"""
    global _gcs_instance
    _gcs_instance = None
    print("🔄 GCS zurückgesetzt")
