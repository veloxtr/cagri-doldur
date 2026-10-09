# -*- mode: python ; coding: utf-8 -*-
# Exe derleme tarifi. Çalıştırma: python build.py
import re

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SURUM = re.search(r'^VERSION = "(.+)"', open("cagri/version.py", encoding="utf-8").read(), re.M).group(1)

GEREKSIZ = [
    "PIL", "numpy", "unittest", "pydoc", "doctest", "pdb", "test", "lib2to3", "xmlrpc",
    "sqlite3", "multiprocessing", "concurrent", "asyncio", "distutils", "setuptools", "pip",
    "tkinter.test", "turtle", "turtledemo", "idlelib", "curses", "lzma", "bz2",
    "pywinauto", "win32com", "pythoncom", "pywintypes", "requests", "urllib3",
]

a = Analysis(
    ["main.py"],
    datas=[("assets", "assets")] + collect_data_files("customtkinter"),
    hiddenimports=["comtypes.gen.UIAutomationClient"] + collect_submodules("comtypes.gen"),
    excludes=GEREKSIZ,
    optimize=1,
)

# Açılışı yavaşlatan, hiç kullanılmayan Tcl/Tk dosyaları: saat dilimleri, diller, örnek resimler.
# Tek dosyalık exe her açılışta içindekileri açar ve antivirüs hepsini tarar; dosya sayısı azaldıkça hızlanır.
def gerekli(hedef):
    h = hedef.replace("\\", "/")
    return not ("/tzdata/" in h or "/msgs/" in h or h.startswith("_tk_data/images/")
                or h.startswith("_tk_data/demos/") or "/tcltest" in h)

once = len(a.datas)
a.datas = [x for x in a.datas if gerekli(x[0])]
print(f"[CagriDoldur] veri dosyası: {once} -> {len(a.datas)}")

pyz = PYZ(a.pure)

splash = Splash(
    "assets/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(16, 218),
    text_size=9,
    text_color="#8B91A3",
    text_default=f"v{SURUM}",
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    a.binaries,
    a.datas,
    [],
    name="CagriDoldur",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icon.ico",
)
