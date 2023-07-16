import time

import config
from qqsdk.message import MsgHandler, GroupMsg, FriendMsg
from qqsdk.message.segment import MessageSegment
from .chatgpt import chat, summary_web
from ..cmdaz import CMD
from ..tts.vits import tts


def send_voice(msg: GroupMsg | FriendMsg, text):
    text = text.replace("喵", "")
    if len(text) <= 60:
        try:
            base64_data = tts(text)
            msg.reply(MessageSegment.voice_base64(base64_data))
        except Exception as e:
            pass


class ChatGPT(MsgHandler):
    desc = "发送 #+消息 或者 @机器人+消息 进行AI对话\n\n发送 总结+网址 进行AI总结网页"
    is_async = True
    bind_msg_types = (GroupMsg, FriendMsg)
    records = {}

    def handle(self, msg: GroupMsg | FriendMsg):
        cmd = CMD("总结", alias=["摘要"], param_len=1)
        cmd2 = CMD("总结", alias=["摘要"], param_len=1, sep="")
        if cmd.az(msg.msg) or cmd2.az(msg.msg):
            url = (cmd.paramList and cmd.paramList[0]) or (cmd2.paramList and cmd2.paramList[0])
            if not url.startswith("http"):
                msg.destroy()
                return
            if res := summary_web(url):
                msg.reply(res + "\n\n" + url)
                msg.destroy()
                return
        context_id = msg.group.qq + "g" if isinstance(msg, GroupMsg) else msg.friend.qq + "f"
        if isinstance(msg, GroupMsg):
            robot_name = msg.group.get_member(str(config.QQ)).get_name()
            cmd = CMD("#", alias=[f"@{robot_name}"], sep="", param_len=1)
            if cmd.az(msg.msg) or getattr(msg, "is_at_me", False):
                # msg.reply(MessageSegment.voice_path("O:\\vits-uma-genshin-honkai\\test.silk"))
                if time.time() - self.records.setdefault(msg.group_member.qq, 0) < 5:
                    return
                self.records[msg.group_member.qq] = time.time()
                use_gpt_4 = msg.group_member.qq == str(config.ADMIN_QQ) and msg.msg.startswith("#")
                res = chat(context_id, cmd.original_cmd or msg.msg, use_gpt4=use_gpt_4)
                send_voice(msg, res)
                msg.reply(res)
        elif isinstance(msg, FriendMsg):
            res = chat(context_id, msg.msg)
            send_voice(msg, res)
            msg.reply(res)
