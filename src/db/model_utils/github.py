from src.db import init_db
from src.db.models.github import Subscriber

session = init_db()


def get_subscribers_from_db(event: str, action: str) -> list[Subscriber]:
    return session.query(Subscriber).filter(Subscriber.event == event, Subscriber.action == action).all()


def add_subscriber_to_db(group_id: str, platform: str, owner: str, repo: str, event: str, action: str = ''):
    # 查询是否已经存在
    e = session.query(Subscriber).filter(Subscriber.group_id == group_id, Subscriber.platform == platform,
                                         Subscriber.owner == owner, Subscriber.repo == repo, Subscriber.event == event,
                                         Subscriber.action == action).exist()
    if e:
        return

    s = Subscriber(group_id=group_id, platform=platform, author=owner, repo=repo, event=event, action=action)
    session.add(s)
    session.commit()

