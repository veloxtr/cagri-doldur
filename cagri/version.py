# -*- coding: utf-8 -*-
"""Uygulama sürümü. Yeni sürüm çıkarırken sadece burayı değiştir, sonra aynı numarayla etiket at (ör. v1.0.1)."""

VERSION = "1.1.0"
APP_NAME = "Çağrı Doldur"
APP_ID = "CagriDoldur"
YAPIMCI = "EYK"
TELIF = "© 2026 EYK · All rights reserved"


def kisa_surum(v=VERSION):
    """1.0.0 -> v1.0, 1.2.3 -> v1.2.3"""
    parcalar = v.split(".")
    while len(parcalar) > 2 and parcalar[-1] == "0":
        parcalar.pop()
    return "v" + ".".join(parcalar)
