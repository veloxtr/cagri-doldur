# -*- coding: utf-8 -*-
"""Ana pencere ve ayarlar penceresi."""
import threading
import time
import tkinter as tk

import customtkinter as ctk

from . import ai, config, filler, guvenlik, paths, themes, updater
from .version import APP_NAME, TELIF, VERSION, kisa_surum

FONT = "Segoe UI"
IPUCU = ("Ne oldu, ne yaptın? Dağınık yazabilirsin.\n\n"
         "Örn: vkn 10 hane uyarısı veriyordu, gümrük carisi boştu, oluşturup seçtim, "
         "gönderim yapıldı müşteri onay verdi")

SERVIS_ADLARI = {"gemini": "Gemini", "anthropic": "Claude API", "kopyala": "Kopyala-yapıştır"}


def _f(size, bold=False):
    return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")


def _ikon_ver(pencere):
    ico = paths.kaynak("assets/icon.ico")
    try:
        pencere.iconbitmap(ico)
        pencere.after(250, lambda: pencere.iconbitmap(ico))  # customtkinter kendi ikonunu basmasın
    except Exception:
        pass


class App:
    def __init__(self):
        self.cfg = config.yukle()
        self.guncelleme = None
        self.mesgul = False
        self.not_metni = ""
        self.ayar_penceresi = None

        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} {kisa_surum()}")
        self.root.geometry("540x470")
        self.root.minsize(440, 400)
        _ikon_ver(self.root)
        self._logo = self._logo_yukle()

        self.kur()
        self.root.after(300, self._acilis_isleri)

    # ------------------------------------------------------------ kurulum
    @property
    def t(self):
        return themes.al(self.cfg.get("tema"))

    def kur(self):
        """Arayüzü (yeniden) çizer. Tema değişince de çağrılır."""
        if hasattr(self, "note") and self.note.winfo_exists():
            self.not_metni = self._not_al()
        for w in self.root.winfo_children():
            if not isinstance(w, ctk.CTkToplevel):
                w.destroy()
        t = self.t
        ctk.set_appearance_mode(t["mod"])
        self.root.configure(fg_color=t["bg"])
        self.root.attributes("-topmost", bool(self.cfg.get("her_zaman_ustte", True)))

        govde = ctk.CTkFrame(self.root, fg_color="transparent")
        govde.pack(fill="both", expand=True, padx=18, pady=(14, 8))

        # --- başlık
        ust = ctk.CTkFrame(govde, fg_color="transparent")
        ust.pack(fill="x")
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
            ctk.CTkButton(satir, text="⚠ Kullandığınız sürüm güncel değil", font=_f(11, True), height=20,
                          corner_radius=8, fg_color=t["warn"], hover_color=t["accent_hover"], text_color="#1A1300",
                          width=10, command=self.guncelleme_sor).pack(side="left", padx=(6, 0), pady=(3, 0))
        ctk.CTkLabel(baslik, text=self._servis_etiketi(), font=_f(11), text_color=t["sub"],
                     height=14).pack(anchor="w")
        ctk.CTkButton(ust, text="⚙", width=38, height=38, corner_radius=10, font=_f(18),
                      fg_color=t["card"], hover_color=t["border"], text_color=t["text"],
                      border_width=1, border_color=t["border"], command=self.ayarlari_ac).pack(side="right")

        # --- kart
        kart = ctk.CTkFrame(govde, fg_color=t["card"], corner_radius=16, border_width=1, border_color=t["border"])
        kart.pack(fill="both", expand=True, pady=(14, 0))
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="both", expand=True, padx=14, pady=14)

        kopyala = self.cfg.get("saglayici") == "kopyala"
        if kopyala:
            ctk.CTkLabel(ic, text="Claude'dan gelen bloğu doldur", font=_f(14, True),
                         text_color=t["text"]).pack(anchor="w")
            ctk.CTkLabel(ic, justify="left", wraplength=440, font=_f(12), text_color=t["sub"],
                         text="1. Claude'a notunu yazıp 'blok' iste.\n"
                              "2. Gelen bloğu kopyala.\n"
                              "3. 'Çağrıyı Tamamla' ekranı açıkken aşağıdaki butona bas.").pack(anchor="w", pady=(8, 0))
            self.note = None
            btn_metni = "Panodan yapıştır ve doldur"
            komut = self.panodan_doldur
        else:
            kutu = ctk.CTkFrame(ic, fg_color="transparent")
            kutu.pack(fill="both", expand=True)
            self.note = ctk.CTkTextbox(kutu, wrap="word", font=_f(13), fg_color=t["input"], text_color=t["text"],
                                       border_width=1, border_color=t["border"], corner_radius=12)
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
            btn_metni = "✦  AI yorumla ve doldur"
            komut = self.ai_ile_doldur

        self.btn = ctk.CTkButton(govde, text=btn_metni, height=46, corner_radius=12, font=_f(14, True),
                                 fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                                 command=komut)
        self.btn.pack(fill="x", pady=(12, 0))

        # --- durum
        durum = ctk.CTkFrame(govde, fg_color="transparent")
        durum.pack(fill="x", pady=(8, 0))
        self.nokta = ctk.CTkLabel(durum, text="●", font=_f(12), text_color=t["sub"], width=14)
        self.nokta.pack(side="left")
        self.durum = ctk.CTkLabel(durum, text="", font=_f(12), text_color=t["sub"], anchor="w", justify="left",
                                  wraplength=460)
        self.durum.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(durum, text="" if kopyala else "Ctrl + Enter", font=_f(11), text_color=t["sub"]).pack(side="right")
        self._durum_varsayilan()

        # --- alt bilgi
        ctk.CTkLabel(self.root, text=TELIF, font=_f(10), text_color=t["sub"]).pack(side="bottom", pady=(0, 8))

        if self.note is not None:
            self.root.after(50, self.note.focus_set)

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
        s = self.cfg.get("saglayici")
        if s == "gemini":
            return "Gemini · " + ("Hızlı" if self.cfg.get("gemini_hiz") == "hizli" else "Dengeli")
        return SERVIS_ADLARI.get(s, "")

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
        t = self.t
        renk = {"ok": t["ok"], "err": t["err"], "is": t["warn"]}.get(tur, t["sub"])
        self.nokta.configure(text_color=renk)
        self.durum.configure(text=metin, text_color=t["text"] if tur in ("ok", "err") else t["sub"])

    def _durum_varsayilan(self):
        s = self.cfg.get("saglayici")
        if s == "gemini" and not self.cfg.get("gemini_key"):
            self.durum_yaz("Başlamak için ⚙ Ayarlar > API ve yönetici ayarları'ndan Gemini anahtarını gir.", "is")
        elif s == "anthropic" and not self.cfg.get("api_key"):
            self.durum_yaz("Başlamak için ⚙ Ayarlar > API ve yönetici ayarları'ndan Claude anahtarını gir.", "is")
        elif s == "kopyala":
            self.durum_yaz("Hazır. 'Çağrıyı Tamamla' ekranını aç, bloğu kopyalayıp butona bas.")
        else:
            self.durum_yaz("Hazır. 'Çağrıyı Tamamla' ekranını aç, notunu yaz.")

    def _mesgul(self, var):
        self.mesgul = var
        self.btn.configure(state="disabled" if var else "normal")

    # ------------------------------------------------------------ açılış
    def _acilis_isleri(self):
        filler.hazirla()  # ekran otomasyonunu önceden kur: ilk doldurma hızlanır
        threading.Thread(target=ai.isit, args=(self.cfg,), daemon=True).start()
        self.guncelleme_kontrol(sessiz=True)

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
        if info and ((sessiz and yeni) or bitince):
            self.root.after(400, self.guncelleme_sor)  # kullanıcıya "güncellensin mi?" diye sor
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
        s = self.cfg.get("saglayici")
        if (s == "gemini" and not self.cfg.get("gemini_key")) or (s == "anthropic" and not self.cfg.get("api_key")):
            self.durum_yaz("API anahtarı girilmemiş: ⚙ Ayarlar > API ve yönetici ayarları.", "is")
            return
        self._mesgul(True)
        self.durum_yaz("AI yorumluyor…", "is")
        t0 = time.perf_counter()

        def is_():
            try:
                vals, sure = ai.yorumla(self.cfg, notu)
                self.root.after(0, lambda: self._ekrana(vals, sure, t0, temizle=True))
            except Exception as e:
                msg = str(e)
                self.root.after(0, lambda: (self._mesgul(False), self.durum_yaz(msg, "err")))

        threading.Thread(target=is_, daemon=True).start()

    def panodan_doldur(self):
        if self.mesgul:
            return
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            text = ""
        vals = ai.metinden_alanlar(text)
        if not vals:
            self.durum_yaz("Panoda doldurulacak blok yok. Önce Claude'daki bloğu kopyala.", "is")
            return
        self._mesgul(True)
        self._ekrana(vals, None, time.perf_counter(), temizle=False)

    def _ekrana(self, vals, ai_sure, t0, temizle):
        self.durum_yaz("Çağrı ekranı dolduruluyor…", "is")
        self.root.update_idletasks()
        t1 = time.perf_counter()
        try:
            filler.doldur(self.cfg["pencere_basligi"], vals)
        except Exception as e:
            self._mesgul(False)
            self.durum_yaz(str(e), "err")
            return
        ekran = time.perf_counter() - t1
        self._mesgul(False)
        if temizle and self.note is not None:
            self.note.delete("1.0", "end")
            self._ipucu_guncelle()
        sure = f"AI {ai_sure:.1f} sn · ekran {ekran:.1f} sn" if ai_sure is not None else f"{ekran:.1f} sn"
        self.durum_yaz(f"Dolduruldu ({sure}). Kontrol edip kapatabilirsin.", "ok")

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

    def __init__(self, app, baslik, boyut, ebeveyn=None, kaydir=True):
        self.app = app
        self.t = t = app.t
        w = self.w = ctk.CTkToplevel(ebeveyn or app.root)
        w.title(baslik)
        w.geometry(boyut)
        w.configure(fg_color=t["bg"])
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
    """Herkesin girebildiği ayarlar. API anahtarları ayrı, şifreli bölümde."""

    def __init__(self, app):
        super().__init__(app, "Ayarlar", "460x600")
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

        self.bolum("Form varsayılanları")
        self.ucret = self.giris("Ücret metni (notta ücret geçmezse)", cfg["varsayilan_ucret"])
        self.kayit = self.giris("'Kayıt no bildirildi' cevabı", cfg["varsayilan_kayit"])

        self.bolum("Güncelleme")
        satir = ctk.CTkFrame(self.alan, fg_color="transparent")
        satir.pack(fill="x", padx=6, pady=(0, 6))
        self.ikincil_buton(satir, "Şimdi kontrol et", self.kontrol_et, width=130).pack(side="left")
        self.kontrol_sonuc = ctk.CTkLabel(satir, text=f"Sürüm {kisa_surum()}", font=_f(11), text_color=t["sub"])
        self.kontrol_sonuc.pack(side="left", padx=10)

        self.bolum("Yetkili")
        kilit = "🔒  API ve yönetici ayarları"
        self.ikincil_buton(self.alan, kilit, self.yonetici_ac, height=40, anchor="w").pack(fill="x", padx=6, pady=(2, 4))
        self.aciklama("Yapay zekâ servisi, API anahtarları, güncelleme kaynağı. Yetkili şifresi ister.")

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
        c["varsayilan_ucret"] = self.ucret.get().strip() or config.VARSAYILAN["varsayilan_ucret"]
        c["varsayilan_kayit"] = self.kayit.get().strip() or "Hayır"
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
    """Şifreyle açılan bölüm: yapay zekâ servisi, anahtarlar, güncelleme kaynağı, şifre değiştirme."""

    def __init__(self, app, ebeveyn):
        super().__init__(app, "API ve yönetici ayarları", "460x640", ebeveyn)
        cfg = app.cfg

        self.bolum("Yapay zekâ")
        self._ters = {v: k for k, v in SERVIS_ADLARI.items()}
        self.servis = ctk.StringVar(value=SERVIS_ADLARI[cfg["saglayici"]])
        self.segment(list(SERVIS_ADLARI.values()), self.servis)
        self.gemini_key = self.giris("Gemini anahtarı (aistudio.google.com → Get API key)", cfg["gemini_key"], gizli=True)
        self.etiket("Gemini hızı")
        self.hiz = ctk.StringVar(value="Hızlı" if cfg.get("gemini_hiz") == "hizli" else "Dengeli")
        self.segment(["Hızlı", "Dengeli"], self.hiz)
        self.aciklama("Hızlı: Flash-Lite, en çabuk cevap. Dengeli: Flash, daha iyi yorum.")
        self.api_key = self.giris("Claude API anahtarı (varsa)", cfg["api_key"], gizli=True)
        self.aciklama("Anahtarlar bu bilgisayarda Windows şifrelemesiyle saklanır; dosya kopyalansa da okunamaz.")

        self.bolum("Sistem")
        self.baslik = self.giris("Çağrı ekranının pencere başlığı", cfg["pencere_basligi"])
        self.repo = self.giris("Güncelleme kaynağı (GitHub kullanıcı/repo)", cfg.get("guncelleme_repo", ""))

        self.bolum("Yetkili şifresini değiştir")
        self.y1 = self.giris("Yeni şifre (boş bırakırsan değişmez)", gizli=True)
        self.y2 = self.giris("Yeni şifre (tekrar)", gizli=True)
        self.hata = ctk.CTkLabel(self.alan, text="", font=_f(11), text_color=self.t["err"])
        self.hata.pack(anchor="w", padx=6)

        self.ana_buton("Kaydet", self.kaydet)

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
        c["saglayici"] = self._ters.get(self.servis.get(), "gemini")
        c["gemini_key"] = self.gemini_key.get().strip()
        c["gemini_hiz"] = "hizli" if self.hiz.get() == "Hızlı" else "dengeli"
        c["api_key"] = self.api_key.get().strip()
        c["pencere_basligi"] = self.baslik.get().strip() or "Çağrıyı Tamamla"
        c["guncelleme_repo"] = self.repo.get().strip()
        if y1:
            c["yetkili_sifre"] = guvenlik.sifre_ozeti(y1)
        self.w.destroy()
        self.app.ayarlar_kaydedildi("API ayarları kaydedildi.")


