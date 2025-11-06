"""
Fix UTF-8 Encoding in v2_column_management_dialog.py
Ersetzt verstümmelte UTF-8 Zeichen durch korrekte Emojis
"""

import sys

# Korrekturen für verstümmelte UTF-8 Zeichen
replacements = {
    # Emojis
    'ðŸ"„': '📋',
    'âœ…': '✅',
    'âŒ': '❌',
    'âš ï¸': '⚠️',
    
    # Deutsche Umlaute
    'Ã¤': 'ä',
    'Ã¶': 'ö',
    'Ã¼': 'ü',
    'Ã„': 'Ä',
    'Ã–': 'Ö',
    'Ãœ': 'Ü',
    'ÃŸ': 'ß',
    
    # Sonderzeichen
    'â€¢': '•',
    'â€"': '–',
}

def fix_utf8_file(filename):
    """Repariert UTF-8 Encoding in Datei"""
    print(f"🔧 Repariere UTF-8 in {filename}...")
    
    try:
        # Datei lesen (mit latin-1 um alle Bytes zu lesen)
        with open(filename, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # Ersetzungen durchführen
        changes = 0
        for old, new in replacements.items():
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                changes += count
                print(f"  ✅ '{old}' → '{new}' ({count}x)")
        
        # Datei schreiben (mit UTF-8)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {changes} Ersetzungen durchgeführt!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    success = fix_utf8_file("v2_column_management_dialog.py")
    sys.exit(0 if success else 1)
