from nonebot import get_plugin_config
from pydantic import BaseModel

class ConfigBiliCard(BaseModel):
    bili_card_ai_model: str = "openai/gpt-4o-mini"


def get_config() -> ConfigBiliCard:
    """
    获取BiliCard配置
    :return: ConfigBiliCard实例
    """
    return get_plugin_config(ConfigBiliCard)

bilicard_config = get_config()