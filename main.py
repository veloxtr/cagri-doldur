# -*- coding: utf-8 -*-
"""Çağrı Doldur - giriş noktası."""
import sys
import time

BASLANGIC = time.perf_counter()
sys.coinit_flags = 2  # COM (ekran otomasyonu): tek thread (STA), tkinter ile uyumlu


def main():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EYK.CagriDoldur")  # görev çubuğunda kendi ikonu
    except Exception:
        pass
    from cagri.ui import App

    guncellendi = None
    if "--guncellendi" in sys.argv:
        i = sys.argv.index("--guncellendi")
        guncellendi = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
    app = App(guncellendi_eski=guncellendi, baslangic=BASLANGIC)
    app.calistir()


if __name__ == "__main__":
    main()
