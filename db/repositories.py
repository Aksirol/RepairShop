from models.models import Client, Device
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