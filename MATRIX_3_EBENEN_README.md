# 3-Ebenen Matrix-Struktur - README

## 🎯 Was ist das?

Die **3-Ebenen Matrix-Struktur** ist die zentrale Datenarchitektur für alle Ansichten im PDVM-System. 

**Kernprinzip**: Jeder Datenwert hat **3 separate Ebenen** im Memory:

```
EBENE 1: Rohdatum        → Direkt aus Datenbank
EBENE 2: AB-Datum (roh)  → Änderungs-Zeitstempel
EBENE 3: Formatiert      → Länderspezifisch (DEU/ENG/USA)
```

## ⚡ Quick Start

```python
# 1. Daten aus DB holen
result = instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
wert, abdatum = result[0], result[1] if isinstance(result, tuple) else (result, None)

# 2. ALLE 3 EBENEN befüllen (atomic!)
row_data[control_key] = wert                                              # EBENE 1
row_data[f"{control_key}_abdatum"] = abdatum                              # EBENE 2
row_data[f"{control_key}_formatiertes_abdatum"] = self._format_abdatum(abdatum)  # EBENE 3
```

## 📁 Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `MATRIX_3_EBENEN_STRUKTUR.md` | 📖 Vollständige Dokumentation |
| `MATRIX_3_EBENEN_ZUSAMMENFASSUNG.md` | 📋 Executive Summary |
| `MATRIX_3_EBENEN_VISUAL.txt` | 🎨 ASCII-Art Diagramme |
| `matrix_3_ebenen_example.py` | 💻 Code-Beispiele |
| `.github/copilot-instructions.md` | 🤖 AI-Assistenten Integration |

## 🔧 Implementierung

| Komponente | Datei |
|------------|-------|
| Matrix-Pipeline | `pdvm_view_matrix_manager.py` |
| BasisMatrix | `pdvm_view_dialog.py` |
| Daten-Layer | `pdvm_view_daten_manager.py` |
| Formatierung | `pd_datetime.py` |
| UI-Integration | `pdvm_view_widget.py` |

## ✅ DO's

- ✅ Alle 3 Ebenen **zusammen** befüllen
- ✅ Show-Spalten kopieren **alle 3 Ebenen**
- ✅ `_format_abdatum()` für EBENE 3 verwenden
- ✅ EBENE 3 in UI-Tooltips anzeigen
- ✅ EBENE 1 für Filter/Suche verwenden

## ❌ DON'Ts

- ❌ Nur EBENE 1 befüllen
- ❌ Nachträgliche Formatierung
- ❌ Show-Spalten ohne EBENE 2+3
- ❌ Direkte Formatierung in UI
- ❌ Inkonsistente Patterns

## 🌍 Formatierung

Automatisch länderspezifisch via `pdvm_DateTime`:

```python
# Raw: 2024310.12500

# DEU → "05.11.2024 03:00:00"
# ENG → "05/11/2024 03:00:00"
# USA → "11/05/2024 03:00:00"
```

## 📊 Memory

Pro Feld: ~36-48 Bytes (3 Keys)  
Bei 1000 Zeilen × 100 Felder: **~4.6 MB**

**Vorteil**: Keine Neu-Berechnungen → **Maximale Performance**

## 🐛 Debugging

```python
from matrix_3_ebenen_example import Matrix3EbenenExample

matrix_manager = Matrix3EbenenExample(gcs)
matrix_manager._debug_print_matrix_structure(row_data)
```

## 📚 Weitere Infos

Siehe `MATRIX_3_EBENEN_STRUKTUR.md` für:
- Detaillierte Architektur-Beschreibung
- Datenfluss-Pipeline
- UI-Integration
- Beispiel-Code
- Troubleshooting

## 💡 Beispiel

```python
# Matrix-Row Struktur:
row_data = {
    'uid_original': '54073c2c-...',
    
    # Geburtsdatum (3 Ebenen)
    'geburtsdatum_original': 1980001.0,
    'geburtsdatum_original_abdatum': 2024310.12500,
    'geburtsdatum_original_formatiertes_abdatum': "05.11.2024 03:00:00",
    
    # Familienname (3 Ebenen)
    'familienname_original': 'Müller',
    'familienname_original_abdatum': 2024305.08000,
    'familienname_original_formatiertes_abdatum': "01.11.2024 01:55:12",
    
    # Show-Spalten (3 Ebenen kopiert)
    'geburtsdatum_show': 1980001.0,
    'geburtsdatum_show_abdatum': 2024310.12500,
    'geburtsdatum_show_formatiertes_abdatum': "05.11.2024 03:00:00",
}
```

---

**Status**: ✅ Produktionsreif  
**Version**: PDVM-System v0.9  
**Stand**: Oktober 2025
