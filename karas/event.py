from enum import Enum
from typing import Optional, Union

from karas.util import BaseModel

from karas.Sender import Client, Friend, Group, Member, Operator, Subject
from karas.messages import MessageBase, MessageEnum
from karas.permission import Permission

__events__ = {
    "messageEvent":
        [
            "MessageBase",
            "FriendMessage",
            "GroupMessage",
            "TempMessage",
            "StrangerMessage",
            "OtherClientMessage"
        ],
}


class EventBase(BaseModel):
    type: str
    selfEvent: bool = False
    fromId: int = 0

    def __str__(self) -> str:
        return f"{self.type}"


class Event(EventBase):
    event: "EventBase"

    def __init__(self, event: "EventBase", **kwargs) -> None:
        super().__init__(**kwargs)
        self.event = event
        self.type = kwargs.get("type") or event.type

    def __call__(self, *args, **kwargs):
        pass

    def __str__(self) -> str:
        return self.event.__str__()


class BotEventBase(EventBase):
    """Bot自身事件"""
    qq: int

    def __str__(self) -> str:
        return f"{self.__class__}: {self.qq}"


class FriendEventBase(EventBase):
    """好友事件"""
    friend: Friend

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.friend.nickname}({self.friend.id})"


class GroupEventBase(EventBase):
    """群组事件"""

    def __init__(self, **kws) -> None:
        super().__init__(**kws)


class RequestEvent(EventBase):
    """申请事件"""
    command: str
    eventId: int
    fromId: int
    groupId: int
    nick: str
    message: str

    @property
    def accept(self):
        self.operate = 0
        return self.__dict__

    @property
    def reject(self):
        self.operate = 1
        return __dict__


class BotOnlineEvent(BotEventBase):
    """Bot登录成功"""
    type: str = "BotEventBase"


class BotOfflineEventActive(BotEventBase):
    """Bot主动离线"""
    type: str = "BotOfflineEventActive"


class BotOfflineEventForce(BotEventBase):
    """Bot被挤下线"""
    type: str = "BotOfflineEventForce"


class BotOfflineEventDropped(BotEventBase):
    """Bot被服务器断开或因网络问题而掉线"""
    type: str = "BotOfflineEventDropped"


class BotReloginEvent(BotEventBase):
    """Bot主动重新登录"""
    type: str = "BotReloginEvent"


class FriendInputStatusChangedEvent(FriendEventBase):
    """好友输入状态改变"""
    type: str = "FriendInputStatusChangedEvent"
    friend: Friend
    inputting: bool


class FriendNickChangedEvent(FriendEventBase):
    """
    好友昵称改变
    from: 原昵称
    to: 现昵称
    """
    type: str = "FriendNickChangedEvent"
    friend: Friend
    From: str
    to: str


class BotGroupPermissionChangeEvent(GroupEventBase):
    """Bot在群里的权限被改变. 操作人一定是群主"""
    type: str = "BotGroupPermissionChangeEvent"
    origin: Permission
    current: Permission
    group: Group

    def __str__(self) -> str:
        return f"{self.__class__.type}:{self.origin.type}->{self.current.type}"


class BotMuteEvent(GroupEventBase):
    """Bot被禁言"""
    type: str = "BotMuteEvent"
    durationSeconds: int
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator}"


class BotUnmuteEvent(GroupEventBase):
    """Bot被取消禁言"""
    type: str = "BotUnmuteEvent"
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator}"


class BotJoinGroupEvent(GroupEventBase):
    """Bot加入了一个新群"""
    type: str = "BotJoinGroupEvent"
    group: Group
    invitor: Optional[Member]

    def __str__(self) -> str:
        return super().__str__() + f":{self.group}"


class BotLeaveEventActive(GroupEventBase):
    """BotLeaveEventActive"""
    type: str = "BotLeaveEventActive"
    group: Group

    def __str__(self) -> str:
        return super().__str__() + f":{self.group}"


class BotLeaveEventKick(GroupEventBase):
    """Bot被踢出一个群"""
    type: str = "BotLeaveEventKick"
    operator: Optional[Member]

    def __str__(self) -> str:
        return super().__str__() + f":{self.group}"


class GroupRecallEvent(GroupEventBase):
    """群消息撤回"""
    type: str = "GroupRecallEvent"
    authorId: int
    messageId: int
    time: int
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} <- {self.messageId}"


class FriendRecallEvent(EventBase):
    """好友消息撤回"""
    type: str = "FriendRecallEvent"
    authorId: int
    messageId: int
    time: int
    operator: int

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} <- {self.messageId}"


class NudgeEvent(EventBase):
    """戳一戳事件"""
    type: str = "NudgeEvent"
    fromId: int
    subject: Subject
    action: str
    suffix: str
    target: int

    def __init__(self, subject: dict, **kwargs) -> None:
        self.subject = Subject(**subject)
        super().__init__(**kwargs)

    def __str__(self) -> str:
        return f"NudgeEvent => [{self.fromId}]{self.action}[{self.target}]{self.suffix}"


