"""
Zentrale Spalten-Projektion basierend auf Controls
Eine einzige Quelle der Wahrheit für Spalten-Sortierung
"""

import logging
logger = logging.getLogger(__name__)

import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

def get_projected_columns(basis_columns):
    """
    ZENTRALE SPALTEN-PROJEKTION
    - Eine einzige Funktion für Dialog UND Tabelle
    - Sortiert ausschließlich nach expertOrder/displayOrder aus den Controls
    - ExpertMode: Alle Spalten nach expertOrder
    - NormalMode: Nur show==True nach displayOrder
    
    Returns: Liste der sortierten Spalten-Objekte
    """
    try:
        if gcs.global_expert_mode:
            # ExpertMode: Alle Spalten nach expertOrder sortiert
            projected_columns = sorted(basis_columns, key=lambda c: c.get('expertOrder', 999))
            logger.debug(f"📊 ExpertMode: {len(projected_columns)} Spalten nach expertOrder sortiert")
        else:
            # NormalMode: Nur show==True Spalten nach displayOrder sortiert  
            visible_columns = [col for col in basis_columns if col.get('show', False)]
            projected_columns = sorted(visible_columns, key=lambda c: c.get('displayOrder', 999))
            logger.debug(f"📊 NormalMode: {len(projected_columns)} sichtbare Spalten nach displayOrder sortiert")
        
        # Debug-Output für Überprüfung
        for i, col in enumerate(projected_columns[:5]):  # Nur erste 5 für Log
            order_key = 'expertOrder' if gcs.global_expert_mode else 'displayOrder'
            logger.debug(f"  {i}: {col['name']} ({order_key}={col.get(order_key, '?')})")
            
        return projected_columns
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Spalten-Projektion: {e}")
        return basis_columns  # Fallback
