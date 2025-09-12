#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINALE INTEGRATION in bestehende Systemsteuerung

Adaptiert die finale GCS-Architektur für die bestehende pdvm_central_systemsteuerung_new.py
"""

import logging
from typing import Any, Dict, Optional
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)

def integrate_finale_architecture():
    """
    Erstelle Migrationsskript für die bestehende Systemsteuerung
    """
    
    migration_code = '''
# FINALE ARCHITEKTUR - Integration in bestehende Systemsteuerung

class PdvmCentralSystemsteuerungFinal:
    """
    Finale Systemsteuerung mit robuster Architektur
    
    Integration der bewährten Patterns:
    1. Robuste Initialisierung mit user_guid + user_data
    2. Parametrisierte Properties (field_value/group_value)
    3. Automatisches Speichern bei allen Settern
    4. Spezielle Stichtag-Behandlung über st_inst
    """
    
    def __init__(self):
        """Initialisierung ohne Daten"""
        self._db = None
        self._user_guid = None
        self._user_data = None
        self._st_inst = None
        self._initialized = False
        
        logger.info("🏗️ Finale Systemsteuerung erstellt")
    
    def initialize(self, user_guid: str, user_data: Dict[str, Any]):
        """
        Robuste Initialisierung nach dem Login
        
        Args:
            user_guid: GUID des Benutzers (aus Login)
            user_data: Benutzerdaten-Dictionary (aus Login)
        """
        if self._initialized:
            raise RuntimeError("Systemsteuerung bereits initialisiert!")
        
        # 1. Benutzerdaten intern speichern
        self._user_guid = user_guid
        self._user_data = user_data.copy()  # Sichere Kopie
        
        # 2. Datenbank-Instanz mit bestehender Logik
        from pdvm_datenbank import PdvmDatenbank
        self._db = PdvmDatenbank()
        
        # 3. Stichtag-Instanz erstellen
        country = self._user_data.get('country', 'DEU')
        self._st_inst = Pdvm_DateTime(country)
        
        # 4. Stichtag aus DB laden und setzen
        stored_stichtag = self._load_user_property('stichtag')
        if stored_stichtag is not None:
            try:
                self._st_inst.PdvmDateTime = float(stored_stichtag)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Ungültiger Stichtag: {stored_stichtag}")
        
        self._initialized = True
        
        logger.info(f"✅ Finale Systemsteuerung initialisiert für {user_guid}")
        logger.info(f"📅 Stichtag: {self._st_inst.FormTimeStamp}")
    
    def _ensure_initialized(self):
        """Prüfe Initialisierung"""
        if not self._initialized:
            raise RuntimeError("Systemsteuerung nicht initialisiert! Rufe initialize() auf.")
    
    def _load_user_property(self, property_name: str) -> Optional[str]:
        """Lade Property für aktuellen User"""
        if not self._db:
            return None
        
        # Nutze bestehende DB-Logik
        return self._db.get_value(gruppe=self._user_guid, feld=property_name)
    
    def _save_user_property(self, property_name: str, value: Any):
        """Speichere Property für aktuellen User"""
        if self._db:
            self._db.set_value(gruppe=self._user_guid, feld=property_name, wert=str(value))
    
    def field_value(self, property_name: str, value: Any = None) -> Optional[Any]:
        """
        KERN-FUNKTION: Parametrisierter Getter/Setter für User-Properties
        
        Beispiele:
            # Getter
            country = gcs.field_value('country')
            stichtag = gcs.field_value('stichtag')
            
            # Setter (mit automatischem Speichern)
            gcs.field_value('country', 'AUT')
            gcs.field_value('stichtag', 2025200.0)
        
        Args:
            property_name: Name der Property
            value: Wert zum Setzen (None = Getter-Modus)
            
        Returns:
            Bei Getter: Wert der Property
            Bei Setter: None
        """
        self._ensure_initialized()
        
        if value is None:
            # GETTER-MODUS
            if property_name == 'stichtag':
                return self._st_inst.PdvmDateTime if self._st_inst else None
            else:
                return self._load_user_property(property_name)
        else:
            # SETTER-MODUS (mit automatischem Speichern)
            if property_name == 'stichtag':
                if self._st_inst:
                    self._st_inst.PdvmDateTime = float(value)
                    # Stichtag persistent speichern
                    self._save_user_property('stichtag', value)
            else:
                # Normale Property speichern
                self._save_user_property(property_name, value)
            
            return None
    
    def group_value(self, group_guid: str, value: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Getter/Setter für Gruppen-Properties (andere GUIDs)
        
        Beispiele:
            # Getter
            group_data = gcs.group_value('some-other-guid')
            
            # Setter
            gcs.group_value('some-other-guid', {'key': 'value'})
        
        Args:
            group_guid: GUID der Gruppe
            value: Dictionary zum Setzen (None = Getter)
            
        Returns:
            Bei Getter: Dictionary mit Gruppen-Daten
            Bei Setter: None
        """
        self._ensure_initialized()
        
        if value is None:
            # GETTER für Gruppe
            if self._db:
                # Alle Felder der Gruppe laden
                return self._db.get_all_fields_for_group(group_guid)
            return {}
        else:
            # SETTER für Gruppe
            if self._db and isinstance(value, dict):
                for field_name, field_value in value.items():
                    self._db.set_value(gruppe=group_guid, feld=field_name, wert=str(field_value))
            return None
    
    def save_values(self):
        """
        Explizite Speicherung aller Werte
        Besonders wichtig: Stichtag aus st_inst speichern
        """
        self._ensure_initialized()
        
        if self._st_inst:
            # Aktuellen Stichtag aus Instanz speichern
            self._save_user_property('stichtag', self._st_inst.PdvmDateTime)
            logger.info(f"💾 Stichtag persistent gespeichert: {self._st_inst.FormTimeStamp}")
        
        # Weitere Speicher-Logik falls nötig
        logger.info("💾 Alle Systemsteuerungs-Werte gespeichert")
    
    # PROPERTIES für einfachen Zugriff
    
    @property
    def st_inst(self) -> Optional[Pdvm_DateTime]:
        """Stichtag-Instanz für DateTimePicker und externe Zugriffe"""
        self._ensure_initialized()
        return self._st_inst
    
    @property
    def stichtag(self) -> Optional[float]:
        """Stichtag als Float-Wert (direkter Zugriff)"""
        self._ensure_initialized()
        return self._st_inst.PdvmDateTime if self._st_inst else None
    
    @property
    def user_guid(self) -> Optional[str]:
        """User-GUID (readonly)"""
        return self._user_guid
    
    @property
    def user_data(self) -> Dict[str, Any]:
        """Benutzerdaten (readonly Kopie)"""
        return self._user_data.copy() if self._user_data else {}
    
    @property
    def is_initialized(self) -> bool:
        """Initialisierungs-Status"""
        return self._initialized

