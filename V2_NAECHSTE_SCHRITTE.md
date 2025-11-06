# 🚀 V2.0 - NÄCHSTE SCHRITTE

**Datum:** 31.10.2025  
**Status:** ✅ Login-System & GCS komplett

---

## ✅ ABGESCHLOSSEN

### 1. Login & Authentifizierung
- ✅ `v2_login_dialog.py` - bcrypt-Passwort-Verifikation
- ✅ Demo-Button für schnellen Login
- ✅ Passwort-Sichtbarkeit Toggle
- ✅ User-Daten werden EINMALIG aus auth.db geladen

### 2. Mandanten-Verwaltung
- ✅ `v2_mandanten_dialog.py` - Mandanten-Auswahl aus User-Liste
- ✅ Korrekte GUID-Struktur (sys_mandanten.uid = GUID)
- ✅ MANDANT_ID aus Daten für Verzeichnis-Pfade

### 3. Datenbank-Migration
- ✅ `v2_init_mandanten_databases.py` - Erstellt Mandanten-DBs
- ✅ `v2_migrate_pdvm_data.py` - Migriert Daten 1:1
- ✅ 8 Tabellen pro Mandant (sys_anwendungsdaten, sys_beschreibungen, etc.)
- ✅ 26 Datensätze pro Mandant (identische Testbasis)
- ✅ V2.0-Schema: uid, daten, name, historisch, source_hash, sec_id, gilt_bis, created_at, modified_at

### 4. Global Central System (GCS)
- ✅ `v2_gcs.py` - Zentrale Systemsteuerung
- ✅ User-Daten (GUID, Rollen, Security-Profiles)
- ✅ Mandanten-Daten (GUID, ID, DB-Pfad)
- ✅ Singleton-Pattern für globalen Zugriff
- ✅ KEINE Verbindung zu auth.db nach Login!

### 5. Hauptanwendung
- ✅ `v2_main.py` - Kompletter Login-Flow
- ✅ GCS-Integration nach Mandanten-Auswahl
- ✅ Rudimentäres Hauptfenster zum Testen

---

## 🎯 NÄCHSTE SCHRITTE

### 1. PdvmDatenbank & PdvmCentralDatenbank in GCS integrieren

**Ziel:** GCS bietet direkten Zugriff auf Mandanten-DB

```python
# In v2_gcs.py erweitern:
from pdvm_datenbank import PdvmDatenbank
from pdvm_central_datenbank import PdvmCentralDatenbank

class V2GlobalCentralSystem:
    def __init__(self, ...):
        # ...
        
        # ⭐ Datenbank-Instanzen
        self._db_instances = {}  # Cache für PdvmDatenbank pro Tabelle
    
    def get_db(self, table_name: str) -> PdvmDatenbank:
        """
        Holt PdvmDatenbank-Instanz für Tabelle
        
        Args:
            table_name: z.B. 'sys_menudaten', 'kunde'
        
        Returns:
            PdvmDatenbank-Instanz (gecacht)
        """
        if table_name not in self._db_instances:
            db = PdvmDatenbank(
                db_path=self.mandant_db_path,
                table_name=table_name
            )
            db.current_stichtag = self.stichtag
            db.user_sec_profiles = self.user_sec_profiles
            self._db_instances[table_name] = db
        
        return self._db_instances[table_name]
    
    def get_record(self, table_name: str, uid: str) -> PdvmCentralDatenbank:
        """
        Holt PdvmCentralDatenbank-Instanz für einen Datensatz
        
        Args:
            table_name: z.B. 'sys_menudaten'
            uid: Datensatz-GUID
        
        Returns:
            PdvmCentralDatenbank-Instanz
        """
        return PdvmCentralDatenbank(
            db_path=self.mandant_db_path,
            table_name=table_name,
            uid=uid
        )
```

**Verwendung:**
```python
from v2_gcs import get_gcs

gcs = get_gcs()

# Alle Menüs laden
menu_db = gcs.get_db('sys_menudaten')
all_menus = menu_db.alle_lesen()

# Einzelnes Menü laden
menu_record = gcs.get_record('sys_menudaten', menu_guid)
menu_name = menu_record.get_value('ROOT', 'BEZEICHNUNG')
```

---

### 2. Menü-System implementieren

**Aufgabe:** User beschreibt die Menü-Struktur

**Wartet auf:** User-Beschreibung der gewünschten Menü-Struktur

**Fragen zu klären:**
- Welche Menü-Ebenen? (Hauptmenü, Untermenüs, Module?)
- Wie soll Navigation funktionieren? (Tabs, Tree, Buttons?)
- Welche Module zuerst implementieren? (Personalwesen, Finanzwesen?)
- Menü-Daten aus sys_menudaten laden oder neu definieren?

---

### 3. View-System anbinden

**Nach Menü-System:**
- Views aus sys_viewdaten laden
- Matrix-Pipeline integrieren
- View-Controller mit GCS verbinden

---

## 📋 OFFENE PUNKTE

### Architektur-Dokumentation
- [ ] `V2_ARCHITECTURE.md` aktualisieren mit GCS-Details
- [ ] Login-Flow-Diagramm erstellen
- [ ] Datenbank-Schema-Diagramm ergänzen

### Testing
- [ ] Unit-Tests für v2_gcs.py
- [ ] Integration-Tests für Login-Flow
- [ ] Mandanten-Wechsel testen

### Cleanup
- [ ] Debug-Skripte aufräumen (check_passwords.py, etc.)
- [ ] Alte Login-Komponenten entfernen (falls nicht mehr benötigt)

---

## 🎨 MENÜ-SYSTEM - VORBEREITUNG

**Fragen an User:**

1. **Menü-Struktur:**
   - Soll das alte Menü-System übernommen werden?
   - Oder komplett neu designen?
   - Welche Bereiche sind wichtig? (Personalwesen, Finanzen, Admin, ...)

2. **Navigation:**
   - Sidebar mit Tree-Navigation?
   - Top-Menu mit Dropdowns?
   - Tab-basiert?
   - Oder Kombination?

3. **Start-Menü:**
   - Was passiert nach Login?
   - Zeige Dashboard?
   - Zeige Start-Menü aus MEINEAPPS?
   - Direkt zur letzten View?

4. **Menü-Daten:**
   - sys_menudaten aus Migration verwenden?
   - Oder neue Menü-Struktur in Daten anlegen?

---

**BEREIT FÜR:** User-Input zur Menü-Struktur! 🎯
