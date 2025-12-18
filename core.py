from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base_model import Base
from database.tg_users import TelegramUser
from database.tasks import Task

engine = create_engine('sqlite:///todo_bot.db')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    print("Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

