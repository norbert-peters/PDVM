# 🔐 PDVM V2.0 - AUTHENTICATION & MULTI-TENANCY

**Version:** 1.0  
**Datum:** 30.10.2025  
**Status:** 📋 DESIGN PHASE  
**Autor:** Norbert Peters

---

## 🎯 ÜBERSICHT

### **KERN-ARCHITEKTUR:**

```
┌─────────────────────────────────────────────────────────────┐
│                    LOGIN-PROZESS V2.0                        │
└─────────────────────────────────────────────────────────────┘

1. LOGIN-DIALOG (PyQt5)
   ↓ Email + Passwort
   
2. PdvmUserDatenbank (pdvm_benutzer Tabelle)
   ↓ User-Daten laden (EINMALIG!)
   
3. USER-DATEN weitergeben
   ↓ uid, daten, mandanten_liste
   
4. MANDANTEN-AUSWAHL
   ↓ User wählt Mandant aus Liste
   
5. MANDANTEN-DB LADEN
   ↓ Daten/mandant_001/datenbank.db
   
6. HAUPTANWENDUNG
   ↓ Mit User-Kontext + Mandanten-DB
```

**WICHTIGE PRINZIPIEN:**
- ✅ User-Daten werden **EINMALIG beim Login geladen**
- ✅ User-Daten werden **weitergegeben, nicht erneut gelesen**
- ✅ Security-Profiles verwenden **generische GRUPPE/FELD-Struktur**
- ✅ Jeder Mandant hat **separate SQLite-Datenbank**

---

## 📊 DATENBANK-STRUKTUR

### **ZENTRALE AUTH-DATENBANK**

```
Daten/
└── auth.db                           # Zentrale Authentifizierung
    └── pdvm_benutzer                 # User-Accounts
```

**Tabellen-Schema:**
```sql
CREATE TABLE pdvm_benutzer (
    benutzer TEXT PRIMARY KEY,        -- Email (z.B. admin@super.de)
    passwort TEXT NOT NULL,           -- Verschlüsselter Hash (bcrypt)
    
    -- Standard-Spalten (wie alle anderen Tabellen!)
    uid TEXT,                         -- User-GUID (NICHT PRIMARY KEY!)
    daten TEXT NOT NULL,              -- User-Einstellungen (GRUPPE/FELD)
    name TEXT,                        -- Anzeigename
    historisch INTEGER DEFAULT 0,
    source_hash TEXT,
    sec_id TEXT,
    gilt_bis TEXT DEFAULT '999365.00000',
    created_at TEXT,
    modified_at TEXT
);
```

**WICHTIG:**
- ✅ `benutzer` (Email) = PRIMARY KEY
- ✅ `uid` = User-GUID (normale Spalte, NICHT Primary Key)
- ✅ `daten` = JSON mit GRUPPE/FELD-Struktur
- ✅ Alle Standard-Spalten wie bei anderen Tabellen

---

### **'daten' SPALTE FORMAT (pdvm_benutzer)**

```json
{
    "USER": {
        "NAME": "Max Mustermann",
        "EMAIL": "max@example.com",
        "TELEFON": "+49 123 456789"
    },
    "SETTINGS": {
        "THEME": "dark",
        "LANGUAGE": "DEU",
        "FONT_SIZE": 10,
        "STICHTAG": "2025244.00000"
    },
    "MANDANTEN": {
        "LIST": [
            "mandant_001",
            "mandant_002",
            "mandant_003"
        ],
        "DEFAULT": "mandant_001"
    },
    "PERMISSIONS": {
        "ROLES": [
            "admin",
            "vertrieb"
        ],
        "SEC_PROFILES": [
            "sec-admin-full",
            "sec-vertrieb"
        ]
    }
}
```

---

### **MANDANTEN-DATENBANKEN**

```
Daten/
├── auth.db                           # Zentrale Auth
│
├── mandant_001/                      # Mandant 1
│   └── datenbank.db
│       ├── sys_menudaten             # ⭐ sys_ Präfix!
│       ├── sys_viewdaten
│       ├── sys_framedaten
│       ├── sys_security_profiles     # ⭐ Security-Profile
│       ├── kunde                     # Geschäfts-Tabellen
│       ├── artikel
│       └── ...
│
├── mandant_002/                      # Mandant 2
│   └── datenbank.db
│       └── ... (identische Struktur)
│
└── mandant_003/                      # Mandant 3
    └── datenbank.db
        └── ... (identische Struktur)
```

---

## 🔐 SECURITY-PROFILES TABELLE

**⭐ WICHTIG: Generische Struktur mit sys_ Präfix!**

```sql
CREATE TABLE sys_security_profiles (    -- ⭐ sys_ Präfix!
    uid TEXT PRIMARY KEY,
    daten TEXT NOT NULL,                -- ⭐ GRUPPE/FELD-Struktur!
    name TEXT,
    historisch INTEGER DEFAULT 0,
    source_hash TEXT,
    sec_id TEXT,                        -- Wer darf Profile bearbeiten?
    gilt_bis TEXT DEFAULT '999365.00000',
    created_at TEXT,
    modified_at TEXT
);
```

