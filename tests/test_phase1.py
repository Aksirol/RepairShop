import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import datetime
import os

# Імпортуємо наші моделі та конфіги
from models.database import Base
from models.models import User, Order
import config


# --- ФІКСТУРИ (Налаштування середовища для тестів) ---

@pytest.fixture
def test_engine():
    """Створює тимчасову базу даних в пам'яті для тестів."""
    engine = create_engine("sqlite:///:memory:")

    # Вмикаємо Foreign Keys для тестової БД
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
    """Надає сесію бази даних для кожного тесту."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


# --- ТЕСТ-КЕЙСИ (Згідно тест-плану) ---

def test_t1_1_db_connection_and_tables(test_engine):
    """
    T1.1: Підключення до БД
    Перевірка коректності ініціалізації SQLite та створення 6+ таблиць.
    """
    with test_engine.connect() as conn:
        # Отримуємо список всіх таблиць в SQLite
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]

        expected_tables = ["users", "clients", "devices", "orders", "masters", "parts", "order_parts"]

        for table in expected_tables:
            assert table in tables, f"Таблиця {table} не була створена!"


def test_t1_2_schema_integrity(db_session):
    """
    T1.2: Цілісність схеми
    Перевірка foreign key обмежень (INSERT із неіснуючим FK повертає IntegrityError).
    """
    # Спроба створити замовлення з клієнтом та пристроєм, яких немає в БД
    invalid_order = Order(
        client_id=999,  # Неіснуючий клієнт
        device_id=999,  # Неіснуючий пристрій
        status=config.STATUS_NEW,
        problem_description="Тестова несправність",
        received_at=datetime.date.today()
    )

    db_session.add(invalid_order)

    # Очікуємо, що коміт викличе помилку цілісності
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_t1_3_password_hashing():
    """
    T1.3: Хешування пароля
    Пароль не зберігається у відкритому вигляді, перевірка bcrypt працює.
    """
    raw_password = "MySuperSecretPassword123"
    user = User(username="test_master", role=config.ROLE_MASTER)

    user.set_password(raw_password)

    # Перевіряємо, що хеш не дорівнює самому паролю
    assert user.password_hash != raw_password
    assert user.password_hash.startswith("$2b$")  # Стандартний префікс bcrypt


def test_t1_4_authentication(db_session):
    """
    T1.4: Автентифікація
    Вхід з правильним та неправильним паролем.
    """
    # 1. Підготовка: створення користувача
    username = "admin_test"
    correct_password = "CorrectHorseBatteryStaple"

    user = User(username=username, role=config.ROLE_ADMIN)
    user.set_password(correct_password)
    db_session.add(user)
    db_session.commit()

    # 2. Дія: спроба входу
    db_user = db_session.query(User).filter(User.username == username).first()

    # Перевірка правильного пароля
    assert db_user is not None
    assert db_user.check_password(correct_password) is True

    # Перевірка неправильного пароля
    assert db_user.check_password("WrongPassword") is False


def test_t1_5_config_file():
    """
    T1.5: Конфіг-файл
    Шляхи формуються коректно, константи доступні, папки створюються.
    """
    # Перевіряємо, що конфіг містить необхідні шляхи
    assert hasattr(config, 'BASE_DIR')
    assert hasattr(config, 'DB_PATH')

    # Перевіряємо, що папки дійсно існують в системі (бо конфіг їх створив)
    assert os.path.exists(config.DB_DIR)
    assert os.path.exists(config.DOCS_DIR)

    # Перевіряємо наявність констант
    assert config.STATUS_NEW == "Новий"
    assert config.ROLE_ADMIN in config.USER_ROLES