from datetime import datetime, timezone, timedelta

from src.db import init_db
from src.db.models.newapi_model_monitor import ModelMonitor

CST = timezone(timedelta(hours=8))
db_session = init_db()


def add_monitor(model_name: str, target_id: str, platform: str, is_private: bool) -> bool:
    existing = db_session.query(ModelMonitor).filter_by(
        model_name=model_name, target_id=target_id, platform=platform
    ).first()
    if existing:
        return False
    monitor = ModelMonitor(
        model_name=model_name,
        target_id=target_id,
        platform=platform,
        is_private=is_private,
        last_status=None,
        created_at=datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
    )
    db_session.add(monitor)
    db_session.commit()
    return True


def remove_monitor(model_name: str, target_id: str, platform: str) -> bool:
    monitor = db_session.query(ModelMonitor).filter_by(
        model_name=model_name, target_id=target_id, platform=platform
    ).first()
    if not monitor:
        return False
    db_session.delete(monitor)
    db_session.commit()
    return True


def get_all_monitors() -> list[ModelMonitor]:
    return db_session.query(ModelMonitor).all()


def get_monitors_by_target(target_id: str, platform: str) -> list[ModelMonitor]:
    return db_session.query(ModelMonitor).filter_by(
        target_id=target_id, platform=platform
    ).all()


def update_status(monitor_id: int, status: bool):
    monitor = db_session.query(ModelMonitor).filter_by(id=monitor_id).first()
    if monitor:
        monitor.last_status = status
        db_session.commit()
