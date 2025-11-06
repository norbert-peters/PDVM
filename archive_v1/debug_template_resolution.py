#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debuggt Template-Auflösung im Admin-Testmenü

AUTOR: Norbert Peters
DATUM: 02.11.2025
"""

import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

# Lade Admin-Testmenü
cursor.execute('SELECT daten FROM sys_menudaten WHERE uid=?', ('113c6a2c-af9a-4022-929b-6544799e8954',))
data = json.loads(cursor.fetchone()[0])

grund = data.get('GRUND', [])

print("=" * 80)
print("🔍 DEBUG: Template-Auflösung Admin-Testmenü")
print("=" * 80)

# Template-Items
template_items = [i for i in grund if i.get('TYPE') == 'SPACER' and i.get('TEMPLATE_GUID')]
print(f"\n📋 Template-Items: {len(template_items)}")
for item in template_items:
    print(f"  - Label: '{item.get('LABEL')}'")
    print(f"    TEMPLATE_GUID: {item.get('TEMPLATE_GUID')}")
    print(f"    SORT_ORDER: {item.get('SORT_ORDER')}")
    print(f"    PARENT_GUID: {item.get('PARENT_GUID')}")

# Top-Level Items (ohne PARENT_GUID)
top_level = [i for i in grund if not i.get('PARENT_GUID')]
print(f"\n📂 Top-Level Items (ohne PARENT_GUID): {len(top_level)}")

# Sortiert nach SORT_ORDER
sorted_items = sorted(top_level, key=lambda x: x.get('SORT_ORDER', 0))
for idx, item in enumerate(sorted_items):
    label = item.get('LABEL', '')
    item_type = item.get('TYPE', '')
    sort_order = item.get('SORT_ORDER', 0)
    
    if item_type == 'SPACER' and item.get('TEMPLATE_GUID'):
        print(f"  {idx+1}. 🔗 TEMPLATE: @{item.get('TEMPLATE_GUID')[:8]}... (SORT: {sort_order})")
    else:
        print(f"  {idx+1}. {label} ({item_type}) - SORT: {sort_order}")

# Lade Template-Menü
print(f"\n{'='*80}")
print("📋 TEMPLATE-MENÜ (Basis-Menü)")
print("=" * 80)

cursor.execute('SELECT daten FROM sys_menudaten WHERE uid=?', ('1a653694-3132-48d9-bc3e-a512962ae8e6',))
template_data = json.loads(cursor.fetchone()[0])

template_grund = template_data.get('GRUND', [])
template_top_level = [i for i in template_grund if not i.get('PARENT_GUID')]

print(f"\nTemplate Top-Level Items: {len(template_top_level)}")
template_sorted = sorted(template_top_level, key=lambda x: x.get('SORT_ORDER', 0))
for idx, item in enumerate(template_sorted):
    label = item.get('LABEL', '')
    item_type = item.get('TYPE', '')
    sort_order = item.get('SORT_ORDER', 0)
    print(f"  {idx+1}. {label} ({item_type}) - SORT: {sort_order}")

# ERWARTETES ERGEBNIS
print(f"\n{'='*80}")
print("✅ ERWARTETES ERGEBNIS nach Template-Auflösung")
print("=" * 80)

expected_result = []

for item in sorted_items:
    if item.get('TYPE') == 'SPACER' and item.get('TEMPLATE_GUID'):
        # Template-Items einfügen
        print(f"\n🔗 Template wird hier eingefügt (SORT: {item.get('SORT_ORDER')}):")
        for t_idx, t_item in enumerate(template_sorted):
            print(f"  {len(expected_result)+1}. {t_item.get('LABEL')} (aus Template)")
            expected_result.append(('TEMPLATE', t_item.get('LABEL')))
    else:
        # Normales Item
        print(f"{len(expected_result)+1}. {item.get('LABEL')} (Original)")
        expected_result.append(('ORIGINAL', item.get('LABEL')))

print(f"\n📊 Erwartete Gesamt-Items: {len(expected_result)}")

conn.close()
