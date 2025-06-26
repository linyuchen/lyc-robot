import dataclasses
from typing import Annotated, TypeAlias

from nonebot.internal.params import Depends
from nonebot_plugin_uninfo import Uninfo

from src.plugins.common.platforms import get_uni_platform


@dataclasses.dataclass
class GroupInfo:
    platform: str
    group_id: str


def get_group(session: Uninfo):
    platform = get_uni_platform(session.adapter.value)
    group_id = session.group.id if session.scene.is_group else None
    if not group_id:
        return None
    return GroupInfo(platform, group_id)


Group: TypeAlias = Annotated[GroupInfo, Depends(get_group)]
