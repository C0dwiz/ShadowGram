import os
import importlib.util
import traceback
from pathlib import Path
from src.core.base_module import BaseModule

class ModuleManager:
    def __init__(self):
        # Определяем путь к плагинам относительно этого файла
        self.plugins_dir = Path(__file__).parent.parent / "modules" / "plugins"
        self.modules = {}

    def discover_modules(self):
        """Сканирует папку плагинов и подгружает классы, наследуемые от BaseModule"""
        self.modules = {}
        if not self.plugins_dir.exists():
            print(f"[MANAGER] Директория не найдена: {self.plugins_dir}")
            return self.modules

        print(f"[MANAGER] Сканирование: {self.plugins_dir}")
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_path = self.plugins_dir / filename
                module_name = f"src.modules.plugins.{filename[:-3]}"
                
                try:
                    # Используем importlib для загрузки модуля по полному имени
                    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
                    module_obj = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module_obj)
                    
                    found_any = False
                    for attr_name in dir(module_obj):
                        attr = getattr(module_obj, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseModule) and 
                            attr is not BaseModule):
                            
                            display_name = getattr(attr, "MODULE_NAME", filename[:-3])
                            self.modules[display_name] = attr
                            print(f"[MANAGER] Загружен плагин: {display_name}")
                            found_any = True
                    
                    if not found_any:
                        print(f"[MANAGER WARNING] В файле {filename} не найдено классов BaseModule")
                            
                except Exception as e:
                    print(f"[MANAGER ERROR] Ошибка загрузки {filename}: {e}")
                    traceback.print_exc()

        return self.modules

    def get_module_class(self, display_name):
        return self.modules.get(display_name)
