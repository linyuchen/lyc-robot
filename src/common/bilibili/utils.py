import re


def check_is_b23(text: str) -> list[str]:
    b23tv = re.findall("(?<=b23.tv/)\w*", text)
    return b23tv


def get_bv_id(text: str):
    # 正则检查B站视频BV号
    result = re.findall(r"(?<=BV)\w+", text, re.I)
    return result and result[0] or ""


def get_av_id(text: str):
    result = re.findall(r"(?<=av)\d{4,}", text, re.I)
    return result and result[0] or ""
