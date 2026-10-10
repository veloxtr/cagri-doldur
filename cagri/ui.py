# -*- coding: utf-8 -*-
"""Ana pencere ve ayarlar penceresi."""
import json
import os
import re
import threading
import time
import tkinter as tk

import customtkinter as ctk

from . import ai, config, filler, gecmis, guvenlik, paths, themes, ucret, updater
from .version import APP_NAME, TELIF, VERSION, kisa_surum

FONT = "Segoe UI"
IPUCU = ("Ne oldu, ne yaptın? Dağınık yazabilirsin.\n\n"
         "Örn: vkn 10 hane uyarısı veriyordu, gümrük carisi boştu, oluşturup seçtim, "
         "gönderim yapıldı müşteri onay verdi")


# Araç çantası: kategori -> [(anahtar, görünen ad)]. Yeni araç = yeni satır.
ARACLAR = [
    ("BSP Entegrasyon", [("cagri", "Çağrı Doldur")]),
    ("Personel", [("mesai", "Mesai Hak Edişi")]),
]
_ARAC_ADLARI = {k: ad for _, liste in ARACLAR for k, ad in liste}


def _f(size, bold=False):
    return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")


# ---------------------------------------------------------------- klavye kısayolları
_GERI = [re.compile(r"\w+\s*$"), re.compile(r"[^\w\s]+\s*$"), re.compile(r"\s+$")]
_ILERI = [re.compile(r"^\s*\w+"), re.compile(r"^\s*[^\w\s]+"), re.compile(r"^\s+")]


def _eslesen_uzunluk(desenler, metin):
    for d in desenler:
        m = d.search(metin)
        if m and m.group(0):
            return len(m.group(0))
    return 1 if metin else 0


def _text_kelime(e, geri):
    w = e.widget
    try:
        w.edit_separator()  # her kelime silme ayrı geri alınabilsin
    except tk.TclError:
        pass
    if w.tag_ranges("sel"):
        w.delete("sel.first", "sel.last")
        return "break"
    if geri:
        n = _eslesen_uzunluk(_GERI, w.get("insert linestart", "insert") or w.get("insert -1c", "insert"))
        w.delete(f"insert -{n}c", "insert")
    else:
        n = _eslesen_uzunluk(_ILERI, w.get("insert", "insert lineend") or w.get("insert", "insert +1c"))
        w.delete("insert", f"insert +{n}c")
    w.event_generate("<KeyRelease>")
    return "break"


def _entry_kelime(e, geri):
    w = e.widget
    if w.selection_present():
        w.delete("sel.first", "sel.last")
        return "break"
    metin, imlec = w.get(), w.index("insert")
    if geri:
        n = _eslesen_uzunluk(_GERI, metin[:imlec])
        w.delete(imlec - n, imlec)
    else:
        n = _eslesen_uzunluk(_ILERI, metin[imlec:])
        w.delete(imlec, imlec + n)
    return "break"


def _tumunu_sec_text(e):
    e.widget.tag_add("sel", "1.0", "end-1c")
    e.widget.mark_set("insert", "end-1c")
    return "break"


def _tumunu_sec_entry(e):
    e.widget.select_range(0, "end")
    e.widget.icursor("end")
    return "break"


def _kisayollari_kur(root):
    """Windows'taki alışılmış kısayollar: Ctrl+Backspace/Delete kelime siler, Ctrl+A tümünü seçer,
    Ctrl+Z / Ctrl+Y geri al / yinele. Tüm yazı ve giriş kutularında geçerlidir."""
    root.bind_class("Text", "<Control-BackSpace>", lambda e: _text_kelime(e, True))
    root.bind_class("Text", "<Control-Delete>", lambda e: _text_kelime(e, False))
    root.bind_class("Entry", "<Control-BackSpace>", lambda e: _entry_kelime(e, True))
    root.bind_class("Entry", "<Control-Delete>", lambda e: _entry_kelime(e, False))
    for tus in ("<Control-a>", "<Control-A>"):
        root.bind_class("Text", tus, _tumunu_sec_text)
        root.bind_class("Entry", tus, _tumunu_sec_entry)

    def yinele(e):
        try:
            e.widget.edit_redo()
        except tk.TclError:
            pass
        e.widget.event_generate("<KeyRelease>")
        return "break"

    def geri_al(e):
        try:
            e.widget.edit_undo()
        except tk.TclError:
            pass
        e.widget.event_generate("<KeyRelease>")
        return "break"

    for tus in ("<Control-z>", "<Control-Z>"):
        root.bind_class("Text", tus, geri_al)
    for tus in ("<Control-y>", "<Control-Y>"):
        root.bind_class("Text", tus, yinele)


def _ikon_ver(pencere):
    ico = paths.kaynak("assets/icon.ico")
    try:
        pencere.iconbitmap(ico)
        pencere.after(250, lambda: pencere.iconbitmap(ico))  # customtkinter kendi ikonunu basmasın
    except Exception:
        pass


