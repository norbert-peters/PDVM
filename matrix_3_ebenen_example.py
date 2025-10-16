# matrix_3_ebenen_example.py
"""
PRAKTISCHES BEISPIEL: 3-Ebenen Matrix-Struktur

Zeigt die vollständige Implementierung der 3-Ebenen-Architektur:
1. Matrix-Erstellung aus DB-Daten
2. Formatierung mit pdvm_DateTime
3. Verwendung in der UI

🎯 VERWENDE DIESES PATTERN FÜR ALLE MATRIX-OPERATIONEN!
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Matrix3EbenenExample:
    """
    Beispiel-Implementierung der 3-Ebenen Matrix-Struktur
    
    EBENE 1: Rohdatum aus DB          → row_data[control_key]
    EBENE 2: AB-Datum (roh)           → row_data[f"{control_key}_abdatum"]
    EBENE 3: Formatiertes AB-Datum    → row_data[f"{control_key}_formatiertes_abdatum"]
    """
    
    def __init__(self, gcs):
        """
        Args:
            gcs: Globale Systemsteuerung für pdvm_DateTime Zugriff
        """
        self.gcs = gcs
        self.matrix: List[Dict[str, Any]] = []
    
    def create_matrix_from_database(self, instances: List[Any], controls_config: Dict[str, Any]):
        """
        HAUPT-METHODE: Matrix aus Datenbank-Instanzen erstellen
        
        Args:
            instances: Liste von PdvmCentralDatenbank Instanzen
            controls_config: Control-Konfigurationen (Spalten-Definitionen)
        
        Returns:
            List[Dict]: Matrix mit 3-Ebenen-Struktur
        """
        logger.info("🏗️ === 3-EBENEN MATRIX ERSTELLEN ===")
        
        if not instances:
            logger.warning("⚠️ Keine Instanzen zum Verarbeiten!")
            return []
        
        rows = []
        
        for idx, instance in enumerate(instances):
            logger.info(f"📊 Verarbeite Instanz {idx+1}/{len(instances)}: {instance.guid}")
            
            # Initialisiere Row-Dict
            row_data = {}
            
            # SPEZIALFALL: uid_original (GUID des Datensatzes)
            row_data['uid_original'] = instance.guid
            row_data['uid_original_abdatum'] = None
            row_data['uid_original_formatiertes_abdatum'] = None
            
            # === STUFE 1: ORIGINAL-FELDER mit 3 Ebenen befüllen ===
            for control_key, control_config in controls_config.items():
                if control_config.get('control_type') == 'original':
                    self._fill_original_control_3_ebenen(
                        row_data, 
                        instance, 
                        control_key, 
                        control_config
                    )
            
            # === STUFE 2: SHOW-FELDER aus ORIGINAL-FELDERN kopieren (inkl. 3 Ebenen) ===
            for control_key, control_config in controls_config.items():
                if control_config.get('control_type') == 'show':
                    self._copy_show_from_original_3_ebenen(
                        row_data,
                        control_key,
                        control_config
                    )
            
            rows.append(row_data)
        
        self.matrix = rows
        logger.info(f"✅ Matrix erstellt: {len(rows)} Zeilen mit 3-Ebenen-Struktur")
        
        # Debug-Output
        self._debug_print_matrix_structure(rows[0] if rows else {})
        
        return rows
    
    def _fill_original_control_3_ebenen(
        self, 
        row_data: Dict, 
        instance: Any, 
        control_key: str, 
        control_config: Dict
    ):
        """
        Befüllt ein Original-Control mit 3-Ebenen-Struktur
        
        🎯 KERN-METHODE: Hier passiert die 3-Ebenen-Logik!
        
        Args:
            row_data: Row-Dictionary zum Befüllen
            instance: PdvmCentralDatenbank Instanz
            control_key: Control-Name (z.B. 'geburtsdatum_original')
            control_config: Control-Konfiguration
        """
        feld = control_config.get('feld')
        gruppe = control_config.get('gruppe', 'SYSTEM')
        
        if not feld:
            logger.debug(f"⚠️ {control_key}: Kein Feld definiert")
            self._set_empty_3_ebenen(row_data, control_key)
            return
        
        try:
            logger.info(f"  🔍 {control_key}: Feld={feld}, Gruppe={gruppe}")
            
            # === DATENABRUF aus Datenbank ===
            result = instance.get_value(gruppe, feld, self.gcs.st_inst.PdvmDateTime)
            logger.info(f"    📋 get_value({gruppe}, {feld}) = {result}")
            
            # === TUPEL AUSPACKEN ===
            if isinstance(result, tuple) and len(result) >= 2:
                wert, abdatum = result[0], result[1]
            else:
                wert, abdatum = result, None
            
            logger.info(f"    💾 Wert: {wert}, Abdatum: {abdatum}")
            
            # === 🎯 3-EBENEN-STRUKTUR BEFÜLLEN ===
            
            # ┌─────────────────────────────────────────────────────────┐
            # │  EBENE 1: ROHDATUM (aus DB)                             │
            # └─────────────────────────────────────────────────────────┘
            row_data[control_key] = wert
            logger.info(f"    ✅ EBENE 1: {control_key} = {wert}")
            
            # ┌─────────────────────────────────────────────────────────┐
            # │  EBENE 2: AB-DATUM (roh, aus DB)                        │
            # └─────────────────────────────────────────────────────────┘
            row_data[f"{control_key}_abdatum"] = abdatum
            logger.info(f"    ✅ EBENE 2: {control_key}_abdatum = {abdatum}")
            
            # ┌─────────────────────────────────────────────────────────┐
            # │  EBENE 3: FORMATIERTES AB-DATUM (länderspezifisch)      │
            # └─────────────────────────────────────────────────────────┘
            if abdatum:
                formatiertes_abdatum = self._format_abdatum(abdatum)
                row_data[f"{control_key}_formatiertes_abdatum"] = formatiertes_abdatum
                logger.info(f"    ✅ EBENE 3: {control_key}_formatiertes_abdatum = {formatiertes_abdatum}")
            else:
                row_data[f"{control_key}_formatiertes_abdatum"] = None
                logger.info(f"    ✅ EBENE 3: {control_key}_formatiertes_abdatum = None")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei {control_key}: {e}")
            self._set_empty_3_ebenen(row_data, control_key)
    
    def _copy_show_from_original_3_ebenen(
        self,
        row_data: Dict,
        control_key: str,
        control_config: Dict
    ):
        """
        Kopiert alle 3 Ebenen von _original zu _show Control
        
        🎯 WICHTIG: Auch Abdatum-Ebenen werden kopiert!
        
        Args:
            row_data: Row-Dictionary
            control_key: Show-Control-Name (z.B. 'vorname_show')
            control_config: Control-Konfiguration
        """
        original_key = control_config.get('original_control_key')
        
        if not original_key:
            logger.warning(f"⚠️ {control_key}: Kein original_control_key definiert")
            self._set_empty_3_ebenen(row_data, control_key)
            return
        
        try:
            # === ALLE 3 EBENEN KOPIEREN ===
            
            # EBENE 1: Wert
            original_value = row_data.get(original_key)
            row_data[control_key] = original_value
            
            # EBENE 2: AB-Datum (roh)
            original_abdatum = row_data.get(f"{original_key}_abdatum")
            row_data[f"{control_key}_abdatum"] = original_abdatum
            
            # EBENE 3: Formatiertes AB-Datum
            original_formatiertes = row_data.get(f"{original_key}_formatiertes_abdatum")
            row_data[f"{control_key}_formatiertes_abdatum"] = original_formatiertes
            
            logger.info(f"  📋 {control_key} kopiert von {original_key} (3 Ebenen)")
            logger.info(f"    → Wert: {original_value}")
            logger.info(f"    → Abdatum: {original_abdatum}")
            logger.info(f"    → Formatiert: {original_formatiertes}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Kopieren {control_key}: {e}")
            self._set_empty_3_ebenen(row_data, control_key)
    
    def _format_abdatum(self, abdatum_value: float) -> Optional[str]:
        """
        Formatiert ein Abdatum länderspezifisch via pdvm_DateTime
        
        🎯 ZENTRALE FORMATIERUNGS-FUNKTION
        
        Args:
            abdatum_value: Rohdatum (z.B. 2024310.12500)
        
        Returns:
            str: Formatiertes Datum (z.B. "05.11.2024 03:00:00" für DEU)
            None: Wenn kein Abdatum vorhanden
        """
        if abdatum_value is None:
            return None
        
        # SPEZIALFALL: Default-Wert 1001.0 (01.01.0001)
        if float(abdatum_value) == 1001.0:
            return "01.01.0001 (Default)"
        
        try:
            # GCS temporäre DateTime-Instanz verwenden
            dt = self.gcs.temp_dt_inst
            if dt is None:
                logger.warning("⚠️ Keine temp_dt_inst in GCS verfügbar!")
                return f"{abdatum_value} (nicht formatiert)"
            
            # PdvmDateTime setzen und formatierte Ausgabe holen
            dt.PdvmDateTime = float(abdatum_value)
            formatted = dt.FormTimeStamp
            
            logger.debug(f"🎨 Formatierung: {abdatum_value} → {formatted}")
            return formatted
            
        except Exception as e:
            logger.debug(f"❌ Fehler bei Abdatum-Formatierung {abdatum_value}: {e}")
            return f"{abdatum_value} (Fehler)"
    
    def _set_empty_3_ebenen(self, row_data: Dict, control_key: str):
        """
        Setzt alle 3 Ebenen auf None/leer
        
        Args:
            row_data: Row-Dictionary
            control_key: Control-Name
        """
        row_data[control_key] = None
        row_data[f"{control_key}_abdatum"] = None
        row_data[f"{control_key}_formatiertes_abdatum"] = None
    
    def get_abdatum_matrix_for_ui(self, projection: List[str]) -> List[List[Optional[str]]]:
        """
        Erstellt eine 2D-Abdatum-Matrix für UI-Tooltips
        
        🎯 VERWENDET EBENE 3 (formatiertes_abdatum)
        
        Args:
            projection: Liste der sichtbaren Spalten
        
        Returns:
            2D-Matrix mit formatierten Abdatum-Werten
        """
        logger.info("📊 Erstelle Abdatum-Matrix für UI...")
        
        abdatum_matrix = []
        
        for row in self.matrix:
            abdatum_row = []
            
            for col_name in projection:
                # EBENE 3: Formatiertes Abdatum holen
                formatted_abdatum = row.get(f"{col_name}_formatiertes_abdatum")
                abdatum_row.append(formatted_abdatum)
            
            abdatum_matrix.append(abdatum_row)
        
        logger.info(f"✅ Abdatum-Matrix: {len(abdatum_matrix)} Zeilen, {len(projection)} Spalten")
        return abdatum_matrix
    
    def _debug_print_matrix_structure(self, sample_row: Dict):
        """
        Debug-Ausgabe der Matrix-Struktur
        
        Args:
            sample_row: Beispiel-Row zum Analysieren
        """
        if not sample_row:
            return
        
        logger.info("🔍 === MATRIX-STRUKTUR (Sample Row) ===")
        
        # Gruppiere Keys nach Control
        control_groups = {}
        
        for key in sample_row.keys():
            # Finde Basis-Control-Name (ohne _abdatum/_formatiertes_abdatum)
            if key.endswith('_formatiertes_abdatum'):
                base_key = key[:-len('_formatiertes_abdatum')]
            elif key.endswith('_abdatum'):
                base_key = key[:-len('_abdatum')]
            else:
                base_key = key
            
            if base_key not in control_groups:
                control_groups[base_key] = {}
            
            if key.endswith('_formatiertes_abdatum'):
                control_groups[base_key]['ebene3'] = sample_row[key]
            elif key.endswith('_abdatum'):
                control_groups[base_key]['ebene2'] = sample_row[key]
            else:
                control_groups[base_key]['ebene1'] = sample_row[key]
        
        # Ausgabe
        for control_name, ebenen in list(control_groups.items())[:5]:  # Erste 5
            logger.info(f"\n  📋 {control_name}:")
            logger.info(f"    ├─ 🗄️ EBENE 1 (Wert):     {ebenen.get('ebene1', 'N/A')}")
            logger.info(f"    ├─ 📅 EBENE 2 (AB-Datum):  {ebenen.get('ebene2', 'N/A')}")
            logger.info(f"    └─ 🎨 EBENE 3 (Format):    {ebenen.get('ebene3', 'N/A')}")


# ============================================================================
# VERWENDUNGS-BEISPIELE
# ============================================================================

def example_usage_full_workflow():
    """
    VOLLSTÄNDIGER WORKFLOW: Von DB-Daten bis UI-Anzeige
    """
    from pdvm_central_systemsteuerung import get_gcs
    from pdvm_central_datenbank import PdvmCentralDatenbank
    
    # 1. GCS holen
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return
    
    # 2. Matrix-Manager erstellen
    matrix_manager = Matrix3EbenenExample(gcs)
    
    # 3. Datenbank-Instanzen laden
    db = PdvmCentralDatenbank(
        db_name="PdvmManager.db",
        table_name="my_table",
        guid=None
    )
    instances = db.lesen_alle_ohne_system(limit=100)
    
    # 4. Controls-Config laden (Beispiel)
    controls_config = {
        'geburtsdatum_original': {
            'control_type': 'original',
            'feld': 'geburtsdatum',
            'gruppe': 'BASIS'
        },
        'geburtsdatum_show': {
            'control_type': 'show',
            'original_control_key': 'geburtsdatum_original'
        },
        'familienname_original': {
            'control_type': 'original',
            'feld': 'familienname',
            'gruppe': 'BASIS'
        },
        'familienname_show': {
            'control_type': 'show',
            'original_control_key': 'familienname_original'
        }
    }
    
    # 5. Matrix erstellen (3 Ebenen!)
    matrix = matrix_manager.create_matrix_from_database(instances, controls_config)
    
    # 6. Abdatum-Matrix für UI holen
    projection = ['geburtsdatum_show', 'familienname_show']
    abdatum_matrix = matrix_manager.get_abdatum_matrix_for_ui(projection)
    
    # 7. UI verwenden (Beispiel)
    logger.info("\n🎯 === UI-VERWENDUNG ===")
    logger.info(f"Matrix: {len(matrix)} Zeilen")
    logger.info(f"Abdatum-Matrix: {len(abdatum_matrix)} Zeilen")
    
    # Beispiel: Tooltip für Zelle (0, 0)
    if abdatum_matrix and abdatum_matrix[0]:
        tooltip_text = f"abdatum: {abdatum_matrix[0][0]}"
        logger.info(f"Tooltip (0,0): {tooltip_text}")


def example_format_abdatum_direct():
    """
    DIREKTES FORMATIERUNGS-BEISPIEL
    """
    from pdvm_central_systemsteuerung import get_gcs
    
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return
    
    matrix_manager = Matrix3EbenenExample(gcs)
    
    # Verschiedene Abdatum-Werte testen
    test_values = [
        2024310.12500,  # Normales Datum
        1001.0,         # Default-Wert
        2024001.00000,  # Jahresanfang ohne Zeit
        None            # Kein Abdatum
    ]
    
    logger.info("\n🎨 === FORMATIERUNGS-TESTS ===")
    for value in test_values:
        formatted = matrix_manager._format_abdatum(value)
        logger.info(f"{value} → {formatted}")


def example_copy_show_controls():
    """
    BEISPIEL: Show-Controls mit 3 Ebenen kopieren
    """
    # Beispiel-Row-Data
    row_data = {
        # Original-Control mit 3 Ebenen
        'vorname_original': 'Hans',
        'vorname_original_abdatum': 2024305.08000,
        'vorname_original_formatiertes_abdatum': '01.11.2024 01:55:12'
    }
    
    # Control-Config
    controls_config = {
        'vorname_show': {
            'control_type': 'show',
            'original_control_key': 'vorname_original'
        }
    }
    
    from pdvm_central_systemsteuerung import get_gcs
    gcs = get_gcs()
    
    matrix_manager = Matrix3EbenenExample(gcs)
    
    # Kopiere Show-Control
    matrix_manager._copy_show_from_original_3_ebenen(
        row_data,
        'vorname_show',
        controls_config['vorname_show']
    )
    
    # Prüfe Ergebnis
    logger.info("\n📋 === KOPIER-ERGEBNIS ===")
    logger.info(f"vorname_show: {row_data['vorname_show']}")
    logger.info(f"vorname_show_abdatum: {row_data['vorname_show_abdatum']}")
    logger.info(f"vorname_show_formatiertes_abdatum: {row_data['vorname_show_formatiertes_abdatum']}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logger.info("🚀 === 3-EBENEN MATRIX BEISPIELE ===\n")
    
    # Beispiel 1: Vollständiger Workflow
    logger.info("=" * 60)
    logger.info("BEISPIEL 1: Vollständiger Workflow")
    logger.info("=" * 60)
    example_usage_full_workflow()
    
    # Beispiel 2: Direkte Formatierung
    logger.info("\n" + "=" * 60)
    logger.info("BEISPIEL 2: Direkte Formatierung")
    logger.info("=" * 60)
    example_format_abdatum_direct()
    
    # Beispiel 3: Show-Controls kopieren
    logger.info("\n" + "=" * 60)
    logger.info("BEISPIEL 3: Show-Controls kopieren")
    logger.info("=" * 60)
    example_copy_show_controls()
    
    logger.info("\n✅ Alle Beispiele ausgeführt!")
