# Stichtag vs. Neues Abdatum - Systemkonzept

## 📅 Zwei verschiedene Zeitpunkte

### 1. **Stichtag** (GCS `st_inst.PdvmDateTime`)
**Zweck**: Bestimmt **WELCHE DATEN** der User sieht

**Verwendung**:
- ✅ **Daten laden** (Anzeige in Controls)
- ✅ **GUID-Auflösung** (Instanzen-Pool)
- ✅ **View-Daten** (Matrix-Pipeline)
- ✅ **Nach Speichern** (Refresh zeigt Daten zum Stichtag)

**Quelle**: `gcs.st_inst.PdvmDateTime` (z.B. 2025213.0 = 01.08.2025)

---

### 2. **Neues Abdatum** (Manager `neues_abdatum_dt`)
**Zweck**: Bestimmt **WANN** neue Daten gespeichert werden

**Verwendung**:
- ✅ **Nur beim Speichern** (`save(neues_abdatum)`)
- ✅ **Zeitstempel** für neue/geänderte Werte

**Quelle**: `self.neues_abdatum_dt.PdvmDateTime` (vom User einstellbar, z.B. 2025188.0 = 07.07.2025)

---

## 🔄 Ablauf-Beispiel

### Szenario: User speichert Wert am 07.07.2025, aber Stichtag ist 01.08.2025

```
[1] LADEN (Stichtag: 01.08.2025)
    ├─ GUID-Auflösung: get_value(..., stichtag=2025213.0)
    ├─ Control-Daten: get_value(..., stichtag=2025213.0)
    └─ Zeigt: Daten, die zum 01.08.2025 gültig waren

[2] USER ÄNDERT WERT
    ├─ Control wird "dirty"
    └─ Neues Abdatum: 07.07.2025 (2025188.0)

[3] SPEICHERN (Neues Abdatum: 07.07.2025)
    ├─ set_value(..., abdatum=2025188.0)
    └─ Wert wird MIT Zeitstempel 07.07.2025 gespeichert

[4] REFRESH (Stichtag: 01.08.2025)
    ├─ get_value(..., stichtag=2025213.0)
    ├─ Findet: Wert mit Abdatum 07.07.2025
    └─ ✅ Zeigt: NEUER WERT (weil 07.07.2025 < 01.08.2025)
```

### ⚠️ EDGE CASE: Neues Abdatum > Stichtag

```
Stichtag: 01.08.2025 (2025213.0)
Neues Abdatum: 15.09.2025 (2025258.0)  ← SPÄTER!

[1] SPEICHERN
    └─ set_value(..., abdatum=2025258.0)

[2] REFRESH
    ├─ get_value(..., stichtag=2025213.0)
    ├─ Sucht: Wert <= 01.08.2025
    └─ ❌ Findet: ALTEN WERT (neuer Wert ist zu spät!)

[3] USER SIEHT
    └─ Sein neuer Wert "verschwindet"
```

**Verhalten**: Dies ist **KORREKT**! Der User hat einen Wert in der Zukunft gespeichert, der zum aktuellen Stichtag noch nicht existiert.

---

## 💾 Code-Implementierung

### GUID-Auflösung (Instanzen-Pool)

```python
# pdvm_input_controls_manager_v2.py:588
stichtag = gcs.st_inst.PdvmDateTime  # ← Stichtag!

result = root_instance.get_value(lookup_gruppe, lookup_feld, stichtag)
guid, abdatum = result

# Instanz mit GUID zum Stichtag erstellen
new_instance = PdvmCentralDatenbank(target_table, guid)
```

**Warum?** 
- Die GUID, die zum Stichtag gültig ist, bestimmt welche Daten geladen werden
- Beispiel: Person hatte am 01.06.2025 Konto A, am 01.08.2025 Konto B
- Stichtag 01.08.2025 → Lädt Konto B

---

### Control: Daten Laden

```python
# pdvm_input_control_v2.py:278
stichtag = gcs.st_inst.PdvmDateTime  # ← Stichtag!

self.wert, self.abdatum_wert = self.db_instance.get_value(
    self.gruppe,
    self.feld,
    stichtag
)
```

**Warum?**
- Zeigt Wert, der zum Stichtag gültig war
- Unabhängig vom "Neues Abdatum" Picker

---

### Control: Daten Speichern

```python
# pdvm_input_control_v2.py:174
self.db_instance.set_value(
    self.gruppe,
    self.feld,
    self.current_value,
    neues_abdatum  # ← Neues Abdatum vom Manager!
)
```

**Warum?**
- Neuer Wert bekommt Zeitstempel vom "Neues Abdatum" Picker
- User bestimmt explizit WANN der Wert gültig wird

---