# GLOBALE INSTANZ-VERWALTUNG

_finale_gcs_instance = None

def initialize_finale_gcs(user_guid: str, user_data: Dict[str, Any]) -> PdvmCentralSystemsteuerungFinal:
    """
    Initialisiere finale globale Systemsteuerung
    
    WICHTIG: Nur nach erfolgreichem Login aufrufen!
    
    Args:
        user_guid: GUID des Benutzers (aus Login)
        user_data: Benutzerdaten-Dictionary (aus Login)
        
    Returns:
        Initialisierte GCS-Instanz
        
    Raises:
        RuntimeError: Falls bereits initialisiert
    """
    global _finale_gcs_instance
    
    if _finale_gcs_instance is not None and _finale_gcs_instance.is_initialized:
        raise RuntimeError("Finale GCS bereits initialisiert!")
    
    _finale_gcs_instance = PdvmCentralSystemsteuerungFinal()
    _finale_gcs_instance.initialize(user_guid, user_data)
    
    logger.info("🌐 Finale globale Systemsteuerung initialisiert")
    return _finale_gcs_instance

def get_finale_gcs() -> PdvmCentralSystemsteuerungFinal:
    """
    Hole finale globale Systemsteuerung
    
    Returns:
        GCS-Instanz
        
    Raises:
        RuntimeError: Falls nicht initialisiert
    """
    if _finale_gcs_instance is None or not _finale_gcs_instance.is_initialized:
        raise RuntimeError("Finale GCS nicht initialisiert! Rufe initialize_finale_gcs() auf.")
    return _finale_gcs_instance

