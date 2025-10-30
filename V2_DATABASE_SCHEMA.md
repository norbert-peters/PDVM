# 🗄️ PDVM V2.0 - DATENBANK-SCHEMA & DATEN-MODELL

**Version:** 1.0  
**Datum:** 30.10.2025  
**Status:** 📋 DESIGN PHASE  
**Autor:** Norbert Peters

---

## 🎯 KERN-KONZEPT: Generisches Container-Modell

### **PHILOSOPHIE:**
```
Datenbank = CONTAINER für Daten
Schema = DEFINIERT durch Controls (nicht durch DB-Spalten!)
Flexibilität = Neue Felder OHNE ALTER TABLE
```

---

## 📋 STANDARD-TABELLEN-STRUKTUR

**ALLE Tabellen (außer `pdvm_benutzer`) haben IDENTISCHE Struktur:**

```sql
CREATE TABLE <tabellenname> (
    uid TEXT PRIMARY KEY,              -- GUID für eindeutige Identifizierung
    daten TEXT NOT NULL,               -- JSON: Gruppen/Feld-Struktur (KERN!)
    name TEXT,                         -- Freie Bezeichnung für Datensatz
    historisch INTEGER,                -- 0 = keine Historie, 1 = mit Historie
    source_hash TEXT,                  -- Reserviert (vorerst nicht verwendet)
    sec_id TEXT,                       -- Zugriffsberechtigung (GUID)
    gilt_bis TEXT,                     -- PdvmDateTime (999365.00000 = offen)
    created_at TEXT,                   -- PdvmDateTime (Erstellung)
    modified_at TEXT                   -- PdvmDateTime (letzte Änderung)
);
```

### **BEISPIELE:**
```sql
-- System-Tabellen (GLEICHE Struktur!)
CREATE TABLE menudaten (...);          -- Menü-Definitionen
CREATE TABLE viewdaten (...);          -- View-Definitionen
CREATE TABLE framedaten (...);         -- Frame-Definitionen

-- User-Tabellen (GLEICHE Struktur!)
CREATE TABLE kunde (...);              -- Kundendaten
CREATE TABLE artikel (...);            -- Artikeldaten
CREATE TABLE rechnung (...);           -- Rechnungsdaten
```

---

## 🔑 AUSNAHME: pdvm_benutzer

**EINZIGE Tabelle mit abweichender Struktur:**

```sql
CREATE TABLE pdvm_benutzer (
    benutzer TEXT PRIMARY KEY,         -- Email-Adresse (z.B. admin@super.de)
    passwort TEXT NOT NULL,            -- Verschlüsselter Hash (bcrypt)
    
    -- Standard-Spalten (wie andere Tabellen)
    uid TEXT,                          -- GUID (NICHT PRIMARY KEY!)
    daten TEXT NOT NULL,               -- User-Einstellungen, Präferenzen
    name TEXT,                         -- Anzeigename
    historisch INTEGER,
    source_hash TEXT,
    sec_id TEXT,
    gilt_bis TEXT,
    created_at TEXT,
    modified_at TEXT
);
```

**BESONDERHEIT:**
- `benutzer` (Email) ist PRIMARY KEY (statt `uid`)
- `uid` ist normale Spalte
- Für Authentifizierung
- Eigene Datenbank-Instanz pro User

---

## 📊 'daten' SPALTE - GRUPPEN/FELD-STRUKTUR

### **NAMENSKONVENTIONEN:**
- **GRUPPE:** GROSSBUCHSTABEN (z.B. `STAMM`, `ADRESSE`)
- **FELD:** GROSSBUCHSTABEN (z.B. `NAME`, `EMAIL`)
- **Tabellennamen:** kleinbuchstaben (z.B. `kunde`, `artikel`)

### **FORMAT: historisch = 0 (KEINE Historie)**

```json
{
    "STAMM": {
        "NAME": "Mustermann",
        "VORNAME": "Max",
        "EMAIL": "max@example.com"
    },
    "ADRESSE": {
        "STRASSE": "Hauptstr. 1",
        "PLZ": "12345",
        "ORT": "Berlin"
    },
    "FINANZEN": {
        "UMSATZ": 50000.00,
        "KATEGORIE": "A"
    }
}
```

**Struktur:**
```
GRUPPE.FELD.Wert

Beispiel:
STAMM.NAME = "Mustermann"
ADRESSE.ORT = "Berlin"
```

---

### **FORMAT: historisch = 1 (MIT Historie)**

