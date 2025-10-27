# IC Autonom - Vereinfachtes Konzept

## 🎯 Problem mit aktueller Architektur

**AKTUELL (FALSCH)**:
- Manager erstellt Instanzen-Pool zentral
- Manager verteilt Instanzen an Controls
- Komplexe Zuordnungslogik
- Fehleranfällig bei Stichtag-Wechsel

**NEU (RICHTIG)**:
- Jedes IC ist vollständig autonom
- IC beschafft sich seine eigene Instanz
- Kein zentraler Instanzen-Pool
- Einfach & robust

---

## 🔄 Autonomer IC-Ablauf

### 1. ROOT-Control (source_path = "root")

```python
# Metadaten:
{
    "field_key": "PERSONDATEN_PERSDATEN_FAMILIENNAME",
    "source_path": "root",
    "label": "Familienname"
}

# IC-Logik:
root_instance = manager.root_instance  # Vom Manager übergeben
wert, abdatum = root_instance.get_value("PERSDATEN", "FAMILIENNAME", gcs.st_inst.PdvmDateTime)
# → Direkt anzeigen
```

**Einfach**: Direkter Zugriff auf ROOT-Instanz

---

### 2. Verschachteltes Control (source_path != "root")

```python
# Metadaten:
{
    "field_key": "FINANZDATEN_FINANZDATEN_KONTOINHABER",
    "source_path": "root_PERSDATEN",
    "label": "Kontoinhaber"
}

# IC-Logik (AUTONOM):

# SCHRITT 1: Parse source_path
tabelle = "FINANZDATEN"     # Aus field_key (Teil 1)
gruppe = "FINANZDATEN"      # Aus field_key (Teil 2)
source_gruppe = "PERSDATEN" # Aus source_path (nach "root_")

# SCHRITT 2: Zuordnungsfeld ermitteln
zuordnungsfeld = f"{tabelle}-{gruppe}"  # "FINANZDATEN-FINANZDATEN"

# SCHRITT 3: GUID aus ROOT holen (STICHTAGGENAU!)
stichtag = gcs.st_inst.PdvmDateTime
result = root_instance.get_value(source_gruppe, zuordnungsfeld, stichtag)

if not result or result[0] is None:
    # KEINE GUID → Control ist READ-ONLY
    self.zugeordnete_guid = None
    self.zugeordnete_instanz = None
    self.read_only = True  # WICHTIG!
    return

guid, guid_abdatum = result

# SCHRITT 4: Instanz holen/erstellen
self.zugeordnete_guid = guid
self.zugeordnete_instanz = self._get_or_create_instance(tabelle, guid)

# SCHRITT 5: Wert aus zugeordneter Instanz holen
wert, abdatum = self.zugeordnete_instanz.get_value(
    gruppe,
    "KONTOINHABER",
    stichtag
)
# → Anzeigen
```

**Autonom**: IC macht ALLES selbst!

---

## 📦 Instanz-Caching (Lokal im IC)

**WICHTIG**: Cache wird **NICHT** bei Stichtag-Wechsel geleert!

```python
class PdvmInputControlV3:
    # Klassen-Variable für Instanz-Cache
    _instance_cache = {}  # {(tabelle, guid): instance}
    
    def _get_or_create_instance(self, tabelle: str, guid: str):
        """
        Holt Instanz aus Cache oder erstellt neue
        
        Cache-Key: (tabelle, guid)
        
        WICHTIG: Instanzen enthalten ALLE historischen Daten!
                 Daher keine Cache-Invalidierung bei Stichtag-Wechsel!
        """
        cache_key = (tabelle.upper(), guid)
        
        if cache_key not in self._instance_cache:
            # Neue Instanz erstellen
            instance = PdvmCentralDatenbank(tabelle, guid)
            self._instance_cache[cache_key] = instance
            logger.debug(f"    ✅ Instanz erstellt: {tabelle}_{guid}")
        else:
            logger.debug(f"    ♻️ Instanz aus Cache: {tabelle}_{guid}")
        
        return self._instance_cache[cache_key]
    
    @classmethod
    def clear_instance_cache(cls):
        """
        Leert Instanz-Cache (nur bei Neustart/Reset)
        
        NICHT bei Stichtag-Wechsel, da Instanzen alle
        historischen Daten enthalten!
        """
        cls._instance_cache.clear()
        logger.info("🗑️ Instanz-Cache geleert")
```

