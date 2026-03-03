import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
from src.ui.main_window import TelegramManager
from src import styles
from src.core.constants import CONFIG_FILE, CONFIG_DIR, FONTS_DIR
from PyQt6.QtCore import QObject, QEvent, Qt

"""
Точка входа в приложение ShadowGram.
Функции:

- load_fonts: загрузка кастомных шрифтов из директории ресурсов
- init_config: инициализация базового файла конфигурации при первом запуске
- ShiftScrollFilter: поддержка горизонтального скролла через Shift + Wheel
- Основной блок: настройка QApplication, стилей и запуск главного окна
"""

class ShiftScrollFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Ищем ближайший родительский виджет, у которого есть горизонтальный скроллбар
                target = obj
                while target:
                    if hasattr(target, "horizontalScrollBar"):
                        bar = target.horizontalScrollBar()
                        if bar.maximum() > 0: # Если скроллбар активен
                            delta = event.angleDelta().y()
                            bar.setValue(bar.value() - delta)
                            return True
                    target = target.parent()
        return super().eventFilter(obj, event)

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

def load_fonts():
    if FONTS_DIR.exists():
        for font_file in os.listdir(FONTS_DIR):
            if font_file.endswith((".ttf", ".otf")):
                path = str(FONTS_DIR / font_file)
                font_id = QFontDatabase.addApplicationFont(path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"[DEBUG] Loaded font: {font_file} as families: {families}")

def init_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "settings": {"api_id": 0, "api_hash": ""},
            "accounts": []
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)

if __name__ == "__main__":
    init_config()
    app = QApplication(sys.argv)
    
    # Включаем горизонтальный скролл через Shift
    scroll_filter = ShiftScrollFilter()
    app.installEventFilter(scroll_filter)
    
    load_fonts()
    app.setStyleSheet(styles.STYLESHEET)
    window = TelegramManager()
    window.show()
    sys.exit(app.exec())
