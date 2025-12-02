"""
PDVM Layout Manager

Zentrale Verwaltung von Layouts, Farben, Fonts und Styles.
Lädt Konfiguration aus sys_layout Tabelle in pdvm_system.db.

AUTOR: Norbert Peters
DATUM: 28.11.2025
VERSION: 1.0
"""

import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PdvmLayoutManager:
    """
    Layout-Manager für PDVM-System.
    
    FUNKTIONEN:
    - Farben aus COLORS Gruppe laden
    - Fonts aus FONTS Gruppe laden
    - Stylesheets aus STYLES Gruppe mit Template-Variablen
    - Cache für Performance
    - Hot-Reload Support
    
    VERWENDUNG:
        gcs.layout.get_color('BACKGROUND')  # → "#ffffff"
        gcs.layout.get_stylesheet('QMenu')  # → Vollständiges Stylesheet
    """
    
    def __init__(self, gcs):
        """
        Initialisiert Layout-Manager.
        
        Args:
            gcs: GlobaleCentraleSystemsteuerung Instanz
        """
        self.gcs = gcs
        self.layout_db = None
        self.active_layout_guid = None
        self._cache = {}  # Cache für kompilierte Stylesheets
        
        self._load_active_layout()
        
        logger.info(f"🎨 Layout-Manager initialisiert: {self.active_layout_guid}")
    
    def _load_active_layout(self):
        """Lädt aktives Layout aus GCS Settings oder Default"""
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Layout-GUID aus Settings holen (falls konfiguriert)
        # WICHTIG: Direkter DB-Zugriff, da während GCS.__init__ _initialized noch False ist!
        layout_guid = None
        if hasattr(self.gcs, '_db') and self.gcs._db and hasattr(self.gcs, 'user_guid'):
            try:
                layout_guid, _ = self.gcs._db.get_value(self.gcs.user_guid, 'ACTIVE_LAYOUT')
            except Exception:
                pass
        
        # Default-Layout verwenden wenn User keine eigene GUID hat
        if not layout_guid:
            layout_guid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
            logger.info(f"🎨 Verwende Default-Layout: {layout_guid}")
        
        try:
            # Layout-Datenbank öffnen
            # WICHTIG: sys_layout ist System-Tabelle (siehe PdvmDatenbank.SYSTEM_TABLES)
            # → Wird automatisch zu pdvm_system.db geroutet!
            self.layout_db = PdvmCentralDatenbank('sys_layout', layout_guid)
            self.active_layout_guid = layout_guid
            
            # Validierung: ROOT Gruppe muss existieren
            root_data = self.layout_db.get_value_by_group('ROOT')
            if root_data:
                layout_name = root_data.get('LAYOUT_NAME', 'Unknown')
                logger.info(f"✅ Layout geladen: {layout_name}")
            else:
                logger.warning(f"⚠️ Layout {layout_guid[:8]}... hat keine ROOT-Gruppe - verwende Defaults")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Layouts: {e}")
            logger.warning("⚠️ Fallback auf hardcoded Defaults")
            self.layout_db = None
    
    def get_color(self, color_name: str, default: str = '#000000') -> str:
        """
        Holt Farbwert aus COLORS Gruppe.
        
        Args:
            color_name: Name der Farbe (z.B. 'BACKGROUND', 'TEXT')
            default: Fallback-Wert wenn nicht gefunden
        
        Returns:
            Farbwert als Hex-String (z.B. "#ffffff")
        
        Beispiel:
            bg = gcs.layout.get_color('BACKGROUND')  # → "#ffffff"
        """
        if not self.layout_db:
            return default
        
        try:
            value, _ = self.layout_db.get_value('COLORS', color_name)
            return value if value else default
        except Exception as e:
            logger.warning(f"⚠️ Farbe '{color_name}' nicht gefunden: {e}")
            return default
    
    def get_font_property(self, property_name: str, default: Any = None) -> Any:
        """
        Holt Font-Eigenschaft aus FONTS Gruppe.
        
        Args:
            property_name: Name der Eigenschaft (z.B. 'FAMILY', 'SIZE_DEFAULT')
            default: Fallback-Wert
        
        Returns:
            Font-Eigenschaft (String oder Int)
        
        Beispiel:
            font_family = gcs.layout.get_font_property('FAMILY')  # → "Arial"
        """
        if not self.layout_db:
            return default
        
        try:
            value, _ = self.layout_db.get_value('FONTS', property_name)
            return value if value is not None else default
        except Exception as e:
            logger.warning(f"⚠️ Font-Property '{property_name}' nicht gefunden: {e}")
            return default
    
    def get_stylesheet(self, widget_type: str) -> str:
        """
        Holt kompiliertes Stylesheet aus STYLES Gruppe.
        
        TEMPLATE-VARIABLEN:
        - {COLORS.BACKGROUND} → Ersetzt durch tatsächlichen Farbwert
        - {FONTS.FAMILY} → Ersetzt durch Font-Familie
        
        Args:
            widget_type: Qt-Widget-Typ (z.B. 'QMenu', 'QComboBox')
        
        Returns:
            Kompiliertes Stylesheet als String
        
        Beispiel:
            menu_style = gcs.layout.get_stylesheet('QMenu')
            menu.setStyleSheet(menu_style)
        """
        # Cache prüfen
        if widget_type in self._cache:
            return self._cache[widget_type]
        
        # Stylesheet kompilieren
        stylesheet = self._compile_stylesheet(widget_type)
        
        # In Cache speichern
        self._cache[widget_type] = stylesheet
        
        return stylesheet
    
    def _compile_stylesheet(self, widget_type: str) -> str:
        """
        Kompiliert Stylesheet mit Template-Variablen-Ersetzung.
        
        Args:
            widget_type: Qt-Widget-Typ
        
        Returns:
            Kompiliertes Stylesheet
        """
        if not self.layout_db:
            logger.warning(f"⚠️ Layout-DB nicht verfügbar für '{widget_type}' - verwende leeres Stylesheet")
            return ""
        
        try:
            # Template aus DB holen
            template, _ = self.layout_db.get_value('STYLES', widget_type)
            
            if not template:
                logger.debug(f"ℹ️ Kein Stylesheet für '{widget_type}' definiert")
                return ""
            
            # Template-Variablen ersetzen
            compiled = self._replace_variables(template)
            
            logger.debug(f"✅ Stylesheet kompiliert: {widget_type} ({len(compiled)} Zeichen)")
            
            return compiled
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Kompilieren von '{widget_type}': {e}")
            return ""
    
    def _replace_variables(self, template: str) -> str:
        """
        Ersetzt Template-Variablen {GRUPPE.FELD} mit tatsächlichen Werten.
        
        Args:
            template: Template-String mit Variablen
        
        Returns:
            String mit ersetzten Werten
        
        Beispiel:
            "background: {COLORS.BACKGROUND};" → "background: #ffffff;"
        """
        if not template or not self.layout_db:
            return template
        
        def replace_match(match):
            """Callback für re.sub - ersetzt einzelne Variable"""
            full = match.group(0)  # Kompletter Match: {COLORS.BACKGROUND}
            path = match.group(1)  # Pfad: COLORS.BACKGROUND
            
            try:
                # Pfad splitten
                parts = path.split('.')
                if len(parts) != 2:
                    logger.warning(f"⚠️ Ungültiger Variablen-Pfad: {path}")
                    return full
                
                gruppe, feld = parts
                
                # Wert aus DB holen
                value, _ = self.layout_db.get_value(gruppe, feld)
                
                if value is None:
                    logger.warning(f"⚠️ Variable '{path}' nicht gefunden - behalte Platzhalter")
                    return full
                
                return str(value)
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Ersetzen von '{path}': {e}")
                return full
        
        # Regex: {GRUPPE.FELD} - GRUPPE und FELD müssen aus A-Z, 0-9, _ bestehen
        pattern = r'\{([A-Z0-9_]+\.[A-Z0-9_]+)\}'
        
        # Alle Variablen ersetzen
        result = re.sub(pattern, replace_match, template)
        
        return result
    
    def reload_layout(self):
        """
        Lädt Layout neu (für Live-Editing im System-Editor).
        
        Löscht Cache und lädt Layout-Datenbank neu.
        """
        logger.info("🔄 Layout wird neu geladen...")
        
        # Cache leeren
        self._cache.clear()
        
        # Layout neu laden
        self._load_active_layout()
        
        logger.info("✅ Layout neu geladen")
    
    def get_available_colors(self) -> Dict[str, str]:
        """
        Gibt alle verfügbaren Farben zurück.
        
        Returns:
            Dict mit {color_name: color_value}
        
        Beispiel:
            colors = gcs.layout.get_available_colors()
            # → {'BACKGROUND': '#ffffff', 'TEXT': '#000000', ...}
        """
        if not self.layout_db:
            return {}
        
        try:
            colors = self.layout_db.get_value_by_group('COLORS')
            return colors if colors else {}
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Farben: {e}")
            return {}
    
    def get_available_widgets(self) -> list:
        """
        Gibt Liste aller Widget-Typen mit Stylesheets zurück.
        
        Returns:
            Liste von Widget-Typen (z.B. ['QMenu', 'QComboBox', ...])
        """
        if not self.layout_db:
            return []
        
        try:
            styles = self.layout_db.get_value_by_group('STYLES')
            return list(styles.keys()) if styles else []
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Widget-Liste: {e}")
            return []


# ===== HELPER-FUNKTIONEN =====

def apply_layout_to_widget(widget, widget_type: str, gcs):
    """
    Wendet Layout-Stylesheet auf Widget an.
    
    Args:
        widget: Qt-Widget
        widget_type: Widget-Typ (z.B. 'QMenu')
        gcs: GlobaleCentraleSystemsteuerung
    
    Beispiel:
        apply_layout_to_widget(menu, 'QMenu', gcs)
    """
    if not hasattr(gcs, 'layout'):
        logger.warning("⚠️ GCS hat kein Layout-System - überspringe Styling")
        return
    
    try:
        stylesheet = gcs.layout.get_stylesheet(widget_type)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            logger.debug(f"✅ Layout angewendet: {widget_type}")
    except Exception as e:
        logger.error(f"❌ Fehler beim Anwenden des Layouts: {e}")
