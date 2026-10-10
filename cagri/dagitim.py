# -*- coding: utf-8 -*-
"""Dağıtım ayarları: AI isteklerinin gittiği proxy (Cloudflare Worker).

Bu dosya GitHub'da BOŞ durur; gerçek değerler derleme sırasında GitHub Actions
tarafından gizli anahtarlardan (BA_PROXY_URL / BA_PROXY_TOKEN) yazılır.
Böylece worker adresi ve uygulama jetonu açık depoda görünmez.

Geliştirirken kendi değerini ortam değişkeniyle verebilirsin:
    BA_PROXY_URL=... BA_PROXY_TOKEN=... python main.py
"""
import os

# Derleme sırasında doldurulur; boşsa ortam değişkenine düşer.
PROXY_URL = ""
PROXY_TOKEN = ""


def proxy_url():
    return (PROXY_URL or os.environ.get("BA_PROXY_URL", "")).strip().rstrip("/")


def proxy_token():
    return (PROXY_TOKEN or os.environ.get("BA_PROXY_TOKEN", "")).strip()


def hazir():
    """Proxy adresi ve jetonu tanımlıysa True."""
    return bool(proxy_url() and proxy_token())
