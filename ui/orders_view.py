import customtkinter as ctk
from tkinter import messagebox
from db.repositories import OrderRepository, ClientRepository, DeviceRepository
from services.order_service import OrderService
from models.database import SessionLocal
import config


class OrdersView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()

        # Ініціалізація репозиторіїв та сервісів
        self.order_repo = OrderRepository(self.db_session)
        self.client_repo = ClientRepository(self.db_session)
        self.device_repo = DeviceRepository(self.db_session)
        self.order_service = OrderService(self.order_repo)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма прийому замовлення ---
        self.form_frame = ctk.CTkFrame(self, width=350)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.form_frame, text="Прийом замовлення", font=("Arial", 16, "bold")).pack(pady=10)

        # Заглушки для ComboBox (в реальному додатку тут треба підтягувати дані з БД)
        self.combo_client = ctk.CTkComboBox(self.form_frame, values=["Виберіть клієнта..."])
        self.combo_client.pack(pady=5, padx=10, fill="x")

        self.combo_device = ctk.CTkComboBox(self.form_frame, values=["Виберіть пристрій..."])
        self.combo_device.pack(pady=5, padx=10, fill="x")

        self.textbox_problem = ctk.CTkTextbox(self.form_frame, height=80)
        self.textbox_problem.insert("1.0", "Опис несправності...")
        self.textbox_problem.pack(pady=5, padx=10, fill="x")

        self.entry_price = ctk.CTkEntry(self.form_frame, placeholder_text="Попередня вартість (грн)")
        self.entry_price.pack(pady=5, padx=10, fill="x")

        self.btn_save = ctk.CTkButton(self.form_frame, text="Оформити та друк", command=self.create_order)
        self.btn_save.pack(pady=15, padx=10, fill="x")

        # --- Права панель: Список замовлень та фільтри ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Панель фільтрів
        self.filter_frame = ctk.CTkFrame(self.list_frame, height=50)
        self.filter_frame.pack(fill="x", padx=10, pady=5)

        self.combo_filter_status = ctk.CTkComboBox(
            self.filter_frame,
            values=["Всі статуси"] + config.ORDER_STATUSES,
            command=self.load_orders
        )
        self.combo_filter_status.pack(side="left", padx=5, pady=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Активні замовлення")
        self.scrollable_frame.pack(padx=10, pady=5, fill="both", expand=True)

    def create_order(self):
        # Тут має бути логіка отримання ID вибраного клієнта та пристрою
        # та виклик self.order_service.create_order(...)
        # Після чого виклик generate_receipt(order)
        messagebox.showinfo("Інфо", "Логіка збереження замовлення та генерації PDF")

    def load_orders(self, choice=None):
        status_filter = self.combo_filter_status.get()
        status = None if status_filter == "Всі статуси" else status_filter

        orders = self.order_repo.filter_orders(status=status)

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for o in orders:
            ctk.CTkLabel(self.scrollable_frame, text=f"№{o.id} | Статус: {o.status} | Дата: {o.received_at}").pack(
                anchor="w")