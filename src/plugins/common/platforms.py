from typing import Literal
TYPE_PLATFORM = Literal['QQ', 'Telegram', 'Unknown']

adapter_platforms: dict[str, TYPE_PLATFORM] = {
    'OneBot V11': 'QQ',
    'OneBot V12': 'QQ',
    'Telegram': 'Telegram',
}

def get_uni_platform(platform: str) -> TYPE_PLATFORM:
    """
    Convert the platform name to a unified format.

    Args:
        platform (str): The platform name to convert.

    Returns:
        str: The unified platform name.
    """
    return adapter_platforms.get(platform, 'Unknown')  # Default to the original if not found