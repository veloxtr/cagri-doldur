# -*- coding: utf-8 -*-
"""Çağrı Doldur - giriş noktası."""
import sys
import time

BASLANGIC = time.perf_counter()
sys.coinit_flags = 2  # COM (ekran otomasyonu): tek thread (STA), tkinter ile uyumlu


def _splash_kapat():
    """Exe açılırken gösterilen açılış ekranını kapatır. Kaynak koddan çalışırken açılış ekranı yoktur."""
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


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
    app.root.after(0, _splash_kapat)
    app.calistir()


if __name__ == "__main__":
    main()
