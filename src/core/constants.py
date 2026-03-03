import os
from pathlib import Path

"""
Глобальные константы и пути проекта.
Определяет:

- BASE_DIR: корневая директория проекта
- CONFIG_FILE: путь к файлу конфигурации JSON
- RESOURCE_DIR: путь к ресурсам (иконки, звуки, шрифты) с поддержкой системных путей
- ICON_PATHр, SOUND_PATH, FONTS_DIR: пямые пути к медиа-ресурсам
"""

BASE_DIR = Path(__file__).parent.parent.parent.absolute()

CONFIG_DIR = BASE_DIR
CONFIG_FILE = BASE_DIR / "config.json"

SYSTEM_RESOURCE_DIR = Path("/usr/share/shadowgram/resources")
LOCAL_RESOURCE_DIR = BASE_DIR / "resources"

if LOCAL_RESOURCE_DIR.exists():
    RESOURCE_DIR = LOCAL_RESOURCE_DIR
else:
    RESOURCE_DIR = SYSTEM_RESOURCE_DIR

ICON_PATH = RESOURCE_DIR / "icons" / "GrobTyanka.png"
LOGO_PATH = RESOURCE_DIR / "icons" / "GrobTyan_logo.png"
SUCCESS_ICON_PATH = RESOURCE_DIR / "icons" / "succure_icon.png"
CANCEL_ICON_PATH = RESOURCE_DIR / "icons" / "cancel_icon.png"
PROXY_ICON_PATH = RESOURCE_DIR / "icons" / "proxy_icon.png"
SOUND_PATH = RESOURCE_DIR / "sounds" / "Nuya.mp3"
FONTS_DIR = RESOURCE_DIR / "fonts"