**Performance-Vorteil**:
- Cache bleibt über Stichtag-Wechsel erhalten
- Keine unnötigen DB-Reconnects
- `get_value()` holt einfach Wert zum neuen Stichtag aus bestehender Instanz

---

## 🔄 Refresh-Logik (bei Stichtag-Wechsel)

**WICHTIG**: Instanz-Cache wird **NICHT** geleert, da Instanzen alle historischen Daten enthalten!

```python
# Manager ruft refresh() auf allen Controls auf:
for control in self.controls:
    control.refresh()

# IC refresh():
def refresh(self):
    """Neu laden nach Stichtag-Wechsel"""
    
    # [1] Instanz NEU auflösen (GUID könnte sich geändert haben!)
    #     Bei verschachtelten Controls: GUID wird mit neuem Stichtag abgefragt
    self._resolve_instance()
    
    # [2] Wert NEU laden (mit neuem Stichtag!)
    #     Instanz enthält ALLE historischen Daten
    self._load_value_from_db()
    
    # [3] UI aktualisieren
    self._update_ui()
```

**GRUND**: 
- Instanzen enthalten **ALLE** historischen Daten
- `get_value(gruppe, feld, stichtag)` holt korrekten Wert zum Stichtag
- Nur die **GUID-Zuordnung** könnte sich ändern (daher `_resolve_instance()`)
- Cache-Leeren wäre unnötig und Performance-Verlust!

---

## 🎯 Vorteile

### ✅ Einfachheit
- Keine zentrale Instanzen-Verwaltung
- Jedes IC ist unabhängig
- Klare, lineare Logik

### ✅ Robustheit
- Stichtag-Wechsel: Einfach alle ICs refreshen
- Keine Synchronisations-Probleme
- Keine "verlorenen" Instanzen

### ✅ Nachvollziehbarkeit
- Jedes IC loggt seinen eigenen Ablauf
- Debugging einfach: Nur ein IC prüfen
- Klare Verantwortlichkeiten

---

## 📋 Manager wird ULTRA einfach

```python
class PdvmInputControlsManagerV2:
    def __init__(self, frame_guid, selected_guid):
        self.frame_guid = frame_guid
        self.selected_guid = selected_guid
        
        # NUR ROOT-Instanz erstellen
        self.root_instance = PdvmCentralDatenbank('persondaten', selected_guid)
        
        # Controls-Liste
        self.controls = []
    
    def get_widget(self):
        # [1] Metadaten laden
        controls_meta = self._load_meta()
        
        # [2] Controls erstellen (AUTONOM!)
        for meta in controls_meta:
            control = PdvmInputControlV2(
                root_instance=self.root_instance,  # NUR ROOT!
                meta=meta
            )
            control.render()  # IC beschafft sich ALLES selbst
            self.controls.append(control)
        
        # [3] UI zusammenbauen
        return self._create_ui()
    
    def save_all(self):
        neues_abdatum = self.neues_abdatum_dt.PdvmDateTime
        
        for control in self.controls:
            control.save(neues_abdatum)
        
        # Commit (optional, da Controls schon gespeichert haben)
    
    def refresh_all(self):
        # Bei Stichtag-Wechsel: Cache leeren!
        PdvmInputControlV2.clear_instance_cache()
        
        for control in self.controls:
            control.refresh()  # IC beschafft sich alles NEU
```

