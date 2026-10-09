# -*- coding: utf-8 -*-
"""Uygulama sürümü. Yeni sürüm için sadece burayı artırıp main'e gönder; GitHub exe'yi derleyip yayınlar."""

VERSION = "1.3.0"
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
