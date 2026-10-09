# -*- coding: utf-8 -*-
"""Çağrı Doldur - giriş noktası."""
import sys

sys.coinit_flags = 2  # COM (ekran otomasyonu): tek thread (STA), tkinter ile uyumlu


def main():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EYK.CagriDoldur")  # görev çubuğunda kendi ikonu
    except Exception:
        pass
    from cagri.ui import App
    App().calistir()


if __name__ == "__main__":
    main()
