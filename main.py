import customtkinter as ctk
from ui.login_view import LoginWindow
from ui.dashboard_view import DashboardView
from ui.clients_view import ClientsView
from ui.orders_view import OrdersView
from ui.parts_view import PartsView
import config

# Базові налаштування теми
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self, user_role):
        super().__init__()

        self.title("Система обліку замовлень на ремонт")
        self.geometry("1200x700")
        self.user_role = user_role

        # Налаштування сітки (2 колонки: 1 для меню, 1 для контенту)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_frames()

        # За замовчуванням відкриваємо Дашборд
        self.show_frame("dashboard")

    def setup_sidebar(self):
        """Створення бокового навігаційного меню"""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # Пустий простір перед нижніми кнопками

        # Логотип / Назва
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="RepairShop", font=("Arial", 20, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Кнопки навігації
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Дашборд",
                                           command=lambda: self.show_frame("dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_orders = ctk.CTkButton(self.sidebar_frame, text="Замовлення",
                                        command=lambda: self.show_frame("orders"))
        self.btn_orders.grid(row=2, column=0, padx=20, pady=10)

        self.btn_clients = ctk.CTkButton(self.sidebar_frame, text="Клієнти", command=lambda: self.show_frame("clients"))
        self.btn_clients.grid(row=3, column=0, padx=20, pady=10)

        self.btn_parts = ctk.CTkButton(self.sidebar_frame, text="Склад запчастин",
                                       command=lambda: self.show_frame("parts"))
        self.btn_parts.grid(row=4, column=0, padx=20, pady=10)

        # Інформація про користувача знизу
        self.lbl_role = ctk.CTkLabel(self.sidebar_frame, text=f"Роль: {self.user_role}", font=("Arial", 12))
        self.lbl_role.grid(row=6, column=0, padx=20, pady=(10, 20))

    def setup_frames(self):
        """Ініціалізація всіх екранів (вони спочатку приховані)"""
        self.frames = {}

        # Створюємо екземпляри наших Views, які ми розробляли в фазах 2-5
        self.frames["dashboard"] = DashboardView(self)
        self.frames["orders"] = OrdersView(self)
        self.frames["clients"] = ClientsView(self)
        self.frames["parts"] = PartsView(self)

        # Розміщуємо їх у правій колонці сітки
        for frame in self.frames.values():
            frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    def show_frame(self, frame_name):
        """Перемикач активного вікна з автоматичним оновленням даних на вкладках"""
        # Ховаємо всі фрейми, відправляючи їх на задній план
        for frame in self.frames.values():
            frame.grid_remove()

        # Показуємо обраний фрейм
        frame = self.frames[frame_name]
        frame.grid()

        # Виклик методів синхронізації даних з БД при переході на вкладку
        if frame_name == "clients" and hasattr(frame, 'load_clients'):
            frame.load_clients()
        elif frame_name == "dashboard" and hasattr(frame, 'load_dashboard_data'):
            frame.load_dashboard_data()
        elif frame_name == "parts" and hasattr(frame, 'load_parts'):
            frame.load_parts()
        elif frame_name == "orders" and hasattr(frame, 'refresh_data'):
            # Викликаємо комплексне оновлення комбобоксів та замовлень
            frame.refresh_data()


def start_app(user_role):
    """Ця функція викликається після успішного логіну"""
    app = MainWindow(user_role)
    app.mainloop()


if __name__ == "__main__":
    # Створюємо вікно логіну. Передаємо йому посилання на функцію start_app
    login_window = LoginWindow(on_login_success=start_app)
    login_window.mainloop()