# 🚀 PDVM V2.0 - Neuaufbau mit linearer Architektur

**Branch:** `v2.0-neuaufbau`  
**Basis:** V0.9 (Tag: `v0.9-stable-2025-10-30`)  
**Status:** 📋 PLANUNG & DESIGN PHASE  
**Erstellt:** 30.10.2025

---

## ⚠️ WICHTIG: Branch-Strategie

Dieses Repository hat **zwei parallele Entwicklungs-Branches**:

### ✅ **V0.9 STABLE** - Branch: `funktionierender-stand-29sept`
- **Status:** PRODUKTIV / NUR BUGFIXES
- **Verwendung:** Aktuelles funktionierendes System
- Tag: `v0.9-stable-2025-10-30`

### 🚀 **V2.0 NEUAUFBAU** - Branch: `v2.0-neuaufbau` ← **SIE SIND HIER**
- **Status:** AKTIVE ENTWICKLUNG / KOMPLETT NEU
- **Verwendung:** Kompletter Architektur-Neuaufbau
- **KEINE Rückwärts-Kompatibilität** zu V0.9!

---

## 📋 V2.0 HAUPT-ÄNDERUNGEN

### 1. **Lineares Menü-System**
❌ Alt: Multi-Tree (`PD_grund`, `PD_menu`, `PD_zusatz`)  
✅ Neu: Flache Struktur mit Parent-Referenzen

### 2. **System-Tabellen mit Prefix**
❌ Alt: `menudaten`, `viewdaten` (mit User-Tabellen vermischt)  
✅ Neu: `sys_menudaten`, `sys_viewdaten` (klare Trennung)

### 3. **HTTP-basierte Authentifizierung**
❌ Alt: Direkter DB-Login  
✅ Neu: Zentraler Auth-Service + Mandantenauswahl

### 4. **Security-Layer (sec_id)**
❌ Alt: Keine Datensatz-Berechtigungen  
✅ Neu: GUID-basierte Zugriffsrechte pro Zeile

---

## 📚 DOKUMENTATION

Bitte lesen Sie die vollständige Planung:

1. **[V2_PROJEKT_PLAN.md](V2_PROJEKT_PLAN.md)** - Kompletter Projekt-Plan mit Zeitplan
2. **[V2_GIT_SETUP.md](V2_GIT_SETUP.md)** - Git-Workflow zwischen V0.9 und V2.0
3. **V2_ARCHITEKTUR.md** - Detaillierte Architektur ⏳ TODO
4. **V2_MENU_SYSTEM.md** - Lineares Menü-Design ⏳ TODO
5. **V2_AUTH_SERVICE.md** - HTTP Auth Spezifikation ⏳ TODO

---

## 🔄 ZWISCHEN BRANCHES WECHSELN

### Zu V0.9 wechseln (z.B. um Code anzuschauen):
```powershell
git checkout funktionierender-stand-29sept
```

### Zurück zu V2.0:
```powershell
git checkout v2.0-neuaufbau
```

### Code aus V0.9 übernehmen:
```powershell
# Auf V2.0 Branch sein!
git checkout funktionierender-stand-29sept -- pdvm_datetime.py
git mv pdvm_datetime.py v2_datetime.py
```

---

## 📂 GEPLANTE STRUKTUR

```
v2.0-neuaufbau/
├── v2_main.py                    # Neuer Entry Point
├── v2_core/                      # Kern-System
│   ├── database_manager.py       # sys_ Tabellen
│   ├── security_manager.py       # sec_id Logik
│   ├── menu_system.py            # Linear!
│   └── command_dispatcher.py
├── v2_auth_service/              # HTTP Auth
│   ├── api.py                    # FastAPI/Flask
│   └── models.py
├── v2_ui/                        # UI-Layer
│   ├── view_controller.py        # Aus V0.9 übernehmen
│   ├── matrix_pipeline.py        # ✅ Aus V0.9 übernehmen
│   └── dialog_manager.py
├── migrations/                   # Daten-Migration
│   └── migrate_v09_to_v20.py
└── tests/                        # Tests
    └── ...
```

---

## 🎯 NÄCHSTE SCHRITTE

### DIESE WOCHE:
- [ ] V2_ARCHITEKTUR.md erstellen
- [ ] V2_MENU_SYSTEM.md erstellen
- [ ] V2_AUTH_SERVICE.md erstellen
- [ ] Datenbank-Schema entwerfen

### NÄCHSTE WOCHE:
- [ ] Ersten Prototyp: Lineares Menü-System
- [ ] HTTP Auth-Service Minimal-Version
- [ ] sys_ Tabellen Schema testen

---

## ⚠️ ENTWICKLUNGS-REGELN

1. **NIEMALS** V0.9 und V2.0 mergen! Nur einzelne Dateien übernehmen.
2. **V0.9 Branch** nur für Bugfixes nutzen
3. **V2.0 Branch** freie Entwicklung, keine Rücksicht auf Kompatibilität
4. **Separate Datenbank** für V2.0 Tests verwenden (`datenbank_v2.db`)

---

## 📞 BEI FRAGEN

Siehe Git-Workflow-Dokumentation: [V2_GIT_SETUP.md](V2_GIT_SETUP.md)

**Happy Coding! 🚀**
