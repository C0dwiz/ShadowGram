import os
import asyncio
import subprocess
import socket
from hydrogram import Client
from hydrogram.errors import FloodWait

"""
Базовый класс для всех модулей автоматизации ShadowGram.
Функции:

- log: отправка отформатированного сообщения в UI
- _get_free_port: получение свободного порта для прокси
- _find_session_file: поиск .session файла в папке профиля
- init_client: полная подготовка клиента (прокси + сессия + коннект)
- run: абстрактный метод для реализации логики модуля
- cleanup: корректное завершение работы (закрытие клиента и туннелей)
"""

class BaseModule:
    # Метаданные модуля (переопределяются в наследниках)
    MODULE_NAME = "Базовый модуль"
    MODULE_DESC = "Описание отсутствует"
    
    # Список необходимых параметров для UI: [{"name": "key", "type": "file/text", "label": "Текст"}]
    PARAMS = []
    
    # Флаг: разрешить запуск только для ОДНОГО аккаунта одновременно
    SINGLE_ACCOUNT = False
    
    # Флаг: разрешить параллельный запуск для всех выбранных аккаунтов
    ALLOW_PARALLEL = False

    def __init__(self, account_data, api_id, api_hash, log_callback):
        """
        :param account_data: Дикт с данными аккаунта (name, workdir, proxy_url, device_name)
        :param api_id: Telegram API ID
        :param api_hash: Telegram API Hash
        :param log_callback: Функция для вывода логов в консоль UI (принимает строку)
        """
        self.acc = account_data
        self.api_id = api_id
        self.api_hash = api_hash
        self.log_callback = log_callback
        
        self.workdir = self.acc.get('workdir')
        self.proxy_url = self.acc.get('proxy_url')
        self.device_name = self.acc.get('device_name', 'ShadowGram-PC')
        
        self.client = None
        self.gost_process = None
        self.local_port = None

    def log(self, message, status="info"):
        """Отправляет отформатированное сообщение в UI"""
        prefix = f"[{self.acc['name']}]"
        color = "white"
        if status == "success": color = "#00e676"
        elif status == "error": color = "#ff5252"
        elif status == "warning": color = "#fbc02d"
        
        formatted_msg = f"<span style='color: {color};'>{prefix} {message}</span>"
        self.log_callback(formatted_msg)

    def _get_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def _find_session_file(self):
        """Ищет .session файл в стандартных путях Telegram Desktop"""
        search_paths = [
            self.workdir,
            os.path.join(self.workdir, "tdata"),
            os.path.join(self.workdir, "tdata", "user_data")
        ]
        for path in search_paths:
            if os.path.exists(path):
                for f in os.listdir(path):
                    if f.endswith(".session"):
                        # Возвращаем путь без расширения для Hydrogram
                        return os.path.join(path, f.replace(".session", ""))
        return None

    async def init_client(self):
        """Полная подготовка клиента: прокси + сессия + коннект"""
        try:
            self.log("Инициализация клиента...", "info")
            session_path = self._find_session_file()
            if not session_path:
                self.log("Файл сессии (.session) не найден в папке профиля!", "error")
                return False

            # Настройка прокси
            proxy_settings = None
            if self.proxy_url:
                import shutil
                if not shutil.which("gost"):
                    self.log("Ошибка: утилита 'gost' не найдена в системе!", "error")
                    return False

                self.local_port = self._get_free_port()
                try:
                    log_path = os.path.join(self.workdir, "gost_module.log")
                    # Открываем файл и НЕ закрываем его до старта Popen
                    log_file = open(log_path, "w")
                    
                    self.log(f"Запуск Gost на порту {self.local_port}...", "info")
                    self.gost_process = subprocess.Popen(
                        ["gost", "-L", f"socks5://127.0.0.1:{self.local_port}", "-F", self.proxy_url],
                        stdout=log_file, stderr=log_file,
                        start_new_session=True
                    )
                    log_file.close() 
                    
                    # Ждем готовности порта
                    port_ready = False
                    for i in range(50):
                        await asyncio.sleep(0.1)
                        if self.gost_process.poll() is not None:
                            self.log("Gost внезапно завершился сразу после старта!", "error")
                            break
                            
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(0.1)
                                if s.connect_ex(('127.0.0.1', self.local_port)) == 0:
                                    port_ready = True
                                    break
                        except:
                            continue
                    
                    if not port_ready:
                        self.log(f"Ошибка: gost не открыл порт {self.local_port} за 5 секунд!", "error")
                        return False
                    
                    self.log("Прокси-туннель готов, ожидание стабилизации...", "info")
                    await asyncio.sleep(1.0)
                    
                    proxy_settings = {
                        "scheme": "socks5",
                        "hostname": "127.0.0.1",
                        "port": self.local_port
                    }
                except Exception as e:
                    self.log(f"Ошибка запуска Gost: {e}", "error")
                    return False

            self.log("Подключение к Telegram API...", "info")
            self.client = Client(
                name=os.path.basename(session_path),
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                workdir=os.path.dirname(session_path),
                proxy=proxy_settings,
                device_model=self.device_name,
                system_version="Arch Linux"
            )

            try:
                await self.client.start()
                self.log("Клиент успешно подключен!", "success")
                return True
            except FloodWait as e:
                self.log(f"Флуд-вейт: нужно подождать {e.value} сек.", "warning")
                return False
            except Exception as e:
                self.log(f"Ошибка подключения: {e}", "error")
                return False
        except asyncio.CancelledError:
            await self.cleanup()
            raise

    async def run(self, **kwargs):
        """Метод для переопределения в модулях-наследниках"""
        raise NotImplementedError("Модуль должен реализовать метод run()")

    async def cleanup(self):
        """Корректное завершение работы"""
        if self.client:
            try: 
                if self.client.is_connected:
                    await self.client.stop()
                else:
                    await self.client.disconnect()
            except: pass
            
        if self.gost_process:
            try:
                self.gost_process.terminate()
                # Неблокирующее ожидание завершения
                for _ in range(20):
                    if self.gost_process.poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                else:
                    self.gost_process.kill()
                self.log("Прокси-туннель закрыт.", "info")
            except: pass

