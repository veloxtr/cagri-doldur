# -*- coding: utf-8 -*-
import json
import os

from . import guvenlik, paths

AYAR_DOSYASI = os.path.join(paths.veri_klasoru(), "ayarlar.json")

SAGLAYICILAR = ("gemini", "anthropic", "kopyala")

VARSAYILAN = {
    "saglayici": "gemini",              # gemini | anthropic | kopyala
    "gemini_key": "",
    "gemini_hiz": "dengeli",            # hizli | dengeli
    "gemini_model": "",                 # boşsa hız seçimine göre otomatik
    "api_key": "",
    "model": "claude-haiku-5-5",
    "tema": "koyu",
    "her_zaman_ustte": True,
    "pencere_basligi": "Çağrıyı Tamamla",
    "varsayilan_ucret": "Ücret talep edilmedi. Müşterinin sözleşmesi bulunduğu için işlem sözleşme kapsamında ücretsiz yapıldı.",
    "varsayilan_kayit": "Hayır",
    "guncelleme_repo": "",              # GitHub "kullanici/repo"
    "yetkili_sifre": None,              # PBKDF2 özeti; şifrenin kendisi saklanmaz
}

GIZLI_ALANLAR = ("gemini_key", "api_key")


def _eski_yerler():
    yerler = [os.path.join(paths.exe_klasoru(), "ayarlar.json"),
              os.path.join(paths.PROJE_KOKU, "ayarlar.json"),
              os.path.join(os.getcwd(), "ayarlar.json")]
    ev = os.path.expanduser("~")
    for masaustu in ("Desktop", "Masaüstü", os.path.join("OneDrive", "Desktop"), os.path.join("OneDrive", "Masaüstü")):
        yerler.append(os.path.join(ev, masaustu, "cagri_doldur", "ayarlar.json"))
    gorulen = []
    for y in yerler:
        if y not in gorulen:
            gorulen.append(y)
    return gorulen


def yukle():
    cfg = dict(VARSAYILAN)
    kaynak = None
    if os.path.exists(AYAR_DOSYASI):
        kaynak = AYAR_DOSYASI
    else:
        for y in _eski_yerler():
            if os.path.exists(y):
                kaynak = y
                break
    if kaynak:
        try:
            with open(kaynak, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    cfg.pop("otomatik_aktar", None)
    acik_kalmis = any(cfg.get(k) and not str(cfg.get(k)).startswith("dpapi:") for k in GIZLI_ALANLAR)
    for k in GIZLI_ALANLAR:
        cfg[k] = guvenlik.ac(cfg.get(k, ""))
    if cfg.get("saglayici") not in SAGLAYICILAR:
        cfg["saglayici"] = "gemini"
    if not str(cfg.get("api_key", "")).startswith("sk-"):
        cfg["api_key"] = ""
    if kaynak and (kaynak != AYAR_DOSYASI or acik_kalmis):
        try:
            kaydet(cfg)  # eski yerden taşı / anahtarları şifreli hâle getir
        except Exception:
            pass
    return cfg


def kaydet(cfg):
    disk = dict(cfg)
    for k in GIZLI_ALANLAR:
        disk[k] = guvenlik.gizle(cfg.get(k, ""))
    tmp = AYAR_DOSYASI + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(disk, f, ensure_ascii=False, indent=2)
    os.replace(tmp, AYAR_DOSYASI)
