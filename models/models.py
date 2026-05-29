from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.database import Base
import bcrypt


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(50), nullable=False)  # Адміністратор, Майстер, Оператор

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


# Фрагменти коду для models.py

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    is_active = Column(Boolean, default=True)  # Додано для soft-delete

    devices = relationship("Device", back_populates="client")
    orders = relationship("Order", back_populates="client")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    type = Column(String(50), nullable=False)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    serial_number = Column(String(100))
    is_active = Column(Boolean, default=True)  # Додано для soft-delete

    client = relationship("Client", back_populates="devices")
    orders = relationship("Order", back_populates="device")


class Master(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)

    orders = relationship("Order", back_populates="master")


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    vendor_code = Column(String(50), unique=True)
    quantity_in_stock = Column(Integer, default=0)
    purchase_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)

    order_parts = relationship("OrderPart", back_populates="part")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=True)

    received_at = Column(Date, nullable=False)
    completed_at = Column(Date, nullable=True)
    status = Column(String(50), nullable=False)
    problem_description = Column(Text, nullable=False)
    price = Column(Float, default=0.0)
    is_paid = Column(Boolean, default=False)

    client = relationship("Client", back_populates="orders")
    device = relationship("Device", back_populates="orders")
    master = relationship("Master", back_populates="orders")
    order_parts = relationship("OrderPart", back_populates="order")


class OrderPart(Base):
    __tablename__ = "order_parts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_at_sale = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_parts")
    part = relationship("Part", back_populates="order_parts")