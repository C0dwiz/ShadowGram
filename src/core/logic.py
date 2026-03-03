import json
import subprocess
import os
import socket
import urllib.request
import shutil
import zipfile
import time

"""
Основная логика приложения.
Функции:

- get_free_port: получение свободного порта для прокси-туннеля
- export_backup: создание ZIP-архива с конфигурацией и сессиями
- import_backup: восстановление данных из ZIP-архива
- check_proxy_validity: проверка работоспособности HTTP/HTTPS прокси
- load_config: загрузка списка аккаунтов из config.json
- start_telegram: запуск процесса Telegram с привязкой к workdir и прокси
- stop_telegram: корректное завершение процессов Telegram и gost
- add_account: добавление новой записи об аккаунте в конфиг
- update_proxy: обновление URL прокси для конкретного аккаунта
- update_notes: сохранение заметок пользователя для аккаунта
- update_device_info: изменение имени устройства (hostname) для профиля
- remove_account: удаление аккаунта из конфигурации
- is_process_running: проверка, активен ли процесс в данный момент
- move_account_in_list: изменение позиции аккаунта в списке (сортировка)
- open_explorer: открытие папки аккаунта в файловом менеджере Thunar
- clear_cache: очистка временных файлов и кэша в папке профиля
"""

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def export_backup(config_file, output_path):
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(config_file, "config.json")
            for acc in data.get("accounts", []):
                workdir = acc["workdir"]
                if os.path.exists(workdir):
                    for file in os.listdir(workdir):
                        if file.endswith(".session") or file == "avatar.jpg":
                            file_path = os.path.join(workdir, file)
                            arcname = os.path.join("accounts", os.path.basename(workdir), file)
                            zipf.write(file_path, arcname)
        return True, "Бэкап успешно создан!"
    except Exception as e:
        return False, f"Ошибка экспорта: {e}"

def import_backup(zip_path, current_config):
    try:
        base_dir = os.path.dirname(os.path.abspath(current_config))
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            for member in zipf.namelist():
                if member.startswith("accounts/"):
                    zipf.extract(member, base_dir)
            zipf.extract("config.json", "/tmp")
            with open("/tmp/config.json", "r") as f:
                new_data = json.load(f)
            with open(current_config, "w") as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
        return True, "Данные успешно импортированы!"
    except Exception as e:
        return False, f"Ошибка импорта: {e}"

def check_proxy_validity(proxy_url):
    if not proxy_url:
        return False
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        opener.open("https://api.telegram.org", timeout=5)
        return True
    except Exception as e:
        print(f"Проверка прокси не удалась: {e}")
        return False

def load_config(config_file):
    try:
        if not os.path.exists(config_file):
            return []
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f).get("accounts", [])
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}")
        return []

def start_telegram(workdir, proxy_url=None, device_name=None):
    print(f"\n[DEBUG] Запуск профиля: {workdir}")
    if not os.path.exists(workdir):
        os.makedirs(workdir, exist_ok=True)
    
    gost_process = None
    tg_bin = shutil.which("telegram-desktop") or shutil.which("Telegram") or "telegram-desktop"
    tg_cmd = [tg_bin, "-workdir", workdir]

    local_port = None
    if proxy_url:
        local_port = get_free_port()
        try:
            log_path = os.path.join(workdir, "gost.log")
            log_file = open(log_path, "w")
            gost_process = subprocess.Popen(
                ["gost", "-L", f"socks5://127.0.0.1:{local_port}", "-F", proxy_url],
                stdout=log_file,
                stderr=log_file,
                start_new_session=True 
            )
            time.sleep(1.2)
            if gost_process.poll() is not None:
                print(f"[ERROR] gost упал.")
            else:
                if shutil.which("proxychains4"):
                    pc_conf_path = os.path.join(workdir, "proxychains.conf")
                    with open(pc_conf_path, "w") as f:
                        f.write("strict_chain\n")
                        f.write("proxy_dns\n")
                        f.write("remote_dns_subnet 224\n")
                        f.write("tcp_read_time_out 15000\n")
                        f.write("tcp_connect_time_out 8000\n")
                        f.write("[ProxyList]\n")
                        f.write(f"socks5 127.0.0.1 {local_port}\n")
                    tg_cmd = ["proxychains4", "-f", pc_conf_path] + tg_cmd
                tg_cmd.extend(["-proxy-server", f"127.0.0.1:{local_port}", "-proxy-type", "socks5"])
        except Exception as e:
            print(f"[ERROR] Ошибка прокси: {e}")

    env = os.environ.copy()
    if local_port:
        env["all_proxy"] = f"socks5://127.0.0.1:{local_port}"
        env["ALL_PROXY"] = f"socks5://127.0.0.1:{local_port}"
    
    if device_name:
        env["DBUS_SESSION_BUS_ADDRESS"] = ""
        env["DBUS_SYSTEM_BUS_ADDRESS"] = ""
        env["HOSTNAME"] = device_name
        env["QT_QPA_PLATFORM"] = "xcb"

    err_log = os.path.join(workdir, "telegram_error.log")
    
    if device_name and shutil.which("firejail"):
        firejail_cmd = [
            "firejail", "--noprofile", "--quiet",
            f"--hostname={device_name}",
            "--nodbus",
            "--env=DBUS_SESSION_BUS_ADDRESS=",
            "--env=DBUS_SYSTEM_BUS_ADDRESS="
        ]
        final_cmd = firejail_cmd + tg_cmd
    elif device_name and shutil.which("unshare"):
        set_hostname_py = (
            "import ctypes, socket; "
            "try: "
            "  libc=ctypes.CDLL('libc.so.6'); "
            f" name=b'{device_name}'; "
            "  libc.sethostname(name, len(name)); "
            "except Exception: pass"
        )
        inner_cmd = " ".join(f'"{c}"' for c in tg_cmd)
        final_cmd = ["unshare", "--uts", "--map-root-user", "sh", "-c", f"python3 -c \"{set_hostname_py}\" && exec {inner_cmd}"]
    else:
        final_cmd = tg_cmd

    try:
        with open(err_log, "w") as f_err:
            tg_process = subprocess.Popen(
                final_cmd,
                stdout=subprocess.DEVNULL,
                stderr=f_err,
                env=env
            )
        return tg_process, gost_process
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {e}")
        if gost_process: gost_process.terminate()
        return None, None

