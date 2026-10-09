# -*- coding: utf-8 -*-
"""Doldurulan çağrıların geçmişi (sadece bu bilgisayarda, %APPDATA%\\CagriDoldur\\gecmis.json)."""
import json
import os
import threading
import time

from . import paths

DOSYA = os.path.join(paths.veri_klasoru(), "gecmis.json")
EN_FAZLA = 200
_kilit = threading.Lock()


def yukle():
    try:
        with open(DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
        return veri if isinstance(veri, list) else []
    except Exception:
        return []


def ekle(cagri_no, notu, alanlar, secimler=None):
    kayit = {
        "zaman": time.strftime("%Y-%m-%d %H:%M"),
        "cagri_no": cagri_no or "",
        "not": notu or "",
        "secimler": secimler or {},
        "alanlar": alanlar,
    }
    with _kilit:
        liste = yukle()
        liste.insert(0, kayit)
        del liste[EN_FAZLA:]
        tmp = DOSYA + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(liste, f, ensure_ascii=False, indent=1)
        os.replace(tmp, DOSYA)
    return kayit


def ara(liste, sorgu):
    sorgu = (sorgu or "").strip().lower()
    if not sorgu:
        return liste
    sonuc = []
    for k in liste:
        metin = " ".join([k.get("cagri_no", ""), k.get("not", ""), k.get("zaman", "")]
                         + list((k.get("alanlar") or {}).values())).lower()
        if sorgu in metin:
            sonuc.append(k)
    return sonuc


def bugun_sayisi(liste=None):
    bugun = time.strftime("%Y-%m-%d")
    return sum(1 for k in (liste if liste is not None else yukle()) if k.get("zaman", "").startswith(bugun))
