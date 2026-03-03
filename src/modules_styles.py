"""
Стили (QSS) для окна модулей автоматизации.
Определяет:

- Темную неоновую тему терминала
- Стили для выпадающих списков и кнопок запуска
- Кастомизацию чекбоксов выбора аккаунтов
"""

from src.styles import FONT_NAME

MODULES_STYLESHEET = f"""
/* Основное окно модулей */
QWidget {{
    background-color: #0d110d;
    color: #e0e0e0;
    font-family: '{FONT_NAME}', sans-serif;
}}

/* Стили для секций (рамок) */
QFrame#SectionFrame {{
    background-color: #161b16;
    border: 1px solid #2d382d;
    border-radius: 10px;
}}

/* Заголовки */
QLabel#SectionTitle {{
    color: #00e676;
    font-weight: bold;
    font-size: 14px;
    text-transform: uppercase;
    margin-bottom: 5px;
}}

/* Выпадающий список */
QComboBox {{
    background-color: #1a1f1a;
    border: 1px solid #2e7d32;
    border-radius: 5px;
    padding: 8px;
    color: #ffffff;
    font-weight: bold;
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: #1a1f1a;
    border: 1px solid #00e676;
    selection-background-color: #2e7d32;
    outline: none;
}}

/* Кнопка запуска (Неоновая) */
QPushButton#RunModuleBtn {{
    background-color: #1b5e20;
    border: 2px solid #00e676;
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
    padding: 15px;
}}

QPushButton#RunModuleBtn:hover {{
    background-color: #2e7d32;
}}

QPushButton#RunModuleBtn:pressed {{
    background-color: #0d330d;
}}

/* Терминальный лог */
QTextEdit#LogOutput {{
    background-color: #050705;
    border: 1px solid #1b5e20;
    border-radius: 5px;
    color: #00ff41;
    font-family: '{FONT_NAME}';
    font-size: 12px;
    padding: 10px;
}}

/* Стилизация чекбоксов */
QCheckBox {{
    spacing: 10px;
    padding: 5px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 1px solid #2e7d32;
    border-radius: 4px;
    background-color: #0d110d;
}}

QCheckBox::indicator:checked {{
    background-color: #00e676;
    border: 1px solid #ffffff;
}}

/* Скроллбары (Тонкие) */
QScrollBar:vertical {{
    border: none;
    background: #0d110d;
    width: 6px;
}}
QScrollBar::handle:vertical {{
    background: #2e7d32;
    border-radius: 3px;
}}
"""