```json
{
    "STAMM": {
        "NAME": {
            "2024100.12345": "Müller",         -- Alter Wert
            "2025244.15678": "Mustermann"      -- Aktueller Wert
        },
        "EMAIL": {
            "2024100.12345": "old@example.com",
            "2025244.15678": "new@example.com"
        }
    },
    "ADRESSE": {
        "ORT": {
            "2024100.00000": "Hamburg",
            "2025244.00000": "Berlin"
        }
    }
}
```

**Struktur:**
```
GRUPPE.FELD.Abdatum.Wert

Beispiel:
STAMM.NAME.2025244.15678 = "Mustermann"
STAMM.EMAIL.2025244.15678 = "new@example.com"

Historische Werte:
STAMM.NAME.2024100.12345 = "Müller"
```

**ZUGRIFF:**
```python
# Aktuellen Wert holen (höchstes Abdatum)
def get_current_value(daten, gruppe, feld):
    field_data = daten[gruppe][feld]
    
    if isinstance(field_data, dict):  # Historisch
        latest_abdatum = max(field_data.keys())
        return field_data[latest_abdatum], latest_abdatum
    else:  # Nicht historisch
        return field_data, None
```

---

## 🔐 SECURITY & GÜLTIGKEIT

### **sec_id - Zugriffsberechtigung**

```sql
-- Beispiel: Datensatz mit Berechtigung
INSERT INTO kunde (
    uid, 
    daten, 
    name, 
    sec_id,              -- ⭐ Verweist auf Security-Profile
    gilt_bis,
    created_at,
    modified_at
) VALUES (
    'guid-kunde-123',
    '{"STAMM": {"NAME": "Mustermann"}}',
    'Mustermann, Max',
    'sec-vertrieb',      -- Security-Profile GUID
    '999365.00000',      -- Offen (kein Ablaufdatum)
    '2025244.12345',     -- Erstellt am
    '2025244.12345'      -- Letzte Änderung
);
```

### **gilt_bis - Gültigkeit**

```python
# PdvmDateTime Format
'999365.00000'  # Offen (keine Begrenzung)
'2026100.00000' # Gültig bis 10.04.2026

# Abfrage nur gültiger Datensätze
SELECT * FROM kunde 
WHERE gilt_bis >= ? OR gilt_bis = '999365.00000'
```

---

## 🏗️ KLASSEN-ARCHITEKTUR

### **HIERARCHIE:**

```
PdvmDatenbank                    (BASIS - Container-Verwaltung)
    ↓ erweitert
PdvmCentralDatenbank             (Instanz für EINEN Datensatz)
```

---

## 📦 PdvmDatenbank (BASIS-KLASSE)

**AUFGABEN:**
- ✅ Lesen/Speichern von Datensätzen
- ✅ Beachtet `gilt_bis` (Gültigkeit)
- ✅ Beachtet `sec_id` (wenn aktiv)
- ✅ Verwaltet `created_at` und `modified_at`
- ❌ KEINE Kenntnis über interne 'daten' Struktur!

