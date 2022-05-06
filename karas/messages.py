from email import message
from enum import Enum
from typing import Union

from karas.util import BaseModel

from karas.Sender import Client, Group, Member, Sender, Friend, Subject
from karas.chain import MessageChain
from karas.elements import ElementBase


class MessageBase(BaseModel):
    """event base"""
    type: str
    sender: Union["ElementBase", "Sender", "Member", "Friend", "Subject"]
    messageChain: MessageChain

    # def __init__(self, *args,**kwargs) -> None:
    #     for _k,_v in kwargs.items():
    #         _type = self.__annotations__.get(_k)
    #         if not isinstance(_v,_type):
    #             _v = _type(**_v) if _k != "messageChain" else _type(*_v)
    #         setattr(self,_k,_v)

    def __str__(self) -> str:
        return self.messageChain.to_str()


class GroupMessage(MessageBase):
    """group message event"""
    type: str = "GroupMessage"
    sender: Member
    messageChain: MessageChain

    def __init__(self, **kws) -> None:
        super().__init__(**kws)
        self.group = kws.get("sender") and self.sender.group

    def __str__(self) -> str:
        return f"GroupMessage:[{self.sender.group.name}({self.sender.group.id})]{self.sender.memberName}({self.sender.id}) => " + super().__str__()


class FriendMessage(MessageBase):
    """friend message event"""
    type: str = "FriendMessage"
    sender: Friend
    messageChain: MessageChain

    def __str__(self) -> str:
        return f"FriendMessage:{self.sender.nickname}({self.sender.nickname}) => " + super().__str__()


class TempMessage(MessageBase):
    """temp message event"""
    type: str = "TempMessage"
    sender: Member
    messageChain: MessageChain

    def __init__(self, **kws) -> None:
        super().__init__(**kws)
        self.group = kws.get("sender") and self.sender.group

    def __str__(self) -> str:
        return f"TempMessage:[{self.sender.memberName}({self.sender.id})]" + super().__str__()


class StrangerMessage(MessageBase):
    """stranger message event base

    Args:
        MessageBase (_type_): _description_
    """
    type: str = "StrangerMessage"
    sender: Sender
    messageChain: MessageChain

    def __str__(self) -> str:
        return f"StrangerMessage:{self.sender.nickname}[{self.sender.id}]" + super().__str__()


class OtherClientMessage(MessageBase):
    type: str = "OtherClientMessage"
    sender: Client
    messageChain: MessageChain


class FriendSyncMessage(MessageBase):
    type: str = "FriendSyncMessage"
    subject: Subject
    messageChain: MessageChain


class MessageEnum(Enum):
    GroupMessage: "GroupMessage" = GroupMessage
    FriendMessage: "FriendMessage" = FriendMessage
    TempMessage: "TempMessage" = TempMessage
    StrangerMessage: "StrangerMessage" = StrangerMessage
