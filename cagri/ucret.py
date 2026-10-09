# -*- coding: utf-8 -*-
"""Ücret seçenekleri ve formdaki "Ücret bilgisi veya ücretsiz işlem gerekçesi" alanının sabit metni.

Bu alan yapay zekâya bırakılmaz: seçime göre her zaman aynı, net cümle yazılır.
Yeni seçenek eklemek için SECENEKLER'e bir satır ve metin()'e bir dal eklemek yeterli.
"""
import re

# Sıra = ekrandaki sıra
SECENEKLER = ["Sözleşmeli", "Yıllık yenilemeli", "Sözleşmesiz destek", "Bayi destek", "Bilgilendirme", "Ücretli"]
VARSAYILAN = "Sözleşmeli"

UCRETLI_TURLER = ["Tek seferlik", "Yıllık"]
SOZLESMESIZ_KONULAR = ["E-belge gönderimi", "Portal / şifre", "Diğer"]

_KONU_METNI = {
    "E-belge gönderimi": "e-belge (e-Fatura / e-İrsaliye) gönderimi",
    "Portal / şifre": "portal ve şifre işlemleri",
}


class UcretHatasi(Exception):
    pass


def tutar_duzenle(metin):
    """'3000+kdv' -> '3.000 + KDV', '5000 kdv dahil' -> '5.000 TL (KDV dahil)', '1.250,50' korunur."""
    ham = (metin or "").strip()
    if not ham:
        return ""
    m = re.match(r"^\s*([\d.,\s]+)\s*(tl|₺)?\s*(\+\s*kdv|kdv\s*dahil|kdv\s*hariç|\+kdv)?\s*(tl|₺)?\s*$", ham, re.I)
    if not m:
        return ham
    sayi = re.sub(r"\s", "", m.group(1))
    kdv = (m.group(3) or "").lower().replace(" ", "")
    if re.fullmatch(r"\d+", sayi):
        sayi = f"{int(sayi):,}".replace(",", ".")
    if kdv in ("+kdv", "kdvhariç"):
        return f"{sayi} TL + KDV"
    if kdv == "kdvdahil":
        return f"{sayi} TL (KDV dahil)"
    return f"{sayi} TL"


def metin(secim, ucretli_tur="Tek seferlik", tutar="", konu="Diğer", sozlesmeli_metni=None):
    """Forma yazılacak ücret cümlesi."""
    if secim == "Sözleşmeli":
        return sozlesmeli_metni or ("Ücret talep edilmedi. Müşterinin sözleşmesi bulunduğu için işlem "
                                    "sözleşme kapsamında ücretsiz yapıldı.")
    if secim == "Yıllık yenilemeli":
        return "Ücret talep edilmedi. Destek, müşterinin yıllık yenilemeli paketi kapsamında verildi."
    if secim == "Sözleşmesiz destek":
        konu_metni = _KONU_METNI.get(konu)
        if konu_metni:
            return (f"Ücret talep edilmedi. {konu_metni[0].upper() + konu_metni[1:]} konusunda sözleşme "
                    "aranmadan destek verildiği için işlem ücretsiz yapıldı.")
        return "Ücret talep edilmedi. Sözleşme aranmadan verilen destek kapsamında işlem ücretsiz yapıldı."
    if secim == "Bayi destek":
        return "Ücret talep edilmedi. Bayi desteği kapsamında sözleşme aranmadan işlem yapıldı."
    if secim == "Bilgilendirme":
        return "Ücret talep edilmedi. Bilgilendirme amaçlı görüşme olduğu için işlem ücretsiz yapıldı."
    if secim == "Ücretli":
        t = tutar_duzenle(tutar)
        if not t:
            raise UcretHatasi("Ücretli seçili: tutarı yaz (ör. 3000+kdv).")
        if ucretli_tur == "Yıllık":
            return f"İşlem yıllık ücretlendirme kapsamında yapıldı. Yıllık ücret: {t}."
        return f"İşlem tek seferlik ücretli olarak yapıldı. Ücret: {t}."
    return sozlesmeli_metni or ""


def ozet(secim, ucretli_tur="", tutar="", konu=""):
    """Geçmişte gösterilecek kısa açıklama."""
    if secim == "Ücretli":
        return f"Ücretli · {ucretli_tur} · {tutar_duzenle(tutar)}"
    if secim == "Sözleşmesiz destek":
        return f"Sözleşmesiz destek · {konu}"
    return secim