```python
class PdvmDatenbank:
    """
    Basis-Klasse für Datenbank-Zugriff
    Verwaltet Container, NICHT Daten-Interna!
    """
    
    def __init__(self, table_name: str, check_sec_id: bool = True):
        """
        Args:
            table_name: Name der Tabelle (kleinbuchstaben!)
            check_sec_id: Soll sec_id geprüft werden?
        """
        self.table_name = table_name
        self.check_sec_id = check_sec_id
        self.db_path = "Daten/datenbank.db"
        self.current_stichtag = None  # Wird gesetzt
        self.user_sec_profiles = []   # User-Berechtigungen
    
    def lesen(self, uid: str) -> Dict:
        """
        Liest EINEN Datensatz
        
        Returns:
            {
                'uid': '...',
                'daten': '{"STAMM": {...}}',  # ⚠️ Als STRING!
                'name': '...',
                'historisch': 0,
                'sec_id': '...',
                'gilt_bis': '999365.00000',
                'created_at': '2025244.12345',
                'modified_at': '2025244.12345'
            }
        """
        sql = """
            SELECT * FROM {table}
            WHERE uid = ?
              AND (gilt_bis >= ? OR gilt_bis = '999365.00000')
        """.format(table=self.table_name)
        
        params = [uid, self.current_stichtag]
        
        # sec_id Check
        if self.check_sec_id:
            sql += " AND sec_id IN ({})".format(
                ','.join(['?'] * len(self.user_sec_profiles))
            )
            params.extend(self.user_sec_profiles)
        
        result = self._execute_query(sql, params)
        return result[0] if result else None
    
    def alle_lesen(self) -> List[Dict]:
        """
        Liest ALLE gültigen Datensätze
        """
        sql = """
            SELECT * FROM {table}
            WHERE (gilt_bis >= ? OR gilt_bis = '999365.00000')
        """.format(table=self.table_name)
        
        params = [self.current_stichtag]
        
        if self.check_sec_id:
            sql += " AND sec_id IN ({})".format(
                ','.join(['?'] * len(self.user_sec_profiles))
            )
            params.extend(self.user_sec_profiles)
        
        return self._execute_query(sql, params)
    
    def speichern(self, uid: str, daten_json: str, name: str = None, 
                  sec_id: str = None, gilt_bis: str = '999365.00000'):
        """
        Speichert/Update Datensatz
        
        Args:
            daten_json: JSON-String! (NICHT dict)
        """
        now = self._get_pdvm_datetime()
        
        # Prüfen ob Datensatz existiert
        existing = self.lesen(uid)
        
        if existing:
            # UPDATE
            sql = """
                UPDATE {table}
                SET daten = ?,
                    name = COALESCE(?, name),
                    sec_id = COALESCE(?, sec_id),
                    gilt_bis = COALESCE(?, gilt_bis),
                    modified_at = ?
                WHERE uid = ?
            """.format(table=self.table_name)
            
            params = [daten_json, name, sec_id, gilt_bis, now, uid]
        else:
            # INSERT
            sql = """
                INSERT INTO {table} 
                (uid, daten, name, historisch, sec_id, gilt_bis, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """.format(table=self.table_name)
            
            historisch = 0  # Default
            params = [uid, daten_json, name, historisch, sec_id, gilt_bis, now, now]
        
        self._execute_update(sql, params)
    
    def loeschen(self, uid: str, hard_delete: bool = False):
        """
        Löscht Datensatz
        
        Args:
            hard_delete: True = DELETE, False = gilt_bis setzen
        """
        if hard_delete:
            sql = f"DELETE FROM {self.table_name} WHERE uid = ?"
            self._execute_update(sql, [uid])
        else:
            # Soft-Delete: gilt_bis = jetzt
            now = self._get_pdvm_datetime()
            sql = f"""
                UPDATE {self.table_name}
                SET gilt_bis = ?, modified_at = ?
                WHERE uid = ?
            """
            self._execute_update(sql, [now, now, uid])
```

---

## 🎯 PdvmCentralDatenbank (ERWEITERTE KLASSE)

**AUFGABEN:**
- ✅ Repräsentiert EINE Datensatz-Instanz
- ✅ Kennt interne 'daten' Struktur (GRUPPE/FELD)
- ✅ get_value(GRUPPE, FELD) / set_value(GRUPPE, FELD, Wert)
- ✅ Verwaltet Historisierung (wenn `historisch = 1`)

