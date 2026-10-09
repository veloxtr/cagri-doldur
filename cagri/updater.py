# -*- coding: utf-8 -*-
"""Online güncelleme: GitHub Releases'tan son sürümü kontrol eder, exe'yi indirip kendini değiştirir.

Yöntem: Windows çalışan bir exe'nin YENİDEN ADLANDIRILMASINA izin verir. Bu yüzden
  CagriDoldur.exe      -> CagriDoldur.exe.eski   (çalışan dosya kenara alınır)
  CagriDoldur.exe.yeni -> CagriDoldur.exe        (yeni sürüm yerine konur)
yapılır, yeni exe başlatılır ve bu süreç kapanır. Harici betik (PowerShell vb.) kullanılmaz;
antivirüslerin engellemesine takılmaz. '.eski' dosya bir sonraki açılışta silinir.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import webbrowser

from . import net, paths


def surum_tuple(v):
    sayilar = [int(x) for x in re.findall(r"\d+", v or "")[:3]]
    return tuple(sayilar + [0] * (3 - len(sayilar)))


def kontrol(repo, mevcut):
    """Yeni sürüm varsa {'version','url','page','notes'} döndürür, yoksa None."""
    repo = (repo or "").strip().strip("/")
    if repo.startswith("https://github.com/"):
        repo = repo[len("https://github.com/"):]
    if repo.count("/") != 1:
        return None
    try:
        d = net.get_json(f"https://api.github.com/repos/{repo}/releases/latest")
    except Exception as e:
        if "404" in str(e):
            return None  # henüz yayınlanmış sürüm yok
        raise
    yeni = (d.get("tag_name") or "").lstrip("vV")
    if not yeni or surum_tuple(yeni) <= surum_tuple(mevcut):
        return None
    asset = next((a for a in d.get("assets", []) if a.get("name", "").lower().endswith(".exe")), None)
    notlar = (d.get("body") or "").split("<!-- test -->")[0].strip()
    return {"version": yeni, "url": asset.get("browser_download_url") if asset else None,
            "page": d.get("html_url"), "notes": notlar}


def _temiz_ortam():
    """PyInstaller'ın bu sürece ait değişkenlerini yeni sürece geçirme; yeni exe kendi
    geçici klasörünü açsın (aksi halde silinmekte olan eski klasörü kullanmaya çalışıp kapanır)."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("_PYI") or k.startswith("_MEI") or k == "_MEIPASS2")}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def yeniden_baslat(exe, *arguman):
    subprocess.Popen(
        [exe, *arguman],
        cwd=os.path.dirname(exe),
        env=_temiz_ortam(),
        creationflags=0x00000008 | 0x00000200,  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        close_fds=True,
    )


def eskileri_temizle():
    """Önceki güncellemeden kalan .eski / .yeni dosyaları siler (kilitliyse sonra tekrar denenir)."""
    if not paths.FROZEN:
        return True
    hepsi_silindi = True
    for f in glob.glob(sys.executable + ".eski*") + glob.glob(sys.executable + ".yeni"):
        try:
            os.remove(f)
        except OSError:
            hepsi_silindi = False
    return hepsi_silindi


def uygula(info, ilerleme=None, eski_surum=""):
    """Exe ise indirir, yerine koyar ve yeni sürümü başlatır. True dönerse uygulama kapanmalı."""
    if not paths.FROZEN or not info.get("url"):
        webbrowser.open(info.get("page") or "https://github.com")
        return False
    exe = sys.executable
    yeni = exe + ".yeni"
    try:
        test_kaynagi = os.environ.get("CAGRI_UPDATE_TEST")
        if test_kaynagi:
            shutil.copyfile(test_kaynagi, yeni)  # GitHub'daki otomatik test: indirme yerine yerel kopya
        else:
            net.indir(info["url"], yeni, ilerleme)
    except PermissionError:
        raise RuntimeError("Exe'nin bulunduğu klasöre yazılamıyor. Exe'yi Masaüstü veya Belgeler "
                           "gibi bir klasöre taşıyıp tekrar dene.")
    if os.path.getsize(yeni) < 1_000_000:
        os.remove(yeni)
        raise RuntimeError("İndirilen dosya eksik görünüyor, güncelleme iptal edildi.")

    eski = exe + ".eski"
    if os.path.exists(eski):
        try:
            os.remove(eski)
        except OSError:
            n = 2
            while os.path.exists(f"{exe}.eski{n}"):
                n += 1
            eski = f"{exe}.eski{n}"
    os.rename(exe, eski)          # çalışan exe kenara alınır
    try:
        os.rename(yeni, exe)      # yeni sürüm yerine konur
    except OSError:
        os.rename(eski, exe)      # geri al
        raise
    yeniden_baslat(exe, "--guncellendi", eski_surum)
    return True
