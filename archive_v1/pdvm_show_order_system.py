#!/usr/bin/env python3
"""
PDVM Show-Order System - Komplett unabhängige Normal/Expert Modi
"""

def initialize_show_order_system(columns):
    """
    Initialisiert das show_order System komplett unabhängig vom Expert-Mode
    
    Regel:
    - Alle expert=False Spalten bekommen fortlaufende show_order (1,2,3,4...)
    - show=True Spalten zuerst, dann show=False Spalten
    - Expert-Spalten (expert=True) bekommen KEINE show_order
    """
    print("🔧 Initialisiere show_order System...")
    
    # 1. Sammle alle Normal-Spalten (expert=False)
    normal_columns = [col for col in columns if not col.get('expert', False)]
    
    # 2. Sortiere: show=True zuerst, dann show=False
    normal_columns.sort(key=lambda col: (not col.get('show', False), col.get('order', 9999)))
    
    # 3. Vergebe fortlaufende show_order
    for i, col in enumerate(normal_columns, 1):
        col['show_order'] = i
        print(f"   📊 {col['name']}: show_order={i} (show={col.get('show', False)})")
    
    # 4. Expert-Spalten bekommen KEINE show_order
    for col in columns:
        if col.get('expert', False):
            if 'show_order' in col:
                del col['show_order']
            print(f"   🔧 {col['name']}: EXPERT - show_order entfernt")
    
    print(f"✅ Show-Order System initialisiert: {len(normal_columns)} Normal-Spalten")
    return columns

def get_normal_mode_columns(columns):
    """Gibt nur Normal-Mode Spalten zurück, sortiert nach show_order"""
    normal_cols = [col for col in columns if not col.get('expert', False)]
    return sorted(normal_cols, key=lambda col: col.get('show_order', 9999))

def get_expert_mode_columns(columns):
    """Gibt alle Spalten zurück, sortiert nach order"""
    return sorted(columns, key=lambda col: col.get('order', 9999))

def move_normal_column_up(columns, column_name):
    """Verschiebt Spalte im Normal-Mode nach oben (nur show_order)"""
    normal_cols = get_normal_mode_columns(columns)
    
    # Finde aktuelle Position
    current_pos = None
    for i, col in enumerate(normal_cols):
        if col['name'] == column_name:
            current_pos = i
            break
    
    if current_pos is None or current_pos == 0:
        return False  # Nicht gefunden oder bereits ganz oben
    
    # Tausche show_order mit vorheriger Spalte
    prev_col = normal_cols[current_pos - 1]
    curr_col = normal_cols[current_pos]
    
    prev_show_order = prev_col['show_order']
    curr_show_order = curr_col['show_order']
    
    prev_col['show_order'] = curr_show_order
    curr_col['show_order'] = prev_show_order
    
    print(f"🔼 Show_order getauscht: {column_name} ↔ {prev_col['name']}")
    return True

def move_normal_column_down(columns, column_name):
    """Verschiebt Spalte im Normal-Mode nach unten (nur show_order)"""
    normal_cols = get_normal_mode_columns(columns)
    
    # Finde aktuelle Position
    current_pos = None
    for i, col in enumerate(normal_cols):
        if col['name'] == column_name:
            current_pos = i
            break
    
    if current_pos is None or current_pos >= len(normal_cols) - 1:
        return False  # Nicht gefunden oder bereits ganz unten
    
    # Tausche show_order mit nächster Spalte
    curr_col = normal_cols[current_pos]
    next_col = normal_cols[current_pos + 1]
    
    curr_show_order = curr_col['show_order']
    next_show_order = next_col['show_order']
    
    curr_col['show_order'] = next_show_order
    next_col['show_order'] = curr_show_order
    
    print(f"🔽 Show_order getauscht: {column_name} ↔ {next_col['name']}")
    return True

def test_show_order_system():
    """Test der Show-Order Funktionalität"""
    print("🧪 Test Show-Order System")
    
    # Test-Daten
    columns = [
        {'name': 'person_id', 'show': True, 'expert': False, 'order': 1},
        {'name': 'nachname', 'show': True, 'expert': False, 'order': 2},
        {'name': 'vorname', 'show': True, 'expert': False, 'order': 3},
        {'name': 'geburtsdatum', 'show': False, 'expert': False, 'order': 4},
        {'name': 'email', 'show': True, 'expert': False, 'order': 5},
        {'name': 'debug_info', 'show': False, 'expert': True, 'order': 10},
        {'name': 'internal_id', 'show': False, 'expert': True, 'order': 8},
    ]
    
    # 1. Initialisierung
    columns = initialize_show_order_system(columns)
    
    print("\n📊 Normal-Mode Spalten:")
    for col in get_normal_mode_columns(columns):
        print(f"   {col['name']}: show_order={col.get('show_order', 'N/A')}, show={col.get('show', False)}")
    
    print("\n📊 Expert-Mode Spalten:")
    for col in get_expert_mode_columns(columns):
        expert_flag = "🔧" if col.get('expert', False) else "👤"
        print(f"   {expert_flag} {col['name']}: order={col.get('order', 'N/A')}")
    
    # 2. Test Verschiebung
    print("\n🔼 Test: email nach oben verschieben")
    move_normal_column_up(columns, 'email')
    
    print("📊 Nach Verschiebung:")
    for col in get_normal_mode_columns(columns):
        print(f"   {col['name']}: show_order={col.get('show_order', 'N/A')}")

if __name__ == "__main__":
    test_show_order_system()
