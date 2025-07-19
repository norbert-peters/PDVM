# Universelle Tab-Dialog-Architektur mit InputControl-Integration

## 🎯 Überblick

Die erweiterte Architektur implementiert Ihre Anforderungen für eine universelle, Tab-basierte Dialog-Lösung mit einheitlicher InputControl-Integration und struktureller Zugriffskontrolle.

## 🏗️ Architektur-Prinzipien

### 1. **Einheitliche Datenpflege über InputControl**
- Alle Datenbearbeitung erfolgt über das bestehende InputControl-System
- Konsistente Bedienung über alle Modi hinweg
- Wiederverwendung der bewährten IC-Parameter-Logik

### 2. **Strukturelle Zugriffsberechtigung**
- Berechtigungen werden über Frame-/Menü-Ebene gesteuert
- Klare Trennung verschiedener Funktionsbereiche
- Kein komplexes Feld-Level-Rechte-System im ersten Schritt

### 3. **IC-basierte Feld-Kontrolle (Erweiterung)**
- Spätere Möglichkeit für feldspezifische Rechte
- Über IC-Parameter steuerbar: `visible: false` (ausblenden), `readonly: true` (nur lesen)
- Eingabeprüfungen über bestehende IC-Validation

## 📋 Modi-Übersicht

### **Mode 0: Datenpflege** 📝
- **Zweck**: Standard-Datenbearbeitung
- **Berechtigung**: Alle Benutzer
- **Tabs**: View + InputFrame
- **InputControl**: Standard-Felder basierend auf Framedaten

### **Mode 1: Pflege Framedaten** 🏗️
- **Zweck**: Verwaltung von Frame-Strukturen
- **Berechtigung**: Administrator
- **Tabs**: View + Frame-Editor
- **InputControl**: Frame-Definition, Tab-Konfiguration, Gruppierungsstile

### **Mode 2: Pflege Menü** 📋
- **Zweck**: Menü-Konfiguration
- **Berechtigung**: Administrator
- **Tabs**: View + Menü-Editor
- **InputControl**: Menü-Struktur, Berechtigungen, Icons

### **Mode 3: Pflege Anwendung** ⚙️
- **Zweck**: System-Einstellungen
- **Berechtigung**: Administrator
- **Tabs**: View + Settings
- **InputControl**: Anwendungsparameter, Datenbank-Config

### **Mode 4: Pflege Benutzereinstellungen** 👤
- **Zweck**: Persönliche Einstellungen
- **Berechtigung**: Eigener Benutzer
- **Tabs**: View + User-Settings
- **InputControl**: Sprache, Theme, Preferences

### **Mode 5: Pflege Benutzer** 👥
- **Zweck**: Benutzer-Verwaltung
- **Berechtigung**: Administrator
- **Tabs**: View + User-Management
- **InputControl**: Benutzer-Daten, Rollen, Berechtigungen

### **Mode > 5: Nicht definiert** ❓
- **Anzeige**: Hinweis "Modus nicht vorhanden"
- **Funktionalität**: Keine

## 🗂️ Tab-Struktur

### **1. View-Tab (immer verfügbar)**
- Zeigt aktuelle Daten in konfigurierbarer Gruppierung
- Verweist auf ViewDaten über GUID
- Gruppierungsstil per Tab konfigurierbar

### **2. InputFrame-Tab (modus-spezifisch)**
- Nutzt bestehende InputControl-Architektur
- Automatische IC-Generierung basierend auf Modus
- Verschiedene Gruppierungsstile: `sections`, `accordion`, `tabs`, `inline`

## 🔧 Framedaten-Struktur

