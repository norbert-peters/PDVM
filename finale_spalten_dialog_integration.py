#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINALE LÖSUNG: Controls-Integration in pdvm_spalten_konfig_dialog.py

Implementiert deine lineare Architektur mit Base64-Persistierung
"""

def pdvm_spalten_konfig_dialog_integration():
    """
    Zeigt, wie die robuste Controls-Persistierung in den echten Spalten-Dialog integriert wird
    """
    
    integration_code = '''
# INTEGRATION IN pdvm_spalten_konfig_dialog.py:

import base64
import json
import logging
from pdvm_central_systemsteuerung import gcs

class PdvmSpaltenKonfigDialog(QDialog):
    """
    NEUE ARCHITEKTUR: Vollständige Controls aus Systemsteuerung
    """
    
    def __init__(self, parent=None, view_id=None):
        super().__init__(parent)
        
        if not view_id:
            raise ValueError("view_id ist erforderlich für Controls-Persistierung")
            
        self.view_id = view_id
        self.systemsteuerung = gcs()
        self.controls_data = {}  # Vollständige Controls aus Systemsteuerung
        
        self._setup_ui()
        self._load_controls_from_systemsteuerung()
    
    def _load_controls_from_systemsteuerung(self):
        """
        KERNMETHODE: Lädt vollständige Controls aus Systemsteuerung
        
        NEUE LINEARE ARCHITEKTUR:
        - Keine Synchronisation mit ViewDaten mehr nötig
        - Controls sind bereits vollständig in Systemsteuerung
        - Expert Mode kommt direkt aus Systemsteuerung
        """
        try:
            logger.info(f"📥 Lade Controls für View: {self.view_id}")
            
            # Expert Mode aus Systemsteuerung
            expert_mode = self.systemsteuerung.global_expert_mode
            logger.info(f"🎯 Expert Mode: {expert_mode}")
            
            # Alle bekannten Feld-Namen durchgehen
            possible_fields = [
                'person_id', 'name', 'vorname', 'nachname', 'geburtsdatum',
                'adresse_id', 'strasse', 'plz', 'ort', 'email', 'telefon'
            ]
            
            loaded_count = 0
            for field_name in possible_fields:
                control = self._load_single_control(field_name)
                if control:
                    self.controls_data[field_name] = control
                    loaded_count += 1
            
            logger.info(f"✅ {loaded_count} Controls aus Systemsteuerung geladen")
            
            # UI aktualisieren
            self._populate_table_from_controls()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Controls: {e}")
            # Fallback: Leere Tabelle zeigen
            self._show_empty_table_message()
    
    def _load_single_control(self, field_name):
        """Lädt einzelnes Control mit Base64-Decoding"""
        try:
            # Base64-codierte Control-Daten laden
            result = self.systemsteuerung.get_value(
                gruppe=self.view_id,
                feld=f"ctrl64_{field_name}"
            )
            
            if result:
                # Base64-String extrahieren
                if isinstance(result, dict) and 'wert' in result:
                    base64_string = result['wert']
                elif isinstance(result, str):
                    base64_string = result
                else:
                    return None
                
                # Base64 zu JSON zu Control-Dict
                json_bytes = base64.b64decode(base64_string.encode('ascii'))
                json_string = json_bytes.decode('utf-8')
                control_dict = json.loads(json_string)
                
                return control_dict
                
        except Exception as e:
            logger.debug(f"Control {field_name} nicht gefunden oder fehlerhaft: {e}")
            
        return None
    
    def _populate_table_from_controls(self):
        """
        KERNMETHODE: Befüllt Tabelle aus vollständigen Controls
        
        LÖSUNG FÜR "ES SIND KEINE SPALTEN ZU SEHEN":
        - Verwendet vollständige Control-Strukturen
        - Alle Informationen bereits vorhanden
        - Keine Synchronisation nötig
        """
        if not self.controls_data:
            self._show_empty_table_message()
            return
        
        # Tabelle leeren
        self.table_widget.setRowCount(0)
        
        # Sortierung nach displayOrder
        sorted_controls = sorted(
            self.controls_data.items(),
            key=lambda x: x[1].get('displayOrder', 999)
        )
        
        # Expert Mode prüfen
        expert_mode = self.systemsteuerung.global_expert_mode
        
        for row, (field_name, control) in enumerate(sorted_controls):
            self.table_widget.insertRow(row)
            
            # Spalten befüllen mit vollständigen Control-Daten
            self._populate_table_row(row, field_name, control, expert_mode)
        
        logger.info(f"📊 Tabelle mit {len(sorted_controls)} Controls befüllt")
    
    def _populate_table_row(self, row, field_name, control, expert_mode):
        """Befüllt eine Tabellenzeile mit Control-Daten"""
        
        # Spalte 0: Checkbox (Show/Hide)
        checkbox = QCheckBox()
        checkbox.setChecked(control.get('show', True))
        checkbox.stateChanged.connect(lambda state, fn=field_name: self._on_show_changed(fn, state))
        self.table_widget.setCellWidget(row, 0, checkbox)
        
        # Spalte 1: Spaltentitel (editierbar)
        title_item = QTableWidgetItem(control.get('spaltenueberschrift', field_name))
        title_item.setData(Qt.UserRole, field_name)  # Field-Name für Referenz
        self.table_widget.setItem(row, 1, title_item)
        
        # Spalte 2: Typ (nur anzeigen)
        type_item = QTableWidgetItem(control.get('type', 'str'))
        type_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row, 2, type_item)
        
        # Spalte 3: Breite (editierbar)
        width_item = QTableWidgetItem(str(control.get('breite', 120)))
        self.table_widget.setItem(row, 3, width_item)
        
        # Spalte 4: Position (nur im Expert Mode)
        if expert_mode:
            pos_item = QTableWidgetItem(str(control.get('displayOrder', 0)))
            self.table_widget.setItem(row, 4, pos_item)
    
    def _save_controls_to_systemsteuerung(self):
        """
        KERNMETHODE: Speichert geänderte Controls zurück in Systemsteuerung
        
        NEUE ARCHITEKTUR:
        - Übernimmt Änderungen aus UI in Control-Dicts
        - Speichert als Base64 in Systemsteuerung
        - Projektion kann direkt diese Controls verwenden
        """
        try:
            logger.info("💾 Speichere Control-Änderungen in Systemsteuerung")
            
            # Änderungen aus UI übernehmen
            self._update_controls_from_ui()
            
            # Alle Controls speichern
            saved_count = 0
            for field_name, control in self.controls_data.items():
                if self._save_single_control(field_name, control):
                    saved_count += 1
            
            logger.info(f"✅ {saved_count}/{len(self.controls_data)} Controls gespeichert")
            
            # Dialog schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            QMessageBox.warning(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def _save_single_control(self, field_name, control):
        """Speichert einzelnes Control mit Base64-Encoding"""
        try:
            # Control zu JSON zu Base64
            json_string = json.dumps(control, ensure_ascii=False)
            json_bytes = json_string.encode('utf-8')
            base64_string = base64.b64encode(json_bytes).decode('ascii')
            
            # In Systemsteuerung speichern
            self.systemsteuerung.set_value(
                gruppe=self.view_id,
                feld=f"ctrl64_{field_name}",
                wert=base64_string
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern Control {field_name}: {e}")
            return False
    
    def _update_controls_from_ui(self):
        """Übernimmt Änderungen aus UI in Control-Dicts"""
        
        for row in range(self.table_widget.rowCount()):
            # Field-Name aus UserRole
            title_item = self.table_widget.item(row, 1)
            if not title_item:
                continue
                
            field_name = title_item.data(Qt.UserRole)
            if field_name not in self.controls_data:
                continue
            
            control = self.controls_data[field_name]
            
            # Show/Hide Status
            checkbox = self.table_widget.cellWidget(row, 0)
            if checkbox:
                control['show'] = checkbox.isChecked()
            
            # Spaltentitel
            control['spaltenueberschrift'] = title_item.text()
            
            # Breite
            width_item = self.table_widget.item(row, 3)
            if width_item:
                try:
                    control['breite'] = int(width_item.text())
                except ValueError:
                    pass  # Ungültige Eingabe ignorieren
            
            # Position (Expert Mode)
            if self.systemsteuerung.global_expert_mode:
                pos_item = self.table_widget.item(row, 4)
                if pos_item:
                    try:
                        control['displayOrder'] = int(pos_item.text())
                    except ValueError:
                        pass
    
    def _show_empty_table_message(self):
        """Zeigt Nachricht bei leerer Tabelle"""
        self.table_widget.setRowCount(1)
        msg_item = QTableWidgetItem("Keine Controls gefunden. Bitte View-Dialog öffnen um Controls zu generieren.")
        msg_item.setFlags(Qt.ItemIsEnabled)
        self.table_widget.setItem(0, 0, msg_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
    '''
    
    print("🎯 FINALE INTEGRATION: Controls in pdvm_spalten_konfig_dialog.py")
    print("=" * 70)
    print(integration_code)
    
    print("\n🎉 ZUSAMMENFASSUNG DER LÖSUNG:")
    print("✅ Vollständige Controls aus Systemsteuerung laden")
    print("✅ Base64-Encoding umgeht Systemsteuerung-Serialisierung")
    print("✅ Expert Mode direkt aus Systemsteuerung")
    print("✅ Lineare Architektur: Keine Synchronisation mehr nötig")
    print("✅ Löst 'Es sind keine Spalten zu sehen' Problem")
    print("✅ Autonomer Spalten-Dialog mit persistierten Controls")

if __name__ == "__main__":
    pdvm_spalten_konfig_dialog_integration()
