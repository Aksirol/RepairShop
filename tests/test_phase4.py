import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.database import Base
from models.models import Client, Device, Part, Order, OrderPart
from db.repositories import OrderRepository, PartRepository
from services.order_service import OrderService


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
def part_repo(db_session):
    return PartRepository(db_session)


@pytest.fixture
def order_service(order_repo):
    return OrderService(order_repo)


@pytest.fixture
def setup_data(db_session, order_service, part_repo):
    """Створює базове замовлення та запчастини для тестів"""
    client = Client(full_name="Тест", phone="099")
    db_session.add(client)
    db_session.commit()

    device = Device(client_id=client.id, type="ПК", brand="Dell", model="X", serial_number="1")
    db_session.add(device)
    db_session.commit()

    order = order_service.create_order(client.id, device.id, "Тест")

    part1 = part_repo.create("Екран", "V01", quantity=10, purchase_price=1000.0, sale_price=1500.55)
    part2 = part_repo.create("Батарея", "V02", quantity=2, purchase_price=500.0, sale_price=800.10)

    return {"order": order, "part1": part1, "part2": part2}


# --- ТЕСТ-КЕЙСИ ---

def test_t4_1_deduct_part(order_service, setup_data, db_session):
    """
    T4.1: Списання запчастини
    Додавання запчастини -> quantity_in_stock зменшується, order_parts запис додано.
    """
    order = setup_data["order"]
    part = setup_data["part1"]
    initial_stock = part.quantity_in_stock

    # Додаємо 2 одиниці запчастини
    order_part = order_service.add_part_to_order(order.id, part.id, quantity=2)

    # Перевіряємо списання
    assert part.quantity_in_stock == initial_stock - 2

    # Перевіряємо запис в БД
    db_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert len(db_order.order_parts) == 1
    assert db_order.order_parts[0].id == order_part.id
    assert db_order.order_parts[0].quantity == 2


def test_t4_2_forbid_excess(order_service, setup_data):
    """
    T4.2: Заборона надміру
    Спроба списати більше, ніж є на складі -> Помилка «Недостатньо на складі».
    """
    order = setup_data["order"]
    part = setup_data["part2"]  # На складі всього 2 шт.

    with pytest.raises(ValueError, match="Недостатньо на складі"):
        order_service.add_part_to_order(order.id, part.id, quantity=5)

    # Перевіряємо, що списання не відбулося
    assert part.quantity_in_stock == 2


def test_t4_3_calculate_price(order_service, setup_data, db_session):
    """
    T4.3: Розрахунок вартості
    Додавання 2 запчастин -> вартість = сума (price_at_sale * qty), round(2).
    """
    order = setup_data["order"]
    part1 = setup_data["part1"]  # sale_price = 1500.55
    part2 = setup_data["part2"]  # sale_price = 800.10

    # Додаємо 1 екран та 2 батареї
    # Очікувана сума: 1500.55 * 1 + 800.10 * 2 = 1500.55 + 1600.20 = 3100.75
    order_service.add_part_to_order(order.id, part1.id, quantity=1)
    order_service.add_part_to_order(order.id, part2.id, quantity=2)

    db_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert db_order.price == 3100.75


def test_t4_4_remove_part(order_service, setup_data, db_session):
    """
    T4.4: Видалення запчастини із замовлення
    Видалення order_parts запису -> залишок повертається, вартість перерахована.
    """
    order = setup_data["order"]
    part = setup_data["part1"]  # stock = 10, price = 1500.55

    # Додаємо 3 шт
    order_part = order_service.add_part_to_order(order.id, part.id, quantity=3)
    assert part.quantity_in_stock == 7
    assert order.price == 4501.65

    # Видаляємо
    order_service.remove_part_from_order(order_part.id)

    # Перевіряємо повернення на склад та перерахунок
    assert part.quantity_in_stock == 10
    assert order.price == 0.0
    assert len(order.order_parts) == 0


def test_t4_5_low_stock_signal(part_repo):
    """
    T4.5: Сигнал малого залишку
    Залишок < порогу (3 шт) - перевірка логіки UI-виділення.
    """
    # Створюємо запчастини з різним залишком
    part_normal = part_repo.create("Шлейф", "C1", quantity=5, purchase_price=10, sale_price=20)
    part_low = part_repo.create("Термопаста", "T1", quantity=2, purchase_price=50, sale_price=100)

    # Імітуємо логіку, яка використовується в ui/parts_view.py
    def get_row_color(stock_quantity):
        return "#FF4C4C" if stock_quantity < 3 else "default_theme"

    assert get_row_color(part_normal.quantity_in_stock) == "default_theme"
    assert get_row_color(part_low.quantity_in_stock) == "#FF4C4C"

    # Перевірка сортування репозиторію (ті, що закінчуються, мають бути першими)
    parts = part_repo.get_all()
    assert parts[0].id == part_low.id  # 2 шт
    assert parts[1].id == part_normal.id  # 5 шт