class GroupNameChangeEvent(GroupEventBase):
    """某个群名改变"""
    type: str = "GroupNameChangeEvent"
    origin: str
    current: str
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f"{self.group}=>origin:{self.origin} -> current{self.current}"


class GroupEntranceAnnouncementChangeEvent(GroupEventBase):
    """某群入群公告改变"""
    type: str = "GroupEntranceAnnouncementChangeEvent"
    origin: str
    current: str
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.group}"


class GroupMuteAllEvent(GroupEventBase):
    """全员禁言"""
    type: str = "GroupMuteAllEvent"
    origin: bool
    current: bool
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} -> {self.group}"


class GroupAllowAnonymousChatEvent(GroupEventBase):
    """匿名聊天"""
    origin: bool
    current: bool
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} -> {self.group}"


class GroupAllowConfessTalkEvent(GroupEventBase):
    """坦白说"""
    origin: bool
    current: bool
    group: Group
    isByBot: bool

    def __str__(self) -> str:
        return super().__str__() + f":{self.group}"


class GroupAllowMemberInviteEvent(GroupEventBase):
    """允许群员邀请好友加群"""
    type: str = "GroupAllowMemberInviteEvent"
    origin: bool
    current: bool
    group: Group
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} -> {self.group}"


class MemberJoinEvent(GroupEventBase):
    """新人入群的事件"""
    type: str = "MemberJoinEvent"
    member: Member
    invitor: None

    def __str__(self) -> str:
        return super().__str__() + f":{self.member}"


class MemberLeaveEventKick(GroupEventBase):
    """成员被踢出群聊(该成员不是bot)"""
    type: str = "MemberLeaveEventKick"
    member: Member
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f":{self.operator} -> {self.member}"


class MemberLeaveEventQuit(GroupEventBase):
    """成员退出群聊(该成员不是bot)"""
    type: str = "MemberLeaveEventQuit"
    member: Member

    def __str__(self) -> str:
        return super().__str__() + f"{self.member}"


class MemberCardChangeEvent(GroupEventBase):
    """群名片改动"""
    type: str = "MemberCardChangeEvent"
    origin: str
    current: str
    member: Member

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class MemberSpecialTitleChangeEvent(GroupEventBase):
    """群头衔改动（只有群主有操作限权）"""
    type: str = "MemberSpecialTitleChangeEvent"
    origin: str
    current: str
    member: Member

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class MemberPermissionChangeEvent(GroupEventBase):
    """成员权限改变的事件（该成员不是Bot）"""
    type: str = "MemberPermissionChangeEvent"
    origin: Permission
    current: Permission
    member: Member

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class MemberMuteEvent(GroupEventBase):
    """群成员被禁言事件（该成员不是Bot）"""
    type: str = "MemberMuteEvent"
    durationSeconds: int
    member: Member
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class MemberUnmuteEvent(GroupEventBase):
    """群成员被取消禁言事件（该成员不是Bot）"""
    type: str = "MemberMuteEvent"
    durationSeconds: int
    member: Member
    operator: Operator

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class MemberHonorChangeEvent(GroupEventBase):
    """群员称号改变"""
    type: str = "MemberHonorChangeEvent"
    member: Member
    action: str
    honor: str

    def __str__(self) -> str:
        return super().__str__() + f": {self.member}"


class NewFriendRequestEvent(RequestEvent):
    """添加好友申请"""
    type: str = "NewFriendRequestEvent"
    command: str = "resp_newFriendRequestEvent"

    @property
    def reject_block(self):
        self.operate = 2
        return __dict__

    def __str__(self) -> str:
        return super().__str__() + f":{self.nick}[{self.fromId}]"


class MemberJoinRequestEvent(RequestEvent):
    """用户入群申请（Bot需要有管理员权限）"""
    type: str = "MemberJoinRequestEvent"
    groupName: str
    command: str = "resp_memberJoinRequestEvent"

    @property
    def ignore(self):
        self.operate = 2
        return self.__dict__

    @property
    def reject_block(self):
        self.operate = 3
        return self.__dict__

    @property
    def ignore_block(self):
        self.operate = 4
        return self.__dict__

    def __str__(self) -> str:
        return super().__str__() + f":{self.groupName}[{self.groupId}]"


class BotInvitedJoinGroupRequestEvent(RequestEvent):
    """Bot被邀请入群申请"""
    type: str = "BotInvitedJoinGroupRequestEvent"
    groupName: str
    command = "resp_botInvitedJoinGroupRequestEvent"

    def __str__(self) -> str:
        return super().__str__() + f":{self.groupId}"


