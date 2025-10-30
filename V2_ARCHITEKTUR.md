# 🏗️ PDVM V2.0 - SYSTEM-ARCHITEKTUR

**Version:** 1.0  
**Datum:** 30.10.2025  
**Status:** 📋 DESIGN PHASE  
**Autor:** Norbert Peters

---

## 📋 INHALTSVERZEICHNIS

1. [Übersicht](#übersicht)
2. [Architektur-Prinzipien](#architektur-prinzipien)
3. [System-Komponenten](#system-komponenten)
4. [Datenbank-Architektur](#datenbank-architektur)
5. [Security-Konzept](#security-konzept)
6. [API-Design](#api-design)
7. [Migration von V0.9](#migration-von-v09)

---

## 🎯 ÜBERSICHT

### **ZIEL:** Vereinfachte, lineare Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    PDVM V2.0 ARCHITEKTUR                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐
│  Login-Service   │◄────►│  Auth-Server     │
│  (PyQt5 Client)  │      │  (FastAPI/HTTP)  │
└────────┬─────────┘      └──────────────────┘
         │
         │ JWT Token + Mandanten-Liste
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    HAUPTANWENDUNG                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ UI-Layer     │  │ Business     │  │ Data-Layer   │      │
│  │              │  │ Logic        │  │              │      │
│  │ - Views      │◄─┤              │◄─┤ - Database   │      │
│  │ - Dialoge    │  │ - Menu       │  │ - Security   │      │
│  │ - Controls   │  │ - Commands   │  │ - Migration  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │
         │ SQL Queries mit sec_id Filter
         ▼
┌─────────────────────────────────────────────────────────────┐
│              DATENBANK (SQLite pro Mandant)                  │
│  ┌──────────────────┐       ┌──────────────────┐           │
│  │ System-Tabellen  │       │ User-Tabellen    │           │
│  │ (sys_ Prefix)    │       │ (ohne Prefix)    │           │
│  │                  │       │                  │           │
│  │ - sys_menudaten  │       │ - kunde          │           │
│  │ - sys_viewdaten  │       │ - artikel        │           │
│  │ - sys_framedaten │       │ - rechnung       │           │
│  │ - sys_users      │       │ - ...            │           │
│  └──────────────────┘       └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 ARCHITEKTUR-PRINZIPIEN

### **1. SEPARATION OF CONCERNS**
```
UI ──► Business Logic ──► Data Access ──► Database
```
- **UI-Layer:** Nur Darstellung und User-Input
- **Business-Logic:** Validierung, Workflows, Berechtigungen
- **Data-Layer:** SQL-Queries, Transaktionen, Caching

### **2. SINGLE RESPONSIBILITY**
- Jede Klasse/Modul hat **EINE** klar definierte Aufgabe
- Keine "God-Classes" die alles machen

### **3. DEPENDENCY INJECTION**
```python
# ❌ V0.9: Direkte Abhängigkeiten
class ViewController:
    def __init__(self):
        self.gcs = get_gcs()  # Globale Abhängigkeit!
        self.db = PdvmDatenbank()  # Fest verdrahtet!

# ✅ V2.0: Injected Dependencies
class V2ViewController:
    def __init__(self, database: V2Database, security: V2Security):
        self.db = database  # Übergeben!
        self.security = security  # Testbar!
```

### **4. INTERFACE-BASED DESIGN**
```python
# Abstract Base Classes für austauschbare Implementierungen
class DatabaseInterface(ABC):
    @abstractmethod
    def query(self, sql: str) -> List[Dict]: pass

class SQLiteDatabase(DatabaseInterface):  # Implementierung 1
    def query(self, sql: str) -> List[Dict]: ...

class PostgresDatabase(DatabaseInterface):  # Implementierung 2
    def query(self, sql: str) -> List[Dict]: ...
```

### **5. LINEARE DATENFLÜSSE**
```
Keine zirkulären Abhängigkeiten!
Keine verschachtelten Callbacks!
Klare, nachvollziehbare Abläufe!
```

---

## 🧩 SYSTEM-KOMPONENTEN

### **LAYER 1: AUTHENTICATION (Neue Komponente)**

```
v2_auth_service/
├── __init__.py
├── server.py              # FastAPI Server
├── models.py              # User, Mandant, Session Models
├── jwt_handler.py         # JWT Token Generation/Validation
└── database.py            # sys_users, sys_mandanten DB
```

**Aufgaben:**
- ✅ User-Login mit Email/Password
- ✅ JWT Token generieren
- ✅ Mandanten-Liste für User laden
- ✅ Session-Management
- ✅ 2-Faktor-Authentifizierung (später)

**API-Endpunkte:**
```
POST   /api/auth/login        # Login
POST   /api/auth/refresh      # Token erneuern
GET    /api/auth/mandanten    # Mandanten-Liste
POST   /api/auth/logout       # Logout
```

---

### **LAYER 2: CORE SYSTEM**

```
v2_core/
├── __init__.py
├── database_manager.py    # Zentrale DB-Verwaltung
├── security_manager.py    # sec_id Berechtigungen
├── menu_system.py         # LINEAR! Keine Multi-Tree
├── command_dispatcher.py  # Einheitliche Command-Ausführung
└── config.py              # System-Konfiguration
```

#### **2.1 Database Manager**
```python
class V2DatabaseManager:
    """
    Zentrale Datenbank-Verwaltung mit sys_ Tabellen
    """
    def __init__(self, mandant_id: str, user_guid: str):
        self.mandant_id = mandant_id
        self.user_guid = user_guid
        self.db_path = f"Daten/{mandant_id}/datenbank.db"
        
    def get_table_data(
        self, 
        table: str, 
        filters: Dict = None,
        apply_security: bool = True
    ) -> List[Dict]:
        """
        Lade Tabellen-Daten mit optionalem Security-Filter
        """
        if apply_security:
            filters = self._add_security_filter(filters)
        
        # SQL Query mit sys_ Präfix für System-Tabellen
        if table.startswith('sys_'):
            return self._query_system_table(table, filters)
        else:
            return self._query_user_table(table, filters)
```

**Vorteile:**
- ✅ Einheitliche DB-API
- ✅ Automatische Security-Filter
- ✅ sys_ vs. User-Tabellen Trennung
- ✅ Connection-Pooling (später)
- ✅ Transaction-Management

#### **2.2 Security Manager**
```python
class V2SecurityManager:
    """
    Verwaltet sec_id basierte Berechtigungen
    """
    def __init__(self, user_guid: str):
        self.user_guid = user_guid
        self.user_roles = self._load_user_roles()
    
    def check_access(
        self, 
        sec_id: str, 
        operation: str  # 'read', 'write', 'delete'
    ) -> bool:
        """
        Prüft ob User Zugriff auf Datensatz hat
        """
        profile = self._get_security_profile(sec_id)
        
        if operation == 'read':
            return any(role in profile.read_roles for role in self.user_roles)
        elif operation == 'write':
            return any(role in profile.write_roles for role in self.user_roles)
        elif operation == 'delete':
            return any(role in profile.delete_roles for role in self.user_roles)
        
        return False
```

**Security-Profiles Tabelle:**
```sql
CREATE TABLE sys_security_profiles (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL,           -- "Vertrieb Lesen"
    description TEXT,
    read_roles TEXT,              -- JSON: ["vertrieb", "admin"]
    write_roles TEXT,             -- JSON: ["admin"]
    delete_roles TEXT,            -- JSON: ["admin"]
    created_at REAL,
    modified_at REAL
);
```

#### **2.3 Menu System (LINEAR!)**
```python
class V2MenuSystem:
    """
    Lineares Menü-System - KEIN Multi-Tree mehr!
    """
    def __init__(self, database: V2DatabaseManager):
        self.db = database
        self.menu_items = []  # Flache Liste!
    
    def load_menu(self, menu_guid: str):
        """
        Lädt Menü aus sys_menudaten
        """
        menu_items = self.db.get_table_data('sys_menudaten', {'menu_guid': menu_guid})
        
        # Flache Liste mit Parent-Referenzen
        self.menu_items = sorted(menu_items, key=lambda x: x['sort_order'])
    
    def get_menu_tree(self) -> List[Dict]:
        """
        Baut Baum-Struktur aus flacher Liste
        """
        return self._build_tree(self.menu_items, parent_id=None)
```

**Menü-Datenstruktur (LINEAR!):**
```json
[
    {
        "uid": "menu-1",
        "parent_id": null,
        "name": "Datei",
        "command": null,
        "sort_order": 0,
        "icon": "folder",
        "menu_type": "horizontal"
    },
    {
        "uid": "menu-2",
        "parent_id": "menu-1",
        "name": "Neu",
        "command": "file.new",
        "sort_order": 0,
        "icon": "file-plus",
        "menu_type": "horizontal"
    },
    {
        "uid": "menu-3",
        "parent_id": "menu-1",
        "name": "Öffnen",
        "command": "file.open",
        "sort_order": 1,
        "icon": "folder-open",
        "menu_type": "horizontal"
    }
]
```

**Vorteile:**
- ✅ Einfache Datenstruktur
- ✅ Leicht zu editieren (Standard-View mit Controls!)
- ✅ Sortierung via `sort_order` Feld
- ✅ Keine Template-Komplexität
- ✅ Parent-Referenzen statt verschachtelter Dicts

#### **2.4 Command Dispatcher**
```python
class V2CommandDispatcher:
    """
    Einheitliche Command-Ausführung
    """
    def __init__(self, main_app):
        self.main_app = main_app
        self.commands = {}  # Command-Registry
    
    def register_command(self, name: str, handler: Callable):
        """
        Registriert Command-Handler
        """
        self.commands[name] = handler
    
    def execute(self, command: str, **kwargs):
        """
        Führt Command aus
        """
        if command not in self.commands:
            raise ValueError(f"Unbekannter Command: {command}")
        
        handler = self.commands[command]
        return handler(**kwargs)
```

**Command-Registration:**
```python
# Bei Startup
dispatcher = V2CommandDispatcher(main_app)

# Commands registrieren
dispatcher.register_command('file.new', lambda: main_app.new_file())
dispatcher.register_command('file.open', lambda: main_app.open_file())
dispatcher.register_command('view.customer', lambda: main_app.open_view('kunde'))

# Aus Menü ausführen
menu_item = {"command": "file.new"}
dispatcher.execute(menu_item["command"])
```

---

### **LAYER 3: UI-LAYER**

```
v2_ui/
├── __init__.py
├── main_window.py         # Hauptfenster
├── view_controller.py     # ✅ AUS V0.9 ÜBERNEHMEN!
├── dialog_manager.py      # Dialog-Verwaltung
├── matrix_pipeline.py     # ✅ AUS V0.9 ÜBERNEHMEN!
├── view_widget.py         # Tabellen-Ansicht
└── menu_renderer.py       # Menü-Darstellung
```

**WICHTIG:** Viele UI-Komponenten aus V0.9 sind **PERFEKT** und werden 1:1 übernommen:
- ✅ Matrix-Pipeline (BasisMatrix → Filter → Sort → Project)
- ✅ View-Controller (mit Anpassungen)
- ✅ View-Widget mit Tooltips
- ✅ Schnellsuche-System
- ✅ Filter-Manager

**NUR ANPASSEN:**
- Menu-Rendering (für lineares System)
- Command-Ausführung (via Dispatcher)
- Database-Zugriff (via V2DatabaseManager)

---

## 💾 DATENBANK-ARCHITEKTUR

### **STRUKTUR: Mandanten-basiert**

```
Daten/
├── auth_server.db                    # Zentrale Auth-DB
│   ├── sys_users                     # User-Accounts
│   ├── sys_mandanten                 # Mandanten-Liste
│   └── sys_user_mandanten            # User → Mandant Mapping
│
├── mandant_001/                      # Mandant 1
│   └── datenbank.db
│       ├── sys_menudaten             # System-Tabellen
│       ├── sys_viewdaten
│       ├── sys_framedaten
│       ├── kunde                     # User-Tabellen
│       ├── artikel
│       └── ...
│
└── mandant_002/                      # Mandant 2
    └── datenbank.db
        └── ... (gleiche Struktur)
```

### **TABELLEN-KONVENTIONEN**

#### **System-Tabellen (sys_ Prefix)**
```sql
-- Menü-Daten (LINEAR!)
CREATE TABLE sys_menudaten (
    uid TEXT PRIMARY KEY,
    parent_id TEXT,               -- Referenz zu anderem Menü-Eintrag
    name TEXT NOT NULL,
    command TEXT,                 -- z.B. "file.new"
    sort_order INTEGER DEFAULT 0,
    icon TEXT,
    menu_type TEXT,               -- 'horizontal', 'vertical'
    sec_id TEXT,                  -- Berechtigungen für Menü-Eintrag
    created_at REAL,
    modified_at REAL,
    FOREIGN KEY (parent_id) REFERENCES sys_menudaten(uid)
);

-- View-Definitionen
CREATE TABLE sys_viewdaten (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_table TEXT NOT NULL,
    view_type TEXT,               -- 'table', 'tree', 'calendar'
    sec_id TEXT,
    controls TEXT,                -- JSON: Control-Definitionen
    created_at REAL,
    modified_at REAL
);

-- Security-Profiles
CREATE TABLE sys_security_profiles (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    read_roles TEXT,              -- JSON: ["role1", "role2"]
    write_roles TEXT,
    delete_roles TEXT,
    created_at REAL,
    modified_at REAL
);
```

#### **User-Tabellen (OHNE Prefix + sec_id)**
```sql
-- Beispiel: Kunden-Tabelle
CREATE TABLE kunde (
    uid TEXT PRIMARY KEY,
    sec_id TEXT NOT NULL,         -- ⭐ NEU: Security-Profile
    name TEXT,
    vorname TEXT,
    email TEXT,
    created_at REAL,
    modified_at REAL,
    FOREIGN KEY (sec_id) REFERENCES sys_security_profiles(uid)
);

-- Beispiel: Artikel-Tabelle
CREATE TABLE artikel (
    uid TEXT PRIMARY KEY,
    sec_id TEXT NOT NULL,         -- ⭐ NEU: Security-Profile
    artikelnummer TEXT,
    bezeichnung TEXT,
    preis REAL,
    created_at REAL,
    modified_at REAL,
    FOREIGN KEY (sec_id) REFERENCES sys_security_profiles(uid)
);
```

---

## 🔐 SECURITY-KONZEPT

### **3-EBENEN SECURITY**

```
EBENE 1: LOGIN (Auth-Server)
    ↓ JWT Token
EBENE 2: MANDANT (Mandanten-Auswahl)
    ↓ Mandanten-DB geladen
EBENE 3: DATENSATZ (sec_id Check)
    ↓ SQL WHERE sec_id IN (...)
DATEN ZUGRIFF
```

### **Security-Profile Beispiele**

```python
# Profile: "Öffentlich Lesen"
{
    "uid": "sec-public-read",
    "name": "Öffentlich Lesen",
    "read_roles": ["*"],          # Alle
    "write_roles": [],
    "delete_roles": []
}

# Profile: "Vertrieb"
{
    "uid": "sec-sales",
    "name": "Vertrieb Standard",
    "read_roles": ["vertrieb", "admin"],
    "write_roles": ["vertrieb", "admin"],
    "delete_roles": ["admin"]
}

# Profile: "Admin Vollzugriff"
{
    "uid": "sec-admin-full",
    "name": "Admin Vollzugriff",
    "read_roles": ["admin"],
    "write_roles": ["admin"],
    "delete_roles": ["admin"]
}
```

### **Automatische Filter-Integration**

```python
# V2DatabaseManager fügt automatisch Security-Filter hinzu
def get_table_data(self, table: str, filters: Dict = None):
    # User-Rollen laden
    user_roles = self.security.user_roles
    
    # Alle sec_ids die User sehen darf
    allowed_sec_ids = self._get_allowed_sec_ids(user_roles, operation='read')
    
    # SQL WHERE Clause erweitern
    sql = f"SELECT * FROM {table} WHERE sec_id IN ({allowed_sec_ids})"
    
    # Weitere Filter hinzufügen
    if filters:
        sql += f" AND {self._build_filter_clause(filters)}"
    
    return self._execute_query(sql)
```

---

## 🔌 API-DESIGN

### **Auth-Service REST API**

```
BASE URL: http://localhost:8000/api
```

#### **1. Login**
```http
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secret123"
}

Response 200:
{
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "uid": "user-guid",
        "email": "user@example.com",
        "name": "Max Mustermann"
    }
}
```

#### **2. Mandanten-Liste laden**
```http
GET /api/auth/mandanten
Authorization: Bearer eyJhbGci...

Response 200:
{
    "mandanten": [
        {
            "uid": "mandant-001",
            "name": "Firma ABC GmbH",
            "db_path": "Daten/mandant_001/datenbank.db"
        },
        {
            "uid": "mandant-002",
            "name": "Firma XYZ AG",
            "db_path": "Daten/mandant_002/datenbank.db"
        }
    ]
}
```

#### **3. Token erneuern**
```http
POST /api/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGci..."
}

Response 200:
{
    "access_token": "eyJhbGci...",
    "expires_in": 3600
}
```

---

## 🔄 MIGRATION VON V0.9

### **PHASE 1: Tabellen umbenennen**
```sql
-- System-Tabellen
ALTER TABLE menudaten RENAME TO sys_menudaten_old;
ALTER TABLE viewdaten RENAME TO sys_viewdaten_old;
ALTER TABLE framedaten RENAME TO sys_framedaten_old;

-- Neue Struktur erstellen
CREATE TABLE sys_menudaten (...);  -- Mit parent_id statt Multi-Tree
CREATE TABLE sys_viewdaten (...);
```

### **PHASE 2: Menü-Struktur konvertieren**
```python
def migrate_menu_structure(old_menu_data):
    """
    Konvertiert Multi-Tree zu Linear mit parent_id
    """
    new_items = []
    
    # PD_grund verarbeiten
    for key, value in old_menu_data.get('PD_grund', {}).items():
        new_items.append({
            'uid': generate_guid(),
            'parent_id': None,
            'name': key,
            'command': old_menu_data['PD_commands'].get(key.replace('.', '_')),
            'sort_order': len(new_items),
            'menu_type': 'horizontal'
        })
    
    # Submenüs rekursiv verarbeiten
    # ...
    
    return new_items
```

### **PHASE 3: sec_id hinzufügen**
```sql
-- Alle User-Tabellen erweitern
ALTER TABLE kunde ADD COLUMN sec_id TEXT;
ALTER TABLE artikel ADD COLUMN sec_id TEXT;

-- Default-Profile zuweisen
UPDATE kunde SET sec_id = 'sec-public-read' WHERE sec_id IS NULL;
UPDATE artikel SET sec_id = 'sec-public-read' WHERE sec_id IS NULL;
```

### **PHASE 4: Daten migrieren**
```python
# migrations/migrate_v09_to_v20.py
def migrate_database(source_db: str, target_db: str):
    """
    Migriert V0.9 Datenbank zu V2.0 Format
    """
    # 1. System-Tabellen umbenennen
    rename_system_tables()
    
    # 2. Menü-Struktur konvertieren
    migrate_menu_structure()
    
    # 3. sec_id Spalten hinzufügen
    add_security_columns()
    
    # 4. Default-Profile erstellen
    create_default_security_profiles()
    
    # 5. Validierung
    validate_migration()
```

---

## 📊 VERGLEICH V0.9 vs V2.0

| Feature | V0.9 | V2.0 |
|---------|------|------|
| **Menü-System** | Multi-Tree (PD_grund/menu/zusatz) | Linear mit parent_id |
| **Commands** | Dict in JSON | Command-Dispatcher |
| **Tabellen** | Gemischt | sys_ Prefix für System |
| **Security** | User-Level | Datensatz-Level (sec_id) |
| **Login** | Direkt in DB | HTTP Auth-Service |
| **Mandanten** | Keine Trennung | Multi-Tenancy |
| **Dependencies** | Global (GCS) | Dependency Injection |
| **Testing** | Schwierig | Testbar (Interfaces) |

---

## 🎯 NÄCHSTE SCHRITTE

1. ✅ V2_ARCHITEKTUR.md erstellt ← **WIR SIND HIER**
2. ⏳ V2_MENU_SYSTEM.md - Detailliertes Menü-Design
3. ⏳ V2_AUTH_SERVICE.md - Auth-Service Implementierung
4. ⏳ V2_DATABASE_SCHEMA.md - Vollständiges DB-Schema
5. ⏳ Prototypen entwickeln

---

**Fragen? Anmerkungen? Änderungswünsche?** 🚀
