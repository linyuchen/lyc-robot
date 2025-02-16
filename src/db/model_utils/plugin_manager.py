from nonebot import get_loaded_plugins

from src.db import init_db
from src.db.models.plugin_manager import PluginManager


def find_plugin_by_name(name: str):
    plugins = get_loaded_plugins()
    for plugin in plugins:
        if plugin.metadata:
            if plugin.metadata.name == name:
                return plugin
        else:
            if plugin.id_ == name:
                return plugin
    return None


db_session = init_db()

config_cache: dict[str, PluginManager] = {}


def init_plugin_manager_config(plugin_ids: [str]) -> dict[str, PluginManager]:
    if config_cache:
        return config_cache
    plugin_configs = db_session.query(PluginManager).filter(PluginManager.plugin_id.in_(plugin_ids)).all()
    plugin_configs = {plugin_config.plugin_id: plugin_config for plugin_config in plugin_configs}
    config_cache.update(plugin_configs)
    return plugin_configs


def check_group_enable(plugin_id: str, group_id: str | int):
    c = config_cache.get(plugin_id)
    if not c:
        return True
    return group_id not in c.disable_groups


def check_global_enable(plugin_id: str):
    c = config_cache.get(plugin_id)
    if not c:
        return True
    return not c.global_disable


def set_group_enable(plugin_id: str, group_id: str | int, enable: bool):
    c = config_cache.get(plugin_id)
    if not c:
        c = config_cache[plugin_id] = PluginManager(plugin_id=plugin_id, global_disable=False, disable_groups=[])
        db_session.add(c)
    if enable:
        if group_id in c.disable_groups:
            c.disable_groups.remove(group_id)
    else:
        if group_id not in c.disable_groups:
            c.disable_groups.append(group_id)
    db_session.commit()


def set_global_enable(plugin_id: str, enable: bool):
    c = config_cache.get(plugin_id)
    if not c:
        c = config_cache[plugin_id] = PluginManager(plugin_id=plugin_id, global_disable=not enable, disable_groups=[])
        db_session.add(c)
    c.global_disable = not enable
    db_session.commit()