### **Erweiterte Framedaten**
```python
{
    "frame_guid": "...",
    "frame_name": "Universal Dialog für XYZ",
    "view_guid": "...",  # Verknüpfung zu ViewDaten
    
    "dialog_config": {
        "dialog_type": "universal_tab_dialog",
        "mode": 0,
        "default_width": 1000,
        "default_height": 700,
        "auto_save": True,
        "confirm_changes": True
    },
    
    "tabs": [
        {
            "tab_id": "view_tab",
            "tab_name": "Ansicht",
            "tab_type": "view",
            "tab_order": 1,
            "tab_icon": "👁️",
            "view_guid": "...",
            "grouping_style": "sections",
            "visible_modes": [0, 1, 2, 3, 4, 5]
        },
        {
            "tab_id": "data_maintenance",
            "tab_name": "Daten bearbeiten",
            "tab_type": "inputframe",
            "tab_order": 2,
            "tab_icon": "📝",
            "grouping_style": "accordion",
            "visible_modes": [0]
        }
    ],
    
    "mode_config": {
        "mode_id": 0,
        "mode_name": "Datenpflege",
        "mode_icon": "📝",
        "requires_admin": False,
        "read_only": False
    },
    
    "database_config": {
        "central_db_instance": "main",
        "primary_table": "...",
        "primary_key_field": "..."
    }
}
```

## 🎛️ InputControl-Integration

### **IC-Generierung per Modus**
- Automatische IC-Konfiguration basierend auf Tab-Typ
- Gruppierung über `group_id` und `grouping_style`
- Mode-spezifische Feldsets

### **Beispiel IC-Konfiguration**
```python
{
    "grunddaten_name": {
        "source_path": "root",
        "label": "Name",
        "type": "text",
        "required": True,
        "group_id": "grunddaten",
        "grouping_style": "sections",
        "visible_modes": [0, 1],
        "access_control": {
            "requires_admin": False
        }
    }
}
```

## 🔒 Zugriffskontrolle

### **Frame-Ebene**
- Berechtigung für gesamten Dialog
- Modi-spezifische Zugriffsprüfung
- Admin-Anforderung für System-Modi

### **Tab-Ebene**
- Tab-Sichtbarkeit basierend auf Modus
- Tab-spezifische Berechtigungen

### **Feld-Ebene (zukünftig)**
- IC-Parameter `visible: false` → Feld ausblenden
- IC-Parameter `readonly: true` → Nur-Lesen-Zugriff
- Validation über bestehende IC-Mechanismen

## 🚀 Implementation

### **Bestehende Module erweitert:**
1. **`TestPdvmInputFrame.py`** - Haupt-Test-Anwendung mit Modi-Auswahl
2. **`universal_frame_structure.py`** - Framedaten-Struktur für Tab-Dialog
3. **`universal_tab_dialog.py`** - PyQt5-Widget für universellen Dialog
4. **`universal_input_control.py`** - IC-Integration für Tab-basierte Modi

### **Integration mit bestehender Architektur:**
- Kompatibilität zu bisherigem `PdvmDialogWidget`
- Wiederverwendung von IC-Parameter-System
- Integration in PdvmCentralDatenbank-Architektur

## 🎯 Vorteile

1. **Einheitlichkeit**: Alle Datenpflege über bewährtes InputControl
2. **Skalierbarkeit**: Einfache Erweiterung um neue Modi
3. **Flexibilität**: Verschiedene Gruppierungsstile pro Tab
4. **Sicherheit**: Strukturelle Zugriffskontrolle ohne Komplexität
5. **Kompatibilität**: Bestehende Systeme bleiben funktionsfähig

## 📝 Nächste Schritte

1. **Test der erweiterten Anwendung** mit verschiedenen Modi
2. **Integration in bestehende PdvmCentralDatenbank**
3. **Erweiterung der ViewDaten-Struktur** falls nötig
4. **Performance-Optimierung** für große Datenmengen
5. **Dokumentation** für Entwickler und Anwender

Die Architektur erfüllt alle Ihre Anforderungen und bietet eine solide Basis für die universelle Tab-basierte Dialog-Lösung mit einheitlicher InputControl-Integration.
