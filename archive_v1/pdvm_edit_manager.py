# pdvm_edit_manager.py
# -*- coding: utf-8 -*-
"""
🎯 PDVM EDIT MANAGER - Adapter für Input-Controls im GenerellerDialog

Vereinfacht und linearisiert die bestehende Input-Control Architektur:
- Nutzt PdvmInputControlWidget (unverändert)
- Vereinfacht Control-Erstellung (keine View-Auswahl)
- Integriert mit GCS (Stichtag, User-GUID)
- Persistiert in ROOT_TABLE.db (stichtagsgenau)

ARCHITEKTUR:
- Adapter-Pattern für PdvmInputWidget/PdvmInputManager
- Direkter GCS-Zugriff (kein call_data Dict)
- Kompatibel mit PdvmInputControlWidget
- Linear und einfach

Version: 1.0.0 (Phase 2.2)
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel

from pdvm_datetime import Pdvm_DateTime
from pdvm_input_manager import FieldMeta
from pdvm_instance_manager import PdvmInstanceManager
from pdvm_input_control_widget import PdvmInputControlWidget

logger = logging.getLogger(__name__)


class ControlObject:
    """
    Control-Objekt für PdvmInputControlWidget
    
    Enthält:
    - meta: FieldMeta (Label, Type, Tooltip, etc.)
    - display_value: Aktueller Wert
    - abdatum_inst: Pdvm_DateTime für Änderungszeitpunkt
    - manager: Referenz zum EditManager
    """
    
    def __init__(self, meta, display_value, abdatum_inst, manager):
        self.meta = meta
        self.display_value = display_value
        self.abdatum_inst = abdatum_inst
        self.manager = manager
        
        # Value-Instanz (für DateTime-Felder)
        self.value_inst = None
        if meta.type == 'datetime' and display_value:
            self.value_inst = Pdvm_DateTime(manager.gcs.field_value('country'))
            try:
                self.value_inst.PdvmDateTime = float(display_value)
            except (ValueError, TypeError):
                logger.warning(f"Kann DateTime nicht parsen: {display_value}")
        
        # UI-Widths (aus FieldMeta oder Manager-Defaults)
        self.label_width = meta.ui_width_label or manager.width_label
        self.value_width = meta.ui_width_value or manager.width_control
        self.button_width = meta.ui_width_button or manager.width_button
        
        # Help-Text (aus Metadaten)
        self.help_text = ""
        self.help_header = ""
        if meta.help_instance:
            try:
                help_data, _ = meta.help_instance.get_value('SYSTEM', 'HELPTEXT', manager.gcs.st_inst.PdvmDateTime)
                self.help_text = help_data or ""
                help_header_data, _ = meta.help_instance.get_value('SYSTEM', 'HELPHEADER', manager.gcs.st_inst.PdvmDateTime)
                self.help_header = help_header_data or ""
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Hilfe für {meta.key}: {e}")


class PdvmEditManager:
    """
    Adapter für Input-Controls im GenerellerDialog
    
    VERANTWORTLICHKEITEN:
    - Framedaten laden (frame_guid)
    - Metadaten parsen → FieldMeta
    - Instanzen verwalten (PdvmInstanceManager)
    - Controls erstellen (ControlObjects)
    - Werte laden/speichern (stichtagsgenau)
    - Widget-Erstellung für UI
    
    VEREINFACHUNGEN gegenüber PdvmInputWidget:
    - Kein call_data Dict → Direkt GCS
    - Kein eigener Stichtag-Picker → Nutzt Dialog-Header
    - Kein eigener Speichern-Button → Nutzt Dialog-Button
    - Linear und einfach
    """
    
    def __init__(self, frame_guid: str, root_table: str, framedaten_db, gcs):
        """
        Initialisiert EditManager
        
        Args:
            frame_guid: GUID der Framedaten
            root_table: Name der Root-Tabelle (z.B. "persondaten")
            framedaten_db: PdvmCentralDatenbank Instanz für Framedaten
            gcs: Globale Systemsteuerung (für Stichtag, User-GUID, etc.)
        """
        logger.info("🎯 === PDVM EDIT MANAGER INITIALISIERUNG ===")
        
        self.frame_guid = frame_guid
        self.root_table = root_table
        self.framedaten_db = framedaten_db
        self.gcs = gcs
        
        # Datensatz-GUID (wird bei load_datensatz gesetzt)
        self.selected_guid = None
        
        # Instanzen-Manager (wird bei load_datensatz erstellt)
        self.instance_manager = None
        
        # Fields (FieldMeta Objekte)
        self.fields: Dict[str, FieldMeta] = {}
        
        # Controls (ControlObjects)
        self.controls: Dict[str, ControlObject] = {}
        
        # UI-Defaults (aus Framedaten ROOT)
        self.width_label = 150
        self.width_control = 200
        self.width_button = 100
        self.width_indent_ab = 50
        
        # Framedaten laden
        self._load_framedaten()
        
        logger.info(f"✅ EditManager initialisiert: frame_guid={frame_guid}, root_table={root_table}")
    
    def _load_framedaten(self):
        """Lädt Framedaten aus framedaten_db (Gruppe/Feld-weise)"""
        logger.info("📂 Lade Framedaten...")
        
        try:
            # UI-Defaults aus ROOT-Gruppe laden
            self.width_label, _ = self.framedaten_db.get_value('ROOT', 'width_label')
            self.width_control, _ = self.framedaten_db.get_value('ROOT', 'width_control')
            self.width_button, _ = self.framedaten_db.get_value('ROOT', 'width_button')
            self.width_indent_ab, _ = self.framedaten_db.get_value('ROOT', 'width_indent_ab')
            
            # Defaults falls nicht gefunden
            self.width_label = self.width_label or 150
            self.width_control = self.width_control or 200
            self.width_button = self.width_button or 100
            self.width_indent_ab = self.width_indent_ab or 50
            
            logger.info(f"  📏 Widths: Label={self.width_label}, Control={self.width_control}")
            
            # Metadaten aus Gruppe "METADATEN" laden (GROSSBUCHSTABEN!)
            self.metadaten = self.framedaten_db.get_gruppe('METADATEN')
            
            # Fallback: Versuche auch lowercase
            if not self.metadaten:
                logger.warning("  ⚠️ Gruppe 'METADATEN' nicht gefunden, versuche 'Metadaten'...")
                self.metadaten = self.framedaten_db.get_gruppe('Metadaten')
            
            if not self.metadaten:
                logger.warning("⚠️ Keine Metadaten in Framedaten gefunden!")
                self.metadaten = {}
            else:
                logger.info(f"  📊 {len(self.metadaten)} Felder in Metadaten gefunden")
            
            logger.info("✅ Framedaten erfolgreich geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Framedaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def load_datensatz(self, guid: str):
        """
        Lädt Datensatz und bereitet Controls vor
        
        Args:
            guid: GUID des zu ladenden Datensatzes (uid_original)
        """
        logger.info(f"🔄 Lade Datensatz: {guid}")
        
        try:
            self.selected_guid = guid
            
            # Instance Manager erstellen
            logger.info("  🔧 Erstelle InstanceManager...")
            self.instance_manager = PdvmInstanceManager(
                root_table=self.root_table,
                root_guid=guid,
                stichtag=self.gcs.st_inst.PdvmDateTime,
                framedaten=self.metadaten  # ← framedaten, nicht metadaten!
            )
            logger.info(f"  ✅ InstanceManager erstellt (Stichtag: {self.gcs.stichtag})")
            
            # Fields erstellen
            logger.info("  🔧 Erstelle Fields...")
            self._create_fields()
            logger.info(f"  ✅ {len(self.fields)} Fields erstellt")
            
            # Controls erstellen
            logger.info("  🔧 Erstelle Controls...")
            self._create_controls()
            logger.info(f"  ✅ {len(self.controls)} Controls erstellt")
            
            logger.info(f"✅ Datensatz erfolgreich geladen: {guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Datensatzes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _create_fields(self):
        """Erstellt FieldMeta Objekte aus Metadaten"""
        self.fields = {}
        
        for key, meta_config in self.metadaten.items():
            try:
                key_lower = key.lower()
                
                # Parse key: tabelle_gruppe_feld
                parts = key_lower.split('_')
                if len(parts) < 3:
                    logger.warning(f"  ⚠️ Ungültiges Key-Format: {key_lower} (erwartet: tabelle_gruppe_feld)")
                    continue
                
                table = parts[0]  # z.B. "persondaten"
                
                # FieldMeta erstellen (wie PdvmInputManager)
                field_meta = FieldMeta(key_lower, meta_config)
                
                # data_instance zuweisen
                source_path = meta_config.get('source_path', 'root')
                field_meta.data_instance = self.instance_manager.get_instance(
                    table,
                    source_path
                )
                
                if not field_meta.data_instance:
                    logger.warning(f"  ⚠️ Keine Instanz für {key_lower} (table={table}, path={source_path})")
                    continue
                
                # dropdown_instance zuweisen
                if field_meta.dropdown_def:
                    dropdown_table = field_meta.dropdown_def.get('table')
                    dropdown_source_path = field_meta.dropdown_def.get('source_path', source_path)
                    if dropdown_table:
                        field_meta.dropdown_instance = self.instance_manager.get_instance(
                            dropdown_table,
                            dropdown_source_path
                        )
                        logger.debug(f"  📦 Dropdown: {key_lower} → {dropdown_table}")
                
                # help_instance zuweisen
                if field_meta.help_def:
                    help_table = field_meta.help_def.get('table')
                    help_source_path = field_meta.help_def.get('source_path', source_path)
                    if help_table:
                        field_meta.help_instance = self.instance_manager.get_instance(
                            help_table,
                            help_source_path
                        )
                        logger.debug(f"  ❓ Help: {key_lower} → {help_table}")
                
                self.fields[key_lower] = field_meta
                logger.debug(f"  ✅ Field erstellt: {key_lower} (type={field_meta.type})")
                
            except Exception as e:
                logger.error(f"  ❌ Fehler beim Erstellen von Field {key}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def _create_controls(self):
        """Erstellt ControlObjects für UI-Widgets"""
        self.controls = {}
        
        for key, field_meta in self.fields.items():
            try:
                # Parse key für Gruppe/Feld
                parts = key.split('_')
                gruppe = parts[1].upper()
                feld = '_'.join(parts[2:]).upper()
                
                # Wert laden (stichtagsgenau!)
                wert, abdatum = field_meta.data_instance.get_value(
                    gruppe,
                    feld,
                    self.gcs.st_inst.PdvmDateTime
                )
                
                # Abdatum-Instanz erstellen
                abdatum_inst = Pdvm_DateTime(self.gcs.field_value('country'))
                if abdatum:
                    try:
                        abdatum_inst.PdvmDateTime = float(abdatum)
                    except (ValueError, TypeError):
                        logger.warning(f"  ⚠️ Kann Abdatum nicht parsen: {abdatum}")
                
                # ControlObject erstellen
                control = ControlObject(
                    meta=field_meta,
                    display_value=wert,
                    abdatum_inst=abdatum_inst,
                    manager=self
                )
                
                self.controls[key] = control
                logger.debug(f"  ✅ Control erstellt: {key} (wert={str(wert)[:30]}...)")
                
            except Exception as e:
                logger.error(f"  ❌ Fehler beim Erstellen von Control {key}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def get_widget(self) -> QWidget:
        """
        Gibt QWidget mit allen Controls zurück
        
        VEREINFACHT: Kein Stichtag-Picker, kein Speichern-Button
        Diese Funktionalität ist im Dialog-Header
        
        Returns:
            QWidget mit ScrollArea und allen Controls
        """
        logger.info("🎨 Erstelle Edit-Widget...")
        
        try:
            # Container mit ScrollArea
            container = QWidget()
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(5)
            
            # Scroll-Area für Controls
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            
            # Content-Widget
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(5, 5, 5, 5)
            content_layout.setSpacing(5)
            
            # Controls hinzufügen (sortiert nach Key)
            if not self.controls:
                # Keine Controls vorhanden
                no_data_label = QLabel("Keine Felder für diesen Datensatz verfügbar.")
                no_data_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
                content_layout.addWidget(no_data_label)
                logger.warning("  ⚠️ Keine Controls zum Anzeigen vorhanden")
            else:
                # Controls sortiert hinzufügen
                sorted_keys = sorted(self.controls.keys())
                for key in sorted_keys:
                    control = self.controls[key]
                    try:
                        widget = PdvmInputControlWidget(control)
                        content_layout.addWidget(widget)
                        logger.debug(f"  ✅ Widget hinzugefügt: {key}")
                    except Exception as e:
                        logger.error(f"  ❌ Fehler beim Erstellen von Widget {key}: {e}")
            
            content_layout.addStretch()
            
            # Content in ScrollArea
            scroll.setWidget(content)
            main_layout.addWidget(scroll)
            
            logger.info(f"✅ Edit-Widget erstellt mit {len(self.controls)} Controls")
            return container
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Widgets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback: Error-Widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"❌ Fehler beim Laden der Controls:\n{str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            return error_widget
    
    def save_changes(self):
        """
        Speichert alle geänderten Werte zurück in die Datenbank
        
        Geht durch alle Controls und speichert deren Werte
        """
        logger.info("💾 Speichere Änderungen...")
        
        try:
            saved_count = 0
            
            for key, control in self.controls.items():
                try:
                    # Parse key
                    parts = key.split('_')
                    gruppe = parts[1].upper()
                    feld = '_'.join(parts[2:]).upper()
                    
                    # Wert speichern
                    instance = control.meta.data_instance
                    instance.set_value(
                        gruppe,
                        feld,
                        control.display_value,
                        control.abdatum_inst.PdvmDateTime if control.abdatum_inst else None
                    )
                    
                    saved_count += 1
                    logger.debug(f"  ✅ Gespeichert: {key}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Fehler beim Speichern von {key}: {e}")
            
            # Alle Instanzen persistieren
            if self.instance_manager:
                self.instance_manager.save_all_instances()
                logger.info(f"✅ {saved_count} Felder erfolgreich gespeichert")
            else:
                logger.warning("⚠️ InstanceManager nicht verfügbar, Daten nicht persistiert!")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def get_value(self, key: str):
        """
        Holt Wert für ein Feld (Kompatibilität mit PdvmInputManager)
        
        Args:
            key: Feld-Key (tabelle_gruppe_feld)
        
        Returns:
            Tuple[Any, float]: (wert, abdatum)
        """
        control = self.controls.get(key)
        if control:
            abdatum = control.abdatum_inst.PdvmDateTime if control.abdatum_inst else None
            return control.display_value, abdatum
        return None, None
    
    def set_value(self, key: str, wert, abdatum):
        """
        Setzt Wert für ein Feld (Kompatibilität mit PdvmInputManager)
        
        Args:
            key: Feld-Key (tabelle_gruppe_feld)
            wert: Neuer Wert
            abdatum: Neues Abdatum (float)
        """
        control = self.controls.get(key)
        if control:
            control.display_value = wert
            if control.abdatum_inst and abdatum:
                control.abdatum_inst.PdvmDateTime = float(abdatum)
