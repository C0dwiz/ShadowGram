import asyncio
import random
from src.core.base_module import BaseModule
from hydrogram.raw import functions

"""
Модуль «Channel Viewer» (Просмотр постов).
Функции:

- run: массовый просмотр сообщений в указанном канале с эмуляцией поведения человека
"""

class ChannelViewerPlugin(BaseModule):
    MODULE_NAME = "👁️ Накрутка просмотров"
    MODULE_DESC = "Параллельно просматривает посты в канале, имитируя активность."
    
    # Разрешаем запускать все аккаунты сразу!
    ALLOW_PARALLEL = True
    
    PARAMS = [
        {"name": "channel_link", "type": "text", "label": "Ссылка на канал (или ID)"},
        {"name": "post_limit", "type": "text", "label": "Лимит постов (60)"}
    ]

    async def run(self, **kwargs):
        channel_id = kwargs.get("channel_link")
        try:
            limit = int(kwargs.get("post_limit", 60))
        except:
            limit = 60

        if not channel_id:
            self.log("ID или ссылка на канал не указана!", "error")
            return

        # Инициализация (база сама поднимет прокси и зайдет в сессию)
        if not await self.init_client():
            return

        try:
            self.log(f"Начинаю сессию просмотра канала {channel_id}...", "info")

            # 1. Имитация живого присутствия: смотрим список чатов
            try:
                count = 0
                async for _ in self.client.get_dialogs(limit=5):
                    count += 1
                await asyncio.sleep(random.uniform(2, 5))
            except: pass

            # 2. Получаем объект чата
            try:
                chat = await self.client.get_chat(channel_id)
            except Exception as e:
                self.log(f"Ошибка доступа к каналу: {e}", "error")
                return

            # 3. Собираем ID последних сообщений
            messages_ids = []
            async for message in self.client.get_chat_history(chat.id, limit=limit):
                if message.id:
                    messages_ids.append(message.id)

            if not messages_ids:
                self.log("В канале нет постов для просмотра.", "warning")
                return

            self.log(f"Найдено {len(messages_ids)} постов. Начинаю эмуляцию...", "info")
            random.shuffle(messages_ids)

            # Получение peer для низкоуровневого вызова
            target_peer = await self.client.resolve_peer(chat.id)
            
            # 4. Просмотр блоками (чанками)
            for i in range(0, len(messages_ids), random.randint(2, 5)):
                chunk = messages_ids[i : i + 5]
                if not chunk: continue 

                try:
                    # Сначала "загружаем" сообщения
                    await self.client.get_messages(chat.id, chunk)
                    await asyncio.sleep(random.uniform(1, 2))

                    # Накручиваем "глазик" через API
                    await self.client.invoke(
                        functions.messages.GetMessagesViews(
                            peer=target_peer,
                            id=chunk,
                            increment=True
                        )
                    )
                    # Читаем историю до макс. ID в блоке
                    await self.client.read_chat_history(chat.id, max_id=max(chunk)) 
                    
                except Exception as e:
                    self.log(f"Ошибка в блоке просмотров: {e}", "warning")
                    break

                # Имитируем долгое чтение: пауза 10-20 сек
                delay = random.uniform(10, 25)
                self.log(f"Читаю блок постов... пауза {delay:.1f} сек.", "info")
                await asyncio.sleep(delay)

            self.log(f"Просмотры для {channel_id} успешно завершены!", "success")

        except Exception as e:
            self.log(f"Критическая ошибка: {e}", "error")
        finally:
            await self.cleanup()
