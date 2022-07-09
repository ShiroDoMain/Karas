from enum import Enum
from typing import Union
from karas.util import BaseModel
from karas.Sender import Client, Member, Sender, Friend, Subject, Stranger, Group
from karas.chain import MessageChain
from karas.elements import ElementBase


class MessageBase(BaseModel):
    """event base"""
    type: str
    sender: Union["ElementBase", "Sender", "Member", "Friend", "Subject"]
    messageChain: MessageChain

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
    """好友同步消息"""
    type: str = "FriendSyncMessage"
    subject: Friend
    messageChain: MessageChain

    def __str__(self) -> str:
        return super().__str__()+": "+self.messageChain.__str__()


class GroupSyncMessage(MessageBase):
    """群组同步消息"""
    type: str = "GroupSyncMessage"
    subject: Group
    messageChain: MessageChain

    def __str__(self) -> str:
        return super().__str__()+": " + self.messageChain.__str__()


class TempSyncMessage(MessageBase):
    """临时同步消息"""
    type: str = "TempSyncMessage"
    subject: Member
    messageChain: MessageChain

    def __str__(self) -> str:
        return super().__str__()+": " + self.messageChain.__str__()


class StrangerSyncMessage(MessageBase):
    """陌生人同步消息"""
    type: str = "StrangerSyncMessage"
    subject: Stranger
    messageChain: MessageChain

    def __str__(self) -> str:
        return super().__str__()+": " + self.messageChain.__str__()



class MessageEnum(Enum):
    GroupMessage: "GroupMessage" = GroupMessage
    FriendMessage: "FriendMessage" = FriendMessage
    TempMessage: "TempMessage" = TempMessage
    StrangerMessage: "StrangerMessage" = StrangerMessage
    GroupSyncMessage: "GroupSyncMessage" = GroupSyncMessage
    FriendSyncMessage: "FriendSyncMessage" = FriendSyncMessage
    TempSyncMessage: "TempSyncMessage" = TempSyncMessage
    StrangerSyncMessage: "StrangerSyncMessage" = StrangerSyncMessage
