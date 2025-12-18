from database.base_model import Base
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

class TelegramUser(Base):
    __tablename__ = 'telegram_users'
    
    telegram_id = Column(
        Integer,
        primary_key=True,
        unique=True
    )
    username = Column(
        String(100),
        nullable=True
    )
    first_name = Column(
        String(100),
        nullable=True
    )
    last_name = Column(
        String(100),
        nullable=True
    )
    registration_date = Column(
        DateTime,
        server_default=func.now()
    )
    last_activity = Column(
        DateTime,
        onupdate=func.now()
    )
    
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

