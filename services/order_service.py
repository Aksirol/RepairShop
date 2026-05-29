from db.repositories import OrderRepository
from models.models import Order, Part, OrderPart
from datetime import date
import config


class OrderService:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo
        self.session = order_repo.session

    def create_order(self, client_id: int, device_id: int, problem_description: str,
                     price: float = 0.0, master_id: int = None) -> Order:
        """Створення нового замовлення зі статусом 'Новий'"""
        return self.order_repo.create(
            client_id=client_id,
            device_id=device_id,
            master_id=master_id,
            problem_description=problem_description,
            status=config.STATUS_NEW,
            price=price
        )

    def assign_master(self, order_id: int, master_id: int) -> Order:
        """Призначення майстра на замовлення"""
        order = self.order_repo.get_by_id(order_id)
        if order:
            order.master_id = master_id
            self.order_repo.session.commit()
        return order

    def change_order_status(self, order_id: int, new_status: str) -> Order:
        """Статусна машина: обробка логіки при переході між статусами"""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Замовлення не знайдено")

        if new_status not in config.ORDER_STATUSES:
            raise ValueError(f"Недійсний статус. Доступні: {config.ORDER_STATUSES}")

        # T3.6: Перевірка наявності майстра перед початком роботи
        if new_status == config.STATUS_IN_PROGRESS and not order.master_id:
            raise ValueError("Призначте майстра перед початком роботи")

        # T3.2: Заборонений перехід
        if order.status == config.STATUS_ISSUED and new_status == config.STATUS_NEW:
            raise ValueError("Неможливий перехід статусу: Видано -> Новий")

        # Бізнес-логіка дозволених статусів
        if new_status == config.STATUS_DONE and order.status != config.STATUS_DONE:
            order.completed_at = date.today()

        elif new_status == config.STATUS_ISSUED:
            if order.status != config.STATUS_DONE:
                raise ValueError("Неможливо видати пристрій, поки ремонт не має статусу 'Готово'")
            order.is_paid = True

        return self.order_repo.update_status(order_id, new_status)

    def add_part_to_order(self, order_id: int, part_id: int, quantity: int = 1) -> OrderPart:
        """
        Прив'язка запчастини до замовлення з автосписанням та округленням вартості.
        """
        order = self.order_repo.get_by_id(order_id)
        part = self.session.query(Part).filter(Part.id == part_id).first()

        if not order:
            raise ValueError("Замовлення не знайдено.")
        if not part:
            raise ValueError("Запчастину не знайдено.")

        if part.quantity_in_stock < quantity:
            # Текст помилки точно відповідає тесту T4.2
            raise ValueError(f"Недостатньо на складі! В наявності: {part.quantity_in_stock} шт.")

        order_part = OrderPart(
            order_id=order.id,
            part_id=part.id,
            quantity=quantity,
            price_at_sale=part.sale_price
        )
        self.session.add(order_part)

        part.quantity_in_stock -= quantity

        # T4.3: Розрахунок без float-помилок (округлення до 2 знаків)
        order.price = round(order.price + (part.sale_price * quantity), 2)

        self.session.commit()
        return order_part

    def remove_part_from_order(self, order_part_id: int):
        """
        Видалення запчастини із замовлення: повернення на склад та перерахунок вартості.
        """
        order_part = self.session.query(OrderPart).filter(OrderPart.id == order_part_id).first()
        if not order_part:
            raise ValueError("Запис не знайдено.")

        order = self.session.query(Order).filter(Order.id == order_part.order_id).first()
        part = self.session.query(Part).filter(Part.id == order_part.part_id).first()

        # T4.4: Повертаємо на склад
        part.quantity_in_stock += order_part.quantity

        # T4.4: Віднімаємо вартість (з округленням)
        order.price = round(order.price - (order_part.price_at_sale * order_part.quantity), 2)

        self.session.delete(order_part)
        self.session.commit()