def stop_telegram(tg_process, gost_process=None):
    processes = [p for p in [tg_process, gost_process] if p is not None]
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except:
            try: p.kill()
            except: pass
    return True

def add_account(config_file, name, workdir, proxy_url=None):
    try:
        data = {"accounts": []}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        data["accounts"].append({
            "name": name, 
            "workdir": workdir,
            "proxy_url": proxy_url,
            "device_name": f"PC-{name}"
        })
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка при добавлении аккаунта: {e}")
        return False

def update_proxy(config_file, workdir, new_proxy_url):
    try:
        with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        for acc in data.get("accounts", []):
            if acc["workdir"] == workdir:
                acc["proxy_url"] = new_proxy_url if new_proxy_url else None
                break
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка при обновлении прокси: {e}")
        return False

def update_notes(config_file, workdir, new_notes):
    try:
        with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        for acc in data.get("accounts", []):
            if acc["workdir"] == workdir:
                acc["notes"] = new_notes if new_notes else None
                break
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка при обновлении заметок: {e}")
        return False

def update_device_info(config_file, workdir, device_name):
    try:
        with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        for acc in data.get("accounts", []):
            if acc["workdir"] == workdir:
                acc["device_name"] = device_name
                break
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка при обновлении устройства: {e}")
        return False

def remove_account(config_file, workdir):
    try:
        with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        data["accounts"] = [acc for acc in data.get("accounts", []) if acc["workdir"] != workdir]
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка при удалении аккаунта: {e}")
        return False

def is_process_running(process):
    return process is not None and process.poll() is None

def move_account_in_list(config_file, workdir, direction):
    try:
        with open(config_file, "r", encoding="utf-8") as f: data = json.load(f)
        accounts = data.get("accounts", [])
        idx = -1
        for i, acc in enumerate(accounts):
            if acc["workdir"] == workdir: idx = i; break
        if idx == -1: return False
        new_idx = idx + direction
        if 0 <= new_idx < len(accounts):
            accounts[idx], accounts[new_idx] = accounts[new_idx], accounts[idx]
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при перемещении: {e}")
        return False

def open_explorer(workdir):
    if not os.path.exists(workdir): os.makedirs(workdir, exist_ok=True)
    try:
        subprocess.Popen(["thunar", workdir])
        return True
    except Exception as e:
        print(f"Ошибка открытия Thunar: {e}")
        return False

def clear_cache(workdir):
    if not os.path.exists(workdir): return False, "Папка не существует"
    cache_dirs = ['cache', 'media_cache', 'thumbnails', 'temp']
    deleted_count = 0
    try:
        for root, dirs, files in os.walk(workdir):
            for d in dirs:
                if d.lower() in cache_dirs:
                    shutil.rmtree(os.path.join(root, d))
                    deleted_count += 1
        return True, f"Успешно очищено {deleted_count} папок."
    except Exception as e: return False, str(e)