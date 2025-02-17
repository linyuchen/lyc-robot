from typing import TypeAlias, Annotated

from nonebot.internal.params import Depends
from nonebot_plugin_uninfo import Uninfo

from src.db.model_utils.game_xiuxian import get_user
from src.db.models.game_xiuxian import GameXiuxianUser


def get_game_user(session: Uninfo):
    group_id = session.group.id if session.scene.is_group else None
    game_user = get_user(session.user.id, session.adapter.value, group_id, session.user.name)
    return game_user


GameUser: TypeAlias = Annotated[GameXiuxianUser, Depends(get_game_user)]