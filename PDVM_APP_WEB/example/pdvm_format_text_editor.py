# -*- coding: utf-8 -*-
"""
PDVM Format Text Editor - Rich-Text-Editor mit HTML-Unterstützung
===================================================================

Dialog zum Bearbeiten von formatiertem Text (HTML).
Bietet Toolbar mit Standard-Formatierungsoptionen.

Features:
- Fett, Kursiv, Unterstrichen
- Schriftgröße und -farbe
- Aufzählungen und Nummerierungen
- Text-Ausrichtung
- HTML-Export/Import

Erstellt: 30.11.2025
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QToolBar, QFontComboBox, QSpinBox, QColorDialog, QAction,
    QLabel, QWidget
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor, QIcon

logger = logging.getLogger(__name__)


class PdvmFormatTextEditor(QDialog):
    """
    Rich-Text-Editor-Dialog für formatierten Text.
    
    Verwendet QTextEdit mit HTML-Unterstützung.
    Bietet Toolbar mit Standard-Formatierungsoptionen.
    """
    
    def __init__(self, initial_html: str = "", parent=None):
        """
        Initialisiert Format-Text-Editor.
        
        Args:
            initial_html: Initialer HTML-Content (optional)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Format-Text Editor")
        self.setMinimumSize(800, 600)
        
        # Result
        self.html_content = initial_html
        self.accepted = False
        
        # UI aufbauen
        self._setup_ui()
        
        # Initialen Content setzen
        if initial_html:
            self.text_edit.setHtml(initial_html)
        
        logger.info("✅ Format-Text-Editor initialisiert")
    
    def _setup_ui(self):
        """Baut UI auf"""
        layout = QVBoxLayout(self)
        
        # === TOOLBAR ===
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Schriftart
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._change_font)
        toolbar.addWidget(QLabel(" Schrift: "))
        toolbar.addWidget(self.font_combo)
        
        toolbar.addSeparator()
        
        # Schriftgröße
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(12)
        self.font_size.valueChanged.connect(self._change_font_size)
        toolbar.addWidget(QLabel(" Größe: "))
        toolbar.addWidget(self.font_size)
        
        toolbar.addSeparator()
        
        # Fett
        bold_action = QAction("B", self)
        bold_action.setCheckable(True)
        bold_action.setFont(QFont("Arial", 10, QFont.Bold))
        bold_action.triggered.connect(self._toggle_bold)
        toolbar.addAction(bold_action)
        self.bold_action = bold_action
        
        # Kursiv
        italic_action = QAction("I", self)
        italic_action.setCheckable(True)
        italic_font = QFont("Arial", 10)
        italic_font.setItalic(True)
        italic_action.setFont(italic_font)
        italic_action.triggered.connect(self._toggle_italic)
        toolbar.addAction(italic_action)
        self.italic_action = italic_action
        
        # Unterstrichen
        underline_action = QAction("U", self)
        underline_action.setCheckable(True)
        underline_font = QFont("Arial", 10)
        underline_font.setUnderline(True)
        underline_action.setFont(underline_font)
        underline_action.triggered.connect(self._toggle_underline)
        toolbar.addAction(underline_action)
        self.underline_action = underline_action
        
        toolbar.addSeparator()
        
        # Textfarbe
        color_action = QAction("🎨 Farbe", self)
        color_action.triggered.connect(self._change_color)
        toolbar.addAction(color_action)
        
        toolbar.addSeparator()
        
        # Ausrichtung
        align_left = QAction("⬅", self)
        align_left.triggered.connect(lambda: self.text_edit.setAlignment(Qt.AlignLeft))
        toolbar.addAction(align_left)
        
        align_center = QAction("↔", self)
        align_center.triggered.connect(lambda: self.text_edit.setAlignment(Qt.AlignCenter))
        toolbar.addAction(align_center)
        
        align_right = QAction("➡", self)
        align_right.triggered.connect(lambda: self.text_edit.setAlignment(Qt.AlignRight))
        toolbar.addAction(align_right)
        
        toolbar.addSeparator()
        
        # Listen
        bullet_action = QAction("• Liste", self)
        bullet_action.triggered.connect(self._insert_bullet_list)
        toolbar.addAction(bullet_action)
        
        number_action = QAction("1. Liste", self)
        number_action.triggered.connect(self._insert_number_list)
        toolbar.addAction(number_action)
        
        layout.addWidget(toolbar)
        
        # === TEXT EDITOR ===
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.cursorPositionChanged.connect(self._update_format_actions)
        layout.addWidget(self.text_edit)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        
        # HTML anzeigen (Debug)
        show_html_btn = QPushButton("📄 HTML anzeigen")
        show_html_btn.clicked.connect(self._show_html)
        button_layout.addWidget(show_html_btn)
        
        button_layout.addStretch()
        
        # Abbrechen
        cancel_btn = QPushButton("❌ Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Übernehmen
        ok_btn = QPushButton("✅ Übernehmen")
        ok_btn.clicked.connect(self._accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _change_font(self, font):
        """Ändert Schriftart"""
        fmt = QTextCharFormat()
        fmt.setFont(font)
        self._merge_format(fmt)
    
    def _change_font_size(self, size):
        """Ändert Schriftgröße"""
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)
    
    def _toggle_bold(self):
        """Schaltet Fett um"""
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if self.bold_action.isChecked() else QFont.Normal)
        self._merge_format(fmt)
    
    def _toggle_italic(self):
        """Schaltet Kursiv um"""
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_action.isChecked())
        self._merge_format(fmt)
    
    def _toggle_underline(self):
        """Schaltet Unterstrichen um"""
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_action.isChecked())
        self._merge_format(fmt)
    
    def _change_color(self):
        """Öffnet Farbwähler"""
        color = QColorDialog.getColor(Qt.black, self, "Textfarbe wählen")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)
    
    def _insert_bullet_list(self):
        """Fügt Aufzählungsliste ein"""
        cursor = self.text_edit.textCursor()
        cursor.insertList(QTextCursor.ListDisc)
    
    def _insert_number_list(self):
        """Fügt nummerierte Liste ein"""
        cursor = self.text_edit.textCursor()
        cursor.insertList(QTextCursor.ListDecimal)
    
    def _merge_format(self, fmt):
        """Wendet Format auf aktuelle Auswahl an"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)
    
    def _update_format_actions(self):
        """Aktualisiert Format-Actions basierend auf aktueller Cursor-Position"""
        fmt = self.text_edit.currentCharFormat()
        
        # Font
        self.font_combo.setCurrentFont(fmt.font())
        self.font_size.setValue(int(fmt.fontPointSize()) if fmt.fontPointSize() > 0 else 12)
        
        # Bold/Italic/Underline
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
    
    def _show_html(self):
        """Zeigt HTML-Code in neuem Dialog (Debug)"""
        from PyQt5.QtWidgets import QMessageBox, QTextEdit
        
        html = self.text_edit.toHtml()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("HTML-Code")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        html_view = QTextEdit()
        html_view.setPlainText(html)
        html_view.setReadOnly(True)
        layout.addWidget(html_view)
        
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _accept(self):
        """Übernimmt HTML und schließt Dialog"""
        self.html_content = self.text_edit.toHtml()
        self.accepted = True
        self.accept()
        logger.info("✅ Format-Text übernommen")
    
    def get_html(self) -> str:
        """
        Gibt HTML-Content zurück.
        
        Returns:
            HTML-String
        """
        return self.html_content


# ========================================
# STANDALONE-TEST
# ========================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test mit initialem Content
    initial_html = """
    <h2>Beispiel-Text</h2>
    <p>Dies ist ein <b>fetter</b> und <i>kursiver</i> Text.</p>
    <ul>
        <li>Punkt 1</li>
        <li>Punkt 2</li>
    </ul>
    """
    
    editor = PdvmFormatTextEditor(initial_html)
    
    if editor.exec_() == QDialog.Accepted:
        print("✅ HTML übernommen:")
        print(editor.get_html())
    else:
        print("❌ Abgebrochen")
    
    sys.exit(0)
