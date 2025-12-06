# -*- coding: utf-8 -*-
"""
Security System - Konstanten

Standard Security-Profile GUIDs für Referenzierung

AUTOR: Norbert Peters
DATUM: 06.12.2025
"""

# Standard Security-Profile GUIDs (FEST - nicht ändern!)
SECURITY_NORMAL_GUID = "11111111-1111-1111-1111-111111111111"
SECURITY_TEMPLATE_GUID = "22222222-2222-2222-2222-222222222222"
SECURITY_SYSTEM_GUID = "33333333-3333-3333-3333-333333333333"
SECURITY_DELETED_GUID = "44444444-4444-4444-4444-444444444444"

# Security-Kategorien
SECURITY_CATEGORY_NORMAL = "normal"
SECURITY_CATEGORY_TEMPLATE = "template"
SECURITY_CATEGORY_SYSTEM = "system"
SECURITY_CATEGORY_DELETED = "deleted"

# Security-Modes (für Views)
SECURITY_MODE_STANDARD = "standard"  # Normal-Sätze
SECURITY_MODE_EXPERT = "expert"      # + Templates
SECURITY_MODE_ADMIN = "admin"        # + System + Deleted
