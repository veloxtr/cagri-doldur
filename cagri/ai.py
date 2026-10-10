# -*- coding: utf-8 -*-
"""Notu AI'ya yorumlatıp 8 alana çevirir."""
import json
import re
import threading
import time

from . import dagitim, gizlilik, net
from .prompt import FIELDS, system_prompt

GEMINI_MODELLERI = {
    "hizli": "gemini-flash-lite-latest",
    "dengeli": "gemini-flash-latest",
}

# Düşünme süresini en aza indirmek için denenecek ayarlar (model hangisini kabul ederse).
_DUSUNME_SECENEKLERI = [{"thinkingLevel": "minimal"}, {"thinkingBudget": 0}, None]
_dusunme_secimi = {}
_kilit = threading.Lock()

_SEMA = {
    "type": "OBJECT",
    "properties": {k: {"type": "STRING"} for k, _ in FIELDS},
    "required": [k for k, _ in FIELDS],
    "propertyOrdering": [k for k, _ in FIELDS],
}


class AIHatasi(Exception):
    pass


# ---------------------------------------------------------------- ayrıştırma
def _json_cikar(text):
    text = re.sub(r"```(?:json)?", "", text or "")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return {key: str(data.get(key, "")).strip() for key, _ in FIELDS}


# ---------------------------------------------------------------- servisler
def _hata_metni(metin):
    try:
        return json.loads(metin).get("error", {}).get("message", metin)
    except Exception:
        return metin


def gemini_modeli(cfg):
    return cfg.get("gemini_model") or GEMINI_MODELLERI.get(cfg.get("gemini_hiz"), GEMINI_MODELLERI["dengeli"])


def _gemini(cfg, notu):
    url = dagitim.proxy_url()
    jeton = dagitim.proxy_token()
    if not (url and jeton):
        raise AIHatasi("Yapay zekâ bağlantısı bu sürümde ayarlı değil. Lütfen uygulamayı güncelleyin.")
    model = gemini_modeli(cfg)
    govde = {
        "system_instruction": {"parts": [{"text": system_prompt(cfg)}]},
        "contents": [{"role": "user", "parts": [{"text": "Not:\n" + notu}]}],
    }
    with _kilit:
        bas = _dusunme_secimi.get(model, 0)
    for i in range(bas, len(_DUSUNME_SECENEKLERI)):
        gen = {"responseMimeType": "application/json", "responseSchema": _SEMA, "maxOutputTokens": 2048}
        if _DUSUNME_SECENEKLERI[i]:
            gen["thinkingConfig"] = _DUSUNME_SECENEKLERI[i]
        govde["generationConfig"] = gen
        durum, metin = net.istek("POST", url, headers={"X-App-Token": jeton},
                                 govde={"model": model, "body": govde}, timeout=60)
        if durum == 400 and "think" in metin.lower() and i < len(_DUSUNME_SECENEKLERI) - 1:
            continue  # bu model bu düşünme ayarını kabul etmiyor, sıradakini dene
        if durum == 401:
            raise AIHatasi("Yapay zekâ sunucusu bu uygulamayı tanımadı. Lütfen uygulamayı güncelleyin.")
        if durum != 200:
            raise AIHatasi(f"Yapay zekâ hatası ({durum}): {_hata_metni(metin)[:300]}")
        with _kilit:
            _dusunme_secimi[model] = i
        parts = (json.loads(metin).get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))
    raise AIHatasi("Yapay zekâ yanıt vermedi.")


def yorumla(cfg, notu, ek_bilgi=None):
    """(alanlar, süre_sn) döndürür. ek_bilgi: hızlı seçimlerden gelen satırlar.
    Gizlilik filtresi açıksa VKN/telefon/e-posta/IBAN AI'ya gitmeden maskelenir, cevapta geri konur."""
    t0 = time.perf_counter()
    esleme = {}
    if cfg.get("gizlilik", True):
        notu, esleme = gizlilik.maskele(notu)
    if ek_bilgi:
        notu = notu.rstrip() + "\n\nEk bilgi:\n" + "\n".join(f"- {s}" for s in ek_bilgi)
    try:
        text = _gemini(cfg, notu)
    except TimeoutError:
        raise AIHatasi("AI çok geç cevap verdi, tekrar dene.")
    except OSError as e:
        raise AIHatasi(f"İnternet bağlantısı kurulamadı ({e}).")
    vals = _json_cikar(text)
    if not vals or not vals.get("cozum"):
        raise AIHatasi("AI yanıtı anlaşılamadı:\n" + (text or "")[:300])
    return gizlilik.geri_koy(vals, esleme), time.perf_counter() - t0


def isit(cfg):
    """Uygulama açılırken bağlantıyı önceden kurar; ilk istek daha hızlı gider."""
    url = dagitim.proxy_url()
    if url:
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname
            if host:
                net.isit(host)
        except Exception:
            pass


def baglanti_testi(cfg):
    """Anahtarı gerçek küçük bir istekle dener. (ok, mesaj) döndürür."""
    try:
        vals, sure = yorumla(cfg, "baglanti testi")
        return True, f"Bağlantı başarılı. Yanıt {sure:.1f} sn'de geldi."
    except AIHatasi as e:
        return False, str(e)
    except Exception as e:
        return False, f"Beklenmeyen hata: {e}"
