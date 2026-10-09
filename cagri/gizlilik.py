# -*- coding: utf-8 -*-
"""Gizlilik filtresi: nottaki kişisel/ticari numaraları AI'ya göndermeden önce maskeler,
AI'nın cevabında yer tutucuları gerçek değerlerle geri değiştirir. Gerçek değerler bilgisayardan çıkmaz.

Örnek:  "vkn 1234567890 tel 0532 111 22 33"  ->  "vkn [VKN-1] tel [TEL-1]"
"""
import re

# Sıra önemli: önce daha belirgin desenler.
_DESENLER = [
    ("EPOSTA", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("IBAN", re.compile(r"\bTR\s?\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.I)),
    # Telefon: +90 / 0 ile başlayan, boşluk/tire/parantezli yazımlar dahil
    ("TEL", re.compile(r"(?<![\w(])\(?(?:\+90[\s-]?|0)\(?[2-5]\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?![\d])")),
    # Başında 0 olmadan yazılmış cep telefonu: 5xx xxx xx xx (ayraçlı)
    ("TEL", re.compile(r"(?<![\w])5\d{2}[\s-]\d{3}[\s-]?\d{2}[\s-]?\d{2}(?![\d])")),
    ("TCKN", re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")),
    ("VKN", re.compile(r"(?<!\d)\d{10}(?!\d)")),
]


def maskele(metin):
    """(maskelenmiş_metin, eşleme) döndürür. eşleme: {"[VKN-1]": "1234567890", ...}"""
    esleme = {}
    ters = {}
    sayac = {}

    def degistir(tur):
        def f(m):
            deger = m.group(0)
            if deger in ters:
                return ters[deger]
            sayac[tur] = sayac.get(tur, 0) + 1
            yer = f"[{tur}-{sayac[tur]}]"
            esleme[yer] = deger
            ters[deger] = yer
            return yer
        return f

    for tur, desen in _DESENLER:
        metin = desen.sub(degistir(tur), metin)
    return metin, esleme


def geri_koy(alanlar, esleme):
    """AI cevabındaki yer tutucuları gerçek değerlerle değiştirir."""
    if not esleme:
        return alanlar
    sonuc = {}
    for k, v in alanlar.items():
        for yer, deger in esleme.items():
            v = v.replace(yer, deger)
        sonuc[k] = v
    return sonuc
