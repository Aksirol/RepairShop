import customtkinter as ctk
from tkinter import messagebox
from db.repositories import PartRepository
from models.database import SessionLocal


class PartsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.db_session = SessionLocal()
        self.part_repo = PartRepository(self.db_session)
        self.editing_part_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва панель: Форма додавання ---
        self.form_frame = ctk.CTkFrame(self, width=300)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.lbl_form_title = ctk.CTkLabel(self.form_frame, text="Нова запчастина", font=("Arial", 16, "bold"))
        self.lbl_form_title.pack(pady=10)

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

        self.btn_cancel = ctk.CTkButton(self.form_frame, text="Скасувати", fg_color="gray", command=self.cancel_edit)
        self.btn_cancel.pack(pady=0, padx=10, fill="x")
        self.btn_cancel.pack_forget()

        # --- Права панель: Складський реєстр (Таблиця) ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, label_text="Складський реєстр (Таблиця)")
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.scrollable_frame.grid_columnconfigure(0, weight=0)  # Артикул
        self.scrollable_frame.grid_columnconfigure(1, weight=1)  # Назва
        self.scrollable_frame.grid_columnconfigure(2, weight=0)  # Залишок
        self.scrollable_frame.grid_columnconfigure(3, weight=0)  # Ціна
        self.scrollable_frame.grid_columnconfigure(4, weight=0)  # Дії

        self.part_widgets = []
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

            if self.editing_part_id:
                self.part_repo.update(self.editing_part_id, name, vendor, qty, buy_price, sell_price)
                messagebox.showinfo("Успіх", "Дані запчастини оновлено!")
            else:
                self.part_repo.create(name, vendor, qty, buy_price, sell_price)
                messagebox.showinfo("Успіх", "Запчастину додано на склад!")

            self.cancel_edit()
            self.load_parts()

        except ValueError as e:
            messagebox.showerror("Помилка", f"Перевірте правильність вводу даних.\nДеталі: {e}")

    def cancel_edit(self):
        self.editing_part_id = None
        self.lbl_form_title.configure(text="Нова запчастина")
        self.btn_save.configure(text="Додати на склад")
        self.btn_cancel.pack_forget()
        for entry in [self.entry_name, self.entry_vendor, self.entry_qty, self.entry_buy_price, self.entry_sell_price]:
            entry.delete(0, 'end')

    def edit_part(self, part):
        self.cancel_edit()
        self.editing_part_id = part.id
        self.lbl_form_title.configure(text=f"Редагування: {part.vendor_code}")
        self.btn_save.configure(text="Оновити дані")
        self.btn_cancel.pack(pady=5, padx=10, fill="x")

        self.entry_name.insert(0, part.name)
        self.entry_vendor.insert(0, part.vendor_code)
        self.entry_qty.insert(0, str(part.quantity_in_stock))
        self.entry_buy_price.insert(0, str(part.purchase_price))
        self.entry_sell_price.insert(0, str(part.sale_price))

    def delete_part(self, part_id):
        if messagebox.askyesno("Видалення", "Видалити запчастину зі складу?"):
            try:
                self.part_repo.delete(part_id)
                self.load_parts()
            except ValueError as e:
                messagebox.showerror("Помилка видалення", str(e))

    def load_parts(self):
        for widget in self.part_widgets:
            widget.destroy()
        self.part_widgets.clear()

        parts = self.part_repo.get_all()

        headers = ["Артикул", "Назва", "Залишок", "Ціна", "Дії"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(self.scrollable_frame, text=text, font=("Arial", 12, "bold"))
            lbl.grid(row=0, column=col, sticky="w", padx=5, pady=5)
            self.part_widgets.append(lbl)

        for row_idx, part in enumerate(parts, start=1):
            text_color = "#FF4C4C" if part.quantity_in_stock < 3 else "default_theme"
            if text_color == "default_theme":
                text_color = ["#000000", "#FFFFFF"]

            font_weight = "bold" if part.quantity_in_stock < 3 else "normal"

            lbl_vendor = ctk.CTkLabel(self.scrollable_frame, text=part.vendor_code, text_color=text_color,
                                      font=("Arial", 12, font_weight))
            lbl_vendor.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

            lbl_name = ctk.CTkLabel(self.scrollable_frame, text=part.name, text_color=text_color,
                                    font=("Arial", 12, font_weight))
            lbl_name.grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)

            lbl_qty = ctk.CTkLabel(self.scrollable_frame, text=f"{part.quantity_in_stock} шт.", text_color=text_color,
                                   font=("Arial", 12, font_weight))
            lbl_qty.grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)

            lbl_price = ctk.CTkLabel(self.scrollable_frame, text=f"{part.sale_price} грн", text_color=text_color,
                                     font=("Arial", 12, font_weight))
            lbl_price.grid(row=row_idx, column=3, sticky="w", padx=5, pady=2)

            btn_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            btn_frame.grid(row=row_idx, column=4, sticky="w", padx=5, pady=2)

            btn_edit = ctk.CTkButton(btn_frame, text="✎", width=30, command=lambda p=part: self.edit_part(p))
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(btn_frame, text="❌", width=30, fg_color="#d9534f", hover_color="#c9302c",
                                    command=lambda pid=part.id: self.delete_part(pid))
            btn_del.pack(side="left", padx=2)

            self.part_widgets.extend([lbl_vendor, lbl_name, lbl_qty, lbl_price, btn_frame])