# pdvm_central_systemsteuerung_global.py
# Globale Instanz für die zentrale Systemsteuerung
"""
Globaler Zugriff auf die zentrale Systemsteuerung.

Verwendung:
    import pdvm_central_systemsteuerung_global
    gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
    
    # Direkte Property-Zugriffe:
    stichtag = gcs.stichtag
    expert_mode = gcs.expert_mode
    mode = gcs.mode
"""

from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung

# Globale Systemsteuerung-Instanz
central_systemsteuerung = PdvmCentralSystemsteuerung()