**ULTRA EINFACH!** Manager macht fast nichts mehr!

---

## 🔧 IC-Struktur (Vereinfacht)

```python
class PdvmInputControlV2:
    # Klassen-Cache für Instanzen
    _instance_cache = {}
    
    def __init__(self, root_instance, meta):
        self.root_instance = root_instance
        self.source_path = meta['source_path']
        self.field_key = meta['field_key']
        # ... weitere Meta-Daten
        
        # Zugeordnete Instanz (wird bei _resolve_instance() gesetzt)
        self.zugeordnete_instanz = None
        self.zugeordnete_guid = None
        
        # Parse field_key
        parts = self.field_key.split('_')
        self.tabelle = parts[0]
        self.gruppe = parts[1]
        self.feld = parts[2]
    
    def render(self):
        """Erstmaliges Laden + UI erstellen"""
        self._resolve_instance()
        self._load_value_from_db()
        self._create_ui()
        self._update_ui()
    
    def _resolve_instance(self):
        """
        Beschafft zugeordnete Instanz (AUTONOM!)
        
        Für source_path = "root": root_instance verwenden
        Für source_path != "root": GUID auflösen + Instanz holen
        """
        if self.source_path == "root":
            # Direkt ROOT verwenden
            self.zugeordnete_instanz = self.root_instance
            self.zugeordnete_guid = self.root_instance.guid
            return
        
        # Parse source_path (z.B. "root_PERSDATEN")
        source_gruppe = self.source_path.replace('root_', '')
        zuordnungsfeld = f"{self.tabelle}-{self.gruppe}"
        
        # GUID auflösen (STICHTAGGENAU!)
        stichtag = gcs.st_inst.PdvmDateTime
        result = self.root_instance.get_value(source_gruppe, zuordnungsfeld, stichtag)
        
        if not result or result[0] is None:
            # KEINE GUID → READ-ONLY
            self.zugeordnete_instanz = None
            self.zugeordnete_guid = None
            self.read_only = True
            logger.warning(f"  ⚠️ Keine GUID für {self.label_text} → Read-Only")
            return
        
        guid, _ = result
        self.zugeordnete_guid = guid
        
        # Instanz holen/erstellen
        self.zugeordnete_instanz = self._get_or_create_instance(self.tabelle, guid)
    
    def _load_value_from_db(self):
        """Lädt Wert aus zugeordneter Instanz"""
        if not self.zugeordnete_instanz:
            self.wert = None
            self.abdatum_wert = None
            return
        
        stichtag = gcs.st_inst.PdvmDateTime
        self.wert, self.abdatum_wert = self.zugeordnete_instanz.get_value(
            self.gruppe,
            self.feld,
            stichtag
        )
    
    def refresh(self):
        """Refresh nach Stichtag-Wechsel"""
        # [1] Instanz NEU auflösen
        self._resolve_instance()
        
        # [2] Wert NEU laden
        self._load_value_from_db()
        
        # [3] UI aktualisieren
        self._update_ui()
```

---

## ✅ Migration-Plan

1. **PdvmInputControlV2 umbauen**:
   - `__init__` bekommt nur `root_instance` + `meta`
   - `_resolve_instance()` Methode hinzufügen
   - `_get_or_create_instance()` Methode hinzufügen
   - Klassen-Cache `_instance_cache` hinzufügen

2. **PdvmInputControlsManagerV2 vereinfachen**:
   - `_build_instances_pool()` ENTFERNEN
   - `_build_controls_matrix()` vereinfachen
   - Nur noch ROOT-Instanz erstellen

3. **Testen**:
   - Erste Person (ohne GUID): Controls read-only ✅
   - Zweite Person (mit GUID): Controls editierbar ✅
   - Stichtag-Wechsel: Alle Controls aktualisieren ✅

---

**Stand**: 22.10.2025 - Autonomes IC-Konzept definiert