**'daten' Spalte Format (GRUPPE/FELD):**

```json
{
    "PROFILE": {
        "NAME": "Vertrieb Standard",
        "DESCRIPTION": "Standard-Rechte für Vertriebsmitarbeiter",
        "LEVEL": "STANDARD"
    },
    "PERMISSIONS": {
        "READ_ROLES": ["vertrieb", "admin", "leitung"],
        "WRITE_ROLES": ["vertrieb", "admin"],
        "DELETE_ROLES": ["admin"]
    },
    "RESTRICTIONS": {
        "MAX_DISCOUNT": 10.0,
        "CAN_VIEW_PRICES": true,
        "CAN_EDIT_MASTER_DATA": false
    }
}
```

**Beispiel-Profile:**

```python
# Profile 1: Öffentlich Lesen
{
    "uid": "sec-public-read",
    "name": "Öffentlich Lesen",
    "historisch": 0,
    "sec_id": "sec-admin-full",    # Nur Admin darf bearbeiten
    "daten": {
        "PROFILE": {
            "NAME": "Öffentlich Lesen",
            "DESCRIPTION": "Alle dürfen lesen",
            "LEVEL": "PUBLIC"
        },
        "PERMISSIONS": {
            "READ_ROLES": ["*"],      # Alle!
            "WRITE_ROLES": [],
            "DELETE_ROLES": []
        }
    }
}

# Profile 2: Vertrieb Standard
{
    "uid": "sec-vertrieb",
    "name": "Vertrieb Standard",
    "historisch": 0,
    "sec_id": "sec-admin-full",
    "daten": {
        "PROFILE": {
            "NAME": "Vertrieb Standard",
            "DESCRIPTION": "Standard-Rechte für Vertrieb",
            "LEVEL": "STANDARD"
        },
        "PERMISSIONS": {
            "READ_ROLES": ["vertrieb", "admin", "leitung"],
            "WRITE_ROLES": ["vertrieb", "admin"],
            "DELETE_ROLES": ["admin"]
        },
        "RESTRICTIONS": {
            "MAX_DISCOUNT": 10.0,
            "CAN_VIEW_PRICES": true,
            "CAN_EDIT_MASTER_DATA": false
        }
    }
}

# Profile 3: Admin Vollzugriff
{
    "uid": "sec-admin-full",
    "name": "Admin Vollzugriff",
    "historisch": 0,
    "sec_id": "sec-admin-full",    # Sich selbst
    "daten": {
        "PROFILE": {
            "NAME": "Admin Vollzugriff",
            "DESCRIPTION": "Volle Rechte für Administratoren",
            "LEVEL": "ADMIN"
        },
        "PERMISSIONS": {
            "READ_ROLES": ["admin"],
            "WRITE_ROLES": ["admin"],
            "DELETE_ROLES": ["admin"]
        },
        "RESTRICTIONS": {
            "MAX_DISCOUNT": 100.0,
            "CAN_VIEW_PRICES": true,
            "CAN_EDIT_MASTER_DATA": true
        }
    }
}
```

**ZUGRIFF MIT PdvmCentralDatenbank:**

```python
# Security-Profile laden
from pdvm_central_datenbank import PdvmCentralDatenbank

# Instanz erstellen (für ein spezifisches Profil)
sec_profile = PdvmCentralDatenbank('sys_security_profiles', 'sec-vertrieb')

# GRUPPE/FELD-Zugriff
profile_name = sec_profile.field_value('PROFILE.NAME')
read_roles = sec_profile.field_value('PERMISSIONS.READ_ROLES')
max_discount = sec_profile.field_value('RESTRICTIONS.MAX_DISCOUNT')

print(f"Profil: {profile_name}")
print(f"Lese-Rechte: {read_roles}")
print(f"Max Rabatt: {max_discount}%")
```

---

## 🔄 LOGIN-ABLAUF (DETAILLIERT)

### **PHASE 1: LOGIN-DIALOG**

