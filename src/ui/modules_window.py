import json
import threading
import asyncio
import os
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QCheckBox, QComboBox, 
                             QTextEdit, QFrame, QMessageBox, QFileDialog, QLineEdit)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from datetime import datetime

"""
Обновленное окно управления модулями ShadowGram.
Поддерживает циклическую работу (ротации) и детальное логирование времени ожидания.
Функции:

- format_time: перевод секунд в формат "X ч. Y мин."
- run_plugins_batch: бесконечный цикл выполнения для параллельных задач
"""

from src.core import logic
from src.core.constants import CONFIG_FILE, START_ICON_PATH
from src.core.module_manager import ModuleManager
from src.modules_styles import MODULES_STYLESHEET
from src.ui.active_tasks_window import ActiveTasksWindow

class ModulesWindow(QWidget):
    log_signal = pyqtSignal(str)
    task_log_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ShadowGram - Plugin System")
        self.resize(950, 750)
        self.setStyleSheet(MODULES_STYLESHEET)
        
        self.manager = ModuleManager()
        self.available_plugins = self.manager.discover_modules()
        self.param_widgets = {}
        
        self.active_tasks_win = ActiveTasksWindow()
        self.active_tasks_win.stop_requested.connect(self.stop_running_task)
        
        self.running_tasks = {} # { task_id: (asyncio_task, loop) }
        
        self.init_ui()
        self.log_signal.connect(self.append_log)
        self.task_log_signal.connect(self.active_tasks_win.append_log)
        self.update_params_panel()
        self.print_welcome_banner()

    def print_welcome_banner(self):
        banner = """
<span style='color: #4caf50; font-family: monospace; white-space: pre;'>
  ██████  ██   ██  █████  ██████   ██████  ██     ██  ██████  ██████   █████  ███    ███ 
 ██       ██   ██ ██   ██ ██   ██ ██    ██ ██     ██ ██       ██   ██ ██   ██ ████  ████ 
  █████   ███████ ███████ ██   ██ ██    ██ ██  █  ██ ██   ███ ██████  ███████ ██ ████ ██ 
      ██  ██   ██ ██   ██ ██   ██ ██    ██ ██ ███ ██ ██    ██ ██   ██ ██   ██ ██  ██  ██ 
  ██████  ██   ██ ██   ██ ██████   ██████   ███ ███   ██████  ██   ██ ██   ██ ██      ██ 
</span>
<span style='color: #4caf50;'> --------------------------------------------------------------------------------------- </span>
<span style='color: #888;'> [ Платформа автоматизации ShadowGram v1.2 ] </span>
<span style='color: #888;'> [ Система готова к работе. Выберите плагин и аккаунты. ] </span>
        """
        self.log_output.append(banner)

    def format_time(self, seconds):
        """Превращает секунды в красивую строку"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        res = []
        if h > 0: res.append(f"{h} ч.")
        if m > 0: res.append(f"{m} мин.")
        if s > 0 and h == 0: res.append(f"{s} сек.")
        return " ".join(res) if res else "0 сек."

    def stop_running_task(self, task_id):
        if task_id in self.running_tasks:
            task, loop = self.running_tasks[task_id]
            self.task_log_signal.emit(task_id, "<b style='color: #ff5252;'>Запрос на остановку...</b>")
            loop.call_soon_threadsafe(task.cancel)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        left_frame = QFrame(); left_frame.setObjectName("SectionFrame")
        left_frame.setFixedWidth(280)
        left_layout = QVBoxLayout(left_frame)
        title_l_layout = QHBoxLayout()
        title_l_layout.addWidget(QLabel("Аккаунты", objectName="SectionTitle"))
        title_l_layout.addStretch()
        self.btn_active_tasks = QPushButton("🚀 АКТИВНЫЕ ЗАДАЧИ")
        self.btn_active_tasks.setFixedWidth(160)
        self.btn_active_tasks.setStyleSheet("background-color: #4527a0; border-color: #5e35b1; font-size: 10px;")
        self.btn_active_tasks.clicked.connect(self.active_tasks_win.show)
        title_l_layout.addWidget(self.btn_active_tasks)
        left_layout.addLayout(title_l_layout)
        
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.checkboxes = []
        self.load_accounts()
        self.scroll.setWidget(self.scroll_content)
        left_layout.addWidget(self.scroll)
        btn_all = QPushButton("ВЫБРАТЬ ВСЕ"); btn_all.clicked.connect(self.toggle_all); left_layout.addWidget(btn_all)
        main_layout.addWidget(left_frame, 1)

        right_frame = QFrame(); right_frame.setObjectName("SectionFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(QLabel("Выбор плагина", objectName="SectionTitle"))
        plugin_select_layout = QHBoxLayout()
        self.module_combo = QComboBox()
        self.module_combo.addItems(list(self.available_plugins.keys()))
        self.module_combo.currentTextChanged.connect(self.update_params_panel)
        plugin_select_layout.addWidget(self.module_combo, 1)
        btn_refresh_plugins = QPushButton("🔄")
        btn_refresh_plugins.setFixedWidth(40)
        btn_refresh_plugins.clicked.connect(self.refresh_plugins_list)
        plugin_select_layout.addWidget(btn_refresh_plugins)
        right_layout.addLayout(plugin_select_layout)
        self.params_container = QFrame()
        self.params_layout = QVBoxLayout(self.params_container)
        self.params_layout.setContentsMargins(0, 10, 0, 10)
        right_layout.addWidget(self.params_container)
        self.btn_run = QPushButton(" ЗАПУСТИТЬ ПЛАГИН")
        self.btn_run.setIcon(QIcon(str(START_ICON_PATH)))
        self.btn_run.setIconSize(QSize(20, 20))
        self.btn_run.setObjectName("RunModuleBtn")
        self.btn_run.clicked.connect(self.start_module_execution)
        right_layout.addWidget(self.btn_run)
        right_layout.addWidget(QLabel("Консоль плагина", objectName="SectionTitle", styleSheet="margin-top: 10px;"))
        self.log_output = QTextEdit(); self.log_output.setObjectName("LogOutput"); self.log_output.setReadOnly(True)
        right_layout.addWidget(self.log_output, 1)
        main_layout.addWidget(right_frame, 2)

    def refresh_plugins_list(self):
        self.available_plugins = self.manager.discover_modules()
        self.module_combo.clear()
        self.module_combo.addItems(list(self.available_plugins.keys()))
        self.append_log("Список плагинов обновлен.")

    def update_params_panel(self):
        self._clear_layout(self.params_layout)
        self.param_widgets = {}
        plugin_name = self.module_combo.currentText()
        p_class = self.available_plugins.get(plugin_name)
        if not p_class or not hasattr(p_class, 'PARAMS'): return
        for param in p_class.PARAMS:
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel(f"{param['label']}:"))
            if param['type'] == 'file':
                le = QLineEdit(); btn = QPushButton("📁"); btn.setFixedWidth(40)
                btn.clicked.connect(lambda ch, l=le: self.browse_file(l))
                param_layout.addWidget(le); param_layout.addWidget(btn); self.param_widgets[param['name']] = le
            elif param['type'] == 'text':
                le = QLineEdit(); param_layout.addWidget(le); self.param_widgets[param['name']] = le
            elif param['type'] == 'textarea':
                te = QTextEdit(); te.setFixedHeight(80); param_layout.addWidget(te); self.param_widgets[param['name']] = te
            self.params_layout.addLayout(param_layout)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                elif item.layout(): self._clear_layout(item.layout())

    def browse_file(self, le):
        fp, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", "All Files (*)")
        if fp: le.setText(fp)

    def load_accounts(self):
        for acc in logic.load_config(CONFIG_FILE):
            cb = QCheckBox(f"{acc['name']}")
            cb.setProperty("acc_data", acc)
            cb.stateChanged.connect(lambda st, c=cb: self.on_account_toggled(st, c))
            self.scroll_layout.addWidget(cb); self.checkboxes.append(cb)

    def on_account_toggled(self, state, cb):
        if state == Qt.CheckState.Checked.value:
            p_class = self.available_plugins.get(self.module_combo.currentText())
            if p_class and getattr(p_class, "SINGLE_ACCOUNT", False):
                for other in self.checkboxes:
                    if other != cb and other.isChecked():
                        other.blockSignals(True); other.setChecked(False); other.blockSignals(False)

    def toggle_all(self):
        p_class = self.available_plugins.get(self.module_combo.currentText())
        if p_class and getattr(p_class, "SINGLE_ACCOUNT", False):
            QMessageBox.information(self, "Внимание", "Только один аккаунт разрешен!")
            return
        st = not all(c.isChecked() for c in self.checkboxes)
        for c in self.checkboxes: c.setChecked(st)

    def append_log(self, text):
        self.log_output.append(f"<span style='color: #888;'>[sys]:</span> {text}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def get_params_values(self):
        res = {}
        for n, w in self.param_widgets.items():
            res[n] = w.text() if isinstance(w, QLineEdit) else w.toPlainText()
        return res

    def start_module_execution(self):
        selected_accounts = [c.property("acc_data") for c in self.checkboxes if c.isChecked()]
        if not selected_accounts: return
        p_name = self.module_combo.currentText()
        p_class = self.manager.get_module_class(p_name)
        params = self.get_params_values()
        self.btn_run.setEnabled(False)
        QTimer.singleShot(2000, lambda: self.btn_run.setEnabled(True))
        
        is_parallel = getattr(p_class, "ALLOW_PARALLEL", False)
        task_id = f"{p_name}_{datetime.now().strftime('%H%M%S')}"
        if is_parallel:
            self.active_tasks_win.add_task_tab(task_id, f"{p_name} ({len(selected_accounts)})")
            self.active_tasks_win.show()
        
        threading.Thread(target=self.run_plugins_batch, args=(selected_accounts, p_class, params, task_id), daemon=True).start()

    def run_plugins_batch(self, accounts, plugin_class, params, task_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with open(CONFIG_FILE, "r") as f: cfg = json.load(f)
            aid, ah = cfg.get("settings", {}).get("api_id"), cfg.get("settings", {}).get("api_hash")
            
            async def run_all():
                is_parallel = getattr(plugin_class, "ALLOW_PARALLEL", False)
                tasks = []
                for i, a in enumerate(accounts):
                    # Callback для логов: дублируем в основную консоль и в окно задач
                    def log_f(msg, acc_name=a['name'], tid=task_id):
                        self.log_signal.emit(msg)
                        self.task_log_signal.emit(tid, msg)
                        
                    instance = plugin_class(a, aid, ah, log_f)
                    
                    # Начальная задержка от 1 до 120 минут для параллельных задач
                    delay = random.randint(60, 7200) if is_parallel else 0
                    
                    async def wrapped_run(inst, d, p):
                        try:
                            if d > 0:
                                inst.log(f"Запуск запланирован через {self.format_time(d)}", "warning")
                                await asyncio.sleep(d)
                            
                            # Начинаем цикл ротаций для параллельных задач
                            while True:
                                inst.log("🚀 Начинаю активную фазу...", "info")
                                await inst.run(**p)
                                
                                if not is_parallel: break # Одиночные задачи не зацикливаем
                                
                                # Расчёт времени отдыха (3 - 6 часов)
                                wait_seconds = random.randint(10800, 21600)
                                inst.log(f"✅ Работа завершена. Сон: {self.format_time(wait_seconds)}", "success")
                                await asyncio.sleep(wait_seconds)
                                
                        except asyncio.CancelledError:
                            await inst.cleanup()
                            raise
                        except Exception as e:
                            inst.log(f"Ошибка: {e}", "error")
                        finally:
                            await inst.cleanup()

                    tasks.append(wrapped_run(instance, delay, params))
                
                if is_parallel: await asyncio.gather(*tasks)
                else: 
                    for t in tasks: await t

            main_task = loop.create_task(run_all())
            self.running_tasks[task_id] = (main_task, loop)
            loop.run_until_complete(main_task)
            self.task_log_signal.emit(task_id, "<b style='color: #00e676;'>Сессия задач завершена.</b>")
        except asyncio.CancelledError:
            self.task_log_signal.emit(task_id, "<b style='color: #ff5252;'>Все процессы в этой вкладке остановлены.</b>")
        finally:
            if task_id in self.running_tasks: del self.running_tasks[task_id]
            try:
                # Отменяем все задачи в цикле
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                if pending:
                    # Даем время на выполнение CancelledError
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Завершаем асинхронные генераторы и исполнителей
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            except Exception as e:
                print(f"Ошибка при закрытии цикла: {e}")
            finally:
                loop.close()
                asyncio.set_event_loop(None)