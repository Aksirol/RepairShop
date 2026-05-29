import pytest
import os
import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.database import Base
from models.models import Client, Device, Master, Order
from db.repositories import OrderRepository
from services.order_service import OrderService
import config
from utils.pdf_generator import generate_receipt


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
def setup_data(db_session):
    """Створює базові дані для тестів: клієнта, пристрій та майстра"""
    client = Client(full_name="Тест Клієнт", phone="0991234567")
    db_session.add(client)
    db_session.commit()

    device = Device(client_id=client.id, type="ПК", brand="Dell", model="Optiplex", serial_number="SN123")
    master = Master(full_name="Майстер Петренко", phone="0509998877")

    db_session.add_all([device, master])
    db_session.commit()

    return {"client": client, "device": device, "master": master}


# --- ТЕСТ-КЕЙСИ ---

def test_t3_1_create_order(order_service, setup_data):
    """
    T3.1: Створення замовлення
    Заповнення форми -> збереження -> status='Новий', received_at=today.
    """
    client = setup_data["client"]
    device = setup_data["device"]

    order = order_service.create_order(
        client_id=client.id,
        device_id=device.id,
        problem_description="Не вмикається"
    )

    assert order.id is not None
    assert order.status == config.STATUS_NEW
    assert order.received_at == datetime.date.today()
    assert order.client_id == client.id
    assert order.device_id == device.id


def test_t3_2_status_transitions(order_service, setup_data):
    """
    T3.2: Переходи статусів
    Дозволені переходи зберігаються, заборонені — ValueError.
    """
    order = order_service.create_order(
        client_id=setup_data["client"].id,
        device_id=setup_data["device"].id,
        master_id=setup_data["master"].id,
        problem_description="Тест"
    )

    # 1. Дозволений перехід: Новий -> В роботі
    updated_order = order_service.change_order_status(order.id, config.STATUS_IN_PROGRESS)
    assert updated_order.status == config.STATUS_IN_PROGRESS

    # 2. Дозволений перехід: В роботі -> Готово
    updated_order = order_service.change_order_status(order.id, config.STATUS_DONE)
    assert updated_order.status == config.STATUS_DONE

    # 3. Дозволений перехід: Готово -> Видано
    updated_order = order_service.change_order_status(order.id, config.STATUS_ISSUED)
    assert updated_order.status == config.STATUS_ISSUED
    assert updated_order.is_paid is True

    # 4. Заборонений перехід: Видано -> Новий
    with pytest.raises(ValueError, match="Неможливий перехід статусу: Видано -> Новий"):
        order_service.change_order_status(order.id, config.STATUS_NEW)


def test_t3_3_filter_orders(order_repo, order_service, setup_data):
    """
    T3.3: Фільтрація замовлень
    Фільтр по статусу "В роботі" повертає лише відповідні записи.
    """
    # Створюємо два замовлення
    order1 = order_service.create_order(
        client_id=setup_data["client"].id, device_id=setup_data["device"].id,
        master_id=setup_data["master"].id, problem_description="Проблема 1"
    )
    order2 = order_service.create_order(
        client_id=setup_data["client"].id, device_id=setup_data["device"].id,
        problem_description="Проблема 2"
    )

    # Переводимо перше в статус "В роботі"
    order_service.change_order_status(order1.id, config.STATUS_IN_PROGRESS)

    # Фільтруємо
    in_progress_orders = order_repo.filter_orders(status=config.STATUS_IN_PROGRESS)

    assert len(in_progress_orders) == 1
    assert in_progress_orders[0].id == order1.id


def test_t3_4_assign_master(order_service, setup_data, db_session):
    """
    T3.4: Призначення майстра
    Призначення замовлення майстру — поле master_id оновлюється.
    """
    master = setup_data["master"]
    order = order_service.create_order(
        client_id=setup_data["client"].id,
        device_id=setup_data["device"].id,
        problem_description="Тест майстра"
    )

    # Спочатку майстра немає
    assert order.master_id is None

    # Призначаємо
    updated_order = order_service.assign_master(order.id, master.id)
    assert updated_order.master_id == master.id

    # Перевірка зв'язку з боку майстра
    db_master = db_session.query(Master).filter(Master.id == master.id).first()
    assert len(db_master.orders) == 1
    assert db_master.orders[0].id == order.id


def test_t3_5_generate_pdf(order_service, setup_data):
    """
    T3.5: Генерація PDF
    Файл .pdf створено, файл фізично існує і має розмір > 0.
    """
    order = order_service.create_order(
        client_id=setup_data["client"].id,
        device_id=setup_data["device"].id,
        problem_description="Тест PDF"
    )

    file_path = generate_receipt(order)

    # Перевіряємо чи файл створився
    assert os.path.exists(file_path) is True
    # Перевіряємо чи файл не порожній
    assert os.path.getsize(file_path) > 0

    # Прибираємо за собою після тесту
    if os.path.exists(file_path):
        os.remove(file_path)


def test_t3_6_order_without_master(order_service, setup_data):
    """
    T3.6: Замовлення без майстра
    Спроба перевести в "В роботі" без майстра викидає помилку.
    """
    order = order_service.create_order(
        client_id=setup_data["client"].id,
        device_id=setup_data["device"].id,
        problem_description="Без майстра",
        master_id=None  # Явно вказуємо, що майстра немає
    )

    with pytest.raises(ValueError, match="Призначте майстра перед початком роботи"):
        order_service.change_order_status(order.id, config.STATUS_IN_PROGRESS)