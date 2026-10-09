# -*- coding: utf-8 -*-
import os
import sys

FROZEN = getattr(sys, "frozen", False)
PROJE_KOKU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kaynak(rel):
    """Paket içindeki dosyalar (logo, ikon). Exe'de PyInstaller'ın açtığı klasörden okunur."""
    base = getattr(sys, "_MEIPASS", PROJE_KOKU)
    return os.path.join(base, rel)


def exe_klasoru():
    return os.path.dirname(sys.executable) if FROZEN else PROJE_KOKU


def veri_klasoru():
    """Ayarlar burada durur; güncellemelerde silinmez."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "CagriDoldur")
    os.makedirs(d, exist_ok=True)
    return d
