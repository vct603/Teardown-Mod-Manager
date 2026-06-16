import os
import sys
import logging
import customtkinter as ctk

__version__ = "v1.2.0"

# ── 日誌設定：寫入 exe 同目錄下的 log 檔 ──
def get_log_path():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "teardown_mod_manager.log")

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)
log = logging.getLogger("TDModManager")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

THEME = {
    "bg": "#1a1a1a",
    "surface": "#242424",
    "surface_alt": "#303030",
    "card": "#2a2a2a",
    "card_border": "#444444",
    "text": "#f2f2f2",
    "muted": "#b8b8b8",
    "subtle": "#8a8a8a",
    "accent": "#f2f2f2",
    "accent_hover": "#ffffff",
    "accent_dark": "#d0d0d0",
    "danger": "#5c5c5c",
    "danger_hover": "#707070",
    "track": "#3a3a3a",
}

def button_colors(kind="primary"):
    if kind == "danger":
        return {
            "fg_color": THEME["danger"],
            "hover_color": THEME["danger_hover"],
            "text_color": THEME["text"],
        }
    if kind == "secondary":
        return {
            "fg_color": THEME["surface_alt"],
            "hover_color": THEME["card_border"],
            "border_width": 1,
            "border_color": THEME["card_border"],
            "text_color": THEME["text"],
        }
    return {
        "fg_color": THEME["accent"],
        "hover_color": THEME["accent_hover"],
        "text_color": "#111111",
    }
