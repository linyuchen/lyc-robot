from typing import Literal

from src.db import init_db
from src.db.models.blacklist import BlackUserList, BlackGroupList

db_session = init_db()

black_user_list: list[str] = [i.target_id for i in db_session.query(BlackUserList).all()]

black_group_list: list[str] = [i.target_id for i in db_session.query(BlackGroupList).all()]


def add_black_target(target_type: Literal['user', 'group'], target_id: str):
    target_id = str(target_id)
    black_list = black_user_list if target_type == 'user' else black_group_list
    model = BlackUserList if target_type == 'user' else BlackGroupList
    if target_id in black_list:
        return
    target = model(target_id=target_id)
    db_session.add(target)
    db_session.commit()
    black_list.append(target_id)


def del_black_target(target_type: Literal['user', 'group'], target_id: str):
    target_id = str(target_id)
    black_list = black_user_list if target_type == 'user' else black_group_list
    model = BlackUserList if target_type == 'user' else BlackGroupList
    if target_id not in black_list:
        return
    target = db_session.query(model).filter(model.target_id == target_id).first()
    if target:
        db_session.delete(target)
        db_session.commit()
    black_list.remove(target_id)


def check_black_target(target_type: Literal['user', 'group'], target_id: str) -> bool:
    black_list = black_user_list if target_type == 'user' else black_group_list
    return target_id in black_list
