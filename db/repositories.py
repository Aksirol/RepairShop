from models.models import Client, Device
from models.models import Part
from sqlalchemy.orm import Session
from sqlalchemy import or_


class ClientRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, full_name: str, phone: str, email: str = "") -> Client:
        # ДОДАНО: Перевірка на дублювання телефону (для тесту T2.3)
        existing_client = self.session.query(Client).filter(Client.phone == phone).first()
        if existing_client:
            raise ValueError("Клієнт з таким номером телефону вже існує")

        client = Client(full_name=full_name, phone=phone, email=email)
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client

    def get_all_active(self):
        return self.session.query(Client).filter(Client.is_active == True).all()

    def search(self, query_str: str):
        """Live-пошук по ПІБ, телефону або email (з підтримкою кирилиці)"""
        query_lower = query_str.lower()
        # Отримуємо всіх активних клієнтів
        all_active = self.session.query(Client).filter(Client.is_active == True).all()

        results = []
        for client in all_active:
            # Фільтруємо засобами Python, який коректно обробляє регістр кирилиці
            if (query_lower in client.full_name.lower() or
                    query_lower in client.phone.lower() or
                    (client.email and query_lower in client.email.lower())):
                results.append(client)

        return results

    def update(self, client_id: int, full_name: str, phone: str, email: str):
        client = self.session.query(Client).filter(Client.id == client_id).first()
        if client:
            client.full_name = full_name
            client.phone = phone
            client.email = email
            self.session.commit()
        return client

    def soft_delete(self, client_id: int):
        client = self.session.query(Client).filter(Client.id == client_id).first()
        if client:
            client.is_active = False
            self.session.commit()
        return client


class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, client_id: int, type: str, brand: str, model: str, serial_number: str) -> Device:
        device = Device(
            client_id=client_id, type=type, brand=brand,
            model=model, serial_number=serial_number
        )
        self.session.add(device)
        self.session.commit()
        self.session.refresh(device)
        return device

    def get_by_client(self, client_id: int):
        return self.session.query(Device).filter(
            Device.client_id == client_id,
            Device.is_active == True
        ).all()

    def soft_delete(self, device_id: int):
        device = self.session.query(Device).filter(Device.id == device_id).first()
        if device:
            device.is_active = False
            self.session.commit()
        return device


from models.models import Order
from datetime import date


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, client_id: int, device_id: int, problem_description: str,
               status: str, price: float = 0.0, master_id: int = None) -> Order:
        order = Order(
            client_id=client_id,
            device_id=device_id,
            master_id=master_id,
            received_at=date.today(),
            status=status,
            problem_description=problem_description,
            price=price
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def get_by_id(self, order_id: int) -> Order:
        return self.session.query(Order).filter(Order.id == order_id).first()

    def get_all(self):
        return self.session.query(Order).order_by(Order.received_at.desc()).all()

    def update_status(self, order_id: int, new_status: str):
        order = self.get_by_id(order_id)
        if order:
            order.status = new_status
            self.session.commit()
        return order

    def filter_orders(self, status: str = None, master_id: int = None):
        query = self.session.query(Order)
        if status:
            query = query.filter(Order.status == status)
        if master_id:
            query = query.filter(Order.master_id == master_id)
        return query.order_by(Order.received_at.desc()).all()

class PartRepository:
    def __init__(self, session):
        self.session = session

    def create(self, name: str, vendor_code: str, quantity: int, purchase_price: float, sale_price: float) -> Part:
        part = Part(
            name=name,
            vendor_code=vendor_code,
            quantity_in_stock=quantity,
            purchase_price=purchase_price,
            sale_price=sale_price
        )
        self.session.add(part)
        self.session.commit()
        self.session.refresh(part)
        return part

    def get_all(self):
        """Отримує всі запчастини, сортуючи ті, що закінчуються, нагору"""
        return self.session.query(Part).order_by(Part.quantity_in_stock.asc()).all()

    def get_by_id(self, part_id: int) -> Part:
        return self.session.query(Part).filter(Part.id == part_id).first()

    def update_stock(self, part_id: int, quantity_added: int):
        part = self.get_by_id(part_id)
        if part:
            part.quantity_in_stock += quantity_added
            self.session.commit()
        return part