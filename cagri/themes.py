# -*- coding: utf-8 -*-
"""Temalar. Yeni tema eklemek için TEMALAR'a bir sözlük eklemek yeterli."""

TEMALAR = {
    "koyu": {
        "ad": "Koyu", "mod": "dark",
        "bg": "#0E1016", "card": "#171A23", "input": "#10131A", "border": "#272C3A",
        "text": "#ECEEF4", "sub": "#8B91A3", "accent": "#7C5CFF", "accent_hover": "#6A48F0",
        "on_accent": "#FFFFFF", "chip": "#231F3D", "chip_text": "#B9A8FF",
        "ok": "#34D399", "err": "#F87171", "warn": "#FBBF24",
    },
    "pembe": {
        "ad": "Pembe", "mod": "light",
        "bg": "#FFF0F6", "card": "#FFFFFF", "input": "#FFF7FA", "border": "#F7C3D9",
        "text": "#3A0F28", "sub": "#9A5A7A", "accent": "#EC4899", "accent_hover": "#DB2777",
        "on_accent": "#FFFFFF", "chip": "#FCE3EF", "chip_text": "#BE185D",
        "ok": "#059669", "err": "#DC2626", "warn": "#D97706",
    },
    "pembe_gece": {
        "ad": "Pembe Gece", "mod": "dark",
        "bg": "#160A11", "card": "#22101B", "input": "#1A0C15", "border": "#41203A",
        "text": "#FCE7F3", "sub": "#C48AAC", "accent": "#F472B6", "accent_hover": "#EC4899",
        "on_accent": "#2A0A1C", "chip": "#3A1430", "chip_text": "#F9A8D4",
        "ok": "#34D399", "err": "#FB7185", "warn": "#FBBF24",
    },
    "gece_mavisi": {
        "ad": "Gece Mavisi", "mod": "dark",
        "bg": "#0A1322", "card": "#111E35", "input": "#0D182B", "border": "#22365A",
        "text": "#E6EEFF", "sub": "#8AA0C6", "accent": "#38BDF8", "accent_hover": "#0EA5E9",
        "on_accent": "#04233A", "chip": "#0F2D4A", "chip_text": "#7DD3FC",
        "ok": "#34D399", "err": "#F87171", "warn": "#FBBF24",
    },
    "acik": {
        "ad": "Açık", "mod": "light",
        "bg": "#F3F4F8", "card": "#FFFFFF", "input": "#F8F9FB", "border": "#E1E4EC",
        "text": "#1A1E29", "sub": "#6B7280", "accent": "#4F46E5", "accent_hover": "#4338CA",
        "on_accent": "#FFFFFF", "chip": "#EEF0FF", "chip_text": "#4338CA",
        "ok": "#059669", "err": "#DC2626", "warn": "#D97706",
    },
}


def al(ad):
    return TEMALAR.get(ad) or TEMALAR["koyu"]


def ad_listesi():
    return [t["ad"] for t in TEMALAR.values()]


def anahtar(gorunen_ad):
    for k, t in TEMALAR.items():
        if t["ad"] == gorunen_ad:
            return k
    return "koyu"
