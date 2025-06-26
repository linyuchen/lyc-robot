from src.db import init_db
from src.db.models.qq_version_monitor import QQVersionSubscriber, QQVersion

db_session = init_db()


def add_subscriber(platform: str, group_id: str):
    """
    Add a subscriber for a specific platform and group ID.
    """
    # 先查找已存在
    existing_subscriber = db_session.query(QQVersionSubscriber).filter_by(platform=platform, group_id=group_id).first()
    if existing_subscriber:
        return  # 如果已存在订阅者，则不添加
    subscriber = QQVersionSubscriber(platform=platform, group_id=group_id)
    db_session.add(subscriber)
    db_session.commit()

def remove_subscriber(platform: str, group_id: str):
    """
    Remove a subscriber for a specific platform and group ID.
    """
    subscriber = db_session.query(QQVersionSubscriber).filter_by(platform=platform, group_id=group_id).first()
    if subscriber:
        db_session.delete(subscriber)
        db_session.commit()


def get_subscribers():
    """
    Get all subscribers.
    """
    return db_session.query(QQVersionSubscriber).all()


def save_version(version: str, detail: str):
    """
    Save the QQ version and its details.
    """
    existing_version = db_session.query(QQVersion).filter_by(version=version).first()
    if existing_version:
        return  # 如果版本已存在，则不添加
    version_entry = QQVersion(version=version, detail=detail)
    db_session.add(version_entry)
    db_session.commit()


def get_version(version: str):
    """
    Get the details of a specific QQ version.
    """
    return db_session.query(QQVersion).filter_by(version=version).first()


def get_versions(count=10) -> list[QQVersion]:
    """
    Get the latest QQ versions.
    """
    return db_session.query(QQVersion).order_by(QQVersion.version.desc()).limit(count).all()