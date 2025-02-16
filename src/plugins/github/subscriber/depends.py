from typing import Annotated, TypeAlias
from nonebot import Bot
from nonebot.params import Depends
from nonebot.adapters.github import Event

from src.db.models.github import Subscriber
from src.db.model_utils.github import get_subscribers_from_db


def get_subscribers(bot: Bot, event: Event):
    action = event.payload.get('action') if isinstance(event.payload, dict) else event.payload.action
    return get_subscribers_from_db(event.name, action)


Subscribers: TypeAlias = Annotated[list[Subscriber], Depends(get_subscribers)]
