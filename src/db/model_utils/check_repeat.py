from src.db import init_db
from src.db.models.check_repeat import CheckRepeatConfig

session = init_db()


cache = {}


def get_ban_duration(group_id: str, platform: str) -> int:
    if (group_id, platform) in cache:
        return cache[(group_id, platform)]
    else:
        cache[(group_id, platform)] = session.query(CheckRepeatConfig).filter(CheckRepeatConfig.group_id == group_id,
                                                    CheckRepeatConfig.platform == platform).first().ban_duration
        return cache[(group_id, platform)]


def set_ban_duration(group_id: str, platform: str, ban_duration: int):
    cache[(group_id, platform)] = ban_duration
    if session.query(CheckRepeatConfig).filter(CheckRepeatConfig.group_id == group_id,
                                               CheckRepeatConfig.platform == platform).count() == 0:
        session.add(CheckRepeatConfig(group_id=group_id, platform=platform, ban_duration=ban_duration))
    else:
        session.query(CheckRepeatConfig).filter(CheckRepeatConfig.group_id == group_id,
                                                 CheckRepeatConfig.platform == platform).update(
            {'ban_duration': ban_duration})
    session.commit()
