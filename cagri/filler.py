# -*- coding: utf-8 -*-
"""Açık olan 'Çağrıyı Tamamla' penceresini bulup alanlarına yazar.
Windows UI Automation'a comtypes ile doğrudan bağlanır (pywinauto/pywin32 gerekmez)."""
import ctypes
import os
import re
from ctypes import wintypes

from . import paths
from .prompt import FIELDS

TESHIS_DOSYASI = os.path.join(paths.veri_klasoru(), "teshis.txt")

# UI Automation sabitleri
_CONTROL_TYPE_PROP = 30003
_EDIT = 50004
_DOCUMENT = 50030
_WINDOW = 50032
_TEXT = 50020
_VALUE_PATTERN = 10002
_SCOPE_CHILDREN = 2
_SCOPE_DESCENDANTS = 4

_uia = None
_UIA = None
URETILDI = False  # arayüz tanımları exe'de hazır gelmeyip çalışırken üretildiyse True (yavaş)


class DoldurmaHatasi(Exception):
    pass


def _otomasyon():
    """IUIAutomation nesnesi (ilk çağrıda oluşturulur)."""
    global _uia, _UIA, URETILDI
    if _uia is None:
        import comtypes.client
        try:
            from comtypes.gen import UIAutomationClient as UIA
        except ImportError:
            URETILDI = True
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen import UIAutomationClient as UIA
        _UIA = UIA
        _uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
    return _uia


def hazirla():
    """Açılışta çağrılır: ilk doldurma beklemesin diye otomasyonu önceden kurar. Ana thread'den."""
    try:
        _otomasyon()
    except Exception:
        pass


# ---------------------------------------------------------------- pencere bulma
def _norm(t):
    t = (t or "").replace("I", "ı").replace("İ", "i").lower()
    for a, b in (("ç", "c"), ("ğ", "g"), ("ı", "i"), ("ö", "o"), ("ş", "s"), ("ü", "u")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", t)


def _eslesir(ad, hedef):
    n = _norm(ad)
    return bool(n) and (hedef in n or ("tamamla" in n and "cagri" in n))


def _hwnd_bul(hedef):
    user32 = ctypes.windll.user32
    bulunan = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _lp):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if _eslesir(buf.value, hedef):
                    bulunan.append(hwnd)
                    return False
        return True

    user32.EnumWindows(cb, 0)
    return bulunan[0] if bulunan else None


def _one_getir(hwnd):
    user32 = ctypes.windll.user32
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _hepsi(dizi):
    return [dizi.GetElement(i) for i in range(dizi.Length)]


def _yavas_bul(uia, hedef):
    """Yedek yol: alt pencereler dahil arar; bulamazsa teşhis dosyası yazar."""
    kosul = uia.CreatePropertyCondition(_CONTROL_TYPE_PROP, _WINDOW)
    gorulen = []
    try:
        ustler = _hepsi(uia.GetRootElement().FindAll(_SCOPE_CHILDREN, kosul))
    except Exception as e:
        ustler = []
        gorulen.append(f"kök hata: {e}")
    for w in ustler:
        ad = w.CurrentName
        gorulen.append(f"[ust] {ad!r}")
        if _eslesir(ad, hedef):
            return w
    for w in ustler:
        try:
            for c in _hepsi(w.FindAll(_SCOPE_DESCENDANTS, kosul)):
                gorulen.append(f"[alt] {c.CurrentName!r}  (ust: {w.CurrentName!r})")
                if _eslesir(c.CurrentName, hedef):
                    return c
        except Exception:
            continue
    try:
        with open(TESHIS_DOSYASI, "w", encoding="utf-8") as f:
            f.write("Aranan: " + hedef + "\n\n" + "\n".join(gorulen))
    except Exception:
        pass
    return None


def pencereyi_bul(baslik):
    uia = _otomasyon()
    hedef = _norm(baslik)
    hwnd = _hwnd_bul(hedef)
    if hwnd:
        _one_getir(hwnd)
        return uia.ElementFromHandle(hwnd)
    return _yavas_bul(uia, hedef)


