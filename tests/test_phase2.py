import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.database import Base
from models.models import Client, Device
from db.repositories import ClientRepository, DeviceRepository
from utils.validators import validate_phone


# --- ФІКСТУРИ ---
@pytest.fixture
def test_engine():
    """Створює тимчасову базу даних в пам'яті для тестів."""
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
    """Надає сесію бази даних."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client_repo(db_session):
    return ClientRepository(db_session)


@pytest.fixture
def device_repo(db_session):
    return DeviceRepository(db_session)


# --- ТЕСТ-КЕЙСИ ---

def test_t2_1_create_client(client_repo, db_session):
    """
    T2.1: Створення клієнта
    Збереження форми -> запис з'являється в таблиці clients.
    """
    initial_count = db_session.query(Client).count()
    client = client_repo.create(full_name="Степан Бандера", phone="0991234567", email="stepan@test.com")

    assert db_session.query(Client).count() == initial_count + 1
    assert client.full_name == "Степан Бандера"
    assert client.phone == "0991234567"
    assert client.is_active is True  # Перевірка дефолтного значення


def test_t2_2_phone_validation():
    """
    T2.2: Валідація телефону
    Перевірка функції валідації на коректних та некоректних даних.
    """
    # Коректні
    assert validate_phone("0991234567") is True
    assert validate_phone("+380991234567") is True
    assert validate_phone("380991234567") is True
    assert validate_phone("+38 (099) 123-45-67") is True  # Якщо ваша валідація чистить символи

    # Некоректні
    assert validate_phone("123") is False
    assert validate_phone("abcdefghij") is False
    assert validate_phone("099123456") is False  # Занадто короткий


def test_t2_3_duplicate_phone(client_repo):
    """
    T2.3: Дублювання телефону
    Спроба зареєструвати двох клієнтів з однаковим номером.
    """
    client_repo.create(full_name="Перший Клієнт", phone="0500001122")

    # Очікуємо, що репозиторій викине ValueError
    with pytest.raises(ValueError, match="Клієнт з таким номером телефону вже існує"):
        client_repo.create(full_name="Другий Клієнт", phone="0500001122")


def test_t2_4_search_client(client_repo):
    """
    T2.4: Пошук клієнта
    Таблиця фільтрується в реальному часі (case-insensitive).
    """
    client_repo.create(full_name="Іван Петренко", phone="0671112233")
    client_repo.create(full_name="Олена Іванова", phone="0509998877")

    # Пошук по частковому імені (case-insensitive)
    search_results = client_repo.search("іван")
    assert len(search_results) == 2  # Має знайти і 'Іван', і 'Іванова'

    # Пошук по телефону
    phone_results = client_repo.search("067")
    assert len(phone_results) == 1
    assert phone_results[0].full_name == "Іван Петренко"


def test_t2_5_link_device(client_repo, device_repo, db_session):
    """
    T2.5: Прив'язка пристрою
    Додавання пристрою до клієнта, перевірка зв'язку.
    """
    client = client_repo.create(full_name="Власник Пристрою", phone="0631234567")

    device = device_repo.create(
        client_id=client.id,
        type="Ноутбук",
        brand="Asus",
        model="ZenBook",
        serial_number="SN999888"
    )

    assert device.client_id == client.id

    # Перевірка через ORM relationship
    db_client = db_session.query(Client).filter(Client.id == client.id).first()
    assert len(db_client.devices) == 1
    assert db_client.devices[0].model == "ZenBook"


def test_t2_6_soft_delete_client_with_devices(client_repo, device_repo, db_session):
    """
    T2.6: Видалення клієнта з пристроями
    Soft-delete: is_active=False, пристрої не видаляються фізично.
    """
    client = client_repo.create(full_name="Клієнт на видалення", phone="0990000000")
    device_repo.create(
        client_id=client.id, type="ПК", brand="Custom",
        model="Tower", serial_number="123"
    )

    # Виконуємо Soft-delete
    client_repo.soft_delete(client.id)

    # 1. Перевіряємо, що клієнт неактивний
    db_client = db_session.query(Client).filter(Client.id == client.id).first()
    assert db_client.is_active is False

    # 2. Перевіряємо, що його немає в списку активних
    active_clients = client_repo.get_all_active()
    assert db_client not in active_clients

    # 3. Перевіряємо, що пристрій НЕ видалився фізично з БД
    device_count = db_session.query(Device).count()
    assert device_count == 1