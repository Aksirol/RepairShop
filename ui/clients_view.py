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
        self.editing_client_id = None  # ID клієнта, якого ми зараз редагуємо

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма ---
        self.form_frame = ctk.CTkFrame(self, width=300)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.lbl_form_title = ctk.CTkLabel(self.form_frame, text="Реєстрація клієнта", font=("Arial", 16, "bold"))
        self.lbl_form_title.pack(pady=10)

        self.entry_name = ctk.CTkEntry(self.form_frame, placeholder_text="ПІБ")
        self.entry_name.pack(pady=5, padx=10, fill="x")

        self.entry_phone = ctk.CTkEntry(self.form_frame, placeholder_text="Телефон (+380...)")
        self.entry_phone.pack(pady=5, padx=10, fill="x")

        self.entry_email = ctk.CTkEntry(self.form_frame, placeholder_text="Email (необов'язково)")
        self.entry_email.pack(pady=5, padx=10, fill="x")

        self.btn_save = ctk.CTkButton(self.form_frame, text="Зберегти", command=self.save_client)
        self.btn_save.pack(pady=15, padx=10, fill="x")

        self.btn_cancel = ctk.CTkButton(self.form_frame, text="Скасувати", fg_color="gray", command=self.cancel_edit)
        self.btn_cancel.pack(pady=0, padx=10, fill="x")
        self.btn_cancel.pack_forget()  # Ховаємо кнопку скасування спочатку

        # --- Права панель: Пошук та Таблиця ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.entry_search = ctk.CTkEntry(self.list_frame, placeholder_text="Пошук клієнтів...")
        self.entry_search.pack(pady=10, padx=10, fill="x")
        self.entry_search.bind("<KeyRelease>", self.on_search)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Таблиця клієнтів")
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Налаштування колонок таблиці
        self.scrollable_frame.grid_columnconfigure(0, weight=0)  # ID
        self.scrollable_frame.grid_columnconfigure(1, weight=1)  # ПІБ
        self.scrollable_frame.grid_columnconfigure(2, weight=1)  # Телефон
        self.scrollable_frame.grid_columnconfigure(3, weight=1)  # Email
        self.scrollable_frame.grid_columnconfigure(4, weight=0)  # Дії

        self.client_widgets = []
        self.load_clients()

    def save_client(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        email = self.entry_email.get().strip()

        if not name or not phone:
            messagebox.showerror("Помилка", "ПІБ та Телефон є обов'язковими!")
            return
        if not validate_phone(phone):
            messagebox.showerror("Помилка", "Невірний формат телефону!")
            return
        if email and not validate_email(email):
            messagebox.showerror("Помилка", "Невірний формат email!")
            return

        try:
            if self.editing_client_id:
                self.client_repo.update(self.editing_client_id, name, phone, email)
                messagebox.showinfo("Успіх", "Дані клієнта оновлено!")
            else:
                self.client_repo.create(name, phone, email)
                messagebox.showinfo("Успіх", "Клієнта успішно додано!")

            self.cancel_edit()
            self.load_clients()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def cancel_edit(self):
        self.editing_client_id = None
        self.lbl_form_title.configure(text="Реєстрація клієнта")
        self.btn_save.configure(text="Зберегти")
        self.btn_cancel.pack_forget()
        self.entry_name.delete(0, 'end')
        self.entry_phone.delete(0, 'end')
        self.entry_email.delete(0, 'end')

    def edit_client(self, client):
        self.cancel_edit()
        self.editing_client_id = client.id
        self.lbl_form_title.configure(text=f"Редагування #{client.id}")
        self.btn_save.configure(text="Оновити дані")
        self.btn_cancel.pack(pady=5, padx=10, fill="x")

        self.entry_name.insert(0, client.full_name)
        self.entry_phone.insert(0, client.phone)
        if client.email:
            self.entry_email.insert(0, client.email)

    def delete_client(self, client_id):
        if messagebox.askyesno("Видалення", "Ви впевнені, що хочете видалити цього клієнта?"):
            self.client_repo.soft_delete(client_id)
            self.load_clients()

    def on_search(self, event):
        self.load_clients(self.entry_search.get())

    def load_clients(self, search_query=""):
        for widget in self.client_widgets:
            widget.destroy()
        self.client_widgets.clear()

        clients = self.client_repo.search(search_query) if search_query else self.client_repo.get_all_active()

        # Заголовки таблиці
        headers = ["ID", "ПІБ", "Телефон", "Email", "Дії"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(self.scrollable_frame, text=text, font=("Arial", 12, "bold"))
            lbl.grid(row=0, column=col, sticky="w", padx=5, pady=5)
            self.client_widgets.append(lbl)

        # Дані таблиці
        for row_idx, client in enumerate(clients, start=1):
            lbl_id = ctk.CTkLabel(self.scrollable_frame, text=str(client.id))
            lbl_id.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

            lbl_name = ctk.CTkLabel(self.scrollable_frame, text=client.full_name)
            lbl_name.grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)

            lbl_phone = ctk.CTkLabel(self.scrollable_frame, text=client.phone)
            lbl_phone.grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)

            lbl_email = ctk.CTkLabel(self.scrollable_frame, text=client.email or "-")
            lbl_email.grid(row=row_idx, column=3, sticky="w", padx=5, pady=2)

            # Кнопки дій
            btn_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            btn_frame.grid(row=row_idx, column=4, sticky="w", padx=5, pady=2)

            btn_edit = ctk.CTkButton(btn_frame, text="✎", width=30, command=lambda c=client: self.edit_client(c))
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(btn_frame, text="❌", width=30, fg_color="#d9534f", hover_color="#c9302c",
                                    command=lambda cid=client.id: self.delete_client(cid))
            btn_del.pack(side="left", padx=2)

            self.client_widgets.extend([lbl_id, lbl_name, lbl_phone, lbl_email, btn_frame])