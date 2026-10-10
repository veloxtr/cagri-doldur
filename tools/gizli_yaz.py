# -*- coding: utf-8 -*-
"""Derleme sırasında çalışır: GitHub gizli anahtarlarından (BA_PROXY_URL / BA_PROXY_TOKEN)
cagri/dagitim.py içindeki boş değerleri doldurur. Gizli değerler depoya yazılmaz."""
import os
import pathlib
import sys

url = (os.environ.get("BA_PROXY_URL") or "").strip()
jeton = (os.environ.get("BA_PROXY_TOKEN") or "").strip()
if not url or not jeton:
    sys.exit("BA_PROXY_URL / BA_PROXY_TOKEN gizli anahtarları tanımlı değil "
             "(repo Settings > Secrets and variables > Actions).")
if '"' in url or '"' in jeton:
    sys.exit("Proxy değerleri çift tırnak içeremez.")

yol = pathlib.Path("cagri/dagitim.py")
metin = yol.read_text(encoding="utf-8")
metin = metin.replace('PROXY_URL = ""', 'PROXY_URL = "%s"' % url, 1)
metin = metin.replace('PROXY_TOKEN = ""', 'PROXY_TOKEN = "%s"' % jeton, 1)
yol.write_text(metin, encoding="utf-8")
print("dagitim.py gizli anahtarlarla dolduruldu (uzunluklar: url=%d, token=%d)." % (len(url), len(jeton)))
