# coding=UTF8
from typing import Type

from qqsdk.message.basemsg import BaseMsg
from qqsdk.message.friendmsg import FriendMsg
from qqsdk.message.groupmsg import GroupMsg
from qqsdk.message.msghandler import MsgHandler
from qqsdk.message.types import MessageTypes

GeneralMsg = Type[GroupMsg | FriendMsg]
