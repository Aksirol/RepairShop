import customtkinter as ctk
from tkinter import messagebox
from models.database import SessionLocal
from models.models import User


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()

        self.title("Авторизація — Система обліку")
        self.geometry("400x350")
        self.resizable(False, False)

        # Функція (callback), яка викличеться при успішному вході
        self.on_login_success = on_login_success
        self.db_session = SessionLocal()

        # --- UI Елементи ---
        self.lbl_title = ctk.CTkLabel(self, text="Вхід у систему", font=("Arial", 24, "bold"))
        self.lbl_title.pack(pady=(40, 20))

        self.entry_username = ctk.CTkEntry(self, placeholder_text="Логін", width=250)
        self.entry_username.pack(pady=10)

        self.entry_password = ctk.CTkEntry(self, placeholder_text="Пароль", show="*", width=250)
        self.entry_password.pack(pady=10)

        self.btn_login = ctk.CTkButton(self, text="Увійти", width=250, command=self.attempt_login)
        self.btn_login.pack(pady=20)

        # Прив'язка клавіші Enter до кнопки входу
        self.bind('<Return>', lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Помилка", "Будь ласка, введіть логін та пароль.")
            return

        user = self.db_session.query(User).filter(User.username == username).first()

        if user and user.check_password(password):
            self.destroy()  # Закриваємо вікно авторизації
            self.on_login_success(user.role)  # Передаємо роль у головне вікно
        else:
            messagebox.showerror("Помилка доступу", "Невірний логін або пароль!")