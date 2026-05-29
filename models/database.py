from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DB_PATH

# Створення рушія SQLite
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ВМИКАЄМО ПІДТРИМКУ ЗОВНІШНІХ КЛЮЧІВ ДЛЯ SQLITE
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Базовий клас для моделей
Base = declarative_base()

# Фабрика сесій
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)