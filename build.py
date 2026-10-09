# -*- coding: utf-8 -*-
"""Exe derler: python build.py  ->  dist/BilnexAssist.exe
Hem bilgisayarda (exe_yap.bat) hem GitHub'da otomatik derlemede aynı tarif (BilnexAssist.spec) kullanılır."""
# Ekran otomasyonu arayüz tanımlarını derlemeden önce üret; exe içine hazır girsin (açılışta üretilmesin).
import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")

import PyInstaller.__main__  # noqa: E402

PyInstaller.__main__.run(["BilnexAssist.spec", "--noconfirm", "--clean"])
