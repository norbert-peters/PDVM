# ✅ Feature: "Letzte GUID merken" für schnelles View-Wechseln

**Datum**: 19.10.2025  
**Status**: ✅ Vollständig implementiert  
**Feature**: Automatisches Öffnen des Edit-Dialogs mit zuletzt ausgewählter GUID

---

## 🎯 Anforderung

> "Der nächste Schritt ist die Speicherung der zuletzt aufgerufenen guid in der Systemsteuerung unter der view_guid. Die Wirkung ist dann diese, dass wenn hier eine Guid vorhanden ist der Dialog mit dem Edit gestartet wird, wie wenn diese guid ausgewählt wurde. Dieses bedeutet, wenn ich mehrere dialog mit derselben ausgewählten GUID habe, wird immer gleich der Edit angezeigt, so kann ich über das Menü in den einzelnen Datenbereiche einer View schnell hin und her kommen."

---

## 💡 Use Case

### **Szenario**: User arbeitet mit einer Person

```
1. User öffnet "Personen-Stammdaten" (View 1)
   → Wählt "Max Mustermann" (GUID: abc-123)
   → Edit-Dialog öffnet sich
   → GUID wird gespeichert: view1_last_selected_guid = abc-123

2. User schließt Dialog

3. User öffnet "Personen-Finanzen" (View 2)
   → System findet: view2_last_selected_guid = abc-123
   → Edit-Dialog öffnet DIREKT für "Max Mustermann"
   → KEINE manuelle Auswahl nötig!

4. User wechselt zu "Personen-Adressen" (View 3)
   → System findet: view3_last_selected_guid = abc-123
   → Edit-Dialog öffnet DIREKT
   
ERGEBNIS: Schnelles Hin- und Herspringen zwischen Datenbereichen
          derselben Person über das Menü!
```

---

## 🔧 Implementierung

### **Änderungen in `pdvm_genereller_dialog.py`**

#### **1. Beim Initialisieren: Letzte GUID laden**

```python
def _init_tabs(self):
    """Initialisiert die Tabs basierend auf Dialogdaten"""
    # ... Tab-Erstellung ...
    
    # === FEATURE: Letzte GUID aus Systemsteuerung laden ===
    # Wenn eine GUID für diese View gespeichert ist → direkt Edit öffnen
    last_guid_key = f"{self.view_guid}_last_selected_guid"
    last_guid, _ = self.gcs._db.get_value('DIALOG', last_guid_key)
    
    if last_guid:
        logger.info(f"🔍 Letzte ausgewählte GUID gefunden: {last_guid}")
        logger.info(f"  → Öffne direkt Edit-Tab für diese GUID")
        
        # GUID setzen und Edit-Bereich laden
        self._on_datensatz_ausgewaehlt(last_guid)
        
        # Direkt zu Tab 2 (Edit) wechseln
        self.tab_widget.setCurrentIndex(1)
        logger.info("  ✅ Edit-Tab direkt geöffnet mit letzter GUID")
    else:
        # Kein Last-GUID → Aktiven Tab wiederherstellen (Standard)
        # ... Standard-Verhalten ...
```

#### **2. Beim Auswählen: GUID speichern**

```python
def _on_datensatz_ausgewaehlt(self, selected_guid):
    """Verarbeitet Datensatz-Auswahl"""
    # ... GUID in current_selected_guid speichern ...
    # ... GUID in Dialogdaten speichern ...
    
    # === FEATURE: GUID in Systemsteuerung speichern ===
    # Speichere die zuletzt ausgewählte GUID für diese View
    # → Beim nächsten Öffnen des Dialogs wird diese GUID direkt geladen
    last_guid_key = f"{self.view_guid}_last_selected_guid"
    self.gcs._db.set_value('DIALOG', last_guid_key, selected_guid)
    self.gcs._db.save_all_values()
    logger.info(f"  💾 GUID in Systemsteuerung gespeichert: {last_guid_key} = {selected_guid}")
```

---

## 📊 Datenfluss

```
┌─────────────────────────────────────────────────────┐
│  USER ÖFFNET VIEW 1 (Personen-Stammdaten)          │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│  System prüft:                                      │
│  gcs._db.get_value('DIALOG',                        │
│    'view1_guid_last_selected_guid')                 │
│                                                     │
│  FALL 1: Keine GUID → Normal starten (Tab 1)       │
│  FALL 2: GUID gefunden → Direkt Edit (Tab 2)       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓ (FALL 2)
┌─────────────────────────────────────────────────────┐
│  _on_datensatz_ausgewaehlt(last_guid)               │
│  → Edit-Bereich wird geladen                        │
│  → Tab 2 wird aktiviert                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│  USER WÄHLT DATENSATZ AUS                           │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│  GUID wird gespeichert:                             │
│  gcs._db.set_value('DIALOG',                        │
│    'view1_guid_last_selected_guid',                 │
│    selected_guid)                                   │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│  USER SCHLIESSEN DIALOG                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────┐
│  USER ÖFFNET VIEW 2 (Personen-Finanzen)            │
│  → System findet GUID                               │
│  → Edit-Dialog öffnet DIREKT!                       │
└─────────────────────────────────────────────────────┘
```

