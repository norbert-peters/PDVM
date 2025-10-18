"""
Quick Fix: Alte Filter-Methoden aus pdvm_view_matrix_manager.py entfernen
"""

with open('pdvm_view_matrix_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde Start und Ende
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '# V3 FILTER-LOGIK: Alte Methoden ENTFERNT' in line:
        start_line = i
    if start_line and '# ENDE FILTER-LOGIK' in line:
        end_line = i
        break

if start_line and end_line:
    print(f"Found old code: lines {start_line} to {end_line}")
    print(f"Deleting {end_line - start_line - 13} lines...")
    
    # Keep nur den Kommentar-Block und die Zeile nach ENDE
    new_lines = lines[:start_line + 13] + lines[end_line + 2:]
    
    with open('pdvm_view_matrix_manager.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Alte Filter-Methoden gelöscht!")
else:
    print(f"❌ Marker nicht gefunden! start={start_line}, end={end_line}")
