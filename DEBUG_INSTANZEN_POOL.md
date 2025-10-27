# Debug: Instanzen-Pool & GUID-Auflösung

## Problem-Analyse (22.10.2025 16:22)

### Symptome

1. **Erste Person (39ae18d4)**: 
   - ⚠️ Keine GUID gefunden für FINANZDATEN
   - Controls ohne Instanz → Read-Only
   - ❌ Keine Daten angezeigt

2. **Zweite Person (0d66233c)**:
   - ✅ GUID gefunden: 74352176-bd00-4254-8ff7-6dab9a466e84
   - Instanz erstellt: FINANZDATEN_74352176...
   - ❌ Aber zeigt möglicherweise falsche Daten?

### Trace-Analyse

```
[Erste Person - 39ae18d4]
16:19:14 - ✅ ROOT: PERSONDATEN_39ae18d4-aa9e-4769-ba7a-a2bd89ec951b
16:19:14 - ⚠️ Keine GUID gefunden: PERSDATEN.FINANZDATEN-FINANZDATEN
16:19:14 - ⚠️ Keine Instanz gefunden für FINANZDATEN_..._KONTONUMMER, verwende ROOT

[Zweite Person - 0d66233c]
16:21:11 - ✅ ROOT: PERSONDATEN_0d66233c-eaf5-4407-ac57-40781922bd94
16:21:11 - ✅ Verschachtelt: FINANZDATEN_74352176-bd00-4254-8ff7-6dab9a466e84
16:21:11 - ✅ Instanzen-Pool aufgebaut: 3 Instanzen
```

### Root-Cause

**Problem**: GUID-Auflösung findet keine GUID für erste Person

**Mögliche Ursachen**:

1. **Stichtag-Problem**:
   - GCS-Stichtag: `2025213.0` (01.08.2025)
   - Aber GUID wurde am `2025152.0` (01.06.2025) angelegt
   - Vielleicht gibt es für erste Person KEINE GUID zu diesem Stichtag?

2. **Fehlender Eintrag in DB**:
   - Für Person 39ae18d4 existiert kein Eintrag `PERSDATEN.FINANZDATEN-FINANZDATEN`
   - → Control ohne Instanz

3. **Falsche Gruppe**:
   - source_path: `root_PERSDATEN` 
   - lookup_gruppe: `PERSDATEN`
   - Aber sollte es `PERSONDATEN` sein?

### Lösung (IMPLEMENTIERT)

#### 1. Debug-Logs hinzugefügt

```python
# In _build_instances_pool():
logger.debug(f"    🔍 Suche GUID: {lookup_gruppe}.{lookup_feld} (Stichtag: {stichtag})")

if isinstance(result, tuple):
    guid, abdatum = result
    logger.debug(f"       → GUID gefunden: {guid} (Abdatum: {abdatum})")
else:
    guid = result
    logger.debug(f"       → GUID gefunden: {guid}")

if not guid or guid == "":
    logger.warning(f"    ⚠️ Keine GUID gefunden: {lookup_gruppe}.{lookup_feld} (Stichtag: {stichtag})")
```

#### 2. Instanz-Zuordnung geloggt

```python
# In _build_controls_matrix():
if not db_instance:
    logger.warning(f"    ⚠️ Keine Instanz gefunden für {field_key}, verwende ROOT")
else:
    logger.debug(f"    ✅ Instanz zugeordnet: {field_key} → {instance_key}")
```

### Nächste Schritte

1. **Test mit neuen Logs**:
   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

2. **Prüfen**:
   - Wird GUID für erste Person gefunden?
   - Welcher Stichtag wird verwendet?
   - Existiert der Eintrag in der DB?

3. **Datenbank-Check** (wenn nötig):
   ```python
   # In persondaten Tabelle für GUID 39ae18d4:
   SELECT * FROM persondaten WHERE guid = '39ae18d4-aa9e-4769-ba7a-a2bd89ec951b';
   # Prüfe ob PERSDATEN.FINANZDATEN-FINANZDATEN vorhanden ist
   ```

4. **Stichtag-Auflösung prüfen**:
   - Verwende Historie-Dialog für "Zuordnung Finanzen"
   - Zeigt Historie: Welche GUIDs zu welchem Zeitpunkt?

### Erwartetes Verhalten

**KORREKT**:
```
Person 1 (39ae18d4):
  PERSDATEN.FINANZDATEN-FINANZDATEN = "guid-person1" (Stichtag: X)
  → Instanz: FINANZDATEN_guid-person1
  → Controls zeigen Daten von guid-person1

Person 2 (0d66233c):
  PERSDATEN.FINANZDATEN-FINANZDATEN = "guid-person2" (Stichtag: Y)
  → Instanz: FINANZDATEN_guid-person2
  → Controls zeigen Daten von guid-person2
```

**FALSCH (aktuell)**:
```
Person 1 (39ae18d4):
  ⚠️ Keine GUID gefunden
  → Keine Instanz
  → Controls leer/read-only

Person 2 (0d66233c):
  ✅ GUID gefunden: guid-person2
  → Instanz: FINANZDATEN_guid-person2
  → Aber zeigt möglicherweise falsche Daten
```

### Theorie: Warum keine GUID?

**Szenario A - Nicht angelegt**:
- Für Person 1 wurde einfach kein FINANZDATEN-Eintrag angelegt
- Lösung: Eintrag erstellen oder "Leer" akzeptieren

**Szenario B - Stichtag zu alt/neu**:
- GUID existiert, aber nicht zum GCS-Stichtag
- Lösung: Stichtag anpassen oder zeitliche Auflösung verbessern

**Szenario C - Falsche Gruppe**:
- Suche in `PERSDATEN` statt `PERSONDATEN`
- Lösung: Gruppennamen prüfen (aber sollte aus Metadaten kommen)

---

## Test-Plan

1. **Test 1**: Erste Person öffnen → Logs prüfen
   - Welcher Stichtag?
   - GUID gefunden?
   - Abdatum?

2. **Test 2**: Historie-Dialog für beide Personen
   - Person 1: Zuordnung Finanzen Historie?
   - Person 2: Zuordnung Finanzen Historie?
   - Unterschiede?

3. **Test 3**: Datenbank direkt prüfen
   - SELECT * FROM persondaten WHERE guid IN ('39ae18d4...', '0d66233c...');
   - Existiert PERSDATEN.FINANZDATEN-FINANZDATEN?

---

**Status**: Debug-Logs implementiert, bereit für Test
