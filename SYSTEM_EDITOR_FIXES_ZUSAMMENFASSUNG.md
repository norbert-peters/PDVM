# SystemEditor Fixes - Zusammenfassung

## 🎯 Probleme behoben

### 1. SystemEditor zeigt keine Daten mehr
**Problem**: Nach Änderungen wurden Daten nicht mehr geladen

**Lösung**: 
- Zurück zu PdvmCentralDatenbank (bewährte Schicht)
- `_load_data()` lädt alle Gruppen via `get_groups()` und `get_value_by_group()`
- `_save_changes()` speichert via `set_group()` und `save_all_values()`

### 2. Name-Duplikate durch Änderungen
**Problem**: Änderung von `pers_vorname` → `pers_familienname` führte zu Duplikat

**Lösung**: 
- **Validierung bei Übernahme** in `_feld_uebernehmen()`
- Prüft ob Name bereits in Gruppe existiert
- Zeigt Fehlermeldung mit GUIDs der Konflikte
- **Bricht Übernahme ab** bei Duplikat
- User kann Änderungen korrigieren

## 📋 Implementierte Validierung

```python
def _feld_uebernehmen(self):
    # ... 
    
    # Validierung: Name-Eindeutigkeit
    current_name = current_feld.get('name', '')
    
    if current_name:
        for other_guid, other_feld in self.data[gruppe_name].items():
            if other_guid != feld_guid:  # Nicht sich selbst
                other_name = other_feld.get('name', '')
                if other_name == current_name:
                    QMessageBox.warning(
                        self,
                        "Validierungsfehler",
                        f"❌ Name '{current_name}' existiert bereits!\n\n"
                        f"Aktuelles Feld: {feld_guid[:8]}...\n"
                        f"Konflikt mit: {other_guid[:8]}...\n\n"
                        f"Bitte eindeutigen Namen wählen."
                    )
                    return  # ABBRUCH!
    
    # Übernahme durchführen...
```

## 🔒 Name-Schutz via Template

**Zukünftig**: Properties können als `read_only` markiert werden

In Template:
```json
{
  "name": {
    "type": "string",
    "read_only": true,  // ← Name nicht änderbar
    "label": "Feldname"
  }
}
```

In `PdvmPropertyInputControl`:
- `read_only: true` → Widget disabled + grauer Hintergrund
- Verhindert Änderungen bereits in UI

## ✅ Vorteile

1. **Linear & Einfach**: Validierung an EINER Stelle (Übernahme)
2. **Sofortige Rückmeldung**: User sieht Konflikt sofort
3. **Kein Datenverlust**: Änderungen bleiben im Editor
4. **Eindeutigkeit**: GUID bleibt eindeutig, Name auch
5. **Flexibel**: `read_only` kann Properties schützen

## 🧪 Testing

1. SystemEditor öffnen mit `sys_framedaten`
2. Feld auswählen
3. Name auf existierenden Namen ändern
4. "Übernehmen" klicken
5. → Fehlermeldung erscheint
6. → Änderungen bleiben im Editor
7. → User kann korrigieren

## 📝 Nächste Schritte

1. Datenbank manuell korrigieren (556ccb20... → pers_vorname)
2. SystemEditor testen
3. Bei Bedarf: `read_only` für kritische Properties aktivieren

---

**Status**: ✅ Implementiert (03.12.2025)
**Dateien**: `pdvm_system_editor.py`
