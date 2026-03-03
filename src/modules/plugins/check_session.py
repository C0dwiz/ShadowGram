import os
from src.core.base_module import BaseModule
from hydrogram.errors import UserDeactivated, AuthKeyUnregistered, Unauthorized

"""
Модуль проверки работоспособности сессий.
Функции:

- run: проверка авторизации сессии, детектирование бана и загрузка аватара
"""

class SessionCheckPlugin(BaseModule):
    MODULE_NAME = "🔍 Проверка сессии"
    MODULE_DESC = "Проверяет статус сессии, наличие бана и загружает аватарку."

    async def run(self):
        # 1. Инициализируем клиента (база сама найдет .session и поднимет прокси)
        if not await self.init_client():
            return

        try:
            self.log("Подключение установлено, запрашиваю данные профиля...", "info")
            me = await self.client.get_me()
            
            # Если есть фото — качаем его
            if me.photo:
                avatar_dest = os.path.join(self.workdir, "avatar.jpg")
                try:
                    await self.client.download_media(me.photo.big_file_id, file_name=avatar_dest)
                    self.log("Аватарка успешно обновлена!", "success")
                except: pass
                
            self.log(f"Статус: АКТИВЕН (@{me.username or me.id})", "success")
            
        except UserDeactivated:
            self.log("Аккаунт в БАНЕ (Deactivated)", "error")
        except (AuthKeyUnregistered, Unauthorized):
            self.log("Сессия невалидна (Unauthorized)", "error")
        except Exception as e:
            self.log(f"Ошибка выполнения: {e}", "error")
        finally:
            # Всегда чистим за собой
            await self.cleanup()