class GuncellemePenceresi(_Pencere):
    """'Sunucuda yeni sürüm var, güncellensin mi?' penceresi; indirme ilerlemesini de gösterir."""

    SARMA = 360

    def __init__(self, app, info):
        super().__init__(app, "Güncelleme", "420x300", kaydir=False)
        self.info = info
        t = self.t
        ctk.CTkLabel(self.alan, text="Yeni sürüm hazır", font=_f(16, True), text_color=t["text"]).pack(anchor="w", padx=6)
        ctk.CTkLabel(self.alan, text=f"Sunucuda v{info['version']} var, sen {kisa_surum()} kullanıyorsun.\n"
                                     "Şimdi güncellensin mi?", font=_f(12), text_color=t["text"],
                     justify="left").pack(anchor="w", padx=6, pady=(6, 4))
        notlar = (info.get("notes") or "").strip()
        if notlar:
            self.aciklama(notlar[:280] + ("…" if len(notlar) > 280 else ""))
        self.aciklama("Ayarların, şifren ve API anahtarların korunur. Uygulama kapanıp yeni sürümle açılır.")
        self.cubuk = ctk.CTkProgressBar(self.alan, progress_color=t["accent"], fg_color=t["input"], height=8)
        self.durum = ctk.CTkLabel(self.alan, text="", font=_f(11), text_color=t["sub"])

        alt = ctk.CTkFrame(self.w, fg_color="transparent")
        alt.pack(fill="x", padx=16, pady=12)
        self.sonra_btn = self.ikincil_buton(alt, "Sonra", self.w.destroy, width=110, height=40)
        self.sonra_btn.pack(side="left")
        self.evet_btn = ctk.CTkButton(alt, text="Şimdi güncelle", height=40, corner_radius=12, font=_f(14, True),
                                      fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["on_accent"],
                                      command=self.baslat)
        self.evet_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

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
                kapat = updater.uygula(self.info, ilerleme)
            except Exception as e:
                msg = str(e)
                app.root.after(0, lambda: self._hata(msg))
                return
            if kapat:
                app.root.after(0, lambda: (self.durum.configure(text="Yeni sürüm açılıyor…"),
                                           app.root.after(400, app.root.destroy)))
            else:
                app.root.after(0, self.w.destroy)

        threading.Thread(target=is_, daemon=True).start()

    def _hata(self, msg):
        if not self.w.winfo_exists():
            return
        self.durum.configure(text=f"Güncelleme olmadı: {msg}", text_color=self.t["err"])
        self.evet_btn.configure(state="normal", text="Tekrar dene")
        self.sonra_btn.configure(state="normal")
