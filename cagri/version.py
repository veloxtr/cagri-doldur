# -*- coding: utf-8 -*-
"""Uygulama sürümü. Yeni sürüm için sadece burayı artırıp main'e gönder; GitHub exe'yi derleyip yayınlar."""

VERSION = "1.5.0"
APP_NAME = "Bilnex Assist"
ARAC_ADI = "Çağrı Doldur"  # Bilnex Assist içindeki ilk araç
APP_ID = "CagriDoldur"
YAPIMCI = "EYK"
TELIF = "© 2026 EYK · All rights reserved"


def kisa_surum(v=VERSION):
    """Ekranda gösterilen sürüm: her zaman tam numara (ör. v1.3.2)."""
    return "v" + v
