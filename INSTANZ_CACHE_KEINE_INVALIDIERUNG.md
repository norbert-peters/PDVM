# Instanz-Cache: KEINE Invalidierung bei Stichtag-Wechsel

## 🎯 Wichtige Erkenntnis

**FRAGE**: Muss der Instanz-Cache bei Stichtag-Wechsel geleert werden?

**ANTWORT**: **NEIN!** ❌

---

## 💡 Grund

### Instanzen enthalten ALLE historischen Daten

```python
# Instanz erstellen
instance = PdvmCentralDatenbank('finanzdaten', 'guid-123')

# Wert zum Stichtag 1 (12.06.2025) abrufen
stichtag1 = 2025163.0
wert1, abdatum1 = instance.get_value('FINANZDATEN', 'KONTOINHABER', stichtag1)
# → "Max Mustermann" (eingetragen am 01.01.2020)

# Stichtag wechseln zu Stichtag 2 (01.08.2025)
stichtag2 = 2025213.0
wert2, abdatum2 = instance.get_value('FINANZDATEN', 'KONTOINHABER', stichtag2)
# → "Maria Beispiel" (eingetragen am 15.07.2025)

# GLEICHE INSTANZ, verschiedene Stichtage! ✅
```

**Die Instanz ist eine Verbindung zur DB-Tabelle, NICHT ein Snapshot!**

---

## ✅ Korrekter Ablauf bei Stichtag-Wechsel

### 1. **Manager koordiniert**
```python
def stichtag_changed(self):
    """Handler für Stichtag-Änderung"""
    
    # Cache bleibt unberührt! 🎉
    
    # Alle Controls refreshen
    self.refresh_all_controls()
```

### 2. **Control lädt NEU**
```python
def refresh(self):
    """Refresh nach Stichtag-Wechsel"""
    
    # [1] Instanz NEU auflösen
    #     WICHTIG: Nur für verschachtelte Controls!
    #     GUID-Zuordnung könnte sich geändert haben!
    self._resolve_instance()
    
    # [2] Wert mit neuem Stichtag laden
    #     Instanz holt Wert zum neuen Stichtag aus DB
    self._load_value_from_db()
    
    # [3] UI aktualisieren
    self._update_ui()
```

### 3. **Instanz bleibt im Cache**
```python
# Cache-Struktur (BLEIBT ERHALTEN):
_instance_cache = {
    ('FINANZDATEN', 'guid-123'): <Instanz 1>,
    ('FINANZDATEN', 'guid-456'): <Instanz 2>,
    ('ADRESSEN', 'guid-789'): <Instanz 3>
}

# Stichtag-Wechsel:
# → Cache bleibt unverändert
# → Instanzen holen Werte mit neuem Stichtag aus DB
# → Performance-Vorteil: Keine DB-Reconnects!
```

---

## ⚠️ WICHTIG: GUID-Auflösung

**Was KANN sich ändern**:
Die **GUID-Zuordnung** bei verschachtelten Controls!

```python
# Beispiel: Finanzdaten-GUID einer Person

# Stichtag 1 (12.06.2025):
guid = root_instance.get_value('PERSDATEN', 'FINANZDATEN-FINANZDATEN', 2025163.0)
# → "guid-123" (alte Bankverbindung)

# Stichtag 2 (01.08.2025):
guid = root_instance.get_value('PERSDATEN', 'FINANZDATEN-FINANZDATEN', 2025213.0)
# → "guid-456" (neue Bankverbindung!)

# GUID hat sich geändert!
# → Control muss andere Instanz aus Cache holen/erstellen
# → Aber Cache wird NICHT geleert!
```

**Daher**:
```python
def refresh(self):
    # Instanz NEU auflösen (GUID könnte sich geändert haben!)
    self._resolve_instance()
    
    # Wert laden (aus möglicherweise anderer Instanz!)
    self._load_value_from_db()
```

---

## 📊 Performance-Vorteil

### FALSCH (Cache leeren):
```python
def stichtag_changed(self):
    # ❌ FALSCH
    PdvmInputControlV3.clear_instance_cache()  # Cache leeren
    
    # Alle Controls refreshen
    for control in self.controls:
        control.refresh()
        # → Muss Instanz NEU erstellen (langsam!)
        # → DB-Reconnect für jedes Control!
```

**Problem**:
- ❌ Alle Instanzen müssen neu erstellt werden
- ❌ DB-Reconnects für jede Instanz
- ❌ Performance-Verlust
- ❌ Unnötig, da Instanzen alle Daten enthalten!

### RICHTIG (Cache behalten):
```python
def stichtag_changed(self):
    # ✅ RICHTIG
    # Cache bleibt unberührt!
    
    # Alle Controls refreshen
    for control in self.controls:
        control.refresh()
        # → Instanz aus Cache holen (schnell!)
        # → Nur get_value() mit neuem Stichtag
```

**Vorteil**:
- ✅ Instanzen bleiben im Cache
- ✅ Keine DB-Reconnects
- ✅ Nur `get_value()` mit neuem Stichtag
- ✅ Schnell und effizient!

---

## 🧪 Wann Cache leeren?

**NUR in folgenden Fällen**:

### 1. Neustart/Reset
```python
def reset_application(self):
    """Anwendung zurücksetzen"""
    PdvmInputControlV3.clear_instance_cache()
```

### 2. Person-Wechsel (theoretisch)
```python
def change_person(self, new_guid):
    """Person wechseln"""
    # Optional: Cache leeren
    # (Oder: Cache bleibt, andere GUIDs werden geholt)
    self.selected_guid = new_guid
    self.refresh_all_controls()
```

**Aber auch hier**: Cache leeren ist optional!
- Cache-Keys sind `(tabelle, guid)`
- Andere Person → andere GUIDs → andere Cache-Keys
- Alte Instanzen bleiben im Cache (schadet nicht)

---

## ✅ Zusammenfassung

| Situation | Cache leeren? | Grund |
|-----------|---------------|-------|
| **Stichtag-Wechsel** | ❌ NEIN | Instanzen enthalten alle historischen Daten |
| **Person-Wechsel** | ⚠️ Optional | Andere GUIDs → andere Cache-Keys |
| **Neustart/Reset** | ✅ JA | Sauberer Zustand |

**REGEL**: 
- Cache leeren ist **fast nie** nötig
- Instanzen sind **zeitpunktunabhängig**
- Nur `get_value(stichtag)` ändert sich

---

## 🎯 Implementierung in V3

### Control V3
```python
def refresh(self):
    """Refresh nach Stichtag-Wechsel"""
    
    # Instanz NEU auflösen (GUID könnte sich ändern!)
    self._resolve_instance()
    
    # Wert mit neuem Stichtag laden (aus bestehender Instanz!)
    self._load_value_from_db()
    
    # UI aktualisieren
    self._update_ui()
```

### Manager V3
```python
def stichtag_changed(self):
    """Handler für Stichtag-Änderung"""
    
    # Cache bleibt unberührt!
    
    # Alle Controls refreshen
    self.refresh_all_controls()
```

**Einfach, effizient, korrekt!** ✅

---

**Stand**: 22.10.2025 - Cache-Strategie geklärt