class App:
    def __init__(self, guncellendi_eski=None, baslangic=None):
        self.baslangic = baslangic or time.perf_counter()
        self.guncellendi_eski = guncellendi_eski
        self.cfg = config.yukle()
        self.guncelleme = None
        self.mesgul = False
        self.not_metni = ""
        self.ayar_penceresi = None
        self.aktif_arac = "cagri"

        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} {kisa_surum()}")
        self.root.geometry("760x620")
        self.root.minsize(680, 560)
        _ikon_ver(self.root)
        _kisayollari_kur(self.root)
        self._logo = self._logo_yukle()

        self.kur()
        self._gosterildi = True
        self._guncelleme_soruluyor = False
        kilitli = (not os.environ.get("CAGRI_SELFTEST") and guncellendi_eski is None
                   and self.cfg.get("acilista_sifre") and self.cfg.get("yetkili_sifre"))
        if kilitli:
            self.root.withdraw()
            self._gosterildi = False
            self._acilis_kilidi()
        else:
            self._basla_normal()
        self.root.after(300, self._acilis_isleri)

    def _acilis_kilidi(self):
        """Açılışta yetkili şifresi sorar; doğru girilince normal başlatma yapılır, kapatılırsa çıkılır."""
        pencere = SifrePenceresi(self, self._basla_normal, self.root)
        try:
            pencere.w.protocol("WM_DELETE_WINDOW", self.root.destroy)
        except Exception:
            pass

    def _basla_normal(self):
        if (not os.environ.get("CAGRI_SELFTEST") and self.guncellendi_eski is None
                and self.cfg.get("guncelleme_repo")):
            # Önce güncelleme var mı bak: varsa sadece "güncellensin mi?" penceresi gelir.
            self.root.withdraw()
            self._gosterildi = False
            self.guncelleme_kontrol(sessiz=True)
            self.root.after(3500, self._ana_goster)  # sunucu geç cevap verirse beklemeden aç
        else:
            self._ana_goster(zorla=True)

    def _ana_goster(self, zorla=False):
        if self._gosterildi or (self._guncelleme_soruluyor and not zorla):
            return
        self._gosterildi = True
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        if self.note is not None:
            self.root.after(50, self.note.focus_set)

    # ------------------------------------------------------------ kurulum
    @property
    def t(self):
        return themes.al(self.cfg.get("tema"))

    def kur(self):
        """Kabuğu (başlık + sol menü + içerik) çizer. Tema/servis değişince de çağrılır."""
        if getattr(self, "aktif_arac", None) == "cagri" and getattr(self, "note", None) is not None:
            try:
                if self.note.winfo_exists():
                    self.not_metni = self._not_al()
            except Exception:
                pass
        for w in self.root.winfo_children():
            if not isinstance(w, ctk.CTkToplevel):
                w.destroy()
        t = self.t
        ctk.set_appearance_mode(t["mod"])
        self.root.configure(fg_color=t["bg"])
        self.root.attributes("-topmost", bool(self.cfg.get("her_zaman_ustte", True)))

        # --- üst başlık (tüm araçlarda ortak)
        ust = ctk.CTkFrame(self.root, fg_color="transparent")
        ust.pack(fill="x", padx=16, pady=(12, 0))
        if self._logo:
            tk.Label(ust, image=self._logo, bd=0, highlightthickness=0, bg=t["bg"]).pack(side="left")
        baslik = ctk.CTkFrame(ust, fg_color="transparent")
        baslik.pack(side="left", padx=(10, 0))
        satir = ctk.CTkFrame(baslik, fg_color="transparent")
        satir.pack(anchor="w")
        ctk.CTkLabel(satir, text=APP_NAME, font=_f(18, True), text_color=t["text"]).pack(side="left")
        ctk.CTkLabel(satir, text=f" {kisa_surum()} ", font=_f(11, True), fg_color=t["chip"],
                     text_color=t["chip_text"], corner_radius=8, height=20).pack(side="left", padx=(8, 0), pady=(3, 0))
        if self.guncelleme:
            ctk.CTkButton(satir, text="⚠ Güncel değil", font=_f(11, True), height=20, corner_radius=8,
                          fg_color=t["warn"], hover_color=t["accent_hover"], text_color="#1A1300",
                          width=10, command=self.guncelleme_sor).pack(side="left", padx=(6, 0), pady=(3, 0))
        ctk.CTkLabel(baslik, text=self._servis_etiketi(), font=_f(11), text_color=t["sub"],
                     height=14).pack(anchor="w")
        ctk.CTkButton(ust, text="⚙", width=38, height=38, corner_radius=10, font=_f(18), fg_color=t["card"],
                      hover_color=t["border"], text_color=t["text"], border_width=1, border_color=t["border"],
                      command=self.ayarlari_ac).pack(side="right")
        ctk.CTkButton(ust, text="🕘", width=38, height=38, corner_radius=10, font=_f(16), fg_color=t["card"],
                      hover_color=t["border"], text_color=t["text"], border_width=1, border_color=t["border"],
                      command=self.gecmisi_ac).pack(side="right", padx=(0, 6))

        ctk.CTkLabel(self.root, text=TELIF, font=_f(10), text_color=t["sub"]).pack(side="bottom", pady=(0, 8))

        # --- gövde: sol menü + içerik
        govde = ctk.CTkFrame(self.root, fg_color="transparent")
        govde.pack(fill="both", expand=True, padx=16, pady=(12, 6))
        self._nav_ciz(govde)
        self.icerik = ctk.CTkFrame(govde, fg_color="transparent")
        self.icerik.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self._icerik_ciz()

    def _nav_ciz(self, govde):
        t = self.t
        ray = ctk.CTkFrame(govde, fg_color=t["card"], corner_radius=14, border_width=1, border_color=t["border"],
                           width=168)
        ray.pack(side="left", fill="y")
        ray.pack_propagate(False)
        self._nav_butonlari = {}
        for kategori, araclar in ARACLAR:
            ctk.CTkLabel(ray, text=kategori.upper(), font=_f(10, True), text_color=t["sub"], anchor="w").pack(
                fill="x", padx=12, pady=(12, 2))
            for anahtar, ad in araclar:
                b = ctk.CTkButton(ray, text=ad, anchor="w", height=34, corner_radius=9, font=_f(12),
                                  command=lambda a=anahtar: self._arac_sec(a))
                b.pack(fill="x", padx=8, pady=2)
                self._nav_butonlari[anahtar] = b
        self._nav_vurgula()

    def _nav_vurgula(self):
        t = self.t
        for anahtar, b in getattr(self, "_nav_butonlari", {}).items():
            if anahtar == self.aktif_arac:
                b.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"])
            else:
                b.configure(fg_color="transparent", hover_color=t["border"], text_color=t["text"])

    def _arac_sec(self, anahtar):
        if anahtar == self.aktif_arac:
            return
        if self.aktif_arac == "cagri" and getattr(self, "note", None) is not None:
            try:
                self.not_metni = self._not_al()
            except Exception:
                pass
        self.aktif_arac = anahtar
        self._nav_vurgula()
        self._icerik_ciz()

    def _icerik_ciz(self):
        for w in self.icerik.winfo_children():
            w.destroy()
        self.note = None
        if self.aktif_arac == "mesai":
            self._sayfa_mesai(self.icerik)
        else:
            self._sayfa_cagri(self.icerik)

    # ------------------------------------------------------------ Çağrı Doldur sayfası
    def _sayfa_cagri(self, govde):
        t = self.t
        kart = ctk.CTkFrame(govde, fg_color=t["card"], corner_radius=16, border_width=1, border_color=t["border"])
        kart.pack(fill="both", expand=True)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="both", expand=True, padx=14, pady=14)

        kutu = ctk.CTkFrame(ic, fg_color="transparent")
        kutu.pack(fill="both", expand=True)
        self.note = ctk.CTkTextbox(kutu, wrap="word", undo=True, maxundo=-1, font=_f(13), fg_color=t["input"],
                                   text_color=t["text"], border_width=1, border_color=t["border"], corner_radius=12)
        self.note.pack(fill="both", expand=True)
        self.ipucu = ctk.CTkLabel(kutu, text=IPUCU, font=_f(12), text_color=t["sub"], justify="left",
                                  wraplength=420, fg_color=t["input"], anchor="nw")
        self.note.bind("<KeyRelease>", lambda e: self._ipucu_guncelle())
        self.note.bind("<FocusIn>", lambda e: self._ipucu_guncelle())
        self.note.bind("<FocusOut>", lambda e: self._ipucu_guncelle())
        self.note.bind("<Control-Return>", self._kisayol)
        self.note.bind("<Control-KP_Enter>", self._kisayol)
        self.ipucu.bind("<Button-1>", lambda e: self.note.focus_set())
        if self.not_metni:
            self.note.insert("1.0", self.not_metni)
        self._ipucu_guncelle()
        self._ucret_alani(ic)
        btn_metni = "✦  AI yorumla ve doldur"
        komut = self.ai_ile_doldur

        self.btn = ctk.CTkButton(govde, text=btn_metni, height=46, corner_radius=12, font=_f(14, True),
                                 fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                                 command=komut)
        self.btn.pack(fill="x", pady=(12, 0))

        durum = ctk.CTkFrame(govde, fg_color="transparent")
        durum.pack(fill="x", pady=(8, 0))
        self.nokta = ctk.CTkLabel(durum, text="●", font=_f(12), text_color=t["sub"], width=14)
        self.nokta.pack(side="left")
        self.durum = ctk.CTkLabel(durum, text="", font=_f(12), text_color=t["sub"], anchor="w", justify="left",
                                  wraplength=420)
        self.durum.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(durum, text="Ctrl + Enter", font=_f(11), text_color=t["sub"]).pack(side="right")
        self._durum_varsayilan()
        if self.note is not None:
            self.root.after(50, self.note.focus_set)

    # ------------------------------------------------------------ Mesai sayfası
    def _sayfa_mesai(self, govde):
        from . import mesai
        t = self.t
        if not hasattr(self, "mesai_maas"):
            self.mesai_maas = ctk.StringVar(value="")
            self.mesai_saat = {k: ctk.StringVar(value="") for k, _, _ in mesai.CARPANLAR}
        kart = ctk.CTkScrollableFrame(govde, fg_color=t["card"], corner_radius=16, border_color=t["border"],
                                      border_width=1)
        kart.pack(fill="both", expand=True)
        ctk.CTkLabel(kart, text="Mesai Hak Edişi", font=_f(16, True), text_color=t["text"]).pack(anchor="w", padx=4, pady=(2, 2))

        uyari = ctk.CTkFrame(kart, fg_color=t["chip"], corner_radius=10)
        uyari.pack(fill="x", padx=4, pady=(4, 10))
        ctk.CTkLabel(uyari, text="⚠  " + mesai.UYARI, font=_f(11), text_color=t["chip_text"], justify="left",
                     wraplength=380, anchor="w").pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(kart, text="Aylık maaş", font=_f(12, True), text_color=t["text"], anchor="w").pack(fill="x", padx=4)
        e = ctk.CTkEntry(kart, textvariable=self.mesai_maas, height=34, corner_radius=10, font=_f(13),
                         placeholder_text="ör. 33.750", fg_color=t["input"], border_color=t["border"], text_color=t["text"])
        e.pack(fill="x", padx=4, pady=(2, 2))
        ctk.CTkLabel(kart, text=f"Saatlik ücret = maaş / {mesai.BOLEN}", font=_f(10), text_color=t["sub"],
                     anchor="w").pack(fill="x", padx=4, pady=(0, 8))

        for anahtar, ad, carpan in mesai.CARPANLAR:
            satir = ctk.CTkFrame(kart, fg_color="transparent")
            satir.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(satir, text=f"{ad}  (x{carpan:g})", font=_f(12), text_color=t["text"], anchor="w",
                         width=200).pack(side="left")
            ec = ctk.CTkEntry(satir, textvariable=self.mesai_saat[anahtar], height=32, corner_radius=9, font=_f(12),
                              placeholder_text="saat", fg_color=t["input"], border_color=t["border"], text_color=t["text"])
            ec.pack(side="left", fill="x", expand=True)
            ec.bind("<Return>", lambda ev: self._mesai_hesapla())

        ctk.CTkButton(kart, text="Hesapla", height=42, corner_radius=12, font=_f(14, True), fg_color=t["accent"],
                      hover_color=t["accent_hover"], text_color=t["on_accent"], command=self._mesai_hesapla).pack(
            fill="x", padx=4, pady=(10, 6))
        self.mesai_sonuc = ctk.CTkFrame(kart, fg_color="transparent")
        self.mesai_sonuc.pack(fill="x", padx=4)

    def _mesai_hesapla(self):
        from . import mesai
        for w in self.mesai_sonuc.winfo_children():
            w.destroy()
        t = self.t
        r = mesai.hesapla(self.mesai_maas.get(), {k: v.get() for k, v in self.mesai_saat.items()})
        if not self.mesai_maas.get().strip():
            ctk.CTkLabel(self.mesai_sonuc, text="Önce maaşı yaz.", font=_f(12), text_color=t["warn"]).pack(anchor="w")
            return
        ctk.CTkLabel(self.mesai_sonuc, text=f"Saatlik ücret: {mesai.tl(r['saatlik'])}", font=_f(12),
                     text_color=t["sub"], anchor="w").pack(fill="x", pady=(2, 4))
        for ad, saat, carpan, tutar in r["satirlar"]:
            if saat:
                sat = ctk.CTkFrame(self.mesai_sonuc, fg_color="transparent")
                sat.pack(fill="x")
                ctk.CTkLabel(sat, text=f"{ad}: {saat:g} saat × {carpan:g}", font=_f(12), text_color=t["text"],
                             anchor="w").pack(side="left")
                ctk.CTkLabel(sat, text=mesai.tl(tutar), font=_f(12), text_color=t["text"], anchor="e").pack(side="right")
        ayr = ctk.CTkFrame(self.mesai_sonuc, fg_color=t["border"], height=1)
        ayr.pack(fill="x", pady=6)
        top = ctk.CTkFrame(self.mesai_sonuc, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=f"Toplam ({r['toplam_saat']:g} saat)", font=_f(13, True), text_color=t["text"],
                     anchor="w").pack(side="left")
        ctk.CTkLabel(top, text=mesai.tl(r["toplam"]), font=_f(14, True), text_color=t["accent"],
                     anchor="e").pack(side="right")

    # ------------------------------------------------------------ ücret seçimi
    def _ucret_durumu_hazirla(self):
        if not hasattr(self, "ucret_secim"):
            self.ucret_secim = ctk.StringVar(value=ucret.VARSAYILAN)
            self.ucretli_tur = ctk.StringVar(value=ucret.UCRETLI_TURLER[0])
            self.tutar = ctk.StringVar(value="")
            self.sozlesmesiz_konu = ctk.StringVar(value=ucret.SOZLESMESIZ_KONULAR[0])

    def _ucret_sifirla(self):
        self.ucret_secim.set(ucret.VARSAYILAN)
        self.ucretli_tur.set(ucret.UCRETLI_TURLER[0])
        self.tutar.set("")
        self.sozlesmesiz_konu.set(ucret.SOZLESMESIZ_KONULAR[0])
        self._ucret_ciz()

    def _ucret_alani(self, ebeveyn):
        """Not kutusunun altındaki ücret seçimi: 3x2 buton + seçime göre açılan ayrıntı satırı."""
        self._ucret_durumu_hazirla()
        t = self.t
        alan = ctk.CTkFrame(ebeveyn, fg_color="transparent")
        alan.pack(fill="x", pady=(10, 0))
        ust = ctk.CTkFrame(alan, fg_color="transparent")
        ust.pack(fill="x")
        ctk.CTkLabel(ust, text="Ücret", font=_f(11, True), text_color=t["sub"], width=46, anchor="nw").pack(
            side="left", anchor="n", pady=(4, 0))
        izgara = ctk.CTkFrame(ust, fg_color="transparent")
        izgara.pack(side="left", fill="x", expand=True)
        self._ucret_butonlari = {}
        for i, ad in enumerate(ucret.SECENEKLER):
            b = ctk.CTkButton(izgara, text=ad, height=28, corner_radius=8, font=_f(11), border_width=1,
                              command=lambda a=ad: (self.ucret_secim.set(a), self._ucret_ciz()))
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2)
            self._ucret_butonlari[ad] = b
        for c in range(3):
            izgara.grid_columnconfigure(c, weight=1, uniform="u")

        self._ucret_detay = ctk.CTkFrame(alan, fg_color="transparent")
        seg = dict(font=_f(11), height=26, fg_color=t["input"], selected_color=t["accent"],
                   selected_hover_color=t["accent_hover"], unselected_color=t["input"],
                   unselected_hover_color=t["border"], text_color=t["text"])
        # Ücretli: tür + tutar
        self._detay_ucretli = ctk.CTkFrame(self._ucret_detay, fg_color="transparent")
        ctk.CTkSegmentedButton(self._detay_ucretli, values=ucret.UCRETLI_TURLER, variable=self.ucretli_tur,
                               width=170, **seg).pack(side="left")
        self._tutar_kutusu = ctk.CTkEntry(self._detay_ucretli, textvariable=self.tutar, height=28, corner_radius=8,
                                          font=_f(12), placeholder_text="Tutar, ör. 3000+kdv",
                                          fg_color=t["input"], border_color=t["border"], text_color=t["text"])
        self._tutar_kutusu.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._tutar_kutusu.bind("<Return>", lambda e: self.ai_ile_doldur())
        # Sözleşmesiz destek: konu
        self._detay_konu = ctk.CTkFrame(self._ucret_detay, fg_color="transparent")
        ctk.CTkSegmentedButton(self._detay_konu, values=ucret.SOZLESMESIZ_KONULAR, variable=self.sozlesmesiz_konu,
                               **seg).pack(fill="x")
        self._ucret_ciz()

    def _ucret_ciz(self):
        if not hasattr(self, "_ucret_butonlari"):
            return
        t = self.t
        secili = self.ucret_secim.get()
        for ad, b in self._ucret_butonlari.items():
            try:
                if ad == secili:
                    b.configure(fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                                border_color=t["accent"])
                else:
                    b.configure(fg_color=t["input"], hover_color=t["border"], text_color=t["text"],
                                border_color=t["border"])
            except tk.TclError:
                return
        for f in (self._detay_ucretli, self._detay_konu):
            f.pack_forget()
        self._ucret_detay.pack_forget()
        if secili == "Ücretli":
            self._ucret_detay.pack(fill="x", padx=(48, 2), pady=(4, 0))
            self._detay_ucretli.pack(fill="x")
            self.root.after(50, self._tutar_kutusu.focus_set)
        elif secili == "Sözleşmesiz destek":
            self._ucret_detay.pack(fill="x", padx=(48, 2), pady=(4, 0))
            self._detay_konu.pack(fill="x")

    def _ucret_bilgisi(self):
        """(forma yazılacak metin, geçmiş özeti). Ücretli ama tutar yoksa UcretHatasi."""
        s, tur, tutar, konu = (self.ucret_secim.get(), self.ucretli_tur.get(), self.tutar.get(),
                               self.sozlesmesiz_konu.get())
        return (ucret.metin(s, tur, tutar, konu, self.cfg.get("varsayilan_ucret")),
                ucret.ozet(s, tur, tutar, konu))

    def _logo_yukle(self):
        """Logo, ekran ölçeğine en yakın boyuttan yüklenir (resim kütüphanesi gerekmez)."""
        try:
            olcek = ctk.ScalingTracker.get_window_scaling(self.root)
        except Exception:
            olcek = 1.0
        boyut = min((34, 43, 51, 68), key=lambda b: abs(b - 34 * olcek))
        try:
            return tk.PhotoImage(file=paths.kaynak(f"assets/logo_{boyut}.png"), master=self.root)
        except Exception:
            return None

    def _servis_etiketi(self):
        metin = "Hızlı" if self.cfg.get("gemini_hiz") == "hizli" else "Dengeli"
        bugun = gecmis.bugun_sayisi()
        return metin + (f" · Bugün {bugun} çağrı" if bugun else "")

    # ------------------------------------------------------------ yardımcılar
    def _not_al(self):
        return self.note.get("1.0", "end").strip() if self.note is not None else ""

    def _ipucu_guncelle(self):
        if self.note is None:
            return
        if self._not_al() or self.root.focus_get() == self.note._textbox:
            self.ipucu.place_forget()
        else:
            self.ipucu.place(x=12, y=10, relwidth=0.92)

    def _kisayol(self, _e):
        self.ai_ile_doldur()
        return "break"

    def durum_yaz(self, metin, tur="bilgi"):
        d = getattr(self, "durum", None)
        try:
            if d is None or not d.winfo_exists():
                return  # başka araç sayfasındayız, durum çubuğu yok
        except Exception:
            return
        t = self.t
        renk = {"ok": t["ok"], "err": t["err"], "is": t["warn"]}.get(tur, t["sub"])
        self.nokta.configure(text_color=renk)
        self.durum.configure(text=metin, text_color=t["text"] if tur in ("ok", "err") else t["sub"])

    def _durum_varsayilan(self):
        self.durum_yaz("Hazır. 'Çağrıyı Tamamla' ekranını aç, notunu yaz.")

    def _mesgul(self, var):
        self.mesgul = var
        try:
            if self.btn.winfo_exists():
                self.btn.configure(state="disabled" if var else "normal")
        except Exception:
            pass

    # ------------------------------------------------------------ açılış
    def _acilis_isleri(self):
        pencere_sn = time.perf_counter() - self.baslangic
        filler.hazirla()  # ekran otomasyonunu önceden kur: ilk doldurma hızlanır
        if os.environ.get("CAGRI_SELFTEST"):
            self._oz_test(pencere_sn)
            return
        threading.Thread(target=ai.isit, args=(self.cfg,), daemon=True).start()
        if not updater.eskileri_temizle():
            self.root.after(8000, updater.eskileri_temizle)  # eski exe hâlâ kilitliyse biraz sonra
        if self.guncellendi_eski is not None:
            self.durum_yaz(f"Güncelleme tamamlandı: {kisa_surum()} kullanıyorsun.", "ok")

    def _oz_test(self, pencere_sn):
        """GitHub'daki otomatik derlemede exe'nin açıldığını, süresini ve güncelleme akışını doğrular."""
        if os.environ.get("CAGRI_UPDATE_TEST") and self.guncellendi_eski is None:
            # Güncelleme testi: kendini 'yeni sürümle' değiştirip yeniden başlat; yeni süreç sonucu yazar.
            if updater.uygula({"url": "test", "version": "test"}, None, VERSION):
                self.root.after(100, self.root.destroy)
            return
        sonuc = {"surum": VERSION, "pencere_sn": round(pencere_sn, 2),
                 "guncellendi": self.guncellendi_eski is not None,
                 "otomasyon": filler._uia is not None, "otomasyon_uretildi": filler.URETILDI,
                 "toplam_sn": round(time.perf_counter() - self.baslangic, 2)}
        try:
            with open(os.environ["CAGRI_SELFTEST"], "w", encoding="utf-8") as f:
                json.dump(sonuc, f)
        finally:
            self.root.after(100, self.root.destroy)

    def guncelleme_kontrol(self, sessiz=False, bitince=None):
        repo = self.cfg.get("guncelleme_repo")
        if not repo:
            if bitince:
                bitince("Güncelleme kaynağı tanımlı değil.")
            return

        def is_():
            try:
                info = updater.kontrol(repo, VERSION)
                mesaj = f"Yeni sürüm var: v{info['version']}" if info else f"En güncel sürümü kullanıyorsun ({kisa_surum()})."
            except Exception as e:
                info, mesaj = None, f"Kontrol edilemedi: {e}"
            self.root.after(0, lambda: self._guncelleme_sonucu(info, mesaj, bitince, sessiz))

        threading.Thread(target=is_, daemon=True).start()

    def _guncelleme_sonucu(self, info, mesaj, bitince, sessiz=False):
        yeni = bool(info) and info != self.guncelleme
        if yeni:
            self.guncelleme = info
            self.kur()
        if info and sessiz and yeni and not self._gosterildi:
            # Açılış: ana pencere gizliyken sadece güncelleme sorusu gösterilir.
            self._guncelleme_soruluyor = True
            self.guncelleme_penceresi = GuncellemePenceresi(self, info, bagimsiz=True)
        elif info and ((sessiz and yeni) or bitince):
            self.root.after(400, self.guncelleme_sor)  # kullanıcıya "güncellensin mi?" diye sor
        if sessiz and not info:
            self._ana_goster()
        if bitince:
            bitince(mesaj)

    def guncelleme_sor(self):
        if not self.guncelleme:
            return
        if self._acik_mi(getattr(self, "guncelleme_penceresi", None)):
            self.guncelleme_penceresi.w.lift()
            return
        self.guncelleme_penceresi = GuncellemePenceresi(self, self.guncelleme)

    # ------------------------------------------------------------ doldurma
    def ai_ile_doldur(self):
        if self.mesgul or self.note is None:
            return
        notu = self._not_al()
        if not notu:
            self.durum_yaz("Önce notunu yaz.", "is")
            return
        try:
            ucret_metni, ucret_ozeti = self._ucret_bilgisi()
        except ucret.UcretHatasi as e:
            self.durum_yaz(str(e), "is")
            self._tutar_kutusu.focus_set()
            return
        self._mesgul(True)
        self.durum_yaz("AI yorumluyor…", "is")
        t0 = time.perf_counter()
        ek = [f"Ücret durumu: {ucret_ozeti}. Ücret alanına aynen şunu yaz: {ucret_metni}"]
        self._son = {"not": notu, "secimler": {"ucret": ucret_ozeti}}

        def is_():
            try:
                vals, sure = ai.yorumla(self.cfg, notu, ek)
                vals["ucret"] = ucret_metni  # ücret alanı her zaman seçime göre sabit metin
                self.root.after(0, lambda: self._ekrana(vals, sure, t0, temizle=True))
            except Exception as e:
                msg = str(e)
                self.root.after(0, lambda: (self._mesgul(False), self.durum_yaz(msg, "err")))

        threading.Thread(target=is_, daemon=True).start()

    def _ekrana(self, vals, ai_sure, t0, temizle):
        self.durum_yaz("Çağrı ekranı dolduruluyor…", "is")
        self.root.update_idletasks()
        t1 = time.perf_counter()
        try:
            cagri_no = filler.doldur(self.cfg["pencere_basligi"], vals)
        except Exception as e:
            self._mesgul(False)
            self.durum_yaz(str(e), "err")
            return
        ekran = time.perf_counter() - t1
        self._mesgul(False)
        son = getattr(self, "_son", None) or {}
        if temizle:
            try:
                gecmis.ekle(cagri_no, son.get("not", ""), vals, son.get("secimler"))
            except Exception:
                pass
        if temizle and self.note is not None:
            self.note.delete("1.0", "end")
            self._ipucu_guncelle()
            self._ucret_sifirla()
        sure = f"AI {ai_sure:.1f} sn · ekran {ekran:.1f} sn" if ai_sure is not None else f"{ekran:.1f} sn"
        self.durum_yaz(f"Dolduruldu ({sure}). Kontrol edip kapatabilirsin.", "ok")

    def gecmisi_ac(self):
        if self._acik_mi(getattr(self, "gecmis_penceresi", None)):
            self.gecmis_penceresi.w.lift()
            self.gecmis_penceresi.w.focus_force()
            return
        self.gecmis_penceresi = GecmisPenceresi(self)

    def gecmisten_doldur(self, kayit):
        self._son = {"not": kayit.get("not", ""), "secimler": kayit.get("secimler", {})}
        self._mesgul(True)
        self._ekrana(kayit.get("alanlar", {}), None, time.perf_counter(), temizle=False)

    # ------------------------------------------------------------ ayarlar
    def _acik_mi(self, pencere):
        try:
            return pencere is not None and pencere.w.winfo_exists()
        except Exception:
            return False

    def ayarlari_ac(self):
        if self._acik_mi(self.ayar_penceresi):
            self.ayar_penceresi.w.deiconify()
            self.ayar_penceresi.w.lift()
            self.ayar_penceresi.w.focus_force()
            return
        self.ayar_penceresi = AyarPenceresi(self)

    def yetkili_islem(self, sonra, ebeveyn=None):
        """Her seferinde yetkili şifresi sorar; doğrulanınca 'sonra'yı çağırır. Şifre yoksa önce belirletir."""
        SifrePenceresi(self, sonra, ebeveyn or self.root)

    def ayarlar_kaydedildi(self, mesaj="Ayarlar kaydedildi."):
        config.kaydet(self.cfg)
        self.kur()
        threading.Thread(target=ai.isit, args=(self.cfg,), daemon=True).start()
        self.durum_yaz(mesaj, "ok")

    def calistir(self):
        self.root.mainloop()


