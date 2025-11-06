"""
VERALTET - Diese Datei wird nicht mehr verwendet!

Die neue Architektur verwendet einfache Projektions-Tabellen direkt in der GCS:
- gcs.get_projection_table(view_guid)
- gcs.get_projection_column_management(view_guid)
- gcs.get_projection_search(view_guid)

Keine komplexen Helper mehr nötig!
"""

# Alte Funktionen für Kompatibilität (werfen Fehler)
def get_projected_columns(basis_columns, view_guid=None, level='table'):
    """VERALTET - Verwende gcs.get_projection_xxx() stattdessen"""
    raise DeprecationWarning("column_projection_helper ist veraltet! Verwende gcs.get_projection_table(), gcs.get_projection_column_management() oder gcs.get_projection_search()")
