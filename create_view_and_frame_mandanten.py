"""
Erstellt View + Frame für sys_mandanten mit system_editor
"""
import sqlite3
import json
import uuid

def create_view_and_frame():
    """Erstellt View + Frame für sys_mandanten"""
    
    conn_system = sqlite3.connect('Daten/pdvm_system.db')
    cursor_system = conn_system.cursor()
    
    # 1. VIEW erstellen
    view_guid = str(uuid.uuid4())
    
    view_data = {
        "ROOT": {
            "TABLE": "sys_mandanten",
            "NAME": "Mandanten Übersicht",
            "VISIBLE_COLUMNS": ["uid", "name"],
            "COLUMN_WIDTHS": {"uid": 300, "name": 400}
        }
    }
    
    cursor_system.execute("""
        INSERT INTO sys_viewdaten 
        (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
        VALUES (?, ?, ?, ?, ?, 0, '', NULL, 9999365.99999)
    """, (view_guid, "Mandanten View", json.dumps(view_data, ensure_ascii=False), 2025351.0, 2025351.0))
    
    print(f"✅ View erstellt: {view_guid}")
    
    # 2. FRAME erstellen
    frame_guid = str(uuid.uuid4())
    dialog_guid = str(uuid.uuid4())
    
    frame_data = {
        "ROOT": {
            "TABLE": "sys_mandanten",
            "NAME": "Mandanten Editor",
            "DESCRIPTION": "Bearbeitung der Mandanten-Datensätze",
            "VIEW_GUID": view_guid,
            "DIALOG_GUID": dialog_guid,
            "HEADER_TEXT": "📋 Mandanten Dictionary Editor",
            "EDIT_TYPE": "system_editor"
        }
    }
    
    cursor_system.execute("""
        INSERT INTO sys_framedaten 
        (uid, name, daten, created_at, modified_at, historisch, source_hash, sec_id, gilt_bis)
        VALUES (?, ?, ?, ?, ?, 0, '', NULL, 9999365.99999)
    """, (frame_guid, "Mandanten Editor Frame", json.dumps(frame_data, ensure_ascii=False), 2025351.0, 2025351.0))
    
    conn_system.commit()
    conn_system.close()
    
    print(f"✅ Frame erstellt: {frame_guid}")
    print(f"\n🧪 TEST:")
    print(f"   start_dialog('{frame_guid}')")
    
    return frame_guid, view_guid

if __name__ == "__main__":
    frame_guid, view_guid = create_view_and_frame()
    print(f"\n📋 Frame-GUID: {frame_guid}")
    print(f"📋 View-GUID: {view_guid}")