def is_finale_gcs_initialized() -> bool:
    """Prüfe ob finale GCS initialisiert ist"""
    return _finale_gcs_instance is not None and _finale_gcs_instance.is_initialized

# USAGE EXAMPLES für die Integration:

"""
# 1. NACH DEM LOGIN (in pdvm_linear_start_new.py oder ähnlich):

user_data = {
    'username': login_username,
    'country': 'DEU',
    'role': user_role,
    'language': 'de-de'
}

# GCS initialisieren
gcs = initialize_finale_gcs(current_user_guid, user_data)

# 2. IN DER STICHTAG-BAR:

# Stichtag lesen
stichtag_inst = gcs.st_inst  # Für DateTimePicker
current_stichtag = gcs.stichtag  # Als Float

# Stichtag ändern
gcs.field_value('stichtag', new_stichtag_value)  # Automatisches Speichern

# 3. FÜR ANDERE PROPERTIES:

# Properties lesen
country = gcs.field_value('country')
mode = gcs.field_value('mode')

# Properties schreiben
gcs.field_value('country', 'AUT')
gcs.field_value('expert_mode', True)

# 4. FÜR GRUPPEN:

# Andere Bereiche
other_data = gcs.group_value('other-guid')
gcs.group_value('other-guid', {'setting': 'value'})
"""
    '''
    
    return migration_code

def create_migration_guide():
    """Erstelle Migrationsleitfaden"""
    
    guide = '''
# MIGRATIONSLEITFADEN: Bestehende Systemsteuerung → Finale Architektur

## 1. ÄNDERUNGEN in pdvm_linear_start_new.py

```python
# ALT:
initialize_gcs(self.current_user_guid)

# NEU:
user_data = {
    'username': self.username,  # Aus Login
    'country': 'DEU',
    'role': 'admin',
    'language': 'de-de'
}
initialize_finale_gcs(self.current_user_guid, user_data)
```

## 2. ÄNDERUNGEN in PDVM-Systemstart-with-new-gcs.py

```python
# ALT:
gcs = get_gcs()
stichtag_value = gcs.stichtag

# NEU:
gcs = get_finale_gcs()
stichtag_value = gcs.stichtag  # Gleich
stichtag_inst = gcs.st_inst   # Für DateTimePicker

# ALT: Spezielle Stichtag-Behandlung
# NEU: Einfacher Setter
gcs.field_value('stichtag', new_value)  # Automatisches Speichern
```

## 3. NEUE FEATURES nutzen

```python
# Parametrisierte Properties
country = gcs.field_value('country')
gcs.field_value('country', 'AUT')

# Flexible Erweiterung
new_setting = gcs.field_value('new_setting')  # Funktioniert automatisch
gcs.field_value('new_setting', 'new_value')

# Gruppen-Handling
other_data = gcs.group_value('some-guid')
```

## 4. VORTEILE der finalen Architektur

✅ Robuste Initialisierung - keine Überraschungen
✅ Parametrisierte Properties - einfache Erweiterung
✅ Automatisches Speichern - kein Datenverlust
✅ Spezielle Stichtag-Behandlung - bewährtes Pattern
✅ Flexible Gruppen-Verwaltung - skalierbar
✅ Saubere Trennung - klare Verantwortlichkeiten

## 5. SCHRITTWEISE MIGRATION

1. Neue finale Systemsteuerung integrieren
2. Login-Prozess anpassen (user_data sammeln)
3. Stichtag-Bar auf neue API umstellen
4. Bestehende Properties migrieren
5. Tests und Validierung
'''
    
    return guide

if __name__ == "__main__":
    print("📋 FINALE ARCHITEKTUR - Integrationshilfe")
    print("=" * 50)
    
    print("🔧 Migration Code erstellt...")
    migration_code = integrate_finale_architecture()
    
    with open("C:/Users/norbe/OneDrive/Dokumente/MyApplication/finale_migration.py", "w", encoding="utf-8") as f:
        f.write(migration_code)
    
    print("📖 Migrationsleitfaden erstellt...")
    guide = create_migration_guide()
    
    with open("C:/Users/norbe/OneDrive/Dokumente/MyApplication/FINALE_MIGRATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Integration vorbereitet!")
    print("📁 Dateien:")
    print("   - finale_migration.py (Code)")
    print("   - FINALE_MIGRATION_GUIDE.md (Anleitung)")