```python
# pdvm_login.py (angepasst für V2.0)
import bcrypt
import json
from PyQt5.QtWidgets import QDialog, QMessageBox
from pdvm_user_db import PdvmUserDatenbank

class PdvmLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user_data = None  # ⭐ User-Daten für Weitergabe
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen: Email, Passwort, Login-Button"""
        # ... PyQt5 UI Code ...
        self.login_button.clicked.connect(self.on_login_clicked)
    
    def on_login_clicked(self):
        email = self.email_input.text()
        password = self.password_input.text()
        
        # 1. User-Datenbank öffnen (EINMALIG!)
        user_db = PdvmUserDatenbank()
        
        # 2. User laden
        user_row = user_db.lesen(email)
        
        if not user_row:
            QMessageBox.warning(self, "Fehler", "User nicht gefunden!")
            return
        
        # 3. Passwort prüfen (bcrypt)
        if not self._verify_password(password, user_row['passwort']):
            QMessageBox.warning(self, "Fehler", "Falsches Passwort!")
            return
        
        # 4. User-Daten parsen und aufbereiten
        self.user_data = {
            'uid': user_row['uid'],
            'email': email,
            'name': user_row['name'],
            'daten': json.loads(user_row['daten'])  # ⭐ WICHTIG: JSON parsen!
        }
        
        # 5. Dialog schließen (Daten bleiben in self.user_data)
        self.accept()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Passwort mit bcrypt verifizieren"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

---

### **PHASE 2: MANDANTEN-AUSWAHL**

```python
# v2_mandanten_dialog.py (NEU)
import json
from typing import Dict
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel

