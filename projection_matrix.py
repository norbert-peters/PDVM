"""
Zentrale Projektions-Matrix für alle View-Komponenten

VEREINFACHTE ARCHITEKTUR:
- Mehrdimensionale Matrix für alle Projektionsebenen
- Automatische Synchronisation bei Änderungen
- Eine Instanz pro View-GUID
- Teil der GCS für Persistenz
"""

import logging
import json
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ProjectionLevel(Enum):
    """Projektionsebenen"""
    TABLE = "table"
    COLUMN_MANAGEMENT = "column_management"
    SEARCH = "search"

class ProjectionMode(Enum):
    """Projektionsmodi"""
    EXPERT = "expert"
    STANDARD = "standard"

class ProjectionMatrix:
    """
    ZENTRALE PROJEKTIONS-MATRIX

    Mehrdimensionale Matrix-Struktur:
    {
        view_guid: {
            ProjectionMode.EXPERT: {
                ProjectionLevel.TABLE: [...],
                ProjectionLevel.COLUMN_MANAGEMENT: [...],
                ProjectionLevel.SEARCH: [...]
            },
            ProjectionMode.STANDARD: {
                ProjectionLevel.TABLE: [...],
                ProjectionLevel.COLUMN_MANAGEMENT: [...],
                ProjectionLevel.SEARCH: [...]
            }
        }
    }

    Automatische Synchronisation:
    - Änderung in einer Ebene → alle Ebenen aktualisiert
    - ExpertMode: Alle Ebenen identisch
    - StandardMode: Column-Management eigene Projektion
    """

    def __init__(self, view_guid: str, gcs_instance=None):
        self.view_guid = view_guid
        self.gcs = gcs_instance
        self.matrix: Dict[str, Dict[str, Dict[str, List]]] = {}

        # Initialisiere Matrix-Struktur
        self._initialize_matrix()

        logger.info(f"✅ ProjectionMatrix für View {view_guid} initialisiert")

    def _initialize_matrix(self):
        """Initialisiert die Matrix-Struktur für beide Modi"""
        for mode in ProjectionMode:
            self.matrix[mode.value] = {}
            for level in ProjectionLevel:
                self.matrix[mode.value][level.value] = []

    def update_basis_columns(self, basis_columns: List[Dict], mode: ProjectionMode = None):
        """
        AKTUELLE BASIS-COLUMNS SETZEN

        Args:
            basis_columns: Neue Basis-Spalten
            mode: Optional - spezifischer Modus, sonst aktueller Modus verwenden
        """
        if mode is None:
            mode = self._get_current_mode()

        logger.info(f"🔄 Aktualisiere Basis-Columns für {mode.value}-Mode")

        # Projektion für alle Ebenen berechnen
        projected_columns = self._calculate_projection(basis_columns, mode)

        # Alle Ebenen aktualisieren
        for level in ProjectionLevel:
            self.matrix[mode.value][level.value] = projected_columns.copy()
            logger.debug(f"  ✅ {level.value}: {len(projected_columns)} Spalten")

        # Persistieren
        self._persist_matrix()

        logger.info(f"✅ Alle Projektionsebenen für {mode.value} synchronisiert")

    def _calculate_projection(self, basis_columns: List[Dict], mode: ProjectionMode) -> List[Dict]:
        """
        BERECHNET PROJEKTION basierend auf Modus

        Args:
            basis_columns: Basis-Spalten
            mode: Projektionsmodus

        Returns:
            List[Dict]: Projizierte Spalten
        """
        try:
            if mode == ProjectionMode.EXPERT:
                # ExpertMode: Alle Spalten nach expertOrder
                return sorted(basis_columns, key=lambda c: c.get('expertOrder', 999))

            elif mode == ProjectionMode.STANDARD:
                # StandardMode: Nur sichtbare Spalten nach displayOrder
                visible_columns = [col for col in basis_columns if col.get('show', False)]
                return sorted(visible_columns, key=lambda c: c.get('displayOrder', 999))

            else:
                logger.warning(f"⚠️ Unbekannter Modus: {mode}")
                return basis_columns

        except Exception as e:
            logger.error(f"❌ Fehler bei Projektionsberechnung: {e}")
            return basis_columns

    def get_columns(self, level: ProjectionLevel, mode: ProjectionMode = None) -> List[Dict]:
        """
        SPALTEN FÜR SPEZIFISCHE EBENE ABRUFEN

        Args:
            level: Gewünschte Ebene
            mode: Optional - spezifischer Modus

        Returns:
            List[Dict]: Spalten für die Ebene
        """
        if mode is None:
            mode = self._get_current_mode()

        try:
            return self.matrix[mode.value][level.value].copy()
        except KeyError:
            logger.warning(f"⚠️ Keine Spalten für {mode.value}/{level.value} gefunden")
            return []

    def get_column_names(self, level: ProjectionLevel, mode: ProjectionMode = None) -> List[str]:
        """
        SPALTENNAMEN FÜR SPEZIFISCHE EBENE ABRUFEN

        Args:
            level: Gewünschte Ebene
            mode: Optional - spezifischer Modus

        Returns:
            List[str]: Spaltennamen
        """
        columns = self.get_columns(level, mode)
        return [col.get('name', '') for col in columns if col.get('name')]

    def update_column_order(self, level: ProjectionLevel, new_order: List[Dict], mode: ProjectionMode = None):
        """
        SPALTENREIHENFOLGE FÜR EINE EBENE ÄNDERN

        Args:
            level: Ebene die geändert wird
            new_order: Neue Spaltenreihenfolge
            mode: Optional - spezifischer Modus
        """
        if mode is None:
            mode = self._get_current_mode()

        logger.info(f"🔄 Aktualisiere Reihenfolge für {level.value} in {mode.value}-Mode")

        # Ebene aktualisieren
        self.matrix[mode.value][level.value] = new_order.copy()

        # Bei ExpertMode: Alle Ebenen synchronisieren
        if mode == ProjectionMode.EXPERT:
            for other_level in ProjectionLevel:
                if other_level != level:
                    self.matrix[mode.value][other_level.value] = new_order.copy()
                    logger.debug(f"  ✅ {other_level.value} synchronisiert")

        # Persistieren
        self._persist_matrix()

        logger.info(f"✅ Reihenfolge für {level.value} aktualisiert")

    def _get_current_mode(self) -> ProjectionMode:
        """AKTUELLEN MODUS AUS GCS ABRUFEN"""
        try:
            if self.gcs and hasattr(self.gcs, 'global_expert_mode'):
                return ProjectionMode.EXPERT if self.gcs.global_expert_mode else ProjectionMode.STANDARD
            else:
                return ProjectionMode.STANDARD  # Fallback
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Abrufen des Modus: {e}")
            return ProjectionMode.STANDARD

    def _persist_matrix(self):
        """MATRIX IN GCS PERSISTIEREN"""
        try:
            if self.gcs:
                matrix_json = json.dumps(self.matrix, indent=2)
                self.gcs.db.set_value(self.view_guid, 'projection_matrix', matrix_json, ab_zeit=999999.0)
                logger.debug(f"💾 ProjectionMatrix für {self.view_guid} persistiert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Persistieren der Matrix: {e}")

    def load_from_gcs(self):
        """MATRIX AUS GCS LADEN"""
        try:
            if self.gcs:
                matrix_json = self.gcs.db.get_value(self.view_guid, 'projection_matrix')
                if matrix_json:
                    self.matrix = json.loads(matrix_json)
                    logger.info(f"📂 ProjectionMatrix für {self.view_guid} aus GCS geladen")
                    return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Matrix: {e}")

        return False

    def get_matrix_summary(self) -> Dict:
        """
        ZUSAMMENFASSUNG DER MATRIX FÜR DEBUGGING

        Returns:
            Dict: Zusammenfassung aller Ebenen und Modi
        """
        summary = {}
        for mode in ProjectionMode:
            summary[mode.value] = {}
            for level in ProjectionLevel:
                columns = self.matrix.get(mode.value, {}).get(level.value, [])
                summary[mode.value][level.value] = {
                    'count': len(columns),
                    'names': [col.get('name', '') for col in columns[:5]]  # Erste 5 für Übersicht
                }
        return summary

    def sync_all_levels(self, basis_columns: List[Dict] = None):
        """
        ALLE EBENEN SYNCHRONISIEREN

        Wenn basis_columns None ist, werden die aktuellen verwendet.
        Andernfalls werden neue Basis-Columns gesetzt und alle Ebenen neu berechnet.

        Args:
            basis_columns: Optional - Neue Basis-Spalten
        """
        if basis_columns is not None:
            # Neue Basis-Columns setzen und alle Ebenen aktualisieren
            self.update_basis_columns(basis_columns)
        else:
            # Aktuelle Basis-Columns verwenden und alle Ebenen neu berechnen
            current_mode = self._get_current_mode()
            if ProjectionMode.EXPERT in self.matrix and self.matrix[ProjectionMode.EXPERT.value]:
                # Verwende vorhandene Daten für Neuberechnung
                expert_data = self.matrix[ProjectionMode.EXPERT.value]
                if 'table' in expert_data and expert_data['table']:
                    # Extrahiere Basis-Columns aus vorhandenen Daten
                    basis_from_existing = []
                    for col in expert_data['table']:
                        if isinstance(col, dict):
                            basis_from_existing.append(col)
                        else:
                            # Fallback: Erstelle Dummy-Column
                            basis_from_existing.append({'name': str(col), 'expertOrder': 999, 'displayOrder': 999, 'show': True})

                    if basis_from_existing:
                        self.update_basis_columns(basis_from_existing)
                        logger.info("✅ Matrix aus vorhandenen Daten synchronisiert")
                        return

            logger.warning("⚠️ Konnte Matrix nicht synchronisieren - keine Basis-Daten verfügbar")