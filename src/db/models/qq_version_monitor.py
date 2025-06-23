from sqlalchemy import Column, String, PrimaryKeyConstraint

from src.db.models.base import Base


class QQVersionSubscriber(Base):
    __tablename__ = 'qq_version_subscriber'
    platform = Column(String)
    group_id = Column(String(64), comment="群号")
    __table_args__ = (
        PrimaryKeyConstraint('platform', 'group_id'),
    )

class QQVersion(Base):
    __tablename__ = 'qq_version'
    version = Column(String(64), primary_key=True, comment="QQ版本号")
    detail = Column(String, comment="更新详情")