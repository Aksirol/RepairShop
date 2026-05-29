from models.database import engine, Base
from models.models import User, Client, Device, Master, Part, Order, OrderPart
from models.database import SessionLocal
from config import ROLE_ADMIN


def initialize_database():
    print("Створення таблиць у базі даних...")
    Base.metadata.create_all(bind=engine)

    # Створення тестового адміністратора, якщо база порожня
    db = SessionLocal()
    admin_exists = db.query(User).filter(User.username == "admin").first()

    if not admin_exists:
        admin_user = User(username="admin", role=ROLE_ADMIN)
        admin_user.set_password("admin123")  # Змініть пароль у реальному проекті
        db.add(admin_user)
        db.commit()
        print("Базу даних ініціалізовано. Створено користувача 'admin' з паролем 'admin123'.")
    else:
        print("База даних вже містить дані.")

    db.close()


if __name__ == "__main__":
    initialize_database()