class V2MandantenDialog(QDialog):
    def __init__(self, user_data: Dict):
        super().__init__()
        self.user_data = user_data
        self.selected_mandant = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen: Mandanten-Dropdown, OK-Button"""
        self.setWindowTitle("Mandant auswählen")
        layout = QVBoxLayout()
        
        # Label
        layout.addWidget(QLabel("Bitte wählen Sie einen Mandanten:"))
        
        # Dropdown
        self.combo_mandanten = QComboBox()
        
        # Mandanten-Liste aus user_data['daten'] holen
        mandanten_list = self.user_data['daten']['MANDANTEN']['LIST']
        default_mandant = self.user_data['daten']['MANDANTEN'].get('DEFAULT')
        
        # Dropdown befüllen
        for mandant_id in mandanten_list:
            mandant_info = self._load_mandant_info(mandant_id)
            self.combo_mandanten.addItem(
                f"{mandant_info['name']} ({mandant_id})",
                mandant_id  # userData
            )
        
        # Default vorauswählen
        if default_mandant:
            index = self.combo_mandanten.findData(default_mandant)
            if index >= 0:
                self.combo_mandanten.setCurrentIndex(index)
        
        layout.addWidget(self.combo_mandanten)
        
        # OK-Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_mandant_selected)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)
    
    def _load_mandant_info(self, mandant_id: str) -> Dict:
        """Lädt Mandanten-Info aus mandanten.json"""
        try:
            with open('Daten/mandanten.json', 'r', encoding='utf-8') as f:
                mandanten = json.load(f)
                return mandanten.get(mandant_id, {'name': mandant_id})
        except:
            return {'name': mandant_id}
    
    def on_mandant_selected(self):
        """Speichert Auswahl und schließt Dialog"""
        self.selected_mandant = self.combo_mandanten.currentData()
        self.accept()
```

---

### **PHASE 3: HAUPTANWENDUNG STARTEN**

```python
# v2_main.py (vereinfacht)
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from pdvm_login import PdvmLoginDialog
from v2_mandanten_dialog import V2MandantenDialog
from v2_main_window import V2MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 1. LOGIN
    login_dialog = PdvmLoginDialog()
    if login_dialog.exec_() != QDialog.Accepted:
        print("Login abgebrochen")
        return
    
    user_data = login_dialog.user_data  # ⭐ EINMALIG geladen!
    print(f"✅ Login erfolgreich: {user_data['name']} ({user_data['email']})")
    
    # 2. MANDANTEN-AUSWAHL
    mandanten_dialog = V2MandantenDialog(user_data)
    if mandanten_dialog.exec_() != QDialog.Accepted:
        print("Mandanten-Auswahl abgebrochen")
        return
    
    selected_mandant = mandanten_dialog.selected_mandant
    print(f"✅ Mandant gewählt: {selected_mandant}")
    
    # 3. MANDANTEN-DB PFAD
    mandant_db_path = f"Daten/{selected_mandant}/datenbank.db"
    
    # 4. HAUPTANWENDUNG STARTEN
    main_window = V2MainWindow(
        user_data=user_data,           # ⭐ Weitergegeben, nicht erneut laden!
        mandant_id=selected_mandant,
        mandant_db_path=mandant_db_path
    )
    
    main_window.show()
    
    print("🚀 Hauptanwendung gestartet")
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

**WICHTIG: User-Daten NICHT erneut laden!**

```python
# ❌ FALSCH - User-Daten erneut laden
class V2MainWindow(QMainWindow):
    def __init__(self, user_data, mandant_id, mandant_db_path):
        super().__init__()
        
        # ❌ FALSCH!
        user_db = PdvmUserDatenbank()
        fresh_data = user_db.lesen(user_data['email'])

# ✅ RICHTIG - User-Daten nutzen wie übergeben
class V2MainWindow(QMainWindow):
    def __init__(self, user_data, mandant_id, mandant_db_path):
        super().__init__()
        
        # ✅ RICHTIG - Daten verwenden!
        self.user_data = user_data
        self.mandant_id = mandant_id
        self.mandant_db_path = mandant_db_path
        
        # Zugriff auf User-Einstellungen
        theme = self.user_data['daten']['SETTINGS']['THEME']
        language = self.user_data['daten']['SETTINGS']['LANGUAGE']
        roles = self.user_data['daten']['PERMISSIONS']['ROLES']
```

---

## 🔧 PdvmUserDatenbank (BESTEHEND - Minimal anpassen)

**Aktueller Stand bleibt weitgehend! Nur kleine Anpassungen:**

```python
# pdvm_user_db.py (minimale Anpassungen für V2.0)
import sqlite3
import uuid
from typing import Dict, Optional
from datetime import datetime

class PdvmUserDatenbank:
    def __init__(self):
        # ⭐ V2.0: Zentrale Auth-DB (nicht mehr aus PdvmInit.json)
        self.db_name = "Daten/auth.db"
        self.table_name = "pdvm_benutzer"
        self._erzeuge_tabelle()
    
    def _erzeuge_tabelle(self):
        """Erstellt pdvm_benutzer Tabelle mit ALLEN Standard-Spalten"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            benutzer TEXT PRIMARY KEY,
            passwort TEXT NOT NULL,
            
            uid TEXT,
            daten TEXT NOT NULL,
            name TEXT,
            historisch INTEGER DEFAULT 0,
            source_hash TEXT,
            sec_id TEXT,
            gilt_bis TEXT DEFAULT '999365.00000',
            created_at TEXT,
            modified_at TEXT
        )'''
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()
    
    def anlegen(self, benutzer: str, passwort_hash: str, daten_dict: Dict, 
                name: str = None) -> bool:
        """
        Neuen User anlegen
        
        Args:
            benutzer: Email
            passwort_hash: bcrypt Hash
            daten_dict: Dict mit USER/SETTINGS/MANDANTEN/PERMISSIONS
            name: Anzeigename
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        uid = str(uuid.uuid4())
        daten_json = json.dumps(daten_dict)
        now = datetime.now().strftime('%Y%j.%H%M%S')
        
        insert_query = f'''
        INSERT INTO {self.table_name}
        (benutzer, passwort, uid, daten, name, created_at, modified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (
            benutzer,
            passwort_hash,
            uid,
            daten_json,
            name or benutzer,
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def lesen(self, benutzer: str) -> Optional[Dict]:
        """
        Liest User-Daten (EINMALIG beim Login!)
        
        Returns:
            {
                'benutzer': 'admin@super.de',
                'passwort': '$2b$12$...',
                'uid': 'guid-user-123',
                'daten': '{"USER": {...}}',  # ⚠️ Als STRING!
                'name': 'Max Mustermann',
                'historisch': 0,
                'sec_id': None,
                'gilt_bis': '999365.00000',
                'created_at': '2025244.120000',
                'modified_at': '2025244.120000'
            }
        """
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        select_query = f'SELECT * FROM {self.table_name} WHERE benutzer = ?'
        cursor.execute(select_query, (benutzer,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    def speichern(self, benutzer: str, daten_dict: Dict) -> bool:
        """
        User-Daten aktualisieren
        
        Args:
            benutzer: Email
            daten_dict: Aktualisierte Daten (USER/SETTINGS/...)
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        daten_json = json.dumps(daten_dict)
        now = datetime.now().strftime('%Y%j.%H%M%S')
        
        update_query = f'''
        UPDATE {self.table_name}
        SET daten = ?, modified_at = ?
        WHERE benutzer = ?
        '''
        
        cursor.execute(update_query, (daten_json, now, benutzer))
        conn.commit()
        conn.close()
        return True
```

---

## 🎯 V2.0 ÄNDERUNGEN

### **WAS BLEIBT:**
✅ PdvmUserDatenbank Klasse (minimal anpassen)  
✅ `pdvm_benutzer` Tabellen-Name  
✅ Email als PRIMARY KEY  
✅ Passwort-Hash (bcrypt)  
✅ Grundlegende Methoden: `anlegen()`, `lesen()`, `speichern()`

### **WAS NEU KOMMT:**

#### **1. Zentrale Auth-DB (separate Datei)**
```python
# V0.9: User in Haupt-DB (aus PdvmInit.json)
self.db_name = self._load_database_from_init()  # "Daten/datenbank.db"

# V2.0: Separate Auth-DB (FEST)
self.db_name = "Daten/auth.db"  # ⭐ FEST codiert!
```

#### **2. Standard-Spalten in pdvm_benutzer**
```sql
-- V0.9: Nur 3 Spalten (benutzerstamm)
CREATE TABLE benutzerstamm (
    benutzer TEXT PRIMARY KEY,
    passwort TEXT NOT NULL,
    daten TEXT NOT NULL
);

-- V2.0: ALLE Standard-Spalten (pdvm_benutzer)
CREATE TABLE pdvm_benutzer (
    benutzer TEXT PRIMARY KEY,
    passwort TEXT NOT NULL,
    
    uid TEXT,              -- ⭐ NEU: User-GUID
    daten TEXT NOT NULL,
    name TEXT,             -- ⭐ NEU: Anzeigename
    historisch INTEGER,    -- ⭐ NEU: Default 0
    source_hash TEXT,      -- ⭐ NEU
    sec_id TEXT,           -- ⭐ NEU
    gilt_bis TEXT,         -- ⭐ NEU: Default '999365.00000'
    created_at TEXT,       -- ⭐ NEU: Erstellungsdatum
    modified_at TEXT       -- ⭐ NEU: Änderungsdatum
);
```

#### **3. Mandanten-Liste in User-Daten**
```json
{
    "MANDANTEN": {
        "LIST": ["mandant_001", "mandant_002"],
        "DEFAULT": "mandant_001"
    }
}
```

#### **4. User-Daten EINMALIG laden (WICHTIG!)**
```python
# ✅ V2.0: Nur beim Login laden!
def main():
    # Login
    login_dialog = PdvmLoginDialog()
    login_dialog.exec_()
    user_data = login_dialog.user_data  # ⭐ EINMALIG laden!
    
    # Weitergabe an Hauptanwendung
    main_window = V2MainWindow(user_data=user_data)
    
    # ❌ NICHT SO:
    # main_window = V2MainWindow(email=user_data['email'])
    # -> Hauptanwendung würde User erneut laden!

# ✅ In Hauptanwendung: Daten NUTZEN, nicht erneut laden!
class V2MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data  # ⭐ Speichern
        
        # Zugriff auf Settings
        theme = self.user_data['daten']['SETTINGS']['THEME']
        roles = self.user_data['daten']['PERMISSIONS']['ROLES']
```

#### **5. sys_ Präfix für System-Tabellen**
```python
# V0.9: Ohne Präfix
'menudaten', 'viewdaten', 'framedaten'

# V2.0: sys_ Präfix
'sys_menudaten', 'sys_viewdaten', 'sys_framedaten', 'sys_security_profiles'
```

---

## 🗂️ MANDANTEN-VERWALTUNG

### **Mandanten-Info-Datei**

```
Daten/mandanten.json             # ⭐ NEU: Zentrale Mandanten-Liste
```

```json
{
    "mandant_001": {
        "name": "Firma ABC GmbH",
        "description": "Hauptmandant",
        "db_path": "Daten/mandant_001/datenbank.db",
        "logo": "mandant_001/logo.png",
        "created_at": "2025100.00000",
        "country": "DEU"
    },
    "mandant_002": {
        "name": "Firma XYZ AG",
        "description": "Zweitmandant",
        "db_path": "Daten/mandant_002/datenbank.db",
        "logo": "mandant_002/logo.png",
        "created_at": "2025200.00000",
        "country": "DEU"
    }
}
```

### **Mandanten-DB erstellen**

```python
import os
import sqlite3
import json
from datetime import datetime

def create_mandant(mandant_id: str, name: str, description: str = None):
    """
    Erstellt neue Mandanten-Datenbank mit allen Standard-Tabellen
    
    Args:
        mandant_id: z.B. "mandant_003"
        name: z.B. "Firma DEF KG"
        description: Optionale Beschreibung
    """
    # 1. Verzeichnis erstellen
    mandant_dir = f"Daten/{mandant_id}"
    os.makedirs(mandant_dir, exist_ok=True)
    print(f"✅ Verzeichnis erstellt: {mandant_dir}")
    
    # 2. Datenbank erstellen
    db_path = f"{mandant_dir}/datenbank.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 3. Standard-Schema für generische Tabellen
    standard_schema = '''
        uid TEXT PRIMARY KEY,
        daten TEXT NOT NULL,
        name TEXT,
        historisch INTEGER DEFAULT 0,
        source_hash TEXT,
        sec_id TEXT,
        gilt_bis TEXT DEFAULT '999365.00000',
        created_at TEXT,
        modified_at TEXT
    '''
    
    # 4. System-Tabellen erstellen (sys_ Präfix)
    system_tables = [
        'sys_menudaten',
        'sys_viewdaten',
        'sys_framedaten',
        'sys_security_profiles',
        'sys_controls'
    ]
    
    for table_name in system_tables:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({standard_schema})')
        print(f"✅ Tabelle erstellt: {table_name}")
    
    # 5. Beispiel Geschäfts-Tabellen (ohne sys_ Präfix)
    business_tables = ['kunde', 'artikel', 'rechnung']
    
    for table_name in business_tables:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({standard_schema})')
        print(f"✅ Tabelle erstellt: {table_name}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Datenbank erstellt: {db_path}")
    
    # 6. Mandanten-Info in mandanten.json speichern
    update_mandanten_json(mandant_id, name, db_path, description)
    print(f"✅ Mandant registriert: {mandant_id}")

def update_mandanten_json(mandant_id: str, name: str, db_path: str, 
                          description: str = None):
    """Aktualisiert mandanten.json"""
    mandanten_file = 'Daten/mandanten.json'
    
    # Bestehende Daten laden
    if os.path.exists(mandanten_file):
        with open(mandanten_file, 'r', encoding='utf-8') as f:
            mandanten = json.load(f)
    else:
        mandanten = {}
    
    # Neuen Mandanten hinzufügen
    now = datetime.now().strftime('%Y%j.00000')
    mandanten[mandant_id] = {
        'name': name,
        'description': description or f"Mandant {mandant_id}",
        'db_path': db_path,
        'logo': f"{mandant_id}/logo.png",
        'created_at': now,
        'country': 'DEU'
    }
    
    # Zurückschreiben
    with open(mandanten_file, 'w', encoding='utf-8') as f:
        json.dump(mandanten, f, ensure_ascii=False, indent=4)

# Beispiel-Aufruf
if __name__ == '__main__':
    create_mandant('mandant_003', 'Firma DEF KG', 'Test-Mandant')
```

---

## 🔐 SECURITY-WORKFLOW

### **Security-Check bei Daten-Zugriff**

```python
import sqlite3
from typing import Dict, List

class V2DatabaseManager:
    """
    Verwaltet Datenbank-Zugriffe mit automatischem Security-Filter
    """
    def __init__(self, mandant_db_path: str, user_data: Dict, stichtag: str):
        self.db_path = mandant_db_path
        self.user_data = user_data
        self.stichtag = stichtag
        
        # User-Rollen extrahieren
        self.user_roles = user_data['daten']['PERMISSIONS']['ROLES']
        self.user_sec_profiles = user_data['daten']['PERMISSIONS']['SEC_PROFILES']
        
        print(f"🔐 Security initialisiert:")
        print(f"   Rollen: {self.user_roles}")
        print(f"   Profiles: {self.user_sec_profiles}")
    
    def get_table_data(self, table: str, additional_filter: str = None) -> List[Dict]:
        """
        Lädt Tabellen-Daten mit automatischem sec_id und gilt_bis Filter
        
        Args:
            table: Tabellen-Name (z.B. 'kunde')
            additional_filter: Optionaler zusätzlicher WHERE-Filter
        
        Returns:
            Liste von Row-Dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # SQL mit sec_id und gilt_bis Filter
        placeholders = ','.join(['?'] * len(self.user_sec_profiles))
        sql = f"""
            SELECT * FROM {table}
            WHERE (gilt_bis >= ? OR gilt_bis = '999365.00000')
              AND sec_id IN ({placeholders})
        """
        
        # Zusätzlichen Filter anhängen
        if additional_filter:
            sql += f" AND {additional_filter}"
        
        # Parameter: Stichtag + sec_profiles
        params = [self.stichtag] + self.user_sec_profiles
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ {len(results)} Datensätze aus {table} geladen (sec_id gefiltert)")
        return results
    
    def check_write_permission(self, table: str, row_sec_id: str) -> bool:
        """
        Prüft Schreib-Berechtigung für einen Datensatz
        
        Args:
            table: Tabellen-Name
            row_sec_id: sec_id des Datensatzes
        
        Returns:
            True wenn User schreiben darf
        """
        # 1. Security-Profile laden
        profile = self._load_security_profile(row_sec_id)
        
        if not profile:
            print(f"⚠️ Security-Profile {row_sec_id} nicht gefunden")
            return False
        
        # 2. WRITE_ROLES prüfen
        write_roles = profile['daten']['PERMISSIONS']['WRITE_ROLES']
        
        # User hat passende Rolle?
        has_permission = any(role in write_roles for role in self.user_roles)
        
        if has_permission:
            print(f"✅ Schreib-Berechtigung: User-Rolle in {write_roles}")
        else:
            print(f"❌ Keine Schreib-Berechtigung: User-Rollen {self.user_roles} nicht in {write_roles}")
        
        return has_permission
    
    def _load_security_profile(self, profile_id: str) -> Dict:
        """Lädt Security-Profile aus sys_security_profiles"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM sys_security_profiles WHERE uid = ?',
            (profile_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            row_dict = dict(result)
            row_dict['daten'] = json.loads(row_dict['daten'])  # JSON parsen
            return row_dict
        
        return None

# BEISPIEL-VERWENDUNG
if __name__ == '__main__':
    user_data = {
        'uid': 'user-123',
        'email': 'vertrieb@firma.de',
        'name': 'Max Vertrieb',
        'daten': {
            'PERMISSIONS': {
                'ROLES': ['vertrieb'],
                'SEC_PROFILES': ['sec-vertrieb', 'sec-public-read']
            }
        }
    }
    
    db = V2DatabaseManager(
        'Daten/mandant_001/datenbank.db',
        user_data,
        '2025305.00000'
    )
    
    # Kunden laden (automatisch gefiltert)
    kunden = db.get_table_data('kunde')
    
    # Schreib-Berechtigung prüfen
    can_write = db.check_write_permission('kunde', 'sec-vertrieb')
```

---

## 📋 MIGRATIONS-PLAN

### **V0.9 → V2.0 Migration (User-Daten)**

```python
import sqlite3
import json
import uuid
from datetime import datetime

def migrate_users_v09_to_v20():
    """
    Migriert User von V0.9 benutzerstamm → V2.0 pdvm_benutzer
    
    SCHRITTE:
    1. Alte DB öffnen (Daten/datenbank.db)
    2. Neue Auth-DB erstellen (Daten/auth.db)
    3. pdvm_benutzer Tabelle mit allen Standard-Spalten erstellen
    4. User kopieren und Daten erweitern
    """
    print("🔄 Starte User-Migration V0.9 → V2.0")
    
    # 1. Alte DB öffnen
    old_db = sqlite3.connect("Daten/datenbank.db")
    old_cursor = old_db.cursor()
    
    # 2. Neue Auth-DB erstellen
    new_db = sqlite3.connect("Daten/auth.db")
    new_cursor = new_db.cursor()
    
    # 3. pdvm_benutzer Tabelle erstellen
    new_cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdvm_benutzer (
            benutzer TEXT PRIMARY KEY,
            passwort TEXT NOT NULL,
            uid TEXT,
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
    
    print("✅ pdvm_benutzer Tabelle erstellt")
    
    # 4. User kopieren
    old_cursor.execute("SELECT * FROM benutzerstamm")
    migrated_count = 0
    
    for row in old_cursor.fetchall():
        benutzer, passwort, old_daten = row
        
        # Alte Daten parsen
        try:
            daten_dict = json.loads(old_daten)
        except:
            daten_dict = {}
        
        # Mandanten-Liste hinzufügen (falls nicht vorhanden)
        if 'MANDANTEN' not in daten_dict:
            daten_dict['MANDANTEN'] = {
                'LIST': ['mandant_001'],  # Default
                'DEFAULT': 'mandant_001'
            }
        
        # PERMISSIONS hinzufügen (falls nicht vorhanden)
        if 'PERMISSIONS' not in daten_dict:
            daten_dict['PERMISSIONS'] = {
                'ROLES': ['admin'],  # Default: Admin
                'SEC_PROFILES': ['sec-admin-full']
            }
        
        # SETTINGS hinzufügen (falls nicht vorhanden)
        if 'SETTINGS' not in daten_dict:
            daten_dict['SETTINGS'] = {
                'THEME': 'light',
                'LANGUAGE': 'DEU',
                'FONT_SIZE': 10
            }
        
        # UID generieren
        uid = str(uuid.uuid4())
        
        # Name extrahieren
        name = daten_dict.get('USER', {}).get('NAME', benutzer)
        
        # Timestamp
        now = datetime.now().strftime('%Y%j.%H%M%S')
        
        # In neue DB einfügen
        new_cursor.execute('''
            INSERT INTO pdvm_benutzer 
            (benutzer, passwort, uid, daten, name, historisch, 
             gilt_bis, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            benutzer,
            passwort,
            uid,
            json.dumps(daten_dict, ensure_ascii=False),
            name,
            0,
            '999365.00000',
            now,
            now
        ))
        
        migrated_count += 1
        print(f"✅ User migriert: {benutzer} ({name})")
    
    new_db.commit()
    new_db.close()
    old_db.close()
    
    print(f"🎉 Migration abgeschlossen: {migrated_count} User migriert")

# BEISPIEL-AUFRUF
if __name__ == '__main__':
    migrate_users_v09_to_v20()
```

### **V0.9 → V2.0 Migration (Datenbank-Struktur)**

```python
def migrate_database_v09_to_v20(mandant_id: str = 'mandant_001'):
    """
    Migriert Datenbank-Struktur von V0.9 → V2.0
    
    SCHRITTE:
    1. Alte DB kopieren nach Daten/mandant_XXX/datenbank.db
    2. Tabellen umbenennen (sys_ Präfix für System-Tabellen)
    3. sys_security_profiles Tabelle erstellen
    """
    import shutil
    
    print(f"🔄 Starte DB-Migration V0.9 → V2.0 (Mandant: {mandant_id})")
    
    # 1. Verzeichnis erstellen
    mandant_dir = f"Daten/{mandant_id}"
    os.makedirs(mandant_dir, exist_ok=True)
    
    # 2. Alte DB kopieren
    old_db_path = "Daten/datenbank.db"
    new_db_path = f"{mandant_dir}/datenbank.db"
    shutil.copy2(old_db_path, new_db_path)
    print(f"✅ DB kopiert: {new_db_path}")
    
    # 3. Neue DB öffnen
    conn = sqlite3.connect(new_db_path)
    cursor = conn.cursor()
    
    # 4. System-Tabellen umbenennen (sys_ Präfix)
    system_tables = {
        'menudaten': 'sys_menudaten',
        'viewdaten': 'sys_viewdaten',
        'framedaten': 'sys_framedaten',
        'controls': 'sys_controls'
    }
    
    for old_name, new_name in system_tables.items():
        try:
            cursor.execute(f'ALTER TABLE {old_name} RENAME TO {new_name}')
            print(f"✅ Tabelle umbenannt: {old_name} → {new_name}")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Fehler bei {old_name}: {e}")
    
    # 5. sys_security_profiles Tabelle erstellen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sys_security_profiles (
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
    print("✅ sys_security_profiles Tabelle erstellt")
    
    # 6. Default Security-Profiles einfügen
    now = datetime.now().strftime('%Y%j.%H%M%S')
    
    default_profiles = [
        {
            'uid': 'sec-admin-full',
            'name': 'Admin Vollzugriff',
            'daten': {
                'PROFILE': {'NAME': 'Admin Vollzugriff', 'LEVEL': 'ADMIN'},
                'PERMISSIONS': {
                    'READ_ROLES': ['admin'],
                    'WRITE_ROLES': ['admin'],
                    'DELETE_ROLES': ['admin']
                }
            }
        },
        {
            'uid': 'sec-public-read',
            'name': 'Öffentlich Lesen',
            'daten': {
                'PROFILE': {'NAME': 'Öffentlich Lesen', 'LEVEL': 'PUBLIC'},
                'PERMISSIONS': {
                    'READ_ROLES': ['*'],
                    'WRITE_ROLES': [],
                    'DELETE_ROLES': []
                }
            }
        }
    ]
    
    for profile in default_profiles:
        cursor.execute('''
            INSERT INTO sys_security_profiles
            (uid, daten, name, historisch, gilt_bis, created_at, modified_at, sec_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile['uid'],
            json.dumps(profile['daten'], ensure_ascii=False),
            profile['name'],
            0,
            '999365.00000',
            now,
            now,
            'sec-admin-full'
        ))
        print(f"✅ Security-Profile erstellt: {profile['name']}")
    
    conn.commit()
    conn.close()
    
    print(f"🎉 DB-Migration abgeschlossen: {new_db_path}")

# BEISPIEL-AUFRUF
if __name__ == '__main__':
    migrate_database_v09_to_v20('mandant_001')
```

---

## 🎯 ZUSAMMENFASSUNG

### **KERN-PRINZIPIEN:**
1. ✅ **Zentrale Auth-DB** (`Daten/auth.db`) - User-Verwaltung getrennt
2. ✅ **Separate DB pro Mandant** (`Daten/mandant_XXX/datenbank.db`)
3. ✅ **User-Daten EINMALIG laden** - Nur beim Login, dann weitergeben
4. ✅ **Security-Profiles als generische Tabelle** - GRUPPE/FELD-Struktur
5. ✅ **sys_ Präfix** - System-Tabellen klar erkennbar

### **CODE-ÄNDERUNGEN:**
| Datei | Änderung | Status |
|-------|----------|--------|
| `pdvm_user_db.py` | Neue Spalten, zentrale Auth-DB | ⚠️ Minimal |
| `pdvm_login.py` | User-Daten weitergeben statt Email | ⚠️ Mittel |
| `v2_mandanten_dialog.py` | Mandanten-Auswahl Dialog | 🆕 NEU |
| `v2_main.py` | User-Daten + Mandant-DB übergeben | ⚠️ Mittel |
| `v2_database_manager.py` | Security-Filter automatisch | 🆕 NEU |

### **VORTEILE:**
✅ **Saubere Mandantentrennung** - Keine Daten-Vermischung  
✅ **Zentrale User-Verwaltung** - Ein Login für alle Mandanten  
✅ **Flexible Security-Profiles** - Granulare Rechteverwaltung  
✅ **Performance** - User-Daten nur 1x laden, nicht bei jedem Zugriff  
✅ **Skalierbarkeit** - Neue Mandanten ohne Code-Änderung  

### **MIGRATIONS-AUFWAND:**
| Komponente | Aufwand | Beschreibung |
|------------|---------|--------------|
| User-Daten | 🟢 Niedrig | Script vorhanden, automatisch |
| DB-Struktur | 🟢 Niedrig | Tabellen umbenennen, neue Tabellen |
| Code-Anpassungen | 🟡 Mittel | Login-Flow, Mandanten-Dialog |
| Testing | 🟡 Mittel | Multi-Mandanten Tests nötig |

### **NÄCHSTE SCHRITTE:**
1. ✅ Dokumentation komplett (diese Datei)
2. ⏳ Migrations-Scripts testen
3. ⏳ V2 Login-Flow implementieren
4. ⏳ Mandanten-Dialog implementieren
5. ⏳ Security-Filter testen
6. ⏳ Integration mit V2 Menu-System

---

**Diese Dokumentation beschreibt die vollständige V2.0 Auth- & Multi-Tenancy-Architektur!** 🎯
