import uuid
import tempfile
from pathlib import Path
from urllib.parse import quote

import requests
# import gradio_client

from .utils import wav2silk_base64, wav2amr

# client = gradio_client.Client("https://v2.genshinvoice.top/")

speakers = ['丹恒', '克拉拉', '穹', '「信使」', '史瓦罗', '彦卿', '晴霓', '杰帕德', '素裳', '绿芙蓉', '罗刹', '艾丝妲',
            '黑塔', '丹枢', '希露瓦', '白露', '费斯曼', '停云', '可可利亚', '景元', '螺丝咕姆', '青镞', '公输师傅',
            '卡芙卡', '大毫', '驭空', '半夏', '奥列格', '娜塔莎', '桑博', '瓦尔特', '阿兰', '伦纳德', '佩拉', '卡波特',
            '帕姆', '帕斯卡', '青雀', '三月七', '刃', '姬子', '布洛妮娅', '希儿', '星', '符玄', '虎克', '银狼', '镜流',
            '「博士」', '「大肉丸」', '九条裟罗', '佐西摩斯', '刻晴', '博易', '卡维', '可莉', '嘉玛', '埃舍尔',
            '塔杰·拉德卡尼', '大慈树王', '宵宫', '康纳', '影', '枫原万叶', '欧菲妮', '玛乔丽', '珊瑚', '田铁嘴', '砂糖',
            '神里绫华', '罗莎莉亚', '荒泷一斗', '莎拉', '迪希雅', '钟离', '阿圆', '阿娜耶', '阿拉夫', '雷泽', '香菱',
            '龙二', '「公子」', '「白老先生」', '优菈', '凯瑟琳', '哲平', '夏洛蒂', '安柏', '巴达维', '式大将', '斯坦利',
            '毗伽尔', '海妮耶', '爱德琳', '纳西妲', '老孟', '芙宁娜', '阿守', '阿祇', '丹吉尔', '丽莎', '五郎', '元太',
            '克列门特', '克罗索', '北斗', '埃勒曼', '天目十五', '奥兹', '恶龙', '早柚', '杜拉夫', '松浦', '柊千里',
            '甘雨', '石头', '纯水精灵？', '羽生田千鹤', '莱依拉', '菲谢尔', '言笑', '诺艾尔', '赛诺', '辛焱', '迪娜泽黛',
            '那维莱特', '八重神子', '凯亚', '吴船长', '埃德', '天叔', '女士', '恕筠', '提纳里', '派蒙', '流浪者',
            '深渊使徒', '玛格丽特', '珐露珊', '琴', '瑶瑶', '留云借风真君', '绮良良', '舒伯特', '荧', '莫娜', '行秋',
            '迈勒斯', '阿佩普', '鹿野奈奈', '七七', '伊迪娅', '博来', '坎蒂丝', '埃尔欣根', '埃泽', '塞琉斯', '夜兰',
            '常九爷', '悦', '戴因斯雷布', '笼钓瓶一心', '纳比尔', '胡桃', '艾尔海森', '艾莉丝', '菲米尼', '蒂玛乌斯',
            '迪奥娜', '阿晃', '阿洛瓦', '陆行岩本真蕈·元素生命', '雷电将军', '魈', '鹿野院平藏', '「女士」', '「散兵」',
            '凝光', '妮露', '娜维娅', '宛烟', '慧心', '托克', '托马', '掇星攫辰天君', '旁白', '浮游水蕈兽·元素生命',
            '烟绯', '玛塞勒', '百闻', '知易', '米卡', '西拉杰', '迪卢克', '重云', '阿扎尔', '霍夫曼', '上杉', '久利须',
            '嘉良', '回声海螺', '多莉', '安西', '德沃沙克', '拉赫曼', '林尼', '查尔斯', '深渊法师', '温迪', '爱贝尔',
            '珊瑚宫心海', '班尼特', '琳妮特', '申鹤', '神里绫人', '艾伯特', '萍姥姥', '萨赫哈蒂', '萨齐因', '阿尔卡米',
            '阿贝多', 'anzai', '久岐忍', '九条镰治', '云堇', '伊利亚斯', '埃洛伊', '塞塔蕾', '拉齐', '昆钧', '柯莱',
            '沙扎曼', '海芭夏', '白术', '空', '艾文', '芭芭拉', '莫塞伊思', '莺儿', '达达利亚', '迈蒙', '长生',
            '阿巴图伊', '陆景和', '莫弈', '夏彦', '左然']


def tts(text: str, speaker: str = "可莉") -> bytes:
    # res = client.predict(text, f"{speaker}_ZH", 0.5, 0.6, 0.9, 1, "auto",
    #                      None, "Happy", "Text prompt", "", 0.7, fn_index=0)
    # wav_path = res[1]
    # url = f"https://genshinvoice.top/api?speaker={quote(speaker)}_ZH&text={quote(text)}=wav&length=1&noise=0.5&noisew=0.9&sdp_ratio=0.2&language=ZH"
    # data = requests.get(url).content
    # wav_path = Path(tempfile.mktemp(suffix=".wav"))
    # with open(wav_path, "wb") as f:
    #     f.write(data)
    url = "https://bv2.firefly.matce.cn/run/predict"
    # url = "https://v2.genshinvoice.top/run/predict"
    data = {
        "data": [text, f"{speaker}_ZH", 0.5, 0.6, 0.9, 1, "auto", True, 1, 0.2, None, "Happy", "", "", 0.7],
        "fn_index": 0,
        "session_hash": str(uuid.uuid4())
    }
    data = requests.post(url, json=data)
    data = data.json()
    wav_url = data.get("data", ['', {}])[1].get("name")
    if not wav_url:
        raise Exception("生成语音失败")
    # wav_url = "https://v2.genshinvoice.top/file=" + wav_url
    wav_url = "https://bv2.firefly.matce.cn/file=" + wav_url
    data = requests.get(wav_url).content
    return data
    # wav_path = Path(tempfile.mktemp(suffix=".wav"))
    # with open(wav_path, "wb") as f:
    #     f.write(data)
    # return wav2amr(wav_path)
    # return data
