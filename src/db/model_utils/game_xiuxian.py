from typing import Tuple

import pytz

from datetime import datetime

from sqlalchemy import extract
from src.db import init_db
from src.db.models.game_xiuxian import GameXiuxianUser, GameXiuxianGroupUser, GameXiuxianSign

session = init_db()


def get_user(user_id: str, platform: str, group_id: str = None, username: str = None) -> GameXiuxianUser:
    user = session.query(GameXiuxianUser).filter(GameXiuxianUser.user_id == user_id,
                                                 GameXiuxianUser.platform == platform).first()
    if not user:
        user = GameXiuxianUser(user_id=user_id, platform=platform)
        session.add(user)
        session.commit()
    if group_id:
        group_user: GameXiuxianGroupUser = session.query(GameXiuxianGroupUser).filter(
            GameXiuxianGroupUser.user_id == user_id, GameXiuxianGroupUser.group_id == group_id,
            GameXiuxianGroupUser.platform == platform).first()
        if group_user is not None:
            if username:
                group_user.username = username
        else:
            group_user = GameXiuxianGroupUser(user_id=user_id, platform=platform, group_id=group_id, username=username)
            session.add(group_user)
        session.commit()

    return user

def save_user(user: GameXiuxianUser) -> GameXiuxianUser:
    if not get_user(user_id=user.user_id, platform=user.platform):
        session.add(user)
    session.commit()
    return user


def sign(user_id: str, platform: str, group_id: str = None, username: str = None) -> bool:
    user = get_user(user_id=user_id, platform=platform, group_id=group_id, username=username)
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    exist_sign = session.query(GameXiuxianSign).filter(GameXiuxianSign.user_id == user.user_id,
                                                       extract('year', GameXiuxianSign.sign_time) == now.year,
                                                       extract('month', GameXiuxianSign.sign_time) == now.month,
                                                       extract('day', GameXiuxianSign.sign_time) == now.day).count()
    if not exist_sign:
        s = GameXiuxianSign(user_id=user.user_id, sign_time=now)
        session.add(s)
        session.commit()
        return True
    return False


def get_top(group_id: str = None, platform: str = None, top: int = 20):
    query = (
        session.query(GameXiuxianUser.user_id,
                      GameXiuxianUser.platform,
                      GameXiuxianUser.point
                      )

    )
    if group_id:
        query = (query.join(GameXiuxianGroupUser, GameXiuxianUser.user_id == GameXiuxianGroupUser.user_id)
                 .filter(GameXiuxianGroupUser.group_id == group_id, GameXiuxianGroupUser.platform == platform)
                 ).add_columns(GameXiuxianGroupUser.username)
    query = query.order_by(GameXiuxianUser.point.desc()).limit(top)
    return query.all()
