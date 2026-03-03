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
SETTINGS_ICON_PATH = RESOURCE_DIR / "icons" / "settings_icon.png"
CASH_ICON_PATH = RESOURCE_DIR / "icons" / "cash_icon.png"
VIEV_ICON_PATH = RESOURCE_DIR / "icons" / "view_icon.png"
MODULS_ICON_PATH = RESOURCE_DIR / "icons" / "moduls_icon.png"
FOLDER_ICON_PATH = RESOURCE_DIR / "icons" / "folder_icon.png"
SEARCH_ICON_PATH = RESOURCE_DIR / "icons" / "search_icon.png"
DELETE_ICON_PATH = RESOURCE_DIR / "icons" / "delete_icon.png"
NOTE_ICON_PATH = RESOURCE_DIR / "icons" / "note_icon.png"
NEW_PROXY_ICON_PATH = RESOURCE_DIR / "icons" / "new_proxy_icon.png"
DEVICE_ICON_PATH = RESOURCE_DIR / "icons" / "device_icon.png"
START_ICON_PATH = RESOURCE_DIR / "icons" / "start_icon.png"
SOUND_PATH = RESOURCE_DIR / "sounds" / "Nuya.mp3"
FONTS_DIR = RESOURCE_DIR / "fonts"

