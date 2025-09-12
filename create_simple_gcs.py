#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VEREINFACHTE GCS-LÖSUNG

Das Problem: Zu komplexe Initialisierung mit Datenbank-Problemen
Die Lösung: Einfache Hardcoded-Werte für den Prototyp
"""

def create_simple_gcs_solution():
    """Erstelle eine einfache GCS-Lösung"""
    
    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EINFACHE GCS für Prototyp - ohne komplexe Datenbank-Initialisierung
"""

from pdvm_datetime import Pdvm_DateTime
import logging

logger = logging.getLogger(__name__)

# Globale Instanzen
_gcs_instance = None
global_stichtag_inst = None

class SimpleGCS:
    """Vereinfachte GCS für Prototyp"""
    
    def __init__(self, user_guid):
        global global_stichtag_inst
        
        self._user_guid = user_guid
        
        # HARDCODED-Werte für den bekannten User
        if user_guid == "4886ad26-061b-4662-a762-c8c83f36692d":
            self._stichtag = 2025152.0  # 01.06.2025 aus deiner Systemsteuerung
            self._country = "DEU"
            self._expert_mode = False
            self._mode = "admin"
            self._language = "de-de"
        else:
            # Defaults für andere User
            dt_now = Pdvm_DateTime("DEU")
            self._stichtag = dt_now.PdvmDateTimeNow()
            self._country = "DEU"
            self._expert_mode = False
            self._mode = "user"
            self._language = "de-de"
        
        # Globale Stichtag-Instanz erstellen
        global_stichtag_inst = Pdvm_DateTime(self._country)
        global_stichtag_inst.PdvmDateTime = self._stichtag
        
        logger.info(f"✅ Simple GCS initialisiert für {user_guid}")
        logger.info(f"📅 Stichtag: {global_stichtag_inst.FormTimeStamp}")
    
    @property
    def stichtag(self):
        """Stichtag als Float-Wert"""
        return self._stichtag
    
    @property
    def global_stichtag_inst(self):
        """Globale Stichtag-Instanz"""
        global global_stichtag_inst
        return global_stichtag_inst
    
    @property
    def country(self):
        return self._country
    
    @property
    def expert_mode(self):
        return self._expert_mode
    
    @property
    def mode(self):
        return self._mode
    
    @property
    def language(self):
        return self._language

def initialize_simple_gcs(user_guid):
    """Initialisiere einfache GCS"""
    global _gcs_instance
    
    if _gcs_instance is not None:
        raise RuntimeError("GCS bereits initialisiert!")
    
    _gcs_instance = SimpleGCS(user_guid)
    return _gcs_instance

def get_simple_gcs():
    """Hole GCS-Instanz"""
    if _gcs_instance is None:
        raise RuntimeError("GCS nicht initialisiert!")
    return _gcs_instance

def is_simple_initialized():
    """Prüfe ob initialisiert"""
    return _gcs_instance is not None

def reset_simple():
    """Reset für Tests"""
    global _gcs_instance, global_stichtag_inst
    _gcs_instance = None
    global_stichtag_inst = None

# Alias für Kompatibilität
gcs = property(get_simple_gcs)
'''
    
    with open("C:/Users/norbe/OneDrive/Dokumente/MyApplication/simple_gcs.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Einfache GCS-Lösung erstellt: simple_gcs.py")

if __name__ == "__main__":
    create_simple_gcs_solution()
    print("💡 Verwende diese einfache Lösung statt der komplexen GCS!")
