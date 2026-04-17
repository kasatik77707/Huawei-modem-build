import customtkinter as ctk
import subprocess
import platform
import threading
import time
from tkinter import messagebox, simpledialog
from huawei_lte_api.Connection import Connection
from huawei_lte_api.api.DialUp import DialUp

# Настройки темы - Светлая, как на сайте
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class StrizhModemApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Конфигурация окна
        self.title("Huawei Control Panel")
        self.geometry("550x750")
        self.configure(fg_color="#f4f7f9") # Фон "Стриж"

        # Данные
        self.modem_url = 'http://admin:admin@192.168.8.1/'
        self.admin_pass = "1234" 
        self.ping_host = "1.1.1.1"
        self.profiles_data = []

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 10), padx=30, fill="x")
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="Управление APN", 
                                        font=("Segoe UI", 28, "bold"), text_color="#1d252d")
        self.label_title.pack(side="left")
        
        self.status_indicator = ctk.CTkLabel(self.header_frame, text="● ПРОВЕРКА...", 
                                             text_color="#aaa", font=("Segoe UI", 16, "bold"))
        self.status_indicator.pack(side="right")

        # --- ОСНОВНАЯ КАРТОЧКА ---
        self.main_card = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        self.main_card.pack(pady=10, padx=25, fill="both", expand=True)

        ctk.CTkLabel(self.main_card, text="ВЫБЕРИТЕ ПРОФИЛЬ APN:", 
                     font=("Segoe UI", 12, "bold"), text_color="#666").pack(pady=(25, 5), padx=30, anchor="w")
        
        self.combo_profiles = ctk.CTkComboBox(self.main_card, values=["Обновите список..."], 
                                              width=400, height=45, corner_radius=12, 
                                              border_color="#e0e6ed", fg_color="#f9fbfe")
        self.combo_profiles.pack(pady=10, padx=30)

        self.btn_refresh = ctk.CTkButton(self.main_card, text="🔄 Обновить список и статус", 
                                         height=40, corner_radius=20, fg_color="transparent", 
                                         text_color="#00BFFF", hover_color="#eef8ff",
                                         command=self.refresh_all)
        self.btn_refresh.pack(pady=5, padx=30, fill="x")
        
        self.btn_activate = ctk.CTkButton(self.main_card, text="ПОДКЛЮЧИТЬ APN", 
                                          fg_color="#e30613", hover_color="#b3050f", 
                                          height=55, corner_radius=28, font=("Segoe UI", 16, "bold"),
                                          command=self.activate_selected)
        self.btn_activate.pack(pady=15, padx=30, fill="x")

        self.btn_quick_sputnik = ctk.CTkButton(
            self.main_card, # или self.main_frame, в зависимости от версии кода
            text="🚀 Добавить APN Спутриковая связь", 
            fg_color="#0099da", 
            hover_color="#007bbd",
            height=45, 
            corner_radius=22, 
            font=("Segoe UI", 13, "bold"),
            command=self.quick_add_sputnik
        )
        self.btn_quick_sputnik.pack(pady=10, padx=30, fill="x")

        # --- СКРЫТАЯ СЕКЦИЯ ---
        self.expand_btn = ctk.CTkButton(self.main_card, text="➕ Добавить новый (Пароль)", 
                                        fg_color="transparent", text_color="#aaa", 
                                        font=("Segoe UI", 12), command=self.unlock_creation)
        self.expand_btn.pack(pady=5)

        self.creation_frame = ctk.CTkFrame(self.main_card, fg_color="#f9fbfe", corner_radius=15)
        
        self.entry_name = ctk.CTkEntry(self.creation_frame, placeholder_text="Имя профиля", height=35)
        self.entry_name.pack(pady=5, padx=20, fill="x")
        
        self.entry_apn = ctk.CTkEntry(self.creation_frame, placeholder_text="APN адрес (dodi.t2.ru)", height=35)
        self.entry_apn.pack(pady=5, padx=20, fill="x")

        self.btn_create = ctk.CTkButton(self.creation_frame, text="СОЗДАТЬ И ВЫБРАТЬ", 
                                        fg_color="#28a745", hover_color="#218838",
                                        height=40, corner_radius=20, font=("Segoe UI", 13, "bold"),
                                        command=self.create_flow)
        self.btn_create.pack(pady=15, padx=20, fill="x")

        # --- ЛОГИ ---
        self.log_box = ctk.CTkTextbox(self.main_card, height=180, corner_radius=12, 
                                      border_width=1, border_color="#eee", font=("Consolas", 12), 
                                      fg_color="#fff", text_color="#555")
        self.log_box.pack(pady=20, padx=30, fill="both")

        # Слоган внизу
        ctk.CTkLabel(self, text="Будьте на связи вместе с нами!", 
                     font=("Segoe UI", 16, "bold"), text_color="#1d252d").pack(pady=15)

        # ПЕРВИЧНЫЙ ЗАПУСК
        self.check_initial_state()

    def log(self, msg, color="#666"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")

    def quick_add_sputnik(self):
        """Быстрое добавление конкретного APN"""
        name = "Sputnikovaya Svyaz Internet"
        apn = "dodi.t2.ru"
        
        self.log(f"Запуск быстрой настройки: {name}...")
        
        def task():
            try:
                with Connection(self.modem_url) as conn:
                    dialup = DialUp(conn)
                    
                    # Получаем текущие профили, чтобы вычислить новый ID
                    profs = dialup.profiles().get('Profiles', {}).get('Profile', [])
                    if isinstance(profs, dict): profs = [profs]
                    idx_list = [int(p['Index']) for p in profs]
                    new_idx = max(idx_list) + 1 if idx_list else 1

                    # Создаем профиль
                    dialup.create_profile(
                        name=name, 
                        apn=apn, 
                        dialup_number='*99#', 
                        username='', 
                        password=''
                    )
                    
                    self.log(f"Профиль '{name}' создан (ID {new_idx})")
                    
                    # Сразу активируем его
                    dialup.set_default_profile(new_idx)
                    self.log(f"Переключение на новый профиль...")
                    
                    time.sleep(10)
                    self.run_ping()
                    self.refresh_all()
            except Exception as e:
                self.log(f"Ошибка быстрого добавления: {e}")

        threading.Thread(target=task, daemon=True).start()

    def run_ping(self, silent=False):
        if not silent: self.log(f"Проверка связи ({self.ping_host})...")
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout = '1000' if platform.system().lower() == 'windows' else '1'
        
        try:
            cmd = ['ping', param, '1', '-w', timeout, self.ping_host]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if res.returncode == 0:
                self.status_indicator.configure(text="● ONLINE", text_color="#178c44")
                if not silent: self.log("Результат: СВЯЗЬ ЕСТЬ", "#178c44")
            else:
                self.status_indicator.configure(text="● OFFLINE", text_color="#e30613")
                if not silent: self.log("Результат: СВЯЗИ НЕТ", "#e30613")
        except Exception as e:
            self.log(f"Ошибка пинга: {e}")

    def check_initial_state(self):
        self.log("Запуск... Синхронизация данных.")
        threading.Thread(target=self.run_ping, daemon=True).start()
        self.refresh_all()

    def unlock_creation(self):
        pwd = simpledialog.askstring("Доступ", "Пароль администратора:", show='*')
        if pwd == self.admin_pass:
            self.expand_btn.pack_forget() # Убираем кнопку
            self.creation_frame.pack(pady=10, padx=30, fill="x", before=self.log_box)
            self.log("Меню администратора открыто.")
        else:
            if pwd is not None: messagebox.showerror("Ошибка", "Неверный пароль!")

    def refresh_all(self):
        threading.Thread(target=self.run_ping, args=(True,), daemon=True).start()
        def task():
            try:
                with Connection(self.modem_url) as conn:
                    dialup = DialUp(conn)
                    data = dialup.profiles()
                    profs = data.get('Profiles', {}).get('Profile', [])
                    if isinstance(profs, dict): profs = [profs]
                    
                    self.profiles_data = profs
                    names = [f"ID {p['Index']}: {p['Name']} [{p['ApnName']}]" for p in profs]
                    self.combo_profiles.configure(values=names)
                    self.log("Список профилей обновлен.")
            except Exception as e:
                self.log(f"Ошибка модема: {e}")
        threading.Thread(target=task, daemon=True).start()

    def activate_selected(self):
        val = self.combo_profiles.get()
        if "ID" not in val:
            self.log("Сначала выберите профиль!")
            return
        
        idx = val.split(":")[0].replace("ID ", "").strip()
        self.log(f"Активация профиля №{idx}...", "#e30613")
        
        def task():
            try:
                with Connection(self.modem_url) as conn:
                    DialUp(conn).set_default_profile(idx)
                    self.log("Команда принята. Ожидаем переподключение (10 сек)...")
                    time.sleep(10)
                    self.run_ping()
            except Exception as e:
                self.log(f"Ошибка активации: {e}")
        threading.Thread(target=task, daemon=True).start()

    def create_flow(self):
        name = self.entry_name.get()
        apn = self.entry_apn.get()
        if not name or not apn:
            messagebox.showwarning("Внимание", "Заполните Имя и APN!")
            return

        def task():
            try:
                with Connection(self.modem_url) as conn:
                    dialup = DialUp(conn)
                    profs = dialup.profiles().get('Profiles', {}).get('Profile', [])
                    if isinstance(profs, dict): profs = [profs]
                    idx_list = [int(p['Index']) for p in profs]
                    new_idx = max(idx_list) + 1 if idx_list else 1

                    self.log(f"Создание профиля ID {new_idx}...")
                    dialup.create_profile(name=name, apn=apn, dialup_number='*99#', username='', password='')
                    
                    self.log(f"Успешно. Переключение на ID {new_idx}...")
                    dialup.set_default_profile(new_idx)
                    time.sleep(10)
                    self.run_ping()
                    self.refresh_all()
            except Exception as e:
                self.log(f"Ошибка создания: {e}")
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = StrizhModemApp()
    app.mainloop()
