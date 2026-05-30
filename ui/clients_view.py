import customtkinter as ctk
from tkinter import messagebox
from utils.validators import validate_phone, validate_email
from db.repositories import ClientRepository
from models.database import SessionLocal


class ClientsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()
        self.client_repo = ClientRepository(self.db_session)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма ---
        self.form_frame = ctk.CTkFrame(self, width=300)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.form_frame, text="Реєстрація клієнта", font=("Arial", 16, "bold")).pack(pady=10)

        self.entry_name = ctk.CTkEntry(self.form_frame, placeholder_text="ПІБ")
        self.entry_name.pack(pady=5, padx=10, fill="x")

        self.entry_phone = ctk.CTkEntry(self.form_frame, placeholder_text="Телефон (+380...)")
        self.entry_phone.pack(pady=5, padx=10, fill="x")

        self.entry_email = ctk.CTkEntry(self.form_frame, placeholder_text="Email (необов'язково)")
        self.entry_email.pack(pady=5, padx=10, fill="x")

        self.btn_save = ctk.CTkButton(self.form_frame, text="Зберегти", command=self.save_client)
        self.btn_save.pack(pady=15, padx=10, fill="x")

        # --- Права панель: Пошук та Список ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.entry_search = ctk.CTkEntry(self.list_frame, placeholder_text="Пошук клієнтів...")
        self.entry_search.pack(pady=10, padx=10, fill="x")
        self.entry_search.bind("<KeyRelease>", self.on_search)  # Live-фільтрація

        # Заглушка для таблиці (рекомендується використовувати CTkScrollableFrame або Treeview)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Список клієнтів")
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.order_widgets = []

        self.load_clients()

    def save_client(self):
        name = self.entry_name.get()
        phone = self.entry_phone.get()
        email = self.entry_email.get()

        if not name or not phone:
            messagebox.showerror("Помилка", "ПІБ та Телефон є обов'язковими!")
            return

        if not validate_phone(phone):
            messagebox.showerror("Помилка", "Невірний формат телефону!")
            return

        if not validate_email(email):
            messagebox.showerror("Помилка", "Невірний формат email!")
            return

        self.client_repo.create(name, phone, email)
        messagebox.showinfo("Успіх", "Клієнта успішно додано!")

        # Очищення полів
        self.entry_name.delete(0, 'end')
        self.entry_phone.delete(0, 'end')
        self.entry_email.delete(0, 'end')
        self.load_clients()

    def load_clients(self, search_query=""):
        # БЕЗПЕЧНЕ ОЧИЩЕННЯ
        for widget in self.client_widgets:
            widget.destroy()
        self.client_widgets.clear()

        if search_query:
            clients = self.client_repo.search(search_query)
        else:
            clients = self.client_repo.get_all_active()

        for client in clients:
            lbl = ctk.CTkLabel(self.scrollable_frame, text=f"{client.full_name} | {client.phone}")
            lbl.pack(anchor="w", pady=2)
            self.client_widgets.append(lbl)

    def on_search(self, event):
        query = self.entry_search.get()
        self.load_clients(query)