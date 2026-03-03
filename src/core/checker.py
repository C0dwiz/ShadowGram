import asyncio
from src.modules import session_checker

"""
Синхронная обертка для асинхронных проверок аккаунтов.
Функции:

- run_check: запуск асинхронной проверки сессии в отдельном цикле событий (event loop)
"""

def run_check(workdir, api_id, api_hash, proxy_url=None):
    try:
        if not api_id or not api_hash:
            return "ConfigError", "API ID или API Hash не установлены!"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            session_checker.check_account(workdir, api_id, api_hash, proxy_url)
        )
        loop.close()
        return result
    except Exception as e:
        return "Error", str(e)