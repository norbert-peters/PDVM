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
VERSION: 1.0
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


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
