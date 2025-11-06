# 📝 Log-Rotation System V2

## ✅ Implementiert in `v2_main.py`

### Funktionsweise

**Automatische Log-Rotation alle 10 Starts:**

| Start-Nummer | Log-Datei | 
|--------------|-----------|
| 1-10 | `v2_main_1.log` |
| 11-20 | `v2_main_2.log` |
| 21-30 | `v2_main_3.log` |
| 31-40 | `v2_main_4.log` |
| ... | ... |

### Technische Details

1. **Start-Counter**: `.v2_main_starts` (versteckte Datei im Projekt-Root)
   - Enthält nur eine Zahl (aktueller Start-Count)
   - Wird bei jedem Start hochgezählt
   
2. **Log-Nummer Berechnung**: 
   ```python
   log_number = ((start_count - 1) // 10) + 1
   ```
   
3. **Automatische Initialisierung**:
   - Wenn `.v2_main_starts` nicht existiert → Start bei 1
   - Wenn Datei defekt/unleserlich → Start bei 0

### Beispiel-Ablauf

```
Start #1  → v2_main_1.log
Start #2  → v2_main_1.log
Start #3  → v2_main_1.log
...
Start #10 → v2_main_1.log
Start #11 → v2_main_2.log  ← NEUE DATEI!
Start #12 → v2_main_2.log
...
Start #20 → v2_main_2.log
Start #21 → v2_main_3.log  ← NEUE DATEI!
```

### Console Output

Bei jedem Start siehst du:
```
🚀 Start #15 → Log: v2_main_2.log
📝 Logging initialisiert: v2_main_2.log
```

### Vorteile

✅ **Automatisch**: Keine manuelle Verwaltung nötig  
✅ **Übersichtlich**: Alte Logs bleiben erhalten (nicht überschrieben)  
✅ **Debuggbar**: Start-Nummer zeigt, wann welcher Log erstellt wurde  
✅ **Persistent**: Counter überlebt Neustarts  
✅ **Failsafe**: Fehler beim Counter-Schreiben brechen Programm nicht ab

### Alte Logs löschen

**Manuell alle Logs löschen:**
```powershell
Remove-Item "v2_main_*.log"
```

**Counter zurücksetzen:**
```powershell
Remove-Item ".v2_main_starts"
```

**Komplett Clean Start:**
```powershell
Remove-Item "v2_main_*.log"; Remove-Item ".v2_main_starts"
```

### .gitignore Empfehlung

Füge zu `.gitignore` hinzu:
```
# V2 Log Files
v2_main_*.log
.v2_main_starts
```

---

**IMPLEMENTIERT**: ✅ 05.11.2025  
**GETESTET**: ⏳ Wartet auf ersten Start
