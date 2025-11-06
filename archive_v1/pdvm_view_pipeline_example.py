"""
🎯 BEISPIEL: PDVM VIEW PIPELINE VERWENDUNG
==========================================

Zeigt, wie die neue View-Pipeline verwendet wird.
ULTRA EINFACH - nur 3 Aufrufe!
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from pdvm_view_pipeline import get_view_pipeline


class PersonenView(QMainWindow):
    """
    Beispiel: Personen-View mit vollständig gekapselter Pipeline
    """
    
    def __init__(self, view_guid: str, matrix_manager):
        super().__init__()
        
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        
        # UI erstellen
        self._setup_ui()
        
        # View-Pipeline initialisieren (EINFACH!)
        self.view_pipeline = get_view_pipeline(view_guid, matrix_manager)
        self.view_pipeline.initialize_view(
            view_parent=self.table_container,
            schnellsuche_parent=self.search_container
        )
    
    def _setup_ui(self):
        """UI-Struktur erstellen"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Schnellsuche-Bereich (Parent für Schnellsuche-Widget)
        self.search_container = QWidget()
        search_layout = QHBoxLayout(self.search_container)
        layout.addWidget(self.search_container)
        
        # Tabellen-Bereich (Parent für View-Widget)
        self.table_container = QWidget()
        table_layout = QVBoxLayout(self.table_container)
        layout.addWidget(self.table_container)
    
    # ========================================
    # EXTERNE AUFRUFE (EINFACH!)
    # ========================================
    
    def on_reset_button_clicked(self):
        """
        Button "Filter zurücksetzen" wurde geklickt
        
        ULTRA EINFACH: Ein Aufruf!
        """
        self.view_pipeline.reset_filters()
    
    def on_refresh_button_clicked(self):
        """
        Button "Aktualisieren" wurde geklickt
        
        ULTRA EINFACH: Ein Aufruf!
        """
        self.view_pipeline.refresh()
    
    def on_stichtag_changed(self, new_stichtag):
        """
        Stichtag wurde geändert
        
        EINFACH: Matrix neu laden, Pipeline durchlaufen
        """
        # 1. Matrix Manager aktualisiert BasisMatrix (extern)
        self.matrix_manager.reload_basis_matrix()
        
        # 2. Pipeline durchlaufen ab BASIS
        from pdvm_pipeline import get_pipeline
        pipeline = get_pipeline(self.view_guid, self.matrix_manager)
        pipeline.run('BASIS')
        
        # 3. View aktualisieren
        self.view_pipeline.refresh()


# ========================================
# VERWENDUNG IM HAUPTMENÜ
# ========================================

def open_personen_view():
    """
    Personen-View öffnen
    
    VORHER (komplex):
        - Controller erstellen
        - UI erstellen
        - Manager erstellen
        - Pipeline erstellen
        - Schnellsuche Manager erstellen
        - Filter-Reset Manager erstellen
        - Alles verbinden
        - Matrix laden
        - Projektion laden
        - View aktualisieren
    
    NACHHER (einfach):
        - Matrix Manager erstellen
        - View erstellen
        - Fertig!
    """
    from pdvm_view_matrix_manager import PdvmViewMatrixManager
    from pdvm_central_systemsteuerung import get_gcs
    
    gcs = get_gcs()
    view_guid = '4886ad26-061b-4662-a762-c8c83f36692d'  # Personen-View
    
    # 1. Matrix Manager erstellen (lädt BasisMatrix)
    matrix_manager = PdvmViewMatrixManager(view_guid, gcs)
    
    # Matrix laden
    instances = []  # TODO: Instanzen aus Datenbank laden
    all_controls = {}  # TODO: Controls aus Konfiguration laden
    matrix_manager.initialize_basis_matrix(instances, all_controls)
    
    # 2. View erstellen (Pipeline wird automatisch initialisiert)
    view = PersonenView(view_guid, matrix_manager)
    view.show()
    
    # FERTIG! Alles weitere passiert automatisch:
    # - Schnellsuche ist verbunden
    # - Filter funktionieren
    # - View ist gefüllt
    # - Projektion ist geladen


# ========================================
# VERGLEICH: VORHER VS NACHHER
# ========================================

"""
VORHER (komplex, viele Abhängigkeiten):

    # Controller
    controller = PdvmViewController(view_guid, gcs)
    
    # Matrix Manager
    matrix_manager = PdvmViewMatrixManager(view_guid, gcs, controller)
    
    # Pipeline
    from pdvm_pipeline import get_pipeline
    pipeline = get_pipeline(view_guid, matrix_manager)
    
    # Schnellsuche Manager
    from schnellsuche_manager import get_schnellsuche_manager
    schnellsuche = get_schnellsuche_manager(view_guid, gcs, matrix_manager)
    schnellsuche.pipeline = pipeline  # Manuell verbinden!
    
    # Filter-Reset Manager
    from filter_reset_manager import get_filter_reset_manager
    filter_reset = get_filter_reset_manager(view_guid, gcs, matrix_manager)
    filter_reset.pipeline = pipeline  # Manuell verbinden!
    
    # UI
    ui = PdvmViewUI(parent_widget)
    controller.ui = ui  # Manuell verbinden!
    
    # Projektion laden
    projection = controller._get_visible_columns_from_gcs()
    
    # Matrix laden
    matrix_manager.initialize_basis_matrix(instances, all_controls)
    pipeline.run('BASIS')
    
    # View aktualisieren
    controller.refresh_ui_from_pipeline()
    
    # Schnellsuche-Feld verbinden
    ui.search_field.textChanged.connect(schnellsuche.execute_schnellsuche)
    
    # Filter-Reset-Button verbinden
    ui.reset_button.clicked.connect(filter_reset.reset_all_filters)


NACHHER (einfach, vollständig gekapselt):

    # Matrix Manager
    matrix_manager = PdvmViewMatrixManager(view_guid, gcs)
    matrix_manager.initialize_basis_matrix(instances, all_controls)
    
    # View-Pipeline (macht ALLES automatisch)
    view_pipeline = get_view_pipeline(view_guid, matrix_manager)
    view_pipeline.initialize_view(view_parent, schnellsuche_parent)
    
    # FERTIG!
    # - Matrix-Pipeline läuft
    # - Projektion geladen
    # - View gefüllt
    # - Schnellsuche verbunden
    # - Filter funktionieren


AUFRUFE VON AUSSEN:

    VORHER:
        schnellsuche_manager.execute_schnellsuche('lau')
        filter_reset_manager.reset_all_filters()
        controller.refresh_ui_from_pipeline()
    
    NACHHER:
        view_pipeline.set_schnellsuche('lau')
        view_pipeline.reset_filters()
        view_pipeline.refresh()
"""
