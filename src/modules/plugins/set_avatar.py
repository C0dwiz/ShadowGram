import os
from src.core.base_module import BaseModule

"""
Модуль установки новой аватарки для профиля.
Функции:

- run: подключение к клиенту и установка фото из указанного пути
"""

class SetAvatarPlugin(BaseModule):
    MODULE_NAME = "🖼️ Установить аватарку"
    MODULE_DESC = "Устанавливает новое фото профиля из выбранного файла."
    SINGLE_ACCOUNT = True
    
    # Описываем параметры для UI
    PARAMS = [
        {"name": "photo_path", "type": "file", "label": "Выбрать изображение"}
    ]

    async def run(self, **kwargs):
        photo_path = kwargs.get("photo_path")
        
        if not photo_path or not os.path.exists(photo_path):
            self.log("Путь к фото не указан или файл не существует!", "error")
            return

        if not await self.init_client():
            return

        try:
            self.log(f"Установка новой аватарки: {os.path.basename(photo_path)}...", "info")
            await self.client.set_profile_photo(photo=photo_path)
            self.log("Аватарка успешно установлена!", "success")
            
            # Также обновим локальную аватарку в папке профиля для UI
            local_dest = os.path.join(self.workdir, "avatar.jpg")
            try:
                import shutil
                shutil.copy2(photo_path, local_dest)
            except: pass
            
        except Exception as e:
            self.log(f"Ошибка при установке фото: {e}", "error")
        finally:
            await self.cleanup()