class OtherClientOnlineEvent(EventBase):
    """其他客户端上线"""
    type: str = "OtherClientOnlineEvent"
    client: Client
    kind: int


class OtherClientOfflineEvent(EventBase):
    """其他客户端下线"""
    type: str = "OtherClientOfflineEvent"
    client: Client


class CommandExecutedEvent(EventBase):
    """命令被执行"""
    type: str = "CommandExecutedEvent"
    name: str
    friend: Optional[Friend]
    member: Optional[Member]
    args: dict


class EventEnum(Enum):
    BotOnlineEvent: "BotOnlineEvent" = BotOnlineEvent
    BotOfflineEventActive: "BotOfflineEventActive" = BotOfflineEventActive
    BotOfflineEventForce: "BotOfflineEventForce" = BotOfflineEventForce
    BotOfflineEventDropped: "BotOfflineEventDropped" = BotOfflineEventDropped
    BotReloginEvent: "BotReloginEvent" = BotReloginEvent

    FriendInputStatusChangedEvent: "FriendInputStatusChangedEvent" = FriendInputStatusChangedEvent
    FriendNickChangedEvent: "FriendNickChangedEvent" = FriendNickChangedEvent

    BotGroupPermissionChangeEvent: "BotGroupPermissionChangeEvent" = BotGroupPermissionChangeEvent
    BotMuteEvent: "BotMuteEvent" = BotMuteEvent
    BotUnmuteEvent: "BotUnmuteEvent" = BotUnmuteEvent
    BotJoinGroupEvent: "BotJoinGroupEvent" = BotJoinGroupEvent
    BotLeaveEventActive: "BotLeaveEventActive" = BotLeaveEventActive
    BotLeaveEventKick: "BotLeaveEventKick" = BotLeaveEventKick
    GroupRecallEvent: "GroupRecallEvent" = GroupRecallEvent
    FriendRecallEvent: "FriendRecallEvent" = FriendRecallEvent
    NudgeEvent: "NudgeEvent" = NudgeEvent

    GroupNameChangeEvent: "GroupNameChangeEvent" = GroupNameChangeEvent
    GroupEntranceAnnouncementChangeEvent: "GroupEntranceAnnouncementChangeEvent" = GroupEntranceAnnouncementChangeEvent
    GroupMuteAllEvent: "GroupMuteAllEvent" = GroupMuteAllEvent
    GroupAllowAnonymousChatEvent: "GroupAllowAnonymousChatEvent" = GroupAllowAnonymousChatEvent
    GroupAllowConfessTalkEvent: "GroupAllowConfessTalkEvent" = GroupAllowConfessTalkEvent
    GroupAllowMemberInviteEvent: "GroupAllowMemberInviteEvent" = GroupAllowMemberInviteEvent
    MemberJoinEvent: "MemberJoinEvent" = MemberJoinEvent
    MemberLeaveEventKick: "MemberLeaveEventKick" = MemberLeaveEventKick
    MemberLeaveEventQuit: "MemberLeaveEventQuit" = MemberLeaveEventQuit
    MemberCardChangeEvent: "MemberCardChangeEvent" = MemberCardChangeEvent
    MemberSpecialTitleChangeEvent: "MemberSpecialTitleChangeEvent" = MemberSpecialTitleChangeEvent
    MemberPermissionChangeEvent: "MemberPermissionChangeEvent" = MemberPermissionChangeEvent
    MemberMuteEvent: "MemberMuteEvent" = MemberMuteEvent
    MemberUnmuteEvent: "MemberUnmuteEvent" = MemberUnmuteEvent
    MemberHonorChangeEvent: "MemberHonorChangeEvent" = MemberHonorChangeEvent
    NewFriendRequestEvent: "NewFriendRequestEvent" = NewFriendRequestEvent
    MemberJoinRequestEvent: "MemberJoinRequestEvent" = MemberJoinRequestEvent
    BotInvitedJoinGroupRequestEvent: "BotInvitedJoinGroupRequestEvent" = BotInvitedJoinGroupRequestEvent
    OtherClientOnlineEvent: "OtherClientOnlineEvent" = OtherClientOnlineEvent
    OtherClientOfflineEvent: "OtherClientOfflineEvent" = OtherClientOfflineEvent
    CommandExecutedEvent: "CommandExecutedEvent" = CommandExecutedEvent


class Auto_Switch_Event(object):
    @staticmethod
    def parse_json(*args, **kwargs) -> Union["MessageBase", "Event"]:
        """将传进的原始数据转换成对应的事件对象

        Returns:
            Event: 一个已经被自动解析完成的事件对象
        """
        _type = kwargs.get("type")
        if _type in __events__.get("messageEvent"):
            _messageEvent: "MessageBase" = MessageEnum[_type].value
            return _messageEvent(**kwargs)
        else:
            _event: "EventBase" = EventEnum[_type].value
            return Event(_event(**kwargs))
