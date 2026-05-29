from db.repositories import OrderRepository
from models.models import Order
from datetime import date
import config


class OrderService:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

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