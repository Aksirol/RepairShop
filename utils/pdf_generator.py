import os
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import config
import textwrap
from models.models import Order


def generate_receipt(order: Order) -> str:
    """Генерує PDF-квитанцію для клієнта і повертає шлях до файлу."""

    receipts_dir = os.path.join(config.DOCS_DIR, "receipts")
    os.makedirs(receipts_dir, exist_ok=True)

    file_path = os.path.join(receipts_dir, f"receipt_{order.id}.pdf")

    # Підключення кириличного шрифту (переконайтеся, що файл arial.ttf є у папці docs)
    font_path = os.path.join(config.DOCS_DIR, "arial.ttf")
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
    except Exception as e:
        print(f"Помилка завантаження шрифту Arial: {e}. Використовується стандартний (можливі проблеми з кирилицею).")

    c = canvas.Canvas(file_path, pagesize=A5)

    try:
        c.setFont("Arial", 16)
    except:
        pass  # Fallback на стандартний шрифт, якщо Arial не знайдено

    # Заголовок
    c.drawString(50, 550, f"КВИТАНЦІЯ № {order.id}")
    c.drawString(50, 535, "-" * 50)

    # Інформація
    try:
        c.setFont("Arial", 12)
    except:
        pass

    c.drawString(50, 500, f"Дата прийому: {order.received_at}")
    c.drawString(50, 480, f"Клієнт: {order.client.full_name}")
    c.drawString(50, 460, f"Телефон: {order.client.phone}")

    c.drawString(50, 430, f"Пристрій: {order.device.type} {order.device.brand} {order.device.model}")
    c.drawString(50, 410, f"Серійний номер: {order.device.serial_number or 'Не вказано'}")

    c.drawString(50, 380, "Опис несправності:")
    # Розбиття довгого тексту на рядки (спрощений варіант)
    c.drawString(50, 380, "Опис несправності:")

    y_pos = 360
    # Автоматичний перенос тексту (ширина 60 символів)
    wrapped_text = textwrap.wrap(order.problem_description, width=60)
    for line in wrapped_text:
        c.drawString(50, y_pos, line)
        y_pos -= 15  # Відступ для наступного рядка

    # Відніміть значення y_pos для наступних блоків, щоб текст не наліз на ціну
    c.drawString(50, y_pos - 20, "-" * 50)
    c.drawString(50, y_pos - 40, f"Попередня вартість: {order.price} грн")
    c.drawString(50, y_pos - 60, f"Статус: {order.status}")

    c.drawString(50, 200, "Підпис приймальника: __________________")
    c.drawString(50, 150, "Підпис клієнта: __________________")

    c.save()
    return file_path