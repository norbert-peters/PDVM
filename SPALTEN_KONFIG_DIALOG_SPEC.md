# 🏗️ SPALTEN-KONFIGURATIONS-DIALOG - SPEZIFIKATION

## 📋 Anforderungen Analyse:

### 1. **Projektion Management**
- **ExpertMode=true:** Alle Spalten anzeigen
- **NormalMode=false:** Nur Spalten mit expertMode=false

### 2. **Reihenfolgen-System**
- **ExpertMode:** ExpertOrder (für alle Spalten)
- **NormalMode:** DisplayOrder (nur für Normal-Spalten)

### 3. **Persistierung**
- **OK-Button:** Order + Show-Status speichern
- **Tabellen-Projektion:** Erneut aufrufen nach Änderungen

### 4. **Show-Management**
- **Beide Modi:** show=true/false pro Zeile änderbar
- **ExpertMode zusätzlich:** expertMode=true/false änderbar

### 5. **Reorder-Logik**
- **Auf/Ab Buttons:** Spalten verschieben
- **NormalMode spezial:** show=false → Ende, neue show=true → Ende der show=true

### 6. **Integration**
- **Global Systemsteuerung:** ExpertMode direkt verwenden
- **Synchronisation:** show + Orders beim Control-Aufbau

## 🎯 Dialog Komponenten:

```
┌─ Spalten Konfiguration ─────────────────────────┐
│ Mode: [ExpertMode Checkbox] Expert-Modus       │
│                                                 │
│ ┌─ Spalten Liste ─────────────────────────────┐ │
│ │ □ Spalte1  [Expert] [▲] [▼] [Show]          │ │
│ │ □ Spalte2  [Expert] [▲] [▼] [Show]          │ │
│ │ ■ Spalte3          [▲] [▼] [Show]          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│                    [OK] [Abbrechen]             │
└─────────────────────────────────────────────────┘
```

## 🔧 Technische Umsetzung:

### Klasse: `PdvmSpaltenKonfigDialog`
- **Basis:** QDialog
- **Data Source:** View-Konfiguration + Global Systemsteuerung
- **Logik:** Intelligente Projektion + Reorder-Management
- **Persistierung:** Spalten-Metadaten + Orders speichern

### Integration Points:
- **pdvm_view_dialog.py:** Dialog aufrufen
- **pdvm_central_systemsteuerung.py:** ExpertMode lesen/schreiben
- **Column Metadata:** ExpertMode + Orders verwalten
