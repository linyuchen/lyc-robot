import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.common.bilibili.api import get_video_info, get_subtitle
from src.common.bilibili.session import session
from src.common.bilicard.config import bilicard_config
from ..ai_chat.chat_engine import chat
from ..stringplus import split_lines

# session = requests.session()


# 获取评论，https://api.bilibili.com/x/v2/reply/wbi/main?oid=683107021&type=1&mode=3
# todo: 获取指定评论，然后判断是否是up的评论，将此评论也放到ai总结里面去

async def gen_text(bv_id: str) -> str:
    video_info = await get_video_info(bv_id)
    if not video_info:
        return ""
    # 利用video_info生成视频简要说明
    title = video_info["title"]
    desc = video_info["desc"]
    duration = video_info["duration"]
    view = video_info["view"]
    danmu = video_info["danmu"]
    like = video_info["like"]
    coin = video_info["coin"]
    share = video_info["share"]
    favorite = video_info["favorite"]
    owner = video_info["owner"]
    upload_time = video_info["upload_time"]
    # desc超过30字则截断
    # if len(desc) > 40:
    #     desc = desc[:40] + "..."
    # 组装成文字
    text = f"标题：{title}\n\n" \
           f"简介：{desc}\n\n" \
           f"时长：{duration:<7}播放：{view:<7}\n" \
           f"弹幕：{danmu:<7}点赞：{like:<7}\n" \
           f"硬币：{coin:<7}收藏：{favorite:<7}\n" \
           f"分享：{share:<7}上传时间：{upload_time}\n作者：{owner}\n"

    return text


async def get_video_summary_by_ai(aid, cid) -> str:
    subtitle = await get_subtitle(aid, cid)
    if subtitle:
        res = await chat("", "#有如下一个视频，请用中文完整的总结:\n" + subtitle, model_name=bilicard_config.bili_card_ai_model)
        return res
    else:
        return ""


async def gen_image(video_info: dict) -> BytesIO:
    base_path = Path(__file__).parent
    # save_path = base_path / f"test.png"
    save_path = tempfile.mktemp(suffix=".png")
    image = Image.new("RGBA", (560, 470 + 15), (255, 255, 255, 255))
    # image.paste((220, 220, 220), (0, 480, 530, 620))
    cover = Image.open(BytesIO(
        (await session.get(video_info["cover_url"])).content)).resize((560, 315), Image.LANCZOS)
    cover_size = (0, 0, 560, 315)

    # mask = Image.new("L", image.size, (255, 255, 255))
    # # 创建 draw 对象
    # draw = ImageDraw.Draw(mask)
    # # 绘制圆角矩形
    # draw.rounded_rectangle((0, 0, image.width, image.height), radius=20, fill=0)
    #
    # # 将 mask 应用到 image 上
    # image.putalpha(mask)
    # 创建遮罩层
    # mask = Image.new("L", cover.size, 0)
    # draw = ImageDraw.Draw(mask)
    # # 绘制圆角矩形
    # draw.rounded_rectangle((0, 0, cover.width, cover.height), radius=20, fill=255)
    # # 将遮罩层与 cover 合并
    # cover.putalpha(mask)

    # 将带有圆角的 cover 贴到 image 上
    image.paste(cover, cover_size)

    # 添加一个灰色透明层，用来显示播放数量，弹幕数量和视频时长
    mask = Image.new("RGBA", (560, 50), (150, 150, 150, 170))
    image_play_icon = Image.open(base_path / "icon-play.png").resize((40, 40))
    image.paste(mask, (0, cover.height - 45), mask)

    # 添加播放数量
    image.paste(image_play_icon, (20, cover.height - 45), image_play_icon)
    text_draw = ImageDraw.Draw(image)
    font = get_font()
    view_count = video_info["view"]
    if view_count >= 10000:
        # 超过一万播放量则显示万,保留一位小数
        view_count = f"{view_count / 10000:.1f}万"
    text_draw.text((70, cover.height - 35), f"{view_count}", font=font)

    # 添加弹幕数量
    image_danmu = Image.open(base_path / "icon-danmu.png").resize((40, 40))
    image.paste(image_danmu, (190, cover.height - 45), image_danmu)
    text_draw = ImageDraw.Draw(image)
    danmu_count = video_info["danmu"]
    text_draw.text((240, cover.height - 35), f"{danmu_count}", font=font)
    # 添加视频时长
    hour, minute = video_info["duration"].split(":")
    text_draw.text((500, cover.height - 35), f"{hour:0>2}:{minute:0>2}", font=font)
    # 添加标题
    font = get_font(32)
    line_width = 16
    title = video_info["title"]
    max_title_len = line_width * 3 - 5
    if len(title) > max_title_len:
        title = title[:max_title_len] + "..."

    next_height = cover.height + 10
    for i, line in enumerate(split_lines(title, line_width)):
        next_height = cover.height + 10 + i * 40
        text_draw.text((20, next_height), f"{line}", font=font,
                       fill=(0, 0, 0))

    font = get_font(25)
    # 作者信息
    text_draw.text((20, cover.height + 140), f"UP: {video_info['owner']}", font=font, fill=(0, 0, 0))
    # 添加视频上传时间
    text_draw.text((340, cover.height + 140), f" {video_info['upload_time']}", font=font, fill=(0, 0, 0))
    temp_img = BytesIO()
    image.save(temp_img, format='PNG')
    return temp_img


def get_font(size=20):
    font = ImageFont.truetype(str(Path(__file__).parent.parent.parent / "common/fonts/仓耳舒圆体.ttf"), size)
    return font
