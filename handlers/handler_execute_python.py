"""
Handler: Python-Code ausführen
================================
Führt Python-Code-String aus (z.B. aus alten Menü-Commands)

⚠️ SICHERHEITSHINWEIS: Nur für vertrauenswürdige Commands verwenden!

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Führt Python-Code aus
    
    Args:
        params: {
            'code': str,                # Python-Code (required)
            'method_name': str,         # Alternativer Methodenname auf main_app
            'timeout': int              # Timeout in Sekunden (optional)
        }
        context: {
            'main_app': V2MainAppComplete,
            'self': any                 # Referenz für self-Aufrufe
        }
        gcs: GlobalCentralSystemsteuerung
    
    Returns:
        True bei Erfolg
    """
    logger.info("🔵 Handler: execute_python")
    
    # Parameter
    code = params.get('code')
    method_name = params.get('method_name')
    
    if not code and not method_name:
        logger.error("❌ Weder 'code' noch 'method_name' angegeben")
        return False
    
    # Hole main_app
    main_app = context.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht im Context")
        return False
    
    try:
        # METHODE 1: Methodenname auf main_app
        if method_name:
            logger.info(f"   Methode: {method_name}")
            
            if not hasattr(main_app, method_name):
                logger.error(f"❌ Methode '{method_name}' existiert nicht auf main_app")
                return False
            
            method = getattr(main_app, method_name)
            
            # Aufruf ohne Parameter
            if callable(method):
                method()
                logger.info(f"✅ Methode {method_name}() ausgeführt")
                return True
            else:
                logger.error(f"❌ {method_name} ist nicht aufrufbar")
                return False
        
        # METHODE 2: Python-Code ausführen
        if code:
            logger.info(f"   Code: {code[:100]}...")
            
            # Code bereinigen (self. durch main_app. ersetzen)
            if 'self.' in code:
                code = code.replace('self.', 'main_app.')
                logger.info(f"   Bereinigt: {code[:100]}...")
            
            # Execution-Namespace vorbereiten
            namespace = {
                'main_app': main_app,
                'gcs': gcs,
                'context': context,
                'params': params
            }
            
            # Ausführen
            exec(code, namespace)
            logger.info("✅ Python-Code erfolgreich ausgeführt")
            return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Python-Ausführung: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False