# ====================================================================== pencereler
class _Pencere:
    """Ayar pencerelerinin ortak yapı taşları."""

    SARMA = 400

    def __init__(self, app, baslik, boyut, ebeveyn=None, kaydir=True, bagimsiz=False):
        self.app = app
        self.t = t = app.t
        w = self.w = ctk.CTkToplevel(ebeveyn or app.root)
        w.title(baslik)
        if bagimsiz:
            # Ana pencere gizliyken tek başına, ekranın ortasında açılır.
            gen, yuk = (int(x) for x in boyut.split("x"))
            olcek = ctk.ScalingTracker.get_window_scaling(w) if hasattr(ctk, "ScalingTracker") else 1.0
            x = max(0, (w.winfo_screenwidth() - int(gen * olcek)) // 2)
            y = max(0, (w.winfo_screenheight() - int(yuk * olcek)) // 3)
            w.geometry(f"{boyut}+{x}+{y}")
        else:
            w.geometry(boyut)
        w.configure(fg_color=t["bg"])
        if not bagimsiz:
            w.transient(ebeveyn or app.root)
        w.attributes("-topmost", True)
        _ikon_ver(w)
        w.after(120, w.focus_force)
        if kaydir:
            self.alan = ctk.CTkScrollableFrame(w, fg_color="transparent")
            self.alan.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        else:
            self.alan = ctk.CTkFrame(w, fg_color="transparent")
            self.alan.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    def bolum(self, metin):
        ctk.CTkLabel(self.alan, text=metin.upper(), font=_f(11, True), text_color=self.t["accent"]).pack(
            anchor="w", padx=6, pady=(14, 4))

    def etiket(self, metin):
        ctk.CTkLabel(self.alan, text=metin, font=_f(12), text_color=self.t["text"]).pack(anchor="w", padx=6)

    def aciklama(self, metin):
        ctk.CTkLabel(self.alan, text=metin, font=_f(11), text_color=self.t["sub"], wraplength=self.SARMA,
                     justify="left").pack(anchor="w", padx=6, pady=(0, 6))

    def giris(self, etiket, deger="", gizli=False):
        self.etiket(etiket)
        e = ctk.CTkEntry(self.alan, show="•" if gizli else "", font=_f(12), height=34, corner_radius=10,
                         fg_color=self.t["input"], border_color=self.t["border"], text_color=self.t["text"])
        e.insert(0, str(deger or ""))
        e.pack(fill="x", padx=6, pady=(2, 8))
        return e

    def segment(self, degerler, degisken):
        t = self.t
        ctk.CTkSegmentedButton(self.alan, values=degerler, variable=degisken, font=_f(12), height=32,
                               fg_color=t["input"], selected_color=t["accent"], selected_hover_color=t["accent_hover"],
                               unselected_color=t["input"], unselected_hover_color=t["border"],
                               text_color=t["text"]).pack(fill="x", padx=6, pady=(2, 8))

    def ikincil_buton(self, ebeveyn, metin, komut, **kw):
        t = self.t
        ayar = dict(text=metin, height=32, corner_radius=8, font=_f(12), fg_color=t["card"],
                    hover_color=t["border"], text_color=t["text"], border_width=1,
                    border_color=t["border"], command=komut)
        ayar.update(kw)
        return ctk.CTkButton(ebeveyn, **ayar)

    def ana_buton(self, metin, komut):
        t = self.t
        b = ctk.CTkButton(self.w, text=metin, height=42, corner_radius=12, font=_f(14, True), fg_color=t["accent"],
                          hover_color=t["accent_hover"], text_color=t["on_accent"], command=komut)
        b.pack(fill="x", padx=16, pady=12)
        return b


class AyarPenceresi(_Pencere):
    """Herkesin girebildiği ayarlar. Yapay zekâ ve yönetici ayarları ayrı, şifreli bölümde."""

    def __init__(self, app):
        super().__init__(app, "Ayarlar", "460x470")
        cfg, t = app.cfg, self.t

        self.bolum("Görünüm")
        self.etiket("Tema")
        self.tema = ctk.StringVar(value=themes.al(cfg["tema"])["ad"])
        ctk.CTkOptionMenu(self.alan, values=themes.ad_listesi(), variable=self.tema, font=_f(12),
                          fg_color=t["input"], button_color=t["accent"], button_hover_color=t["accent_hover"],
                          text_color=t["text"], dropdown_fg_color=t["card"], dropdown_text_color=t["text"],
                          dropdown_hover_color=t["border"], corner_radius=10, height=34).pack(fill="x", padx=6, pady=(2, 8))
        self.ustte = ctk.BooleanVar(value=bool(cfg.get("her_zaman_ustte", True)))
        ctk.CTkSwitch(self.alan, text="Pencere her zaman üstte kalsın", variable=self.ustte, font=_f(12),
                      text_color=t["text"], progress_color=t["accent"]).pack(anchor="w", padx=6, pady=(0, 4))

        self.bolum("Güncelleme")
        satir = ctk.CTkFrame(self.alan, fg_color="transparent")
        satir.pack(fill="x", padx=6, pady=(0, 6))
        self.ikincil_buton(satir, "Şimdi kontrol et", self.kontrol_et, width=130).pack(side="left")
        self.kontrol_sonuc = ctk.CTkLabel(satir, text=f"Sürüm {kisa_surum()}", font=_f(11), text_color=t["sub"])
        self.kontrol_sonuc.pack(side="left", padx=10)

        self.bolum("Güvenlik")
        self.acilis = ctk.BooleanVar(value=bool(cfg.get("acilista_sifre", False)))
        ctk.CTkSwitch(self.alan, text="Açılışta şifre sor", variable=self.acilis, font=_f(12),
                      text_color=t["text"], progress_color=t["accent"]).pack(anchor="w", padx=6, pady=(0, 2))
        self.aciklama("Uygulama her açıldığında yetkili şifresini ister.")

        self.bolum("Yetkili")
        kilit = "🔒  Yapay zekâ ve yönetici ayarları"
        self.ikincil_buton(self.alan, kilit, self.yonetici_ac, height=40, anchor="w").pack(fill="x", padx=6, pady=(2, 4))
        self.aciklama("Yorumlama hızı, gizlilik filtresi, bağlantı testi, güncelleme kaynağı. Yetkili şifresi ister.")

        self.ana_buton("Kaydet", self.kaydet)

    def kontrol_et(self):
        self.kontrol_sonuc.configure(text="Kontrol ediliyor…")

        def bitti(mesaj):
            if self.w.winfo_exists():
                self.kontrol_sonuc.configure(text=mesaj)

        self.app.guncelleme_kontrol(bitince=bitti)

    def yonetici_ac(self):
        app = self.app
        if app._acik_mi(getattr(app, "yonetici_penceresi", None)):
            app.yonetici_penceresi.w.lift()
            return

        def ac():
            app.yonetici_penceresi = YoneticiPenceresi(app, self.w)

        app.yetkili_islem(ac, self.w)

    def kaydet(self):
        c = self.app.cfg
        c["tema"] = themes.anahtar(self.tema.get())
        c["her_zaman_ustte"] = bool(self.ustte.get())
        if self.acilis.get() and not c.get("yetkili_sifre"):
            # Açılış kilidi için önce bir şifre belirlensin.
            def tamamla():
                c["acilista_sifre"] = True
                config.kaydet(c)
                self.w.destroy()
                self.app.ayarlar_kaydedildi()
            SifrePenceresi(self.app, tamamla, self.w)
            return
        c["acilista_sifre"] = bool(self.acilis.get())
        self.w.destroy()
        self.app.ayarlar_kaydedildi()


class SifrePenceresi(_Pencere):
    """Yetkili şifresini sorar; hiç belirlenmemişse belirletir."""

    SARMA = 320
    _hatali = 0
    _kilit_bitis = 0.0

    def __init__(self, app, basarili, ebeveyn):
        self.belirle = not app.cfg.get("yetkili_sifre")
        super().__init__(app, "Yetkili şifresi", "380x360" if self.belirle else "380x250", ebeveyn, kaydir=False)
        self.basarili = basarili
        t = self.t
        if self.belirle:
            ctk.CTkLabel(self.alan, text="Yetkili şifresi belirle", font=_f(15, True), text_color=t["text"]).pack(anchor="w", padx=6)
            self.aciklama("API ayarlarına girmek için kullanılacak. Unutursan ayarlar sıfırlanmadan geri alınamaz.")
            self.s1 = self.giris("Yeni şifre (en az 4 karakter)", gizli=True)
            self.s2 = self.giris("Yeni şifre (tekrar)", gizli=True)
            self.s2.bind("<Return>", lambda e: self.tamam())
        else:
            ctk.CTkLabel(self.alan, text="Yetkili şifresi", font=_f(15, True), text_color=t["text"]).pack(anchor="w", padx=6)
            self.s1 = self.giris("Şifre", gizli=True)
            self.s1.bind("<Return>", lambda e: self.tamam())
        self.hata = ctk.CTkLabel(self.alan, text="", font=_f(11), text_color=t["err"])
        self.hata.pack(anchor="w", padx=6)
        self.ana_buton("Devam", self.tamam)
        self.w.after(200, self.s1.focus_set)
        self.w.grab_set()

    def tamam(self):
        sifre = self.s1.get()
        if self.belirle:
            if len(sifre) < 4:
                self.hata.configure(text="Şifre en az 4 karakter olmalı.")
                return
            if sifre != self.s2.get():
                self.hata.configure(text="Şifreler aynı değil.")
                return
            self.app.cfg["yetkili_sifre"] = guvenlik.sifre_ozeti(sifre)
            config.kaydet(self.app.cfg)
        else:
            kalan = SifrePenceresi._kilit_bitis - time.monotonic()
            if kalan > 0:
                self.hata.configure(text=f"Çok fazla hatalı deneme. {int(kalan) + 1} sn bekle.")
                return
            if not guvenlik.sifre_dogru(sifre, self.app.cfg.get("yetkili_sifre")):
                SifrePenceresi._hatali += 1
                if SifrePenceresi._hatali >= 5:
                    SifrePenceresi._hatali = 0
                    SifrePenceresi._kilit_bitis = time.monotonic() + 30
                self.hata.configure(text="Şifre yanlış.")
                self.s1.delete(0, "end")
                return
            SifrePenceresi._hatali = 0
        self.w.grab_release()
        self.w.destroy()
        self.basarili()


class YoneticiPenceresi(_Pencere):
    """Şifreyle açılan bölüm: yorumlama hızı, gizlilik, bağlantı testi, güncelleme kaynağı, şifre değiştirme."""

    def __init__(self, app, ebeveyn):
        super().__init__(app, "Yapay zekâ ve yönetici ayarları", "460x520", ebeveyn)
        cfg = app.cfg

        self.bolum("Yapay zekâ")
        self.aciklama("Yapay zekâ bağlantısı uygulamanın içinde hazırdır; anahtar girmene gerek yok.")
        self.etiket("Yorumlama hızı")
        self.hiz = ctk.StringVar(value="Hızlı" if cfg.get("gemini_hiz") == "hizli" else "Dengeli")
        self.segment(["Hızlı", "Dengeli"], self.hiz)
        self.aciklama("Hızlı: en çabuk cevap. Dengeli: biraz daha yavaş ama daha iyi yorum.")
        self.gizlilik = ctk.BooleanVar(value=bool(cfg.get("gizlilik", True)))
        ctk.CTkSwitch(self.alan, text="Gizlilik filtresi", variable=self.gizlilik, font=_f(12),
                      text_color=self.t["text"], progress_color=self.t["accent"]).pack(anchor="w", padx=6, pady=(4, 2))
        self.aciklama("VKN, TC kimlik no, telefon, e-posta ve IBAN yapay zekâya gönderilmeden maskelenir; "
                      "forma gerçek değerleri yazılır.")
        tsat = ctk.CTkFrame(self.alan, fg_color="transparent")
        tsat.pack(fill="x", padx=6, pady=(4, 0))
        self.test_btn = self.ikincil_buton(tsat, "Bağlantıyı test et", self.baglanti_test, width=150)
        self.test_btn.pack(side="left")
        self.test_sonuc = ctk.CTkLabel(tsat, text="", font=_f(11), text_color=self.t["sub"])
        self.test_sonuc.pack(side="left", padx=8)

        self.bolum("Sistem")
        self.baslik = self.giris("Çağrı ekranının pencere başlığı", cfg["pencere_basligi"])
        self.repo = self.giris("Güncelleme kaynağı (GitHub kullanıcı/repo)", cfg.get("guncelleme_repo", ""))

        self.bolum("Yetkili şifresini değiştir")
        self.y1 = self.giris("Yeni şifre (boş bırakırsan değişmez)", gizli=True)
        self.y2 = self.giris("Yeni şifre (tekrar)", gizli=True)
        self.hata = ctk.CTkLabel(self.alan, text="", font=_f(11), text_color=self.t["err"])
        self.hata.pack(anchor="w", padx=6)

        self.ana_buton("Kaydet", self.kaydet)

    def baglanti_test(self):
        c = dict(self.app.cfg)
        c["gemini_hiz"] = "hizli" if self.hiz.get() == "Hızlı" else "dengeli"
        self.test_btn.configure(state="disabled")
        self.test_sonuc.configure(text="Test ediliyor…", text_color=self.t["sub"])

        def is_():
            ok, mesaj = ai.baglanti_testi(c)
            self.app.root.after(0, lambda: bitti(ok, mesaj))

        def bitti(ok, mesaj):
            if not self.w.winfo_exists():
                return
            self.test_btn.configure(state="normal")
            self.test_sonuc.configure(text=mesaj, text_color=self.t["ok"] if ok else self.t["err"])

        threading.Thread(target=is_, daemon=True).start()

    def kaydet(self):
        y1 = self.y1.get()
        if y1 or self.y2.get():
            if len(y1) < 4:
                self.hata.configure(text="Yeni şifre en az 4 karakter olmalı.")
                return
            if y1 != self.y2.get():
                self.hata.configure(text="Yeni şifreler aynı değil.")
                return
        c = self.app.cfg
        c["gemini_hiz"] = "hizli" if self.hiz.get() == "Hızlı" else "dengeli"
        c["gizlilik"] = bool(self.gizlilik.get())
        c["pencere_basligi"] = self.baslik.get().strip() or "Çağrıyı Tamamla"
        c["guncelleme_repo"] = self.repo.get().strip()
        if y1:
            c["yetkili_sifre"] = guvenlik.sifre_ozeti(y1)
        self.w.destroy()
        self.app.ayarlar_kaydedildi("Ayarlar kaydedildi.")


class GuncellemePenceresi(_Pencere):
    """'Sunucuda yeni sürüm var, güncellensin mi?' penceresi; indirme ilerlemesini de gösterir."""

    SARMA = 360

    def __init__(self, app, info, bagimsiz=False):
        super().__init__(app, f"{APP_NAME} · Güncelleme", "440x320", kaydir=False, bagimsiz=bagimsiz)
        self.info = info
        self.bagimsiz = bagimsiz
        self.w.protocol("WM_DELETE_WINDOW", self.sonra)
        t = self.t
        ctk.CTkLabel(self.alan, text="Yeni sürüm hazır", font=_f(16, True), text_color=t["text"]).pack(anchor="w", padx=6)
        ctk.CTkLabel(self.alan, text=f"Sunucuda v{info['version']} var, sen {kisa_surum()} kullanıyorsun.\n"
                                     "Şimdi güncellensin mi?", font=_f(12), text_color=t["text"],
                     justify="left").pack(anchor="w", padx=6, pady=(6, 4))
        notlar = _notlari_sadelestir(info.get("notes") or "")
        if notlar:
            self.aciklama(notlar[:300] + ("…" if len(notlar) > 300 else ""))
        self.aciklama("Ayarların, şifren ve API anahtarların korunur. Uygulama kapanıp yeni sürümle açılır.")
        self.cubuk = ctk.CTkProgressBar(self.alan, progress_color=t["accent"], fg_color=t["input"], height=8)
        self.durum = ctk.CTkLabel(self.alan, text="", font=_f(11), text_color=t["sub"])

        alt = ctk.CTkFrame(self.w, fg_color="transparent")
        alt.pack(fill="x", padx=16, pady=12)
        self.sonra_btn = self.ikincil_buton(alt, "Sonra", self.sonra, width=110, height=40)
        self.sonra_btn.pack(side="left")
        self.evet_btn = ctk.CTkButton(alt, text="Şimdi güncelle", height=40, corner_radius=12, font=_f(14, True),
                                      fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                                      command=self.baslat)
        self.evet_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def sonra(self):
        if str(self.sonra_btn.cget("state")) == "disabled":
            return  # indirme sürerken kapatılmasın
        self.w.destroy()
        if self.bagimsiz:
            self.app._guncelleme_soruluyor = False
            self.app._ana_goster(zorla=True)

    def baslat(self):
        app = self.app
        self.evet_btn.configure(state="disabled", text="İndiriliyor…")
        self.sonra_btn.configure(state="disabled")
        self.cubuk.set(0)
        self.cubuk.pack(fill="x", padx=6, pady=(8, 2))
        self.durum.pack(anchor="w", padx=6)

        def ilerleme(oran):
            app.root.after(0, lambda: (self.cubuk.set(oran), self.durum.configure(text=f"%{int(oran * 100)} indirildi")))

        def is_():
            try:
                kapat = updater.uygula(self.info, ilerleme, VERSION)
            except Exception as e:
                msg = str(e)
                app.root.after(0, lambda: self._hata(msg))
                return
            if kapat:
                app.root.after(0, lambda: (self.cubuk.set(1), self.durum.configure(text="Tamamlandı. Yeni sürüm açılıyor…"),
                                           app.root.after(700, app.root.destroy)))
            else:
                app.root.after(0, lambda: (self.sonra_btn.configure(state="normal"), self.sonra()))

        threading.Thread(target=is_, daemon=True).start()

    def _hata(self, msg):
        if not self.w.winfo_exists():
            return
        self.durum.configure(text=f"Güncelleme olmadı: {msg}", text_color=self.t["err"])
        self.evet_btn.configure(state="normal", text="Tekrar dene")
        self.sonra_btn.configure(state="normal")


def _notlari_sadelestir(metin):
    """Sürüm notlarındaki Markdown işaretlerini (**, -, #) okunur metne çevirir."""
    satirlar = []
    for satir in metin.replace("\r", "").split("\n"):
        satir = satir.strip().replace("**", "").lstrip("#").strip()
        if not satir:
            continue
        if satir.startswith(("- ", "* ")):
            satir = "• " + satir[2:]
        satirlar.append(satir)
    return "\n".join(satirlar)


class GecmisPenceresi(_Pencere):
    """Doldurulan çağrıların listesi: ara, ayrıntıya bak, ekrana tekrar doldur, notu geri al."""

    SARMA = 470

    def __init__(self, app):
        super().__init__(app, "Geçmiş", "540x620", kaydir=False)
        t = self.t
        self.liste = gecmis.yukle()
        ust = ctk.CTkFrame(self.alan, fg_color="transparent")
        ust.pack(fill="x", padx=6)
        ctk.CTkLabel(ust, text="Geçmiş", font=_f(16, True), text_color=t["text"]).pack(side="left")
        ctk.CTkLabel(ust, text=f"{len(self.liste)} kayıt · bugün {gecmis.bugun_sayisi(self.liste)}",
                     font=_f(11), text_color=t["sub"]).pack(side="left", padx=10)
        self.arama = ctk.CTkEntry(self.alan, placeholder_text="Ara: Çağrı No, müşteri, konu…", font=_f(12),
                                  height=34, corner_radius=10, fg_color=t["input"], border_color=t["border"],
                                  text_color=t["text"])
        self.arama.pack(fill="x", padx=6, pady=(10, 6))
        self.arama.bind("<KeyRelease>", lambda e: self.listele())
        self.kutu = ctk.CTkScrollableFrame(self.alan, fg_color="transparent")
        self.kutu.pack(fill="both", expand=True)
        self.alt = ctk.CTkFrame(self.w, fg_color="transparent")
        self.alt.pack(fill="x", padx=14, pady=10)
        self.listele()

    def _temizle(self):
        for c in self.kutu.winfo_children():
            c.destroy()
        for c in self.alt.winfo_children():
            c.destroy()

    def listele(self):
        self._temizle()
        t = self.t
        bulunan = gecmis.ara(self.liste, self.arama.get())
        if not bulunan:
            ctk.CTkLabel(self.kutu, text="Henüz kayıt yok." if not self.liste else "Eşleşen kayıt yok.",
                         font=_f(12), text_color=t["sub"]).pack(pady=20)
            return
        for k in bulunan[:100]:
            ozet = (k.get("alanlar") or {}).get("ozet") or k.get("not", "")
            ozet = ozet if len(ozet) <= 110 else ozet[:107] + "…"
            baslik = f"{k.get('cagri_no') or 'Çağrı No okunamadı'}   ·   {k.get('zaman', '')}"
            kart = ctk.CTkFrame(self.kutu, fg_color=t["card"], corner_radius=10, border_width=1,
                                border_color=t["border"])
            kart.pack(fill="x", padx=2, pady=3)
            l1 = ctk.CTkLabel(kart, text=baslik, font=_f(12, True), text_color=t["text"], anchor="w")
            l1.pack(fill="x", padx=10, pady=(6, 0))
            l2 = ctk.CTkLabel(kart, text=ozet, font=_f(11), text_color=t["sub"], anchor="w", justify="left",
                              wraplength=450)
            l2.pack(fill="x", padx=10, pady=(0, 6))
            for w in (kart, l1, l2):
                w.bind("<Button-1>", lambda e, kayit=k: self.ayrinti(kayit))
                w.configure(cursor="hand2")

    def ayrinti(self, k):
        self._temizle()
        t = self.t
        ctk.CTkLabel(self.kutu, text=f"{k.get('cagri_no') or 'Çağrı No okunamadı'}  ·  {k.get('zaman', '')}",
                     font=_f(13, True), text_color=t["text"], anchor="w").pack(fill="x", padx=4, pady=(0, 6))
        bloklar = [("Not", k.get("not", ""))]
        secim = k.get("secimler") or {}
        if secim:
            bloklar.append(("Ücret seçimi", secim.get("ucret", "-")))
        alanlar = k.get("alanlar") or {}
        from .prompt import FIELDS
        bloklar += [(etiket, alanlar.get(anahtar, "")) for anahtar, etiket in FIELDS]
        for etiket, metin in bloklar:
            ctk.CTkLabel(self.kutu, text=etiket, font=_f(11, True), text_color=t["accent"], anchor="w").pack(
                fill="x", padx=4, pady=(6, 0))
            ctk.CTkLabel(self.kutu, text=metin or "-", font=_f(12), text_color=t["text"], anchor="w",
                         justify="left", wraplength=470).pack(fill="x", padx=4)

        self.ikincil_buton(self.alt, "← Geri", self.listele, width=80, height=36).pack(side="left")
        self.ikincil_buton(self.alt, "Notu kutuya al", lambda: self.notu_al(k), width=120,
                           height=36).pack(side="left", padx=6)
        ctk.CTkButton(self.alt, text="Ekrana tekrar doldur", height=36, corner_radius=10, font=_f(13, True),
                      fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                      command=lambda: self.app.gecmisten_doldur(k)).pack(side="right", fill="x", expand=True)

    def notu_al(self, k):
        app = self.app
        if app.note is None:
            return
        app.note.delete("1.0", "end")
        app.note.insert("1.0", k.get("not", ""))
        app._ipucu_guncelle()
        app.root.lift()
        app.note.focus_set()
