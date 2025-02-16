from src.db.models.base import Base
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

LEVEL_POINTS = [
    0,
    10000,
    100000,
    1000000,
    10000000,
    100000000,
    1000000000,
    10000000000,
    100000000000,
    200000000000,
]

LEVEL_NAMES = ["人凡期", "灵基期", "纳真期", "破虚期", "辟神期", "合道期", "易位期", "泰剧期", "超凡期", "仙道者"]


class GameXiuxianUser(Base):
    __tablename__ = 'game_xiuxian_user'
    user_id = Column(String, primary_key=True)
    platform = Column(String, primary_key=True)
    point = Column(Integer, default=0)
    groups = relationship('GameXiuxianGroupUser', backref='user',
                          primaryjoin='GameXiuxianUser.user_id == GameXiuxianGroupUser.user_id, GameXiuxianUser.platform == GameXiuxianGroupUser.platform')

    @property
    def level(self) -> int:
        level = 0
        for index, point in enumerate(LEVEL_POINTS):
            if self.point <= point:
                level = LEVEL_NAMES[index]
        return level

    @property
    def level_name(self) -> str:
        return LEVEL_NAMES[self.level]


class GameXiuxianGroupUser(Base):
    __tablename__ = 'game_xiuxian_group_user'
    user_id = Column(String, primary_key=True)
    group_id = Column(String, primary_key=True)
    platform = Column(String, primary_key=True)
    username = Column(String)


class GameXiuxianSign(Base):
    __tablename__ = 'game_xiuxian_sign'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    sign_time = Column(DateTime)