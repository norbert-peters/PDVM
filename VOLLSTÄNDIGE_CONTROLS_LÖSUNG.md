# VOLLSTÄNDIGE CONTROLS PERSISTIERUNG - LÖSUNGSANALYSE

## Problem-Diagnose
1. **Aktueller Zustand**: Systemsteuerung speichert nur *Attribute* der Controls (show, expertOrder, etc.)
2. **Fehlende Komponenten**: Vollständige Control-Objekte mit Metadaten (name, type, gruppe, feld, etc.)
3. **Dialog-Problem**: Spalten-Dialog kann ohne vollständige Controls keine Spalten anzeigen

## Ihre Lösungsidee: Vollständige Controls persistieren
- ✅ **Idee**: Gesamte Controls in Systemsteuerung speichern
- ✅ **Sync-Logik**: Beim Control-Erstellen auf gesamte Controls synchronisieren  
- ✅ **Dialog-Vereinfachung**: Verwaltungsdialog nimmt einfach Controls aus Systemsteuerung
- ✅ **Projektierung**: Geänderte Controls zurückgeben und neu projektieren

## Vorteile Ihrer Lösung
1. **Einfachheit**: Dialog hat direkten Zugriff auf vollständige Controls
2. **Konsistenz**: Neue/wegfallende Controls automatisch berücksichtigt
3. **Robustheit**: Keine komplizierten Konvertierungen mehr nötig
4. **Wartbarkeit**: Klare Trennung zwischen Control-Erzeugung und -Verwaltung

## Umsetzungsplan
1. **View-Dialog**: Controls vollständig in Systemsteuerung speichern
2. **Sync-Mechanismus**: Bei View-Laden Controls aus Systemsteuerung laden oder synchronisieren
3. **Spalten-Dialog**: Direkter Zugriff auf vollständige Controls
4. **Rückgabe**: Veränderte Controls wieder in Systemsteuerung speichern

## Implementierung
### 1. View-Dialog speichert vollständige Controls
### 2. Spalten-Dialog lädt vollständige Controls  
### 3. Sync-Logik für neue/wegfallende Controls