# ---------------------------------------------------------------- doldurma
def _kutulari_bul(uia, win):
    edits = _hepsi(win.FindAll(_SCOPE_DESCENDANTS, uia.CreatePropertyCondition(_CONTROL_TYPE_PROP, _EDIT)))
    if not edits:
        edits = _hepsi(win.FindAll(_SCOPE_DESCENDANTS, uia.CreatePropertyCondition(_CONTROL_TYPE_PROP, _DOCUMENT)))
    if len(edits) > len(FIELDS):
        gorunur = [e for e in edits if not e.CurrentIsOffscreen]
        if len(gorunur) >= len(FIELDS):
            edits = gorunur

    def sira(e):
        r = e.CurrentBoundingRectangle
        return (r.top, r.left)

    edits.sort(key=sira)
    return edits


_CAGRI_NO = re.compile(r"\b[A-ZÇĞİÖŞÜ]{2,6}-\d{4}-\d{3,}\b")


def _cagri_no_oku(uia, win):
    """Pencerede görünen 'Çağrı No' değerini (ör. DSK-2026-0195787) bulur; yoksa boş döner."""
    try:
        m = _CAGRI_NO.search(win.CurrentName or "")
        if m:
            return m.group(0)
        for e in _hepsi(win.FindAll(_SCOPE_DESCENDANTS, uia.CreatePropertyCondition(_CONTROL_TYPE_PROP, _TEXT))):
            m = _CAGRI_NO.search(e.CurrentName or "")
            if m:
                return m.group(0)
    except Exception:
        pass
    return ""


def _yaz(edit, metin):
    desen = edit.GetCurrentPattern(_VALUE_PATTERN)
    if not desen:
        raise DoldurmaHatasi("Bir kutuya yazılamadı (ValuePattern yok).")
    desen.QueryInterface(_UIA.IUIAutomationValuePattern).SetValue(metin)


def _teshis_yaz(win, edits):
    try:
        with open(TESHIS_DOSYASI, "w", encoding="utf-8") as f:
            f.write(f"Pencere bulundu: {win.CurrentName!r}\nKutu sayısı: {len(edits)}\n\n")
            hepsi = _hepsi(win.FindAll(_SCOPE_DESCENDANTS, _otomasyon().CreateTrueCondition()))
            for c in hepsi[:300]:
                try:
                    r = c.CurrentBoundingRectangle
                    f.write(f"{c.CurrentLocalizedControlType}  {c.CurrentName!r}  "
                            f"({r.left},{r.top},{r.right},{r.bottom})\n")
                except Exception:
                    pass
    except Exception:
        pass


def doldur(baslik, values):
    """Alanları yazar; ekranda okunabildiyse Çağrı No'yu döndürür."""
    try:
        uia = _otomasyon()
    except Exception as e:
        raise DoldurmaHatasi(f"Windows ekran otomasyonu başlatılamadı: {e}")
    win = pencereyi_bul(baslik)
    if win is None:
        raise DoldurmaHatasi(
            "'Çağrıyı Tamamla' penceresi bulunamadı.\n"
            "Ekranın açık olduğundan emin ol. Açıksa Bilnex Assist'i sağ tık > "
            "'Yönetici olarak çalıştır' ile aç.")
    edits = _kutulari_bul(uia, win)
    if len(edits) < len(FIELDS):
        _teshis_yaz(win, edits)
        raise DoldurmaHatasi(
            f"Çağrı ekranı bulundu ama {len(FIELDS)} kutu yerine {len(edits)} kutu görüldü.\n"
            f"Teşhis dosyası: {TESHIS_DOSYASI}")
    for edit, (key, _) in zip(edits, FIELDS):
        try:
            edit.SetFocus()
        except Exception:
            pass
        _yaz(edit, values[key])
    try:
        edits[0].SetFocus()  # son kutunun da kaydedilmesi için odağı değiştir
    except Exception:
        pass
    return _cagri_no_oku(uia, win)