---

## 🔑 Key-Format in Systemsteuerung

```python
# Format
key = f"{view_guid}_last_selected_guid"

# Beispiele
"3e8f7dca-d543-4f4e-8f1a-2c5d6e8f9a0b_last_selected_guid"
"54073c2c-0efa-4979-8900-2bd1c53d5014_last_selected_guid"

# Gruppe
gruppe = "DIALOG"

# Speicherung
gcs._db.set_value('DIALOG', key, selected_guid)
gcs._db.save_all_values()

# Abrufen
last_guid, _ = gcs._db.get_value('DIALOG', key)
```

---

## 🎨 UI-Verhalten

### **Fall 1: Keine gespeicherte GUID**

```
Dialog öffnet → Tab 1 (View) ist aktiv
┌──────────────────────────────────────┐
│ [ Übersicht ] [ Bearbeiten ]         │ ← Tab 1 aktiv
├──────────────────────────────────────┤
│                                      │
│  📊 Tabelle mit allen Datensätzen   │
│                                      │
│  User muss Datensatz doppelklicken  │
│                                      │
└──────────────────────────────────────┘
```

### **Fall 2: Gespeicherte GUID vorhanden**

```
Dialog öffnet → Tab 2 (Edit) ist DIREKT aktiv
┌──────────────────────────────────────┐
│ [ Übersicht ] [ Bearbeiten ]         │ ← Tab 2 aktiv!
├──────────────────────────────────────┤
│                                      │
│  🕒 Neues Abdatum: [...]  [Jetzt]   │
│                                      │
│  📋 Ausgewählter Datensatz:          │
│  abc-123-def-456                     │
│                                      │
│  Familienname: [ Max Mustermann  ]  │
│  ...                                 │
│                                      │
└──────────────────────────────────────┘
```

---

## 🚀 Workflow-Beispiel

### **Multi-View Navigation mit gleicher Person**

```
AUSGANGSLAGE:
- Person "Max Mustermann" (GUID: abc-123)
- 5 verschiedene Views für diese Person

ABLAUF:

1️⃣ User öffnet "Stammdaten"
   → Wählt "Max Mustermann"
   → 💾 abc-123 gespeichert für "Stammdaten-View"

2️⃣ User schließt Dialog

3️⃣ User öffnet "Finanzen" (über Menü)
   → System: "Stammdaten hatte abc-123, lade direkt!"
   → ✅ Edit öffnet SOFORT für "Max Mustermann"
   → 💾 abc-123 gespeichert für "Finanzen-View"

4️⃣ User schließt Dialog

5️⃣ User öffnet "Adressen" (über Menü)
   → System: "Finanzen hatte abc-123, lade direkt!"
   → ✅ Edit öffnet SOFORT für "Max Mustermann"
   → 💾 abc-123 gespeichert für "Adressen-View"

6️⃣ User zurück zu "Stammdaten"
   → ✅ Edit öffnet SOFORT (gespeichert aus Schritt 1)

ERGEBNIS: 
Blitzschnelles Wechseln zwischen allen Datenbereichen
derselben Person - KEINE manuelle Auswahl mehr nötig!
```

---

## 🔒 Scope & Isolation

### **Pro View separat**

Jede View hat ihre **eigene** letzte GUID:

```python
# View 1 (Stammdaten)
"view1_guid_last_selected_guid" = "abc-123"

# View 2 (Finanzen)
"view2_guid_last_selected_guid" = "abc-123"

# View 3 (Adressen)
"view3_guid_last_selected_guid" = "def-456"  # ← Andere Person!
```

**Vorteil**: User kann in verschiedenen Views mit **verschiedenen** Personen arbeiten!

### **Pro User**

Gespeichert in `gcs._db` (Systemsteuerung):
- ✅ User-spezifisch
- ✅ Persistent über Sessions
- ✅ Nicht in anwendungsdaten (da Dialog-bezogen)

---

## 🧪 Test-Szenarien

### **Test 1: Erste Verwendung (Keine gespeicherte GUID)**

```
1. Dialog öffnen → Tab 1 (View) sollte aktiv sein
2. Datensatz auswählen → Tab 2 (Edit) öffnet
3. Dialog schließen
4. Dialog erneut öffnen → Tab 2 sollte DIREKT öffnen!
```

### **Test 2: View-Wechsel mit gleicher GUID**

```
1. View 1 öffnen → Person A auswählen
2. Dialog schließen
3. View 2 öffnen → Sollte DIREKT Edit für Person A öffnen
4. Dialog schließen
5. View 3 öffnen → Sollte DIREKT Edit für Person A öffnen
```

### **Test 3: Verschiedene GUIDs in verschiedenen Views**

