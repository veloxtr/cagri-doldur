# -*- coding: utf-8 -*-
"""Online güncelleme: GitHub Releases'tan son sürümü kontrol eder, exe'yi indirip kendini değiştirir."""
import base64
import os
import re
import subprocess
import sys
import tempfile
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
    return {"version": yeni, "url": asset.get("browser_download_url") if asset else None,
            "page": d.get("html_url"), "notes": d.get("body") or ""}


def _ps_tirnak(s):
    return "'" + s.replace("'", "''") + "'"


def uygula(info, ilerleme=None):
    """Exe ise indirir, kapanınca eskisinin yerine koyup yeniden başlatır. True dönerse uygulama kapanmalı."""
    if not paths.FROZEN or not info.get("url"):
        webbrowser.open(info.get("page") or "https://github.com")
        return False
    exe = sys.executable
    yeni = os.path.join(tempfile.gettempdir(), "CagriDoldur_yeni.exe")
    net.indir(info["url"], yeni, ilerleme)
    if os.path.getsize(yeni) < 1_000_000:
        raise RuntimeError("İndirilen dosya eksik görünüyor, güncelleme iptal edildi.")
    betik = (
        f"$p={os.getpid()}; "
        "while (Get-Process -Id $p -ErrorAction SilentlyContinue) { Start-Sleep -Milliseconds 300 }; "
        "Start-Sleep -Milliseconds 500; "
        f"Move-Item -Force -LiteralPath {_ps_tirnak(yeni)} -Destination {_ps_tirnak(exe)}; "
        f"Start-Process -FilePath {_ps_tirnak(exe)}"
    )
    kodlu = base64.b64encode(betik.encode("utf-16-le")).decode("ascii")
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
         "-EncodedCommand", kodlu],
        creationflags=0x08000000 | 0x00000008,  # CREATE_NO_WINDOW | DETACHED_PROCESS
        close_fds=True,
    )
    return True
