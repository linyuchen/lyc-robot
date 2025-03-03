from sqlalchemy import Column, INT, String

from src.db.models.base import Base


class CheckRepeatConfig(Base):
    __tablename__ = 'check_repeat_config'

    id = Column(INT, primary_key=True, autoincrement=True)
    group_id = Column(String)
    platform = Column(String)
    ban_duration = Column(INT)