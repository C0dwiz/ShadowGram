import os
import asyncio
import socket
import subprocess
from hydrogram import Client
from hydrogram.errors import UserDeactivated, AuthKeyUnregistered, Unauthorized

"""
Модуль проверки статуса сессий Telegram.
Функции:

- get_free_port: получение свободного порта для прокси-туннеля
- check_account: асинхронная проверка работоспособности сессии и загрузка аватара
"""

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

async def check_account(workdir, api_id, api_hash, proxy_url=None, device_name="ShadowGram-PC"):
    session_file = None
    search_paths = [workdir, os.path.join(workdir, "tdata"), os.path.join(workdir, "tdata", "user_data")]
    
    for path in search_paths:
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith(".session"):
                    session_file = os.path.join(path, f.replace(".session", ""))
                    break
        if session_file: break

    if not session_file:
        return "NoSession", "Файл .session не найден"

    gost_process = None; proxy_settings = None
    if proxy_url:
        local_port = get_free_port()
        try:
            gost_process = subprocess.Popen(
                ["gost", "-L", f"socks5://127.0.0.1:{local_port}", "-F", proxy_url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            proxy_settings = {"scheme": "socks5", "hostname": "127.0.0.1", "port": local_port}
            await asyncio.sleep(1.5)
        except: pass

    client = Client(
        name=os.path.basename(session_file),
        api_id=int(api_id),
        api_hash=api_hash,
        workdir=os.path.dirname(session_file),
        proxy=proxy_settings,
        device_model=device_name or "PC",
        system_version="Arch Linux"
    )

    try:
        await client.connect()
        me = await client.get_me()
        
        if me.photo:
            avatar_dest = os.path.join(workdir, "avatar.jpg")
            try:
                await client.download_media(me.photo.big_file_id, file_name=avatar_dest)
            except: pass
            
        await client.disconnect()
        return "Alive", f"Активен (@{me.username or me.id})"
    except UserDeactivated: return "Banned", "Аккаунт в БАНЕ"
    except (AuthKeyUnregistered, Unauthorized): return "Unauthorized", "Сессия вылетела"
    except Exception as e: return "Error", str(e)
    finally:
        try: await client.disconnect()
        except: pass
        if gost_process:
            gost_process.terminate()
            gost_process.wait()