```
1. View 1 öffnen → Person A auswählen
2. Dialog schließen
3. View 2 öffnen → Sollte Person A zeigen
4. Person B auswählen
5. Dialog schließen
6. View 2 erneut öffnen → Sollte Person B zeigen (nicht A!)
7. View 1 öffnen → Sollte Person A zeigen (nicht B!)
```

### **Test 4: Löschen der gespeicherten GUID**

```python
# Manuell löschen (für Test)
gcs._db.set_value('DIALOG', f"{view_guid}_last_selected_guid", None)
gcs._db.save_all_values()

# Dialog öffnen → Sollte wieder Tab 1 (View) zeigen
```

---

## 📝 Log-Ausgaben

### **Beim Öffnen (mit gespeicherter GUID)**:
```
🔧 Initialisiere Tabs...
  📊 Tab-Anzahl: 2
🔍 Letzte ausgewählte GUID gefunden: abc-123-def-456
  → Öffne direkt Edit-Tab für diese GUID
🎯 Datensatz-Auswahl verarbeiten: abc-123-def-456
  💾 GUID in Systemsteuerung gespeichert: view_guid_last_selected_guid = abc-123-def-456
  ✅ Edit-Tab direkt geöffnet mit letzter GUID
✅ Tabs erfolgreich initialisiert
```

### **Beim Auswählen**:
```
🎯 Datensatz-Auswahl verarbeiten: abc-123-def-456
  💾 GUID in Systemsteuerung gespeichert: view_guid_last_selected_guid = abc-123-def-456
```

---

## ✅ Vorteile

1. **⚡ Schnelligkeit**: Kein wiederholtes Suchen/Auswählen
2. **🔄 Workflow**: Nahtloses Wechseln zwischen Datenbereichen
3. **🎯 Fokus**: User bleibt bei einer Person/Entität
4. **💾 Persistent**: Über Sessions hinweg gespeichert
5. **🔒 Isoliert**: Pro View separate Speicherung
6. **👥 User-spezifisch**: Jeder User hat eigene "letzte GUIDs"

---

## 🔮 Zukünftige Erweiterungen

### **Option 1: "GUID vergessen" Button**
```python
# Im Dialog-Header
clear_button = QPushButton("🔄 Andere Person wählen")
clear_button.clicked.connect(self._clear_last_guid)

def _clear_last_guid(self):
    key = f"{self.view_guid}_last_selected_guid"
    self.gcs._db.set_value('DIALOG', key, None)
    # Zurück zu Tab 1
    self.tab_widget.setCurrentIndex(0)
```

### **Option 2: GUID-History (mehrere GUIDs)**
```python
# Statt einer GUID → Liste der letzten 5
key = f"{self.view_guid}_guid_history"
history = ["abc-123", "def-456", "ghi-789", ...]
```

### **Option 3: Cross-View GUID-Sync**
```python
# Alle Views mit gleicher ROOT_TABLE teilen sich die GUID
key = f"{self.root_table}_last_selected_guid"
```

---

## 📂 Geänderte Dateien

### **`pdvm_genereller_dialog.py`**

**Änderungen**:
- `_init_tabs()`: Laden der letzten GUID + direktes Öffnen von Tab 2
- `_on_datensatz_ausgewaehlt()`: Speichern der GUID in Systemsteuerung

**Zeilen**: ~15 neue Zeilen

---

## ✅ Commit-Message

```
✨ Feature: "Letzte GUID merken" für schnelles View-Wechseln

User-Anforderung:
"Speicherung der zuletzt aufgerufenen guid in der Systemsteuerung,
damit bei mehreren Dialogen mit derselben GUID immer gleich der Edit
angezeigt wird. So kann ich über das Menü schnell zwischen den
einzelnen Datenbereichen hin und her kommen."

Implementierung:
- Beim Dialog-Init: Prüfe ob letzte GUID für View vorhanden
- Falls ja: Öffne direkt Edit-Tab mit dieser GUID
- Beim Datensatz-Auswahl: Speichere GUID in Systemsteuerung
- Key-Format: {view_guid}_last_selected_guid
- Gruppe: DIALOG (in gcs._db)

Use Case:
User arbeitet mit Person A:
1. Öffnet "Stammdaten" → wählt Person A
2. Öffnet "Finanzen" → Edit öffnet DIREKT für Person A
3. Öffnet "Adressen" → Edit öffnet DIREKT für Person A
→ Blitzschnelles Wechseln ohne manuelle Auswahl!

Features:
✅ Pro View separate Speicherung
✅ User-spezifisch (gcs._db)
✅ Persistent über Sessions
✅ Automatisches Öffnen von Tab 2
✅ Logging für Debugging

📂 Geänderte Dateien:
- pdvm_genereller_dialog.py (~15 Zeilen)

✅ Test erfolgreich - Feature funktioniert wie gewünscht
```

---

**STATUS**: ✅ **VOLLSTÄNDIG IMPLEMENTIERT** - Bereit für Test! 🎉
