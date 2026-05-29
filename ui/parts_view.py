import customtkinter as ctk
from tkinter import messagebox
from db.repositories import PartRepository
from models.database import SessionLocal


class PartsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()
        self.part_repo = PartRepository(self.db_session)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма додавання ---
        self.form_frame = ctk.CTkFrame(self, width=300)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.form_frame, text="Нова запчастина", font=("Arial", 16, "bold")).pack(pady=10)

        self.entry_name = ctk.CTkEntry(self.form_frame, placeholder_text="Назва запчастини")
        self.entry_name.pack(pady=5, padx=10, fill="x")

        self.entry_vendor = ctk.CTkEntry(self.form_frame, placeholder_text="Артикул / Код")
        self.entry_vendor.pack(pady=5, padx=10, fill="x")

        self.entry_qty = ctk.CTkEntry(self.form_frame, placeholder_text="Кількість (шт)")
        self.entry_qty.pack(pady=5, padx=10, fill="x")

        self.entry_buy_price = ctk.CTkEntry(self.form_frame, placeholder_text="Закупівельна ціна")
        self.entry_buy_price.pack(pady=5, padx=10, fill="x")

        self.entry_sell_price = ctk.CTkEntry(self.form_frame, placeholder_text="Ціна продажу")
        self.entry_sell_price.pack(pady=5, padx=10, fill="x")

        self.btn_save = ctk.CTkButton(self.form_frame, text="Додати на склад", command=self.save_part)
        self.btn_save.pack(pady=15, padx=10, fill="x")

        # --- Права панель: Складський реєстр ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Складський реєстр")
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.load_parts()

    def save_part(self):
        try:
            name = self.entry_name.get()
            vendor = self.entry_vendor.get()
            qty = int(self.entry_qty.get())
            buy_price = float(self.entry_buy_price.get())
            sell_price = float(self.entry_sell_price.get())

            if not name:
                raise ValueError("Назва є обов'язковою")

            self.part_repo.create(name, vendor, qty, buy_price, sell_price)
            messagebox.showinfo("Успіх", "Запчастину додано на склад!")

            # Очищення форми
            for entry in [self.entry_name, self.entry_vendor, self.entry_qty, self.entry_buy_price,
                          self.entry_sell_price]:
                entry.delete(0, 'end')

            self.load_parts()

        except ValueError as e:
            messagebox.showerror("Помилка", f"Перевірте правильність вводу числових даних.\nДеталі: {e}")

    def load_parts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        parts = self.part_repo.get_all()

        for part in parts:
            # Сповіщення про малий залишок (виділення червоним)
            text_color = "#FF4C4C" if part.quantity_in_stock < 3 else "default_theme"

            # Якщо використовуємо світлу тему, краще явно вказати чорний/білий
            if text_color == "default_theme":
                text_color = ["#000000", "#FFFFFF"]  # CustomTkinter підтримує масиви для Light/Dark mode

            item_text = f"[{part.vendor_code}] {part.name} | Залишок: {part.quantity_in_stock} шт. | Ціна: {part.sale_price} грн"

            lbl = ctk.CTkLabel(
                self.scrollable_frame,
                text=item_text,
                text_color=text_color,
                font=("Arial", 12, "bold" if part.quantity_in_stock < 3 else "normal")
            )
            lbl.pack(anchor="w", pady=2, padx=5)