import customtkinter as ctk
from tkinter import messagebox
import datetime
from models.database import SessionLocal
from services.report_service import ReportService
import os
import shutil
import datetime
from tkinter import filedialog
import config


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()
        self.report_service = ReportService(self.db_session)

        self.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self, text="Панель управління (Дашборд)", font=("Arial", 20, "bold")).grid(row=0, column=0,
                                                                                                columnspan=2, pady=20)

        # Віджети статистики
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_orders = ctk.CTkLabel(self.stats_frame, text="Замовлень (місяць):\nЗавантаження...",
                                       font=("Arial", 16))
        self.lbl_orders.grid(row=0, column=0, pady=20)

        self.lbl_revenue = ctk.CTkLabel(self.stats_frame, text="Виручка (місяць):\nЗавантаження...",
                                        font=("Arial", 16, "bold"), text_color="#28a745")
        self.lbl_revenue.grid(row=0, column=1, pady=20)

        self.lbl_debt = ctk.CTkLabel(self.stats_frame, text="Борги клієнтів:\nЗавантаження...", font=("Arial", 16),
                                     text_color="#dc3545")
        self.lbl_debt.grid(row=0, column=2, pady=20)

        # Кнопки звітів
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(self.actions_frame, text="Експорт звітів", font=("Arial", 16, "bold")).pack(pady=10)

        self.btn_period_report = ctk.CTkButton(self.actions_frame, text="Звіт за поточний місяць (PDF)",
                                               command=self.generate_monthly_report)
        self.btn_period_report.pack(pady=10)

        self.btn_backup = ctk.CTkButton(self.actions_frame, text="Створити резервну копію БД", command=self.backup_db)
        self.btn_backup.pack(pady=10)

        self.load_dashboard_data()

    def load_dashboard_data(self):
        # Визначаємо початок та кінець поточного місяця
        today = datetime.date.today()
        start_date = today.replace(day=1)

        stats = self.report_service.get_period_stats(start_date, today)

        self.lbl_orders.configure(text=f"Замовлень (місяць):\n{stats['total_orders']}")
        self.lbl_revenue.configure(text=f"Виручка (місяць):\n{stats['paid_revenue']:.2f} грн")
        self.lbl_debt.configure(text=f"Борги клієнтів:\n{stats['unpaid_revenue']:.2f} грн")

    def generate_monthly_report(self):
        today = datetime.date.today()
        start_date = today.replace(day=1)

        try:
            path = self.report_service.generate_period_report_pdf(start_date, today)
            messagebox.showinfo("Успіх", f"Звіт збережено за шляхом:\n{path}")

            # Спроба автоматично відкрити PDF (працює на Windows)
            if os.name == 'nt':
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося згенерувати звіт:\n{e}")

    def backup_db(self):
        """Створення резервної копії бази даних SQLite"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("Всі файли", "*.*")],
            initialfile=f"backup_repair_shop_{datetime.date.today()}.db",
            title="Зберегти резервну копію"
        )
        if file_path:
            try:
                shutil.copy2(config.DB_PATH, file_path)
                messagebox.showinfo("Успіх", f"Резервну копію успішно збережено!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося створити копію:\n{e}")