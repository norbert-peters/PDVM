# Quick fix for pdvm_view_widget.py - Central Stichtag Architecture

Diese Datei implementiert die zentrale Stichtag-Architektur:

## Änderungen:

### 1. Neue reload() Methode ohne Parameter
- Ruft PdvmCentralStichtagManager.get_stichtag_float() auf
- Eliminiert Parameter-Weitergabe
- Vermeidet Synchronisationsfehler

### 2. reload_with_stichtag() als deprecated
- Nur für Kompatibilität
- Ruft zentrale reload() auf
- Ignoriert übergebenen Parameter

### 3. ViewManager bekommt refresh_with_central_stichtag()
- Statt Parameter zu übergeben
- Holt sich Stichtag zentral ab

## Implementation:

```python
def reload(self):
    """
    ZENTRALE STICHTAG-ARCHITEKTUR: View mit zentralem Stichtag refreshen
    """
    try:
        # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
        from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
        central_manager = PdvmCentralStichtagManager()
        new_stichtag = central_manager.get_stichtag_float()
        
        logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - Refresh mit zentralem Stichtag: {new_stichtag}")
        
        # SYNCHRONISATION mit zentralem Stichtag
        old_stichtag = getattr(self, 'stichtag', None)
        self.stichtag = new_stichtag
        self.call_daten['stichtag'] = new_stichtag
        
        # ViewManager mit zentralem Stichtag refreshen
        if self.view_manager:
            refreshed_count = self.view_manager.refresh_with_central_stichtag()
            logger.info(f"📊 {refreshed_count} Datensätze mit zentralem Stichtag refresht")
            
            self._reload_table_completely()
            logger.info(f"✅ ZENTRALER REFRESH erfolgreich")
        else:
            self.load_data()
            
    except Exception as e:
        logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
        if 'old_stichtag' in locals() and old_stichtag is not None:
            self.stichtag = old_stichtag
            self.call_daten['stichtag'] = old_stichtag
```

## Nächste Schritte:
1. ViewManager um refresh_with_central_stichtag() erweitern
2. Alle Aufrufe von reload_with_stichtag() durch reload() ersetzen
3. System testen
