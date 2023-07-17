import base64
import io
import re
import uuid
from pathlib import Path

import requests
from PIL import Image

import config
from msgplugins.chatgpt.chatgpt import chat

base_url = config.SD_HTTP_API + "/sdapi/v1/"

session = requests.Session()
session.timeout = 30


def trans2en(txt: str):
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\uff00-\uffef]')  # Unicode范围：中文字符
    # if not match_chinese:
    #     prompt = "下面这段文字是否包含了任何不良的信息，如果包含了返回'1dog'，如果没有包含则返回原文(不要加任何前后缀): \n"
    #     return txt
    # else:
    #     prompt = "从现在开始你是一名基于输入描述的绘画AI提示词生成器，你会根据我输入的中文描述，生成符合主题的完整提示词。请注意，你生成后的内容服务于一个绘画AI，它只能理解具象的提示词而非抽象的概念，我将提供简短的描述，以便生成器可以为我提供准确的提示词。我希望生成的提示词能够包含人物的姿态、服装、妆容、情感表达和环境背景等细节，并且在必要时进行优化和重组以提供更加准确的描述，并且过滤掉不良的、不适合公共场所、NSFW的相关词汇，以便更好地服务于我的绘画AI，请严格遵守此条规则，也只输出翻译后的英文内容。请模仿结构示例生成准确提示词。示例输入：一位坐在床上的少女。 示例输出：1girl, sitting on, hand on own chest, head tilt, (indian_style:1.1), light smile, aqua eyes, (large breasts:1.2), blondehair, shirt, pleated_skirt, school uniform, (torn pantyhose:0.9), black garter belt, mary_janes, flower ribbon, glasses, looking at viewer, on bed,indoors,between legs. 请开始将下面的句子生成我需要的英文内容\n"
    prompt = "如果下面的内容或者翻译后的内容有不良的词汇就输出'1dog';(否则翻译成英文，不能翻译的词汇则保持原样.请直接输出翻译后的结果不要带任何附加信息):\n"
    result = chat("", prompt + txt)
    match_chinese = re.search(chinese_pattern, result)
    if match_chinese:
        return ""
    return result


def __api_get(url_path: str, params: dict = None):
    url = base_url + url_path
    resp = session.get(url, params=params)
    return resp.json()


def __api_post(url_path: str, data: dict = None):
    url = base_url + url_path
    resp = session.post(url, json=data)
    return resp.json()


def txt2img(txt: str, width: int = 512, height: int = 512):
    """
    文字转图片
    :param txt: 文字
    :param width: 图片宽度
    :param height: 图片高度
    :return: 图片的base64编码
    """

    txt = txt.lower().replace("nsfw", "")
    if "I'm sorry" in txt:
        txt = ""
    txt = trans2en(txt)
    # 添加lora
    res_loras = __api_get("loras")
    for lora in res_loras:
        txt += f",<lora:{lora['name']}:1>,"
    data = {
        "prompt": "(masterpiece:1,2), best quality, masterpiece, highres, original, extremely detailed wallpaper, perfect lighting,(extremely detailed CG:1.2)," + txt,
        "negative_prompt": "(NSFW:2), (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, age spot, (ugly:1.331), (duplicate:1.331), (morbid:1.21), (mutilated:1.21), (tranny:1.331), mutated hands, (poorly drawn hands:1.5), blurry, (bad anatomy:1.21), (bad proportions:1.331), extra limbs, (disfigured:1.331), (missing arms:1.331), (extra legs:1.331), (fused fingers:1.61051), (too many fingers:1.61051), (unclear eyes:1.331), lowers, bad hands, missing fingers, extra digit,bad hands, missing fingers, (((extra arms and legs))),NSFW, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, age spot, (ugly:1.331), (duplicate:1.331), (morbid:1.21), (mutilated:1.21), (tranny:1.331), mutated hands, (poorly drawn hands:1.5), blurry, (bad anatomy:1.21), (bad proportions:1.331), extra limbs, (disfigured:1.331), (missing arms:1.331), (extra legs:1.331), (fused fingers:1.61051), (too many fingers:1.61051), (unclear eyes:1.331), lowers, bad hands, missing fingers, extra digit,bad hands, missing fingers, (((extra arms and legs))),",
        "steps": 20,
        "width": width,
        "height": height,
        "sampler_index": "DPM++ 2M Karras"
    }
    r = __api_post("txt2img", data)
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
        image_path = Path(__file__).parent / (str(uuid.uuid4()) + ".png")
        image.save(image_path)
        # image.show()
        return str(image_path)


def __get_models():
    res = __api_get("sd-models")
    options = __api_get("options")
    current_model_hash = options["sd_checkpoint_hash"]
    models = []
    for m in res:
        model_name = m["model_name"]
        if current_model_hash == m["sha256"]:
            model_name = f"*当前模型：{model_name}*"
        models.append(model_name)
    models = "\n".join(models)
    return models


def __get_loras():
    res = __api_get("loras")
    # loras = [{"name": lora["name"], "frequency_tag": lora["metadata"]["ss_tag_frequency"].keys()} for lora in res]
    loras = []
    for lora in res:
        trigger_tags = lora["metadata"].get("ss_tag_frequency", {}).keys()
        if not trigger_tags:
            continue
        trigger_tags = [tag.split("_")[1] for tag in trigger_tags]
        trigger_tags = "，".join(trigger_tags)
        loras.append(f"{lora['name']}：{trigger_tags}")

    loras = "\n\n".join(loras)
    return loras


def get_models():
    res = f"模型列表：\n{__get_models()}"
    return res


def get_loras():
    res = f"lora列表：\n{__get_loras()}"
    return res


def set_model(model_name: str):
    res = __api_get("sd-models")
    model = filter(lambda m: model_name in m["model_name"], res)
    model = list(model)
    if len(model) == 0:
        return f"模型{model_name}不存在"
    model_name = model[0]["model_name"]
    data = {
        "sd_model_checkpoint": model_name
    }
    r = __api_post("options", data)
    return f"模型已切换为：{model_name}"


if __name__ == '__main__':
    # print(txt2img("1girl", 1024, 768))
    # print(txt2img("1girl,keqingdef,wake"))
    print(txt2img("1girl, sky, sunshine, flowers,鸟在天上飞，阴部"))
    # print(txt2img("一个女孩在床上展示她的头发"))
    # print(txt2img("一个女孩在床上展示她的胸部"))
    # print(txt2img("(watercolor pencil),1girl, nude,nipples,full body, spread leg, arm up, large breasts,shaved pussy,((heart-shaped pupils)),(uncensored) , sexually suggestive,saliva trail, suggestive fluid, (cum on body), tattoo, sweating, presenting, exhibitionism, wet cream dripping, female orgasm, liquid crystal fluid radiant cinematic lighting, solo uncensored cute assertive drunk blush"))
    # print(get_models())
    # text = "(masterpiece:1,2), best quality, masterpiece, highres, original, extremely detailed wallpaper, perfect lighting,(extremely detailed CG:1.2),"
    # pattern = re.compile(r'[\u4e00-\u9fff\uff00-\uffef]')  # Unicode范围：中文字符
    # match = res.search(pattern, text)
    # print(match)
    # print(get_models())
    # print(set_model("二次元：AbyssOrangeMix2_sfw"))
    # print(set_model("国风4"))
    # print(trans2en("裸体 女孩"))
