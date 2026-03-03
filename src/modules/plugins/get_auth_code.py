import re
import asyncio
from src.core.base_module import BaseModule

"""
Модуль перехвата кодов подтверждения Telegram.
Функции:

- run: ожидание входящих сообщений от сервисного аккаунта 777000 и поиск кодов
"""

class AuthCodePlugin(BaseModule):
    MODULE_NAME = "🔑 Получить код"
    MODULE_DESC = "Ожидает входящий код подтверждения от Telegram (777000)."

    async def run(self, timeout=60):
        if not await self.init_client():
            return

        try:
            self.log("Слушаю сообщения от 777000...", "info")
            telegram_id = 777000
            
            # Сначала проверим последние сообщения (вдруг уже пришел)
            async for message in self.client.get_chat_history(telegram_id, limit=3):
                if message.text:
                    code = re.findall(r"\b(\d{5})\b", message.text)
                    if code:
                        self.log(f"КОД НАЙДЕН: {code[0]}", "success")
                        return

            # Если нет — ждем в реальном времени
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                async for message in self.client.get_chat_history(telegram_id, limit=1):
                    if message.text:
                        code = re.findall(r"\b(\d{5})\b", message.text)
                        if code:
                            self.log(f"ПОЛУЧЕН НОВЫЙ КОД: {code[0]}", "success")
                            return
                await asyncio.sleep(2)
                
            self.log("Время ожидания истекло. Код не найден.", "warning")
            
        except Exception as e:
            self.log(f"Ошибка: {e}", "error")
        finally:
            await self.cleanup()
