from enum import Enum
from typing import Optional, Union
from karas.util import BaseModel
from karas.chain import MessageChain
from karas.permission import Permission, PermissionEnum

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

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]"


class Sender(ReceptorBase):
    type: str = "Sender"
    id: int
    nickname: str
    remark: str

    def __str__(self) -> str:
        return f"{self.nickname}[{self.id}]"


class Friend(ReceptorBase):
    type: str = "Friend"
    id: int
    nickname: str
    remark: str

    def __str__(self) -> str:
        return f"{self.nickname}[{self.id}]"


class Stranger(ReceptorBase):
    type: str = "Stranger"
    id: int
    nickname: str
    remark: str

    def __str__(self) -> str:
        return f"{self.nickname}[{self.id}]"


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

    def __str__(self) -> str:
        return f"{self.memberName}[{self.id}]"


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

    def __str__(self) -> str:
        return f"{self.memberName}[{self.id}]"


class Subject(ReceptorBase):
    """"""
    type: str = "Subject"
    id: int
    kind: str


class Client(ReceptorBase):
    """"""
    type: str = "Client"
    id: int
    platform: str


class Announcement(ReceptorBase):
    """公告
    content                     内容

    senderId                    发布者账号

    fid                         群公告id

    allConfirmed                是否所有群成员已确认

    confirmedMembersCount       确认群成员人数

    publicationTime             发布时间

    """
    group: Group
    content: str
    senderId: int
    fid: int
    allConfirmed: bool
    confirmedMembersCount: int
    publicationTime: int


class ElementsEnum(Enum):
    friend: "Friend" = Friend
    group: "Group" = Group
    member: "Member" = Member
    sender: "Sender" = Sender
    operator: "Operator" = Operator
    subject: "Subject" = Subject
    messageChain: "MessageChain" = MessageChain
    client: "Client" = Client
