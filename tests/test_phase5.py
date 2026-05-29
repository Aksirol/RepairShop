import pytest
import os
import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.database import Base
from models.models import Client, Device, Master, Order
from db.repositories import OrderRepository
from services.order_service import OrderService
from services.report_service import ReportService
import config


# --- ФІКСТУРИ ---
@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def order_repo(db_session):
    return OrderRepository(db_session)


@pytest.fixture
def order_service(order_repo):
    return OrderService(order_repo)


@pytest.fixture
def report_service(db_session):
    return ReportService(db_session)


@pytest.fixture
def setup_data(db_session, order_service):
    """Створює базові дані: клієнта, пристрій та майстра"""
    client = Client(full_name="Фінансовий Клієнт", phone="0501112233")
    db_session.add(client)
    db_session.commit()

    device = Device(client_id=client.id, type="Ноутбук", brand="HP", model="Pavilion", serial_number="HP1")
    master = Master(full_name="Майстер Іваненко", phone="0679998877")

    db_session.add_all([device, master])
    db_session.commit()

    return {"client": client, "device": device, "master": master}


# --- ТЕСТ-КЕЙСИ ---

def test_t5_1_report_date_filter(order_service, report_service, setup_data, db_session):
    """
    T5.1: Фільтр звіту за датою
    Звіт «01.01–31.01» повертає лише замовлення в цьому діапазоні.
    """
    client_id = setup_data["client"].id
    device_id = setup_data["device"].id

    # Створюємо 3 замовлення
    o1 = order_service.create_order(client_id, device_id, "Один")
    o2 = order_service.create_order(client_id, device_id, "Два")
    o3 = order_service.create_order(client_id, device_id, "Три")

    # Мануально змінюємо дати в БД для симуляції різних місяців
    o1.received_at = datetime.date(2026, 1, 15)  # Січень
    o2.received_at = datetime.date(2026, 1, 25)  # Січень
    o3.received_at = datetime.date(2026, 2, 5)  # Лютий
    db_session.commit()

    # Запитуємо статистику лише за січень
    start_date = datetime.date(2026, 1, 1)
    end_date = datetime.date(2026, 1, 31)
    stats = report_service.get_period_stats(start_date, end_date)

    assert stats["total_orders"] == 2


def test_t5_2_revenue_calculation(order_service, report_service, setup_data, db_session):
    """
    T5.2: Розрахунок виручки
    Сума оплачених замовлень збігається, round(2) застосований.
    """
    # Створюємо 2 замовлення, встановлюємо ціну
    o1 = order_service.create_order(setup_data["client"].id, setup_data["device"].id, "Тест")
    o1.price = 100.55
    o2 = order_service.create_order(setup_data["client"].id, setup_data["device"].id, "Тест2")
    o2.price = 200.45
    db_session.commit()

    # Переводимо в статус Готово і оплачуємо
    order_service.change_order_status(o1.id, config.STATUS_DONE)
    order_service.process_payment(o1.id)

    order_service.change_order_status(o2.id, config.STATUS_DONE)
    order_service.process_payment(o2.id)

    today = datetime.date.today()
    stats = report_service.get_period_stats(today, today)

    # 100.55 + 200.45 = 301.00 (без помилок float)
    assert stats["paid_revenue"] == 301.00
    assert stats["unpaid_revenue"] == 0.0


def test_t5_3_pdf_report(order_service, report_service, setup_data):
    """
    T5.3: PDF-звіт
    Генерація PDF -> файл створюється, не порожній.
    """
    order_service.create_order(setup_data["client"].id, setup_data["device"].id, "Для PDF")

    today = datetime.date.today()
    file_path = report_service.generate_period_report_pdf(today, today)

    assert os.path.exists(file_path) is True
    assert os.path.getsize(file_path) > 0

    if os.path.exists(file_path):
        os.remove(file_path)


def test_t5_4_master_stats(order_service, report_service, setup_data, db_session):
    """
    T5.4: Звіт по майстрах
    Майстер Іваненко виконав 5 замовлень — у звіті саме 5, сума відповідає.
    """
    master = setup_data["master"]
    client_id = setup_data["client"].id
    device_id = setup_data["device"].id

    # Створюємо 5 замовлень для Іваненка
    for _ in range(5):
        order = order_service.create_order(client_id, device_id, "Ремонт")
        order.master_id = master.id
        order.price = 1000.0
        db_session.commit()

        # Переводимо у Готово
        order_service.change_order_status(order.id, config.STATUS_DONE)

    today = datetime.date.today()
    stats = report_service.get_master_stats(today, today)

    assert len(stats) == 1
    assert stats[0].full_name == "Майстер Іваненко"
    assert stats[0].completed_orders == 5
    assert stats[0].revenue == 5000.0


def test_t5_5_empty_report(report_service):
    """
    T5.5: Порожній звіт
    Звіт за датами, коли замовлень немає -> Помилка "Немає даних", PDF не генерується.
    """
    # Беремо дати з майбутнього, де точно немає замовлень
    future_date = datetime.date(2050, 1, 1)

    with pytest.raises(ValueError, match="Немає даних за обраний період"):
        report_service.generate_period_report_pdf(future_date, future_date)