## 🔄 Ablauf: Datensatz-Wechsel

```
[1] User wählt Person in View
    └─ selected_guid = "abc-123"

[2] Manager: get_widget()
    ├─ Instanzen-Pool aufbauen (mit Stichtag!)
    │   ├─ ROOT: PERSONDATEN_abc-123
    │   └─ GUID auflösen: get_value(..., stichtag=GCS)
    │       └─ FINANZDATEN_xyz-789 (zum Stichtag!)
    │
    ├─ Controls erstellen
    │   └─ Jedes Control bekommt passende Instanz
    │
    └─ Controls laden (mit Stichtag!)
        └─ _load_value_from_db() → get_value(..., stichtag=GCS)

[3] User sieht Daten
    └─ Alle Daten zum aktuellen Stichtag
```

---

## 📋 Wichtige Regeln

### ✅ DO

1. **IMMER GCS-Stichtag für Anzeige**
   ```python
   stichtag = gcs.st_inst.PdvmDateTime
   result = instance.get_value(gruppe, feld, stichtag)
   ```

2. **IMMER Neues Abdatum für Speichern**
   ```python
   neues_abdatum = self.neues_abdatum_dt.PdvmDateTime
   instance.set_value(gruppe, feld, wert, neues_abdatum)
   ```

3. **Nach Speichern: Refresh mit Stichtag**
   ```python
   control.refresh()  # Lädt mit GCS-Stichtag neu
   ```

### ❌ DON'T

1. **NIEMALS Neues Abdatum für Laden verwenden**
   ```python
   # ❌ FALSCH
   result = instance.get_value(gruppe, feld, neues_abdatum)
   ```

2. **NIEMALS Stichtag für Speichern verwenden**
   ```python
   # ❌ FALSCH
   instance.set_value(gruppe, feld, wert, stichtag)
   ```

3. **NIEMALS davon ausgehen dass gespeicherter Wert sofort sichtbar ist**
   ```python
   # ⚠️ ACHTUNG: Kann "verschwinden" wenn neues_abdatum > stichtag
   ```

---

## 🎯 Beispiel: Historie-Dialog

Der Historie-Dialog zeigt **ALLE** Werte (unabhängig vom Stichtag):

```python
# get_field() holt ALLE historischen Werte
history_data = db_instance.get_field(gruppe, feld)

# Ergebnis:
{
    2025258.0: "Neuer Wert" (15.09.2025) ← Noch nicht sichtbar!
    2025188.0: "Alter Wert" (07.07.2025) ← Aktuell sichtbar
    2025152.0: "Sehr alter Wert" (01.06.2025)
}

# Bei Stichtag 01.08.2025 (2025213.0):
# → get_value(..., 2025213.0) liefert "Alter Wert" (07.07.2025)
# → "Neuer Wert" (15.09.2025) ist noch nicht gültig!
```

---

## 🔍 Debug-Szenarien

### Problem: "Keine GUID gefunden"

```
⚠️ Keine GUID gefunden: PERSDATEN.FINANZDATEN-FINANZDATEN (Stichtag: 2025213.0)
```

**Mögliche Ursachen**:
1. ✅ **Kein Eintrag vorhanden** → Person hat kein Finanzkonto
2. ✅ **Eintrag zu neu** → GUID wurde NACH Stichtag angelegt
3. ✅ **Eintrag gelöscht** → GUID existierte, wurde aber vor Stichtag entfernt

**Lösung**: Historie-Dialog prüfen → Welche GUIDs zu welchem Zeitpunkt?

---

### Problem: "Gespeicherter Wert verschwindet"

```
User speichert: "Max Mustermann" am 15.09.2025
Nach Refresh: Zeigt "Alter Name" (oder leer)
```

**Ursache**: `neues_abdatum > stichtag`

**Lösung**: 
- Stichtag anpassen (auf 15.09.2025 oder später)
- Oder: Neues Abdatum anpassen (auf vor Stichtag)

---

## 📚 Zusammenfassung

| Aktion | Zeitpunkt | Quelle |
|--------|-----------|--------|
| **Daten anzeigen** | Stichtag | `gcs.st_inst.PdvmDateTime` |
| **GUID auflösen** | Stichtag | `gcs.st_inst.PdvmDateTime` |
| **Daten speichern** | Neues Abdatum | `neues_abdatum_dt.PdvmDateTime` |
| **Nach Speichern** | Stichtag | `gcs.st_inst.PdvmDateTime` |

**Essenz**: 
- **Stichtag** = "Wann will ich die Daten sehen?"
- **Neues Abdatum** = "Wann werden neue Daten gültig?"

---

**Stand**: 22.10.2025 - Korrekte Implementierung bestätigt ✅
