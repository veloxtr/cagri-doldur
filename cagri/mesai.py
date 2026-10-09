# -*- coding: utf-8 -*-
"""Mesai hak edişi hesabı. Hiçbir veri dışarı gitmez, her şey bu bilgisayarda hesaplanır.

Saatlik ücret = aylık maaş / 225.
Çarpanlar: hafta içi x1, hafta sonu x1.5, özel gün (resmi tatil) x2.
"""

BOLEN = 225
CARPANLAR = [
    ("hafta_ici", "Hafta içi", 1.0),
    ("hafta_sonu", "Hafta sonu", 1.5),
    ("ozel_gun", "Özel gün (resmi tatil)", 2.0),
]

UYARI = ("Sadece yaptığınız mesai saatlerini ilgili alanlara yazınız. "
         "Çarpana göre otomatik hesaplamayı sistem yapar.")


def _sayi(deger):
    """'1.234,5' / '1234.5' / '2' -> float; boş/geçersiz -> 0."""
    s = str(deger or "").strip().replace(" ", "")
    if not s:
        return 0.0
    if "," in s:
        # Virgül varsa o ondalık ayraç; nokta(lar) binlik ayracıdır.
        s = s.replace(".", "").replace(",", ".")       # 1.234,5 -> 1234.5
    elif "." in s:
        parcalar = s.split(".")
        if len(parcalar[-1]) == 3:
            s = "".join(parcalar)                      # 33.750 / 1.234.567 -> binlik ayracı
        # aksi halde nokta ondalık: 1234.5 / 133.33 olduğu gibi kalır
    try:
        return float(s)
    except ValueError:
        return 0.0


def tl(deger):
    """1275.0 -> '1.275,00 TL'"""
    tam = f"{deger:,.2f}"                            # 1,275.00
    tam = tam.replace(",", "#").replace(".", ",").replace("#", ".")
    return tam + " TL"


def hesapla(maas, saatler):
    """maas: aylık maaş; saatler: {'hafta_ici':..., 'hafta_sonu':..., 'ozel_gun':...}
    Döndürür: {'saatlik', 'satirlar':[(ad, saat, carpan, tutar)], 'toplam_saat', 'toplam'}"""
    m = _sayi(maas)
    saatlik = m / BOLEN if m else 0.0
    satirlar = []
    toplam = 0.0
    toplam_saat = 0.0
    for anahtar, ad, carpan in CARPANLAR:
        saat = _sayi(saatler.get(anahtar))
        tutar = saat * saatlik * carpan
        satirlar.append((ad, saat, carpan, tutar))
        toplam += tutar
        toplam_saat += saat
    return {"saatlik": saatlik, "satirlar": satirlar, "toplam_saat": toplam_saat, "toplam": toplam}
