from src.db import init_db
from src.db.models.group_cmd_manager import GroupIgnoreCMD

db_session = init_db()

group_ignore_cmds: [str, GroupIgnoreCMD] = {}
group_ignore_cmds.update({g.group_id: g for g in db_session.query(GroupIgnoreCMD).all()})


def check_group_message(group_id: str, message: str) -> bool:
    group_id = str(group_id)
    group: GroupIgnoreCMD = group_ignore_cmds.get(group_id)
    if not group:
        return True
    for cmd in group.cmds:
        if message.strip().startswith(cmd):
            return False
    return True


def add_group_ignore_cmd(group_id: str, cmd: str):
    group_id = str(group_id)
    group = group_ignore_cmds.get(group_id)
    if not group:
        group = GroupIgnoreCMD(group_id=group_id, cmds=[])
        db_session.add(group)
    if cmd not in group.cmds:
        group.cmds.append(cmd)
    db_session.commit()


def remove_group_ignore_cmd(group_id: str, cmd: str):
    group_id = str(group_id)
    group: GroupIgnoreCMD = group_ignore_cmds.get(group_id)
    if not group:
        return
    if cmd not in group.cmds:
        return
    else:
        group.cmds.remove(cmd)
    db_session.commit()


def get_group_ignore_cmds(group_id: str) -> list[str]:
    group_id = str(group_id)
    if group := group_ignore_cmds.get(group_id):
        return group.cmds
    return []
