import base64
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Self


# from .friendmsg import FriendMsg
# from .groupmsg import GroupMsg


class MessageSegment:
    """
    用于封装成发送的消息
    """

    def __init__(self, msg_type: Optional[str] = None, content: Optional[str] = None):
        self.msg_id = None
        self.msg_type = msg_type
        self.content = content
        self.quote_msg = None  # FriendMsg or GroupMsg
        self.is_at_me = False
        self.is_at_other = False
        self.is_at_all = False
        self.origin_data: List[Tuple[str, str]] = []
        if msg_type and content:
            self.origin_data.append((msg_type, content))

    @staticmethod
    def text(content: str):
        return MessageSegment("Plain", content)

    @staticmethod
    def image(image_url: str):
        return MessageSegment("ImageUrl", image_url)

    @staticmethod
    def image_path(path: str | Path | list[Path]):
        paths = []
        if not isinstance(path, list):
            paths = [path]
        else:
            paths = path
        _msg = MessageSegment("ImagePath", str(paths[0]))
        for path in paths[1:]:
            _msg += MessageSegment("ImagePath", str(path))
        return _msg

    @staticmethod
    def image_b64(data: str):
        return MessageSegment("ImageBase64", data)

    @staticmethod
    def voice_path(path: str | Path):
        return MessageSegment("VoicePath", str(path))

    @staticmethod
    def voice_base64(base64_data):
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]
        return MessageSegment("VoiceBase64", base64_data)

    @staticmethod
    def at(qq: str, is_at_me: bool = False, is_at_other=False, is_at_all=False):
        ms = MessageSegment("At", qq)
        ms.is_at_me = is_at_me
        ms.is_at_other = is_at_other
        ms.is_at_all = is_at_all
        return ms

    @staticmethod
    def reply(msg_id: str):
        ms = MessageSegment("reply", msg_id)
        return ms

    @staticmethod
    def to_onebot11_data(msg_type: str, content: str):
        data = {"type": msg_type}
        if msg_type == "Plain":
            data.update({"data": {"text": content}, "type": "text"})
        elif msg_type == "ImagePath":
            content = Path(content)
            base64_data = base64.b64encode(content.read_bytes()).decode()
            # 复制一份到临时目录
            # temp_path = Path(tempfile.mktemp(content.suffix))
            # temp_path.write_bytes(content.read_bytes())
            data.update({"type": "image", "data": {"file": "base64://" + base64_data}})
        elif msg_type == "At":
            data.update({"type": "at", "data": {"qq": content}})
        # elif msg_type == "ImageUrl":
        #     data.update({"type": "Image", "data": {"url": content}})
        elif msg_type == "ImageBase64":
            # content = base64.b64decode(content)
            # temp_path = Path(tempfile.mktemp(".png"))
            # temp_path.write_bytes(content)
            data.update({"type": "image", "data": {"file": f"base64://{content}"}})
        elif msg_type == "VoicePath":
            base64_data = base64.b64encode(Path(content).read_bytes()).decode()
            data.update({"type": "voice", "data": {"file": f"base64://{base64_data}"}})
        # elif msg_type == "VoiceBase64":
        #     data.update({"type": "Voice", "base64": content})
        elif msg_type == "reply":
            data.update({"type": "reply", "data": {"id": content}})
        return data

    @staticmethod
    def to_data(msg_type: str, content: str):
        """
        可以在外部更改此方法
        """
        data = {"type": msg_type}
        if msg_type == "Plain":
            data.update({"text": content})
        elif msg_type == "ImageUrl":
            data.update({"type": "Image", "url": content})
        elif msg_type == "ImagePath":
            data.update({"type": "Image", "path": content})
        elif msg_type == "ImageBase64":
            data.update({"type": "Image", "base64": content})
        elif msg_type == "VoicePath":
            data.update({"type": "Voice", "path": content})
        elif msg_type == "VoiceBase64":
            data.update({"type": "Voice", "base64": content})
        elif msg_type == "At":
            data.update({"type": "At", "target": int(content)})
        return data

    @property
    def data(self) -> List:
        result = []
        for msg_data in self.origin_data:
            result.append(self.to_data(msg_data[0], msg_data[1]))
        return result

    @property
    def onebot11_data(self) -> List[dict]:
        result = []
        for msg_data in self.origin_data:
            result.append(self.to_onebot11_data(msg_data[0], msg_data[1]))
        return result

    def __add__(self, other: Self) -> Self:
        ms = MessageSegment()
        ms.origin_data = self.origin_data
        ms.origin_data.extend(other.origin_data)
        return ms

    def get_text(self):
        """获取纯文本"""
        return "".join([msg_data.get("text") or msg_data.get("data", {}).get("text") for msg_data in self.data if msg_data["type"] == "Plain"])

    def get_image_urls(self) -> list[str]:
        """获取图片链接"""
        result = []
        for msg_data in self.data:
            if msg_data["type"] == "Image":
                if "url" in msg_data:
                    result.append(msg_data["url"])
            elif msg_data["type"] == "image":
                # onebot 11
                pass
                # result.append(msg_data["data"]["file"])
        return result

    def get_image_paths(self) -> list[Path]:
        """获取图片路径"""
        result = []
        for msg_data in self.data:
            if msg_data["type"] == "Image":
                if "path" in msg_data:
                    result.append(Path(msg_data["path"]))
            elif msg_data["type"] == "image":
                # onebot 11
                result.append(Path(msg_data["data"]["file"]))
        return result

    def __str__(self):
        return str(self.onebot11_data)


if __name__ == '__main__':
    msg = MessageSegment.text("123")
    print(msg.data)
    msg += MessageSegment.text("123")
    msg += MessageSegment.text("123")
    print(msg.data)
    msg = MessageSegment.at("123") + msg
    print(msg.data)
