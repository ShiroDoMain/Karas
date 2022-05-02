from enum import Enum
from typing import Optional, Union
from .util import BaseModel
from .chain import MessageChain
from .permission import Permission, PermissionEnum

"""
由于api统一发送者为sender，所以需要在事件里对sender进行区分
这些都是消息的载体
"""


class ReceptorBase(BaseModel):
    id: int

    def __init__(self, **kws) -> None:
        _permission = kws.get("permission")
        if _permission:
            kws["permission"] = PermissionEnum[_permission].value()
        super().__init__(**kws)

    # def __init__(self, **attrs) -> None:
    #     for _attr,_value in attrs.items():
    #         _attr_type = self.__annotations__.get(_attr)
    #         if not isinstance(_value,_attr_type):
    #             _value = _attr_type(_value) if isinstance(_value,str) else _attr_type(**_value)
    #         setattr(self,_attr,_value)


class Group(ReceptorBase):
    """
    id: 群组的唯一id
    permission: bot在群组中的权限
    """
    type: str = "Group"
    id: int
    name: str
    permission: Permission


class Sender(ReceptorBase):
    type: str = "Sender"
    id: int
    nickname: str
    remark: str


class Friend(ReceptorBase):
    type: str = "Friend"
    id: int
    nickname: str
    remark: str


class Stranger(ReceptorBase):
    type: str = "Stranger"
    id: int
    nickname: str
    remark: str


class Operator(ReceptorBase):
    """
    id                  操作者的QQ号
    memberName          操作者的群名片
    permission          操作者在群中的权限,OWNER、ADMINISTRATOR或MEMBER
    group               Bot被禁言所在群的信息
    """
    type: str = "Operator"
    id: int
    memberName: str
    permission: Permission
    group: Group
    specialTitle: str
    joinTimestamp: int
    lastSpeakTimestamp: int
    muteTimeRemaining: int


class Member(ReceptorBase):
    """
    """
    type: str = "Member"
    id: int
    memberName: str
    specialTitle: str
    permission: Permission
    joinTimestamp: int
    lastSpeakTimestamp: int
    muteTimeRemaining: int
    group: Group


class Subject(ReceptorBase):
    """"""
    type: str = "Subject"
    id: int
    kind: Union["Group", "Friend"]


class Client(ReceptorBase):
    """"""
    type: str = "Client"
    id: int
    platform: str


class ElementsEnum(Enum):
    friend: "Friend" = Friend
    group: "Group" = Group
    member: "Member" = Member
    sender: "Sender" = Sender
    operator: "Operator" = Operator
    subject: "Subject" = Subject
    messageChain: "MessageChain" = MessageChain
    client: "Client" = Client
