from sqlalchemy import func
from models.models import Order, Master
from datetime import date
import os
import config

# ReportLab імпорти для побудови PDF з таблицями
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class ReportService:
    def __init__(self, session):
        self.session = session

        # Реєстрація кириличного шрифту для PDF
        font_path = os.path.join(config.DOCS_DIR, "arial.ttf")
        try:
            pdfmetrics.registerFont(TTFont('Arial', font_path))
        except Exception:
            pass  # Fallback

    def get_period_stats(self, start_date: date, end_date: date):
        """Звіт за період: кількість, статуси, виручка"""
        query = self.session.query(Order).filter(
            Order.received_at >= start_date,
            Order.received_at <= end_date
        )

        total_orders = query.count()

        # T5.2: Розрахунок виручки з жорстким округленням round(2)
        paid_revenue = round(self.session.query(func.sum(Order.price)).filter(
            Order.received_at >= start_date, Order.received_at <= end_date, Order.is_paid == True
        ).scalar() or 0.0, 2)

        unpaid_revenue = round(self.session.query(func.sum(Order.price)).filter(
            Order.received_at >= start_date, Order.received_at <= end_date, Order.is_paid == False
        ).scalar() or 0.0, 2)

        status_counts = self.session.query(Order.status, func.count(Order.id)).filter(
            Order.received_at >= start_date, Order.received_at <= end_date
        ).group_by(Order.status).all()

        return {
            "total_orders": total_orders,
            "paid_revenue": paid_revenue,
            "unpaid_revenue": unpaid_revenue,
            "status_counts": dict(status_counts)
        }

    def get_master_stats(self, start_date: date, end_date: date):
        """Звіт по майстрах: виконані замовлення та принесена виручка"""
        stats = self.session.query(
            Master.full_name,
            func.count(Order.id).label("completed_orders"),
            func.sum(Order.price).label("revenue")
        ).join(Order, Master.id == Order.master_id).filter(
            Order.completed_at >= start_date,
            Order.completed_at <= end_date,
            Order.status.in_([config.STATUS_DONE, config.STATUS_ISSUED])
        ).group_by(Master.id).all()

        return stats

    def generate_period_report_pdf(self, start_date: date, end_date: date) -> str:
        """Експорт звіту за період у PDF за допомогою Platypus (таблиці)"""
        stats = self.get_period_stats(start_date, end_date)

        # T5.5: Захист від генерації порожніх звітів
        if stats["total_orders"] == 0:
            raise ValueError("Немає даних за обраний період")

        reports_dir = os.path.join(config.DOCS_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        file_path = os.path.join(reports_dir, f"period_report_{start_date}_{end_date}.pdf")

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        # Додаємо підтримку кирилиці в стилі
        if 'Arial' in pdfmetrics.getRegisteredFontNames():
            title_style = ParagraphStyle('CyrillicTitle', parent=styles['Heading1'], fontName='Arial', spaceAfter=14)
            normal_style = ParagraphStyle('CyrillicNormal', parent=styles['Normal'], fontName='Arial', fontSize=12,
                                          spaceAfter=10)
        else:
            title_style = styles['Heading1']
            normal_style = styles['Normal']

        elements.append(Paragraph(f"Фінансовий звіт за період: {start_date} — {end_date}", title_style))
        elements.append(Spacer(1, 12))

        # Дані для таблиці
        data = [
            ["Показник", "Значення"],
            ["Всього замовлень", str(stats["total_orders"])],
            ["Оплачена виручка", f"{stats['paid_revenue']:.2f} грн"],
            ["Очікувана (неоплачена) виручка", f"{stats['unpaid_revenue']:.2f} грн"],
            ["Загальний обіг", f"{stats['paid_revenue'] + stats['unpaid_revenue']:.2f} грн"]
        ]

        # Форматування таблиці
        t = Table(data, colWidths=[200, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial' if 'Arial' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(t)
        doc.build(elements)

        return file_path