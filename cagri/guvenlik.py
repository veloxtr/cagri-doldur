# -*- coding: utf-8 -*-
"""Yetkili şifresi ve API anahtarlarının diskte şifreli saklanması.

- Yetkili şifresi hiçbir zaman açık saklanmaz; sadece tuzlanmış PBKDF2 özeti tutulur.
- API anahtarları Windows DPAPI ile şifrelenir: dosya başka bir bilgisayara/kullanıcıya
  kopyalansa bile anahtar okunamaz.
"""
import base64
import hashlib
import hmac
import os

_TUR = 200_000


# ---------------------------------------------------------------- yetkili şifresi
def sifre_ozeti(sifre):
    tuz = os.urandom(16)
    ozet = hashlib.pbkdf2_hmac("sha256", sifre.encode("utf-8"), tuz, _TUR)
    return {"tuz": tuz.hex(), "ozet": ozet.hex(), "tur": _TUR}


def sifre_dogru(sifre, kayit):
    if not kayit:
        return False
    try:
        tuz = bytes.fromhex(kayit["tuz"])
        beklenen = bytes.fromhex(kayit["ozet"])
        ozet = hashlib.pbkdf2_hmac("sha256", sifre.encode("utf-8"), tuz, int(kayit.get("tur", _TUR)))
    except Exception:
        return False
    return hmac.compare_digest(ozet, beklenen)


# ---------------------------------------------------------------- DPAPI
def _dpapi(veri, coz):
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    tampon = ctypes.create_string_buffer(veri, len(veri))
    giris = BLOB(len(veri), ctypes.cast(tampon, ctypes.POINTER(ctypes.c_char)))
    cikis = BLOB()
    crypt32 = ctypes.windll.crypt32
    if coz:
        ok = crypt32.CryptUnprotectData(ctypes.byref(giris), None, None, None, None, 0x1, ctypes.byref(cikis))
    else:
        ok = crypt32.CryptProtectData(ctypes.byref(giris), "CagriDoldur", None, None, None, 0x1, ctypes.byref(cikis))
    if not ok:
        raise OSError("DPAPI başarısız")
    try:
        return ctypes.string_at(cikis.pbData, cikis.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(cikis.pbData, ctypes.c_void_p))


def gizle(metin):
    if not metin:
        return ""
    try:
        return "dpapi:" + base64.b64encode(_dpapi(metin.encode("utf-8"), False)).decode("ascii")
    except Exception:
        return metin  # Windows dışı ortam: açık sakla


def ac(metin):
    if not metin:
        return ""
    if not metin.startswith("dpapi:"):
        return metin  # eski sürümden kalan açık değer
    try:
        return _dpapi(base64.b64decode(metin[6:]), True).decode("utf-8")
    except Exception:
        return ""  # başka bilgisayardan kopyalanmış: okunamaz


# ---------------------------------------------------------------- parola ile şifreleme (taşınabilir)
# Dışa aktarılan ayar dosyası için: DPAPI yerine parola tabanlı, bağımsız (AES gerektirmez) şema.
# PBKDF2 ile anahtar türetilir, SHA-256 akış şifresiyle şifrelenir, HMAC-SHA256 ile bütünlük korunur.
def _anahtar(parola, tuz):
    return hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"), tuz, _TUR, dklen=64)


def _akis_xor(veri, k):
    out = bytearray(len(veri))
    i = 0
    sayac = 0
    while i < len(veri):
        blok = hashlib.sha256(k + sayac.to_bytes(8, "big")).digest()
        for b in blok:
            if i >= len(veri):
                break
            out[i] = veri[i] ^ b
            i += 1
        sayac += 1
    return bytes(out)


def parola_sifrele(metin, parola):
    tuz = os.urandom(16)
    k = _anahtar(parola, tuz)
    sifre, mac = k[:32], k[32:]
    ct = _akis_xor(metin.encode("utf-8"), sifre)
    etiket = hmac.new(mac, tuz + ct, hashlib.sha256).hexdigest()
    return {"v": 1, "tuz": tuz.hex(), "veri": base64.b64encode(ct).decode("ascii"), "mac": etiket}


def parola_coz(blob, parola):
    tuz = bytes.fromhex(blob["tuz"])
    ct = base64.b64decode(blob["veri"])
    k = _anahtar(parola, tuz)
    sifre, mac = k[:32], k[32:]
    beklenen = hmac.new(mac, tuz + ct, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(beklenen, blob.get("mac", "")):
        raise ValueError("Şifre yanlış ya da dosya bozuk.")
    return _akis_xor(ct, sifre).decode("utf-8")
