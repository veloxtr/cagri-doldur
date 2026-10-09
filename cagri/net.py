# -*- coding: utf-8 -*-
"""Hafif HTTP katmanı (Python'un yerleşik modülleriyle; requests gerekmez).
Bağlantılar açık tutulur, böylece ardışık isteklerde TLS el sıkışması tekrarlanmaz.
Windows sertifika deposu ve sistem proxy ayarı kullanılır."""
import http.client
import json
import ssl
import threading
import urllib.parse
import urllib.request

from .version import APP_ID, VERSION

_CTX = ssl.create_default_context()
_HAVUZ = {}
_KILIT = threading.Lock()
_UA = f"{APP_ID}/{VERSION}"


def _baglanti(host, timeout):
    proxy = urllib.request.getproxies().get("https")
    if proxy and not urllib.request.proxy_bypass(host):
        p = urllib.parse.urlsplit(proxy if "://" in proxy else "http://" + proxy)
        c = http.client.HTTPSConnection(p.hostname, p.port or 8080, timeout=timeout, context=_CTX)
        c.set_tunnel(host, 443)
        return c
    return http.client.HTTPSConnection(host, 443, timeout=timeout, context=_CTX)


def istek(method, url, headers=None, govde=None, timeout=60):
    """(durum_kodu, metin) döndürür. Ağ hatalarında OSError fırlatır."""
    u = urllib.parse.urlsplit(url)
    yol = u.path + ("?" + u.query if u.query else "")
    veri = json.dumps(govde).encode("utf-8") if govde is not None else None
    h = {"User-Agent": _UA, "Accept-Encoding": "identity"}
    if veri is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    for deneme in range(2):
        with _KILIT:
            c = _HAVUZ.pop(u.hostname, None)
        yeni = c is None
        if yeni:
            c = _baglanti(u.hostname, timeout)
        try:
            c.timeout = timeout
            if c.sock is not None:
                c.sock.settimeout(timeout)
            c.request(method, yol, body=veri, headers=h)
            r = c.getresponse()
            icerik = r.read()
        except TimeoutError:
            c.close()
            raise
        except (http.client.HTTPException, OSError):
            c.close()
            if deneme == 0 and not yeni:
                continue  # eski bağlantı kopmuş, yenisiyle bir kez daha dene
            raise
        if (r.getheader("Connection") or "").lower() == "close":
            c.close()
        else:
            with _KILIT:
                _HAVUZ[u.hostname] = c
        return r.status, icerik.decode("utf-8", "replace")
    raise OSError("Bağlantı kurulamadı")


def isit(host):
    """Bağlantıyı önceden açıp havuza koyar."""
    try:
        with _KILIT:
            if host in _HAVUZ:
                return
        c = _baglanti(host, 8)
        c.connect()
        with _KILIT:
            _HAVUZ.setdefault(host, c)
    except Exception:
        pass


def get_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def indir(url, hedef, ilerleme=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r, open(hedef, "wb") as f:
        toplam = int(r.headers.get("Content-Length") or 0)
        inen = 0
        while True:
            parca = r.read(256 * 1024)
            if not parca:
                break
            f.write(parca)
            inen += len(parca)
            if ilerleme and toplam:
                ilerleme(inen / toplam)
