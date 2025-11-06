"""
🔧 Fix: Ersetze alle content_layout Referenzen durch workspace_layout

Nach der V3.1 Architektur-Änderung (3-Ebenen-Trennung) müssen alle
Referenzen zu content_layout durch workspace_layout ersetzt werden.
"""

import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_workspace_layout_references():
    """Ersetzt content_layout durch workspace_layout in v2_systemstart.py"""
    
    file_path = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\v2_systemstart.py"
    
    logger.info("🔧 Starte Layout-Referenz-Fix...")
    logger.info(f"📂 Datei: {file_path}")
    
    try:
        # Datei lesen
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Ersetze self.content_layout durch self.workspace_layout
        # AUSSER in Kommentaren und Docstrings
        
        replacements = [
            (r'self\.content_layout\.addWidget\(', r'self.workspace_layout.addWidget('),
            (r'self\.content_layout\.addSpacing\(', r'self.workspace_layout.addSpacing('),
            (r'self\.content_layout\.addStretch\(', r'self.workspace_layout.addStretch('),
            (r'self\.content_layout\.removeWidget\(', r'self.workspace_layout.removeWidget('),
            (r'self\.content_layout\.count\(\)', r'self.workspace_layout.count()'),
            (r'self\.content_layout\.takeAt\(', r'self.workspace_layout.takeAt('),
        ]
        
        total_replacements = 0
        for old_pattern, new_pattern in replacements:
            matches = re.findall(old_pattern, content)
            count = len(matches)
            if count > 0:
                content = re.sub(old_pattern, new_pattern, content)
                logger.info(f"  ✅ {count}x ersetzt: {old_pattern} → {new_pattern}")
                total_replacements += count
        
        if total_replacements > 0:
            # Backup erstellen
            backup_path = file_path + ".backup_before_layout_fix"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            logger.info(f"💾 Backup erstellt: {backup_path}")
            
            # Geänderte Datei speichern
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ {total_replacements} Referenzen korrigiert!")
            logger.info("🎉 Layout-Referenz-Fix abgeschlossen!")
        else:
            logger.info("ℹ️ Keine Änderungen notwendig")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Fix: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    fix_workspace_layout_references()
