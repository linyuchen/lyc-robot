from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint

from src.db.models.base import Base


class ModelMonitor(Base):
    __tablename__ = "model_monitor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    last_status = Column(Boolean, nullable=True)
    created_at = Column(String)

    __table_args__ = (
        UniqueConstraint("model_name", "target_id", "platform", name="uq_model_target"),
    )