```python
class PdvmCentralDatenbank:
    """
    Datenbank-Instanz für EINEN Datensatz
    Versteht GRUPPE/FELD Struktur!
    """
    
    def __init__(self, table_name: str, uid: str = None):
        """
        Args:
            table_name: Tabellenname (kleinbuchstaben)
            uid: Datensatz-GUID (None = neue Instanz)
        """
        self.table_name = table_name
        self.uid = uid or self._generate_guid()
        self.base_db = PdvmDatenbank(table_name)
        
        # Datensatz laden (falls existiert)
        self._daten_dict = {}       # Interne Daten (als Dict!)
        self._name = None
        self._historisch = 0
        self._sec_id = None
        self._gilt_bis = '999365.00000'
        
        if uid:
            self._load()
    
    def _load(self):
        """Lädt Datensatz von Basis-DB"""
        row = self.base_db.lesen(self.uid)
        if row:
            self._daten_dict = json.loads(row['daten'])
            self._name = row['name']
            self._historisch = row['historisch']
            self._sec_id = row['sec_id']
            self._gilt_bis = row['gilt_bis']
    
    def get_value(self, gruppe: str, feld: str, stichtag: float = None):
        """
        Holt Wert aus GRUPPE.FELD
        
        Args:
            gruppe: GROSSBUCHSTABEN (z.B. 'STAMM')
            feld: GROSSBUCHSTABEN (z.B. 'NAME')
            stichtag: PdvmDateTime für historische Abfrage
        
        Returns:
            (wert, abdatum) - Tuple
            oder (wert, None) - wenn nicht historisch
        """
        if gruppe not in self._daten_dict:
            return None, None
        
        if feld not in self._daten_dict[gruppe]:
            return None, None
        
        field_data = self._daten_dict[gruppe][feld]
        
        # HISTORISCH?
        if self._historisch and isinstance(field_data, dict):
            # Format: {"2025244.12345": "Wert1", "2025244.56789": "Wert2"}
            if stichtag:
                # Historische Abfrage
                valid_abdaten = [ad for ad in field_data.keys() if float(ad) <= stichtag]
                if valid_abdaten:
                    latest_abdatum = max(valid_abdaten, key=float)
                    return field_data[latest_abdatum], float(latest_abdatum)
                return None, None
            else:
                # Aktueller Wert (höchstes Abdatum)
                latest_abdatum = max(field_data.keys(), key=float)
                return field_data[latest_abdatum], float(latest_abdatum)
        else:
            # NICHT HISTORISCH
            return field_data, None
    
    def set_value(self, gruppe: str, feld: str, wert, abdatum: float = None):
        """
        Setzt Wert in GRUPPE.FELD
        
        Args:
            abdatum: Nur relevant wenn historisch=1
        """
        if gruppe not in self._daten_dict:
            self._daten_dict[gruppe] = {}
        
        if self._historisch:
            # MIT HISTORIE
            if feld not in self._daten_dict[gruppe]:
                self._daten_dict[gruppe][feld] = {}
            
            abdatum = abdatum or self._get_pdvm_datetime()
            abdatum_str = str(abdatum)
            
            # Format: GRUPPE.FELD.Abdatum.Wert
            self._daten_dict[gruppe][feld][abdatum_str] = wert
        else:
            # OHNE HISTORIE
            # Format: GRUPPE.FELD.Wert
            self._daten_dict[gruppe][feld] = wert
    
    def get_all_values(self) -> Dict:
        """
        Gibt komplette Daten-Struktur zurück
        """
        return self._daten_dict.copy()
    
    def save_all_values(self):
        """
        Speichert alle Änderungen zurück in DB
        """
        daten_json = json.dumps(self._daten_dict, ensure_ascii=False)
        
        self.base_db.speichern(
            uid=self.uid,
            daten_json=daten_json,
            name=self._name,
            sec_id=self._sec_id,
            gilt_bis=self._gilt_bis
        )
    
    def delete(self, hard: bool = False):
        """Löscht Datensatz"""
        self.base_db.loeschen(self.uid, hard_delete=hard)
```

---

## 🔍 VERWENDUNGS-BEISPIELE

### **BEISPIEL 1: Kunde anlegen (NICHT historisch)**

```python
# 1. Neue Instanz erstellen
kunde_db = PdvmCentralDatenbank('kunde')

# 2. Werte setzen
kunde_db.set_value('STAMM', 'NAME', 'Mustermann')
kunde_db.set_value('STAMM', 'VORNAME', 'Max')
kunde_db.set_value('STAMM', 'EMAIL', 'max@example.com')
kunde_db.set_value('ADRESSE', 'STRASSE', 'Hauptstr. 1')
kunde_db.set_value('ADRESSE', 'PLZ', '12345')
kunde_db.set_value('ADRESSE', 'ORT', 'Berlin')

# 3. Name und sec_id setzen
kunde_db._name = 'Mustermann, Max'
kunde_db._sec_id = 'sec-vertrieb'

# 4. Speichern
kunde_db.save_all_values()

print(f"Kunde erstellt: {kunde_db.uid}")
```

**Resultierende 'daten' Spalte:**
```json
{
    "STAMM": {
        "NAME": "Mustermann",
        "VORNAME": "Max",
        "EMAIL": "max@example.com"
    },
    "ADRESSE": {
        "STRASSE": "Hauptstr. 1",
        "PLZ": "12345",
        "ORT": "Berlin"
    }
}
```

---

### **BEISPIEL 2: Kunde ändern (MIT Historie)**

```python
# 1. Existierenden Kunden laden (mit historisch=1)
kunde_db = PdvmCentralDatenbank('kunde', uid='guid-kunde-123')
kunde_db._historisch = 1  # Historie aktiviert

# 2. Email ändern (mit aktuellem Abdatum)
jetzt = 2025244.15678
kunde_db.set_value('STAMM', 'EMAIL', 'neue@example.com', abdatum=jetzt)

# 3. Speichern
kunde_db.save_all_values()

# 4. Historische Werte abrufen
email_alt, abdatum_alt = kunde_db.get_value('STAMM', 'EMAIL', stichtag=2025240.00000)
email_neu, abdatum_neu = kunde_db.get_value('STAMM', 'EMAIL')

print(f"Alt: {email_alt} (ab {abdatum_alt})")
print(f"Neu: {email_neu} (ab {abdatum_neu})")
```

