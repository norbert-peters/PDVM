# 🧪 V2.0 LOGIN-FLOW TEST-ANLEITUNG

**Datum:** 30.10.2025  
**Version:** 1.0  
**Status:** ✅ Implementiert & Testbereit

---

## 📋 ÜBERSICHT

Der **V2.0 Login-Flow** ist vollständig implementiert und bereit zum Testen:

1. ✅ **Login-Dialog** (`v2_login_dialog.py`) - Email/Passwort mit bcrypt
2. ✅ **Mandanten-Auswahl** (`v2_mandanten_dialog.py`) - Dropdown aus sys_mandanten
3. ✅ **Hauptanwendung** (`v2_main.py`) - Entry-Point mit rudimentärer Anzeige

---

## 🔐 TEST-ZUGÄNGE

### **Admin-User:**
- **Email:** `admin@super.de`
- **Passwort:** `admin`
- **Zugriff:** mandant_001 + mandant_002
- **Rollen:** admin
- **Security:** sec-admin-full

### **Work-User:**
- **Email:** `user@super.de`
- **Passwort:** `user`
- **Zugriff:** nur mandant_001
- **Rollen:** user, vertrieb
- **Security:** sec-public-read, sec-vertrieb

---

## 🚀 KOMPLETTEN FLOW TESTEN

```bash
python v2_main.py
```

**Ablauf:**
1. **Login-Dialog** öffnet sich
2. Email + Passwort eingeben
3. **Mandanten-Dialog** öffnet sich
4. Mandant aus Dropdown wählen
5. **Hauptanwendung** zeigt User-Daten + Mandanten-Info

---

## 🧪 EINZELNE KOMPONENTEN TESTEN

### **1. Nur Login-Dialog:**
```bash
python v2_login_dialog.py
```
- Testet Email/Passwort-Validierung
- Testet bcrypt-Verifikation
- Zeigt User-Daten nach erfolgreichem Login

### **2. Nur Mandanten-Dialog:**
```bash
python v2_mandanten_dialog.py
```
- Mock User-Daten werden verwendet
- Zeigt Mandanten-Liste aus sys_mandanten
- Testet Mandanten-Auswahl

---

## ✅ TEST-SZENARIEN

### **Szenario 1: Admin - Beide Mandanten**
1. Login: `admin@super.de` / `admin`
2. Mandanten-Auswahl: Dropdown zeigt 2 Mandanten
3. Wähle "Hauptverwaltung (mandant_001)"
4. Hauptanwendung zeigt:
   - User: Norbert Peters
   - Rollen: admin
   - Mandant: Hauptverwaltung
   - Start-Menü GUID

### **Szenario 2: User - Nur ein Mandant**
1. Login: `user@super.de` / `user`
2. Mandanten-Auswahl: Dropdown zeigt nur 1 Mandant
3. Wähle "Hauptverwaltung (mandant_001)"
4. Hauptanwendung zeigt:
   - User: Laurenne Hans
   - Rollen: user, vertrieb
   - Mandant: Hauptverwaltung

### **Szenario 3: Falsches Passwort**
1. Login: `admin@super.de` / `falsch`
2. Fehlermeldung: "Falsches Passwort!"
3. Dialog bleibt offen
4. Passwort-Feld wird geleert

### **Szenario 4: Unbekannter User**
1. Login: `test@test.de` / `test`
2. Fehlermeldung: "Benutzer 'test@test.de' nicht gefunden!"
3. Dialog bleibt offen

### **Szenario 5: Login abbrechen**
1. Login-Dialog: "Abbrechen" klicken
2. Anwendung beendet sich
3. Keine Fehlermeldungen

---

## 📊 WAS WIRD ANGEZEIGT

### **Hauptanwendung zeigt:**

1. **User-Info:**
   - Name, Email, UID
   - Rollen
   - Security-Profiles

2. **Mandanten-Info:**
   - Name, ID, DB-Name
   - Land, Status

3. **Einstellungen:**
   - Theme, Language, Country
   - Mode, Stichtag

4. **MeineApps:**
   - Start-Menü GUID

---

## 🔍 WICHTIGE PRÜFPUNKTE

### **Login-Dialog:**
- ✅ Email-Validierung (nicht leer)
- ✅ Passwort-Validierung (nicht leer)
- ✅ bcrypt-Verifikation funktioniert
- ✅ User-Daten werden einmalig geladen
- ✅ User-Daten werden als Dict weitergegeben

### **Mandanten-Dialog:**
- ✅ Mandanten-Liste aus User-Daten
- ✅ Mandanten-Info aus sys_mandanten geladen
- ✅ Default-Mandant vorausgewählt
- ✅ Dropdown zeigt "Name (ID)"

### **Hauptanwendung:**
- ✅ User-Daten NICHT erneut geladen
- ✅ Alle Gruppen angezeigt (USER, SETTINGS, PERMISSIONS, MEINEAPPS, ANWENDUNGEN)
- ✅ Mandanten-Info korrekt
- ✅ Fenster-Titel zeigt Mandanten-Name

---

## 🐛 BEKANNTE LIMITIERUNGEN

1. **Rudimentäre Hauptanwendung:**
   - Zeigt nur Daten an
   - Keine Menü-Funktionalität
   - Keine View-Funktionalität
   - → Für initiales Testing ausreichend

2. **Keine Fehlerbehandlung für fehlende Mandanten-DB:**
   - `Daten/mandant_001/datenbank.db` existiert noch nicht
   - → Wird in nächsten Schritten erstellt

3. **Keine Session-Verwaltung:**
   - Logout nicht implementiert
   - User-Wechsel nicht implementiert
   - → Für V2.0 Phase 1 nicht nötig

---

## 📋 NÄCHSTE SCHRITTE

### **Phase 1: Mandanten-Datenbanken erstellen** ⏳
```bash
python v2_create_mandant_databases.py
```
- Erstellt `Daten/mandant_001/datenbank.db`
- Erstellt `Daten/mandant_002/datenbank.db`
- Mit sys_* Tabellen (sys_menudaten, sys_viewdaten, etc.)

### **Phase 2: Lineares Menü-System** ⏳
- V2 Menu-Handler implementieren
- Menü-Daten aus mandantenspezifischer DB laden
- MeineApps.START Menü anzeigen

### **Phase 3: View-System integrieren** ⏳
- View-Pipeline an Mandanten-DB anpassen
- GCS mit mandantenspezifischer DB initialisieren
- Stichtag-System pro Mandant

---

## 💡 TESTEN SIE JETZT!

```bash
# Kompletter Flow
python v2_main.py

# Einzelne Komponenten
python v2_login_dialog.py
python v2_mandanten_dialog.py
```

**Viel Erfolg beim Testen!** 🚀
