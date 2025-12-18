from database.base_model import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

class Task(Base):
    __tablename__ = 'tasks'
    
    task_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    title = Column(
        String(200),
        nullable=False
    )
    description = Column(
        String(1000),
        nullable=True
    )
    created_at = Column(
        DateTime,
        server_default=func.now()
    )
    completed = Column(
        Boolean,
        default=False
    )
    completed_at = Column(
        DateTime,
        nullable=True
    )
    priority = Column(
        Integer,
        default=1  # 1-низкий, 2-средний, 3-высокий
    )
    
    telegram_id = Column(
        Integer,
        ForeignKey('telegram_users.telegram_id', ondelete='CASCADE'),
        nullable=False
    )
    
    user = relationship("TelegramUser", back_populates="tasks")

