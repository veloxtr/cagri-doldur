# -*- coding: utf-8 -*-
"""Exe derler: python build.py  ->  dist/CagriDoldur.exe
Hem bilgisayarda (exe_yap.bat) hem GitHub'da otomatik derlemede aynı ayarlar kullanılır."""
import os

# Ekran otomasyonu arayüzlerini derlemeden önce üret; exe içine hazır girsin.
import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")

import PyInstaller.__main__  # noqa: E402

GEREKSIZ = [
    "PIL", "numpy", "unittest", "pydoc", "doctest", "pdb", "test", "lib2to3", "xmlrpc",
    "sqlite3", "multiprocessing", "concurrent", "asyncio", "distutils", "setuptools", "pip",
    "tkinter.test", "turtle", "turtledemo", "idlelib", "curses", "lzma", "bz2",
    "pywinauto", "win32com", "pythoncom", "pywintypes", "requests", "urllib3",
]

PyInstaller.__main__.run([
    "main.py",
    "--name=CagriDoldur",
    "--onefile",
    "--noconsole",
    "--noconfirm",
    "--clean",
    "--icon=assets/icon.ico",
    f"--add-data=assets{os.pathsep}assets",
    "--collect-data=customtkinter",
    "--hidden-import=comtypes.gen.UIAutomationClient",
    "--collect-submodules=comtypes.gen",
    *[f"--exclude-module={m}" for m in GEREKSIZ],
])