**Resultierende 'daten' Spalte:**
```json
{
    "STAMM": {
        "NAME": "Mustermann",
        "EMAIL": {
            "2024100.12345": "old@example.com",
            "2025244.15678": "neue@example.com"
        }
    }
}
```

---

### **BEISPIEL 3: Alle Kunden laden**

```python
# PdvmDatenbank für Massen-Abfragen
db = PdvmDatenbank('kunde')
db.current_stichtag = 2025244.00000
db.user_sec_profiles = ['sec-vertrieb', 'sec-admin']

# Alle gültigen Kunden
kunden = db.alle_lesen()

for kunde_row in kunden:
    # 'daten' ist STRING!
    daten = json.loads(kunde_row['daten'])
    
    name = daten.get('STAMM', {}).get('NAME', 'Unbekannt')
    email = daten.get('STAMM', {}).get('EMAIL', '-')
    
    print(f"{kunde_row['uid']}: {name} ({email})")
```

---

## 🔧 V2.0 ANPASSUNGEN

### **WAS ÜBERNOMMEN WIRD:**
✅ **Tabellen-Struktur** - Bleibt IDENTISCH (perfekt!)  
✅ **GRUPPE/FELD-System** - Bewährtes Konzept  
✅ **PdvmDateTime** - Zeitstempel-Format beibehalten  
✅ **Historisierung** - Eingebaute Versionierung  

### **WAS NEU KOMMT:**

#### **1. Automatische sec_id Verwaltung**
```python
# V2SecurityManager integriert in PdvmDatenbank
db = PdvmDatenbank('kunde', check_sec_id=True)
db.user_sec_profiles = security_manager.get_user_profiles(user_guid)
```

#### **2. Audit-Log (optional)**
```python
# Automatisches Logging aller Änderungen
class PdvmDatenbank:
    def speichern(self, ...):
        # ... normale Speicherung ...
        
        # Audit-Log schreiben
        self._log_change(
            table=self.table_name,
            uid=uid,
            action='UPDATE',
            user=current_user,
            timestamp=now
        )
```

#### **3. Validierung vor Speicherung**
```python
class PdvmCentralDatenbank:
    def save_all_values(self):
        # Validierung
        if not self._validate_data():
            raise ValueError("Daten-Validierung fehlgeschlagen")
        
        # ... normale Speicherung ...
```

---

## 📊 MIGRATIONS-STRATEGIE V0.9 → V2.0

### **GUTE NACHRICHT: Minimale Migration!**

```python
def migrate_database_v09_to_v20():
    """
    Migration ist EINFACH - Struktur bleibt gleich!
    """
    # 1. Tabellen-Namen anpassen (falls nötig)
    # menudaten → menudaten (bleibt!)
    
    # 2. sec_id Default setzen (wo NULL)
    """
    UPDATE kunde 
    SET sec_id = 'sec-default' 
    WHERE sec_id IS NULL;
    """
    
    # 3. gilt_bis Default setzen (wo NULL)
    """
    UPDATE kunde 
    SET gilt_bis = '999365.00000' 
    WHERE gilt_bis IS NULL;
    """
    
    # 4. created_at/modified_at befüllen (wo NULL)
    """
    UPDATE kunde 
    SET created_at = '2025244.00000',
        modified_at = '2025244.00000'
    WHERE created_at IS NULL;
    """
    
    # FERTIG! Daten bleiben IDENTISCH!
```

---

## 🎯 ZUSAMMENFASSUNG

### **KERN-MERKMALE:**
1. ✅ **Generisches Container-Modell** - Eine Struktur für ALLES
2. ✅ **GRUPPE/FELD-System** - Flexibel ohne Schema-Änderungen
3. ✅ **Eingebaute Historisierung** - Transparente Versionierung
4. ✅ **Security auf Datensatz-Ebene** - sec_id pro Zeile
5. ✅ **Gültigkeits-Verwaltung** - gilt_bis für Soft-Delete

### **KLASSEN:**
- `PdvmDatenbank` - Container-Verwaltung (keine Daten-Kenntnis)
- `PdvmCentralDatenbank` - Instanz für EINEN Datensatz (GRUPPE/FELD-Zugriff)

### **VORTEILE:**
- ✅ Extrem flexibel
- ✅ Minimale Migration
- ✅ Bewährtes System
- ✅ Matrix-Pipeline kompatibel

---

**Passt dieser Entwurf zu Ihren Vorstellungen?** 🎯
