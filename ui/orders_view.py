import customtkinter as ctk
from tkinter import messagebox
from db.repositories import OrderRepository, ClientRepository, DeviceRepository
from services.order_service import OrderService
from utils.pdf_generator import generate_receipt
from models.database import SessionLocal
import config


class OrdersView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()

        # Ініціалізація компонентів доступу до даних
        self.order_repo = OrderRepository(self.db_session)
        self.client_repo = ClientRepository(self.db_session)
        self.device_repo = DeviceRepository(self.db_session)
        self.order_service = OrderService(self.order_repo)

        # Словники для зіставлення текстових рядків у ComboBox з числовими ID з БД
        self.clients_map = {}
        self.devices_map = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма прийому замовлення ---
        self.form_frame = ctk.CTkFrame(self, width=350)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.form_frame, text="Прийом замовлення", font=("Arial", 16, "bold")).pack(pady=10)

        # Вибір клієнта
        ctk.CTkLabel(self.form_frame, text="Виберіть клієнта:", font=("Arial", 12)).pack(anchor="w", padx=10,
                                                                                         pady=(5, 0))
        self.combo_client = ctk.CTkComboBox(self.form_frame, values=["Завантаження..."],
                                            command=self.on_client_selected)
        self.combo_client.pack(pady=5, padx=10, fill="x")

        # Вибір пристрою
        ctk.CTkLabel(self.form_frame, text="Виберіть пристрій клієнта:", font=("Arial", 12)).pack(anchor="w", padx=10,
                                                                                                  pady=(5, 0))
        self.combo_device = ctk.CTkComboBox(self.form_frame, values=["Спочатку виберіть клієнта"])
        self.combo_device.pack(pady=5, padx=10, fill="x")

        # Опис несправності
        ctk.CTkLabel(self.form_frame, text="Опис несправності:", font=("Arial", 12)).pack(anchor="w", padx=10,
                                                                                          pady=(5, 0))
        self.textbox_problem = ctk.CTkTextbox(self.form_frame, height=100)
        self.textbox_problem.pack(pady=5, padx=10, fill="x")

        # Попередня вартість
        ctk.CTkLabel(self.form_frame, text="Попередня вартість ремонту (грн):", font=("Arial", 12)).pack(anchor="w",
                                                                                                         padx=10,
                                                                                                         pady=(5, 0))
        self.entry_price = ctk.CTkEntry(self.form_frame, placeholder_text="0.0")
        self.entry_price.pack(pady=5, padx=10, fill="x")

        self.btn_save = ctk.CTkButton(self.form_frame, text="Оформити та друк квитанції", command=self.create_order)
        self.btn_save.pack(pady=20, padx=10, fill="x")

        # --- Права панель: Список замовлень та фільтри ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Панель фільтрації
        self.filter_frame = ctk.CTkFrame(self.list_frame, height=50)
        self.filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.filter_frame, text="Фільтрація за статусом:", font=("Arial", 12)).pack(side="left", padx=10,
                                                                                                 pady=5)
        self.combo_filter_status = ctk.CTkComboBox(
            self.filter_frame,
            values=["Всі статуси"] + config.ORDER_STATUSES,
            command=self.load_orders
        )
        self.combo_filter_status.pack(side="left", padx=5, pady=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Активні замовлення в системі")
        self.scrollable_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # ВИПРАВЛЕННЯ 1: Створюємо масив для безпечного відстеження віджетів списку
        self.order_widgets = []

        # Первинне завантаження вмісту екрану
        self.refresh_data()

    def refresh_data(self):
        """Комплексний метод оновлення інтерфейсу"""
        self.load_clients_to_combo()
        self.load_orders()

    def load_clients_to_combo(self):
        """Завантаження активних клієнтів із бази даних у випадаючий список"""
        try:
            clients = self.client_repo.get_all_active()
            self.clients_map = {}
            combo_values = []

            for client in clients:
                display_str = f"ID {client.id} | {client.full_name} ({client.phone})"
                self.clients_map[display_str] = client.id
                combo_values.append(display_str)

            if combo_values:
                self.combo_client.configure(values=combo_values)
                current_selection = self.combo_client.get()
                if current_selection not in combo_values:
                    self.combo_client.set(combo_values[0])
                    self.on_client_selected(combo_values[0])
            else:
                self.combo_client.configure(values=["Немає активних клієнтів"])
                self.combo_client.set("Немає активних клієнтів")
                self.combo_device.configure(values=["Спочатку додайте клієнта"])
                self.combo_device.set("Спочатку додайте клієнта")
        except Exception as e:
            print(f"Помилка при завантаженні клієнтів у форму: {e}")

    def on_client_selected(self, selected_text):
        """Подія вибору клієнта: динамічно фільтрує та відображає пристрої цього клієнта"""
        client_id = self.clients_map.get(selected_text)
        if not client_id:
            return

        try:
            devices = self.device_repo.get_by_client(client_id)
            self.devices_map = {}
            combo_values = []

            for device in devices:
                display_str = f"ID {device.id} | {device.type} {device.brand} {device.model}"
                self.devices_map[display_str] = device.id
                combo_values.append(display_str)

            if combo_values:
                self.combo_device.configure(values=combo_values)
                self.combo_device.set(combo_values[0])
            else:
                self.combo_device.configure(values=["У клієнта немає зареєстрованих пристроїв"])
                self.combo_device.set("У клієнта немає зареєстрованих пристроїв")
        except Exception as e:
            print(f"Помилка при завантаженні пристроїв клієнта: {e}")

    def create_order(self):
        """Обробка створення нового замовлення на ремонт та генерація квитанції"""
        client_text = self.combo_client.get()
        device_text = self.combo_device.get()

        client_id = self.clients_map.get(client_text)
        device_id = self.devices_map.get(device_text)

        if not client_id:
            messagebox.showerror("Помилка", "Не вибрано клієнта із бази даних.")
            return

        if not device_id:
            messagebox.showerror("Помилка", "Не вибрано пристрій для ремонту.")
            return

        problem_description = self.textbox_problem.get("1.0", "end-1c").strip()
        if not problem_description:
            messagebox.showerror("Помилка", "Будь ласка, вкажіть опис несправності пристрою.")
            return

        try:
            price_str = self.entry_price.get().strip()
            price = float(price_str) if price_str else 0.0
            if price < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Помилка", "Попередня вартість повинна бути коректним позитивним числом.")
            return

        try:
            # Збереження через бізнес-логіку сервісу
            order = self.order_service.create_order(
                client_id=client_id,
                device_id=device_id,
                problem_description=problem_description,
                price=price
            )

            # ВИПРАВЛЕННЯ 2: Примусове оновлення об'єкта, щоб SQLAlchemy підтягнув order.client для генерації PDF
            self.db_session.refresh(order)

            # Автоматична генерація друкованої PDF-квитанції
            pdf_path = generate_receipt(order)

            messagebox.showinfo("Успіх", f"Замовлення №{order.id} успішно створено!\nКвитанцію збережено: {pdf_path}")

            # Очищення полів форми для нового вводу
            self.textbox_problem.delete("1.0", "end")
            self.entry_price.delete(0, "end")

            # Перезавантаження списку замовлень на екрані
            self.load_orders()

        except Exception as e:
            import traceback
            traceback.print_exc()  # Виведе деталі в консоль для діагностики
            messagebox.showerror("Помилка", f"Критична помилка при створенні замовлення: {e}")

    def delete_order(self, order_id):
        if messagebox.askyesno("Видалення", f"Ви впевнені, що хочете безповоротно видалити замовлення №{order_id}?"):
            self.order_repo.delete(order_id)
            self.load_orders()

    def load_orders(self, choice=None):
        """Завантаження замовлень у вигляді таблиці"""
        try:
            status_filter = self.combo_filter_status.get()
            status = None if status_filter == "Всі статуси" else status_filter

            orders = self.order_repo.filter_orders(status=status)

            for widget in self.order_widgets:
                widget.destroy()
            self.order_widgets.clear()

            if not orders:
                lbl = ctk.CTkLabel(self.scrollable_frame, text="Замовлень не знайдено", font=("Arial", 12, "italic"))
                lbl.grid(row=0, column=0, pady=10)
                self.order_widgets.append(lbl)
                return

            # Налаштування колонок таблиці
            self.scrollable_frame.grid_columnconfigure(0, weight=0)  # ID
            self.scrollable_frame.grid_columnconfigure(1, weight=1)  # Клієнт
            self.scrollable_frame.grid_columnconfigure(2, weight=1)  # Пристрій
            self.scrollable_frame.grid_columnconfigure(3, weight=0)  # Статус
            self.scrollable_frame.grid_columnconfigure(4, weight=0)  # Ціна
            self.scrollable_frame.grid_columnconfigure(5, weight=0)  # Дії

            # Заголовки
            headers = ["№", "Клієнт", "Пристрій", "Статус", "Ціна", "Дії"]
            for col, text in enumerate(headers):
                lbl = ctk.CTkLabel(self.scrollable_frame, text=text, font=("Arial", 12, "bold"))
                lbl.grid(row=0, column=col, sticky="w", padx=5, pady=5)
                self.order_widgets.append(lbl)

            # Рядки з даними
            for row_idx, o in enumerate(orders, start=1):
                client_name = o.client.full_name if o.client else "Невідомо"
                device_info = f"{o.device.brand} {o.device.model}" if o.device else "Видалено"

                lbl_id = ctk.CTkLabel(self.scrollable_frame, text=str(o.id))
                lbl_id.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

                lbl_client = ctk.CTkLabel(self.scrollable_frame, text=client_name)
                lbl_client.grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)

                lbl_dev = ctk.CTkLabel(self.scrollable_frame, text=device_info)
                lbl_dev.grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)

                # Колір статусу
                status_color = "#28a745" if o.status in ["Готово", "Видано"] else "default_theme"
                if status_color == "default_theme": status_color = ["#000000", "#FFFFFF"]

                lbl_status = ctk.CTkLabel(self.scrollable_frame, text=o.status, text_color=status_color)
                lbl_status.grid(row=row_idx, column=3, sticky="w", padx=5, pady=2)

                lbl_price = ctk.CTkLabel(self.scrollable_frame, text=f"{o.price} грн")
                lbl_price.grid(row=row_idx, column=4, sticky="w", padx=5, pady=2)

                btn_del = ctk.CTkButton(self.scrollable_frame, text="❌", width=30, fg_color="#d9534f",
                                        hover_color="#c9302c",
                                        command=lambda oid=o.id: self.delete_order(oid))
                btn_del.grid(row=row_idx, column=5, sticky="w", padx=5, pady=2)

                self.order_widgets.extend([lbl_id, lbl_client, lbl_dev, lbl_status, lbl_price, btn_del])

        except Exception as e:
            print(f"Помилка завантаження реєстру замовлень: {e}")