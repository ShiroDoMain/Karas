import inspect
from aiohttp import ClientSession, ClientWebSocketResponse
import asyncio
from typing import (
    Coroutine,
    Awaitable,
    BinaryIO,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    AsyncGenerator,
    NoReturn
)
import aiohttp
from karas.util import DefaultNamespace, status_code_exception
from karas.util.sync import async_to_sync_wrap
from karas.chain import Forward, MessageChain, node
from karas.Sender import Friend, Group, Member, Stranger, ReceptorBase, Announcement
from karas.messages import MessageBase
from karas.event import Auto_Switch_Event, EventBase, MemberJoinRequestEvent, NewFriendRequestEvent, RequestEvent, \
    Event, NudgeEvent, BotOfflineEventActive, BotOnlineEvent
from karas.elements import ElementBase, File, FlashImage, GroupConfig, Image, MemberInfo, Plain, Source, Voice, \
    FriendProfile, MemberProfile, \
    BotProfile, UserProfile
from karas.exceptions import *
from karas.util.Logger import Logging
from karas.util.network import error_throw, URL_Route, wrap_data_json

__version__ = "0.2.5"


async def _build_content_json(
        _type: str,
        _obj: Union[ReceptorBase, int],
        _quote: Optional[Source],
        _chain: List
):
    return {
        _type: _obj if isinstance(_obj, int) else _obj.id,
        "quote": _quote and _quote.id,
        "messageChain": _chain
    }


class Karas(object):
    """
    Karas:
        负责处理消息事件
    """
    listeners = {}
    loop: asyncio.AbstractEventLoop = None

    @classmethod
    async def event_parse(cls, original: dict, _logger: Logging = None) -> AsyncGenerator:
        _logger.debug(original)
        _event: Union[MessageBase,
                      Event] = Auto_Switch_Event.parse_json(**original)
        isBotEvent = yield _event
        _logger.info(_event.__str__())
        if not isBotEvent:
            await cls._executor(_event)
        yield

    @classmethod
    async def bot_event(cls, _event: dict):
        # bot触发的事件
        _event: MessageBase = Auto_Switch_Event.parse_json(**_event)
        return _event

    @classmethod
    async def _executor(cls, message: Union["MessageBase", "EventBase"] = None) -> Optional[str]:
        events = cls.listeners.get(message.type)
        if events is None:
            return
        for listener in events:
            ca, cb, cb_args = listener
            if cb:
                cb_args = cb_args or ()
                cb(message.raw, *cb_args)
            _message_dict = message.__dict__
            _func_params = ca.__annotations__

            _reversed = {_v if isinstance(type, type(_v)) else type(
                _v): _k for _k, _v in _message_dict.items()}
            _types = [v if isinstance(type, type(v)) else type(v)
                      for v in _message_dict.values()]
            _o = {}
            for k, t in _func_params.items():
                if t in _types:
                    _o[k] = _message_dict[_reversed[t]]
            if inspect.iscoroutinefunction(ca):
                cls.loop.create_task(ca(**_o))
            else:
                ca(**_o)


def _get_event_loop():
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        _loop = asyncio.get_event_loop()
    return _loop


@async_to_sync_wrap
class Yurine(object):
    """
    Yurine:
        负责服务器的连接，Karas的调度
    """

    def __init__(
            self,
            host: str,
            port: int,
            account: int,
            verifyKey: str,
            loop: asyncio.AbstractEventLoop = None,
            karas: Karas = None,
            protocol: str = "ws",
            sessionKey: str = None,
            session: ClientSession = None,
            ws: ClientWebSocketResponse = None,
            loggerLevel: str = "INFO",
            logToFile=False,
            logFileName: str = None,
            logRecordLevel: str = None
    ) -> None:
        self._host = host
        self._port = port
        self.url = f"{protocol}://{host}:{port}"
        self.protocol = protocol
        self._account = account
        self._verifyKey = verifyKey
        self.sessionKey = sessionKey
        self._session = session
        self._ws = ws

        self.route = URL_Route(self.url)
        self.logging = Logging(loggerLevel.upper(), account, filename=logFileName, logFile=logToFile,
                               recordLevel=logRecordLevel)
        self._loop = loop or _get_event_loop()
        self.karas = karas or Karas
        self.karas.loop = self.loop

        self.namespace = DefaultNamespace

        self._is_running = False
        self._receiver_is_running = False
        self._receiveData = {}
        self._tasks = {}

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def loop(self):
        return self._loop

    @property
    def session(self):
        return self._session

    @property
    def ws(self):
        return self._ws

    @property
    def verifyKey(self):
        return self._verifyKey

    @property
    def is_running(self):
        return self._is_running

    @property
    def account(self):
        return self._account

    @error_throw
    async def _initialization(self) -> int:
        """初始化"""
        self.logging.debug(f"URL:  {self.url}")
        if not self.session:
            self._session = ClientSession(loop=self.loop)
            await self._connect()
            self.logging.info("Account verify success")
            self.logging.debug(f"got verifyKey {self.sessionKey}")
        self.logging.info("connect success")
        self.logging.info("++++++++++++++++++++++++++++++++++++++++")
        return 0

    @error_throw
    async def _release(self):
        """
        对当前bot持有的session key进行释放请求
            NOTE:由于使用了ws接口,无需对sessionKey进行释放
        """
        async with self.session.post(
                "/release",
                json={
                    "sessionKey": self.sessionKey,
                    "qq": self.account
                }
        ) as _release_response:
            _release_response.raise_for_status()
            _release = await _release_response.json()
            self.logging.debug(f"release verifyKey {_release}")
            if _release.get("msg") == "success":
                self.logging.info("Succeed release sessionKey")
            else:
                self.logging.error(f"Failed release sessionKey => {_release}")

    @error_throw
    async def _ping(self) -> None:
        """向服务端发送心跳"""
        self.logging.info("create heartbeat service")
        while True:
            try:
                await self.ws.ping()
            except ConnectionResetError:
                return
            except Exception:
                raise
            else:
                await asyncio.sleep(.5)

    @error_throw
    async def _connect(self) -> Optional[int]:
        """
        向服务器发起 WebSocket 连接
        :return 返回连接是否成功
        :raise VerifyException
        """
        self.logging.debug(f"connect websocket server {self.url}")
        try:
            self._ws = await self.session.ws_connect(
                url=self.route("all"),
                headers={
                    "verifyKey": self.verifyKey,
                    "qq": str(self.account)
                }
            )
        except aiohttp.ClientConnectionError as exc:
            raise ConnectException from exc
        self.sessionKey: str = (await self._raise_status()).get("session")
        self.loop.create_task(self._ping())
        return 0

    @error_throw
    async def _receiver(self, data: Dict = None) -> NoReturn:
        """事件监听器"""
        self._receiver_is_running = True
        while True:
            try:
                _receive_data: Dict = data or await self.ws.receive_json()
            # except (BotBaseException, TypeError):
            #     pass
            except Exception:
                raise
            syncId = _receive_data.get("syncId")
            if syncId == "-1":
                _parser = self.karas.event_parse(
                    _receive_data["data"], self.logging)
                _event = await _parser.__anext__()
                if not self._is_running and isinstance(_event, BotOnlineEvent):
                    self.logging.info("bot online")
                    self._is_running = True
                if isinstance(_event, BotOfflineEventActive):
                    self.logging.warning("Bot offline, waiting reload...")
                    self._is_running = self.is_running and False
                    await asyncio.sleep(1)
                    await _parser.asend(False)
                    continue
                await _parser.asend(self.account == _event.event.fromId) \
                    if isinstance(_event, Event) else await _parser.asend(False)
            elif syncId:
                self.logging.debug(f"sync Event {_receive_data}")
                self._receiveData[syncId] = _receive_data
            else:
                self.logging.debug(f"Unknown event:{_receive_data}")
            if data:
                self.logging.debug(f"got other data {data}")
                break

    def listen(self, registerEvent: Union[str, "EventBase", "MessageBase", List], callback: Callable = None,
               cb_args: Optional[Tuple] = None):
        """事件装饰器
        Args:
            registerEvent (str, Event, Message, list): 要监听的事件或者消息类型
            callback: 设定一个callback,当监听到指定事件会将该事件原始数据(Dict)作为第一个参数传入
            cb_args:传入到callback的其他参数

        callback用法:
        def callback(eventData: Dict, arg1, arg2,...) -> ...: ...
        yurine.listen(GroupMessage, callback=callback, cb_args=(a1,a2,a3)0) -> None:...

        使用函数处理:
        @yurine.listen("GroupMessage")
        async def listen_gm(message:MessageChain):...

        @yurine.listen(["GroupMessage", "TempMessage"])
        async def multi_listen(message:MessageChain) -> None: ...

        Note: 如果要将一个函数监听绑定多个事件类型，需要注意函数能接受的参数必须是这些消息时间类型所具有的共通的参数，例如你不能让一个带有Friend类型参数的函数监听GroupMessage

        Returns:
            None: NoReturn
        """
        registerEvents = [(e if isinstance(e, str) else e.type) for e in registerEvent] if isinstance(
            registerEvent, List) else (registerEvent,) if isinstance(registerEvent, str) else (registerEvent.type,)

        def register_decorator(func: Awaitable):
            """
            Args:
                func: 监听到事件时所作的动作
            """
            def register_wrapper(*_, **__):
                for _event in registerEvents:
                    self.logging.debug(
                        f"register listener [{func.__name__}] for Event[{_event}]"
                    )
                    if Karas.listeners.get(_event):
                        Karas.listeners.get(_event).append(
                            (func, callback, cb_args))
                    else:
                        Karas.listeners[_event] = [
                            (func, callback, cb_args)]

            return register_wrapper()

        return register_decorator

    @error_throw
    async def accept(
            self,
            requestEvent: "RequestEvent",
            message: str = ""
    ) -> None:
        """接受该请求事件

        Args:
            requestEvent (RequestEvent): 一个请求事件
            message (str, optional): 同意该请求时附带的消息. Defaults to None.
        """
        if not isinstance(requestEvent, RequestEvent):
            self.logging.error("非法请求")
        else:
            requestEvent.message = message
            await self.ws.send_json(
                wrap_data_json(
                    syncId="accept",
                    command=requestEvent.command,
                    content=requestEvent.accept
                )
            )

    @error_throw
    async def reject(
            self,
            requestEvent: "RequestEvent",
            message: str = ""
    ) -> None:
        """拒绝该请求事件

        Args:
            requestEvent (RequestEvent): 一个请求事件
            message (str, optional): 拒绝该请求时附带的消息. Defaults to None.
        """
        if not isinstance(requestEvent, RequestEvent):
            self.logging.error("非法请求")
        else:
            requestEvent.message = message
            await self.ws.send_json(
                wrap_data_json(
                    syncId="reject",
                    command=requestEvent.command,
                    content=requestEvent.reject
                )
            )

    @error_throw
    async def reject_block(
            self,
            requestEvent: Union[NewFriendRequestEvent, MemberJoinRequestEvent],
            message: str = ""
    ) -> None:
        """拒绝添加好友或者入群并添加黑名单，不再接收该用户的好友申请

        Args:
            requestEvent (RequestEvent): 一个请求事件
            message (str, optional): 拒绝该请求时附带的消息. Defaults to None.
        """
        if not isinstance(requestEvent, (NewFriendRequestEvent, MemberJoinRequestEvent)):
            self.logging.error("非法请求")
        else:
            requestEvent.message = message
            await self.ws.send_json(
                wrap_data_json(
                    syncId="reject",
                    command=requestEvent.command,
                    content=requestEvent.reject_block
                )
            )

    @error_throw
    async def ignore(
            self,
            requestEvent: MemberJoinRequestEvent,
            message: str = ""
    ) -> None:
        """忽略该请求事件

        Args:
            requestEvent (RequestEvent): 一个请求事件
            message (str, optional): 忽略该请求时附带的消息. Defaults to None.
        """
        if not isinstance(requestEvent, RequestEvent):
            self.logging.error("非法请求")
        else:
            requestEvent.message = message
            await self.ws.send_json(
                wrap_data_json(
                    syncId="reject",
                    command=requestEvent.command,
                    content=requestEvent.ignore
                )
            )

    @error_throw
    async def ignore_block(
            self,
            requestEvent: MemberJoinRequestEvent,
            message: str = ""
    ) -> None:
        """忽略入群并添加黑名单，不再接收该用户的入群申请

        Args:
            requestEvent (RequestEvent): 一个请求事件
            message (str, optional): 忽略该请求时附带的消息. Defaults to None.
        """
        if not isinstance(requestEvent, RequestEvent):
            self.logging.error("非法请求")
        else:
            requestEvent.message = message
            await self.ws.send_json(
                wrap_data_json(
                    syncId="reject",
                    command=requestEvent.command,
                    content=requestEvent.ignore_block
                )
            )

    @error_throw
    async def uploadFile(self, group: Union[int, Group], file: Union[str, BinaryIO, bytes, None], type_: str = "group",
                         path: str = "") -> File:
        """上传群文件，返回的是上传的该文件对象

        args:
            group (int) :上传的群组 
            file (Union[str,BinaryIO,bytes,None]) : 要上传的文件，可以是路径或者一个已经打开了的二进制文件读取流
            path (str) :上传到群组指定的文件路径，默认为根目录

        Returns:
            File: 上传的文件对象
        """
        async with self.session.post(
                self.route("/file/upload"),
                data={
                    "sessionKey": self.sessionKey,
                    "type": type_,
                    "target": str(group if isinstance(group, int) else group.id),
                    "path": path,
                    "file": open(file, "rb") if isinstance(file, str) else file
                }
        ) as _response:
            parsed_data = await self._raise_status(await _response.json())
            return File(**parsed_data)

    @error_throw
    async def uploadMultipart(self, obj: Union["Voice", "Image", "FlashImage"], type_: str) -> None:
        """上传多媒体类型文件(语音, 图片),该方法仅作为上传方法，发送请使用sendXxxx(xxx,[Voice(file=xxx)])形式"""
        uploadType = "Image" if isinstance(obj, FlashImage) else obj.type
        if hasattr(obj, "url"):
            return
        async with self.session.post(
                self.route(f"upload{uploadType}"),
                data={
                    "sessionKey": self.sessionKey,
                    "type": type_,
                    obj.ftype: open(obj.file, "rb") if isinstance(
                        obj.file, str) else obj.file
                }
        ) as _response:
            parsed_data = await self._raise_status(await _response.json())
            obj(**parsed_data)
            obj.file = None

    async def _element_check(self, element: "ElementBase", type_: str):
        if isinstance(element, (Image, Voice, FlashImage)):
            await self.uploadMultipart(element, type_=type_)
        if isinstance(element, Forward):
            nodeList = element.nodeList
            if nodeList:
                element.nodeList = [await self._element_check(node_, type_=type_) for node_ in nodeList]
        if isinstance(element, node):
            element.messageChain = [await self._element_check(e, type_=type_) for e in
                                    element.messageChain._get_elements()]
        if isinstance(element, File):
            raise FunctionException("文件上传请使用uploadFile方法，该方法仅支持发送消息")
        return element.elements if isinstance(element, ElementBase) else element

    @error_throw
    async def about(self):
        """获取mirai-api-http的版本"""
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="about",
            )
        )
        version = await self._raise_status(syncId=syncId)
        return version.get("data").get("version")

    @error_throw
    async def sendGroup(
            self,
            group: Union[int, "Group"],
            Elements: Union[List[Union[ElementBase, MessageChain]], MessageChain],
            quote: Union[int, Source] = None
    ) -> Optional[int]:
        """发送群组消息


        Args:
            group (Union[int,Group]): 要发送的群组id或者对象
            Elements (list,Element): 要发送的消息类型，可以是单个类型或者一个列表
            quote (Union[int,Source]): 引用一条消息的messageId进行回复

        Returns:
            int: 一个Int类型属性，标识本条消息，用于撤回和引用回复
        """
        _chain = [(await self._element_check(_e, type_="group")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = await _build_content_json("group", group, quote, _chain)
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="sendGroupMessage",
                content=content
            ))
        self.logging.info(
            f"Group({group.name if isinstance(group, Group) else group}) <= {MessageChain(*_chain).to_str()}")
        echo = await self._raise_status(syncId=syncId)
        return echo.get("messageId")

    @error_throw
    async def sendFriend(
            self,
            friend: Union[Friend, int],
            Elements: Union[List[Union[ElementBase, MessageChain]], MessageChain],
            quote: Optional[Source] = None
    ) -> Optional[int]:

        """发送好友消息


        Args:
            friend (Union[int,friend]): 要发送的好友id或者对象
            Elements (list,Element): 要发送的消息类型，可以是单个类型或者一个列表
            quote (Union[int,Source]): 引用一条消息的messageId进行回复

        Returns:
            int: 一个Int类型属性，标识本条消息，用于撤回和引用回复
        """
        _chain = [(await self._element_check(_e, type_="friend")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = await _build_content_json("target", friend, quote, _chain)
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="sendFriendMessage",
                content=content
            )
        )
        self.logging.info(
            f"Friend:{friend.nickname if isinstance(friend, Friend) else friend} <= {MessageChain(*_chain).__str__()}")
        echo = await self._raise_status(syncId=syncId)
        return echo.get("messageId")

    @error_throw
    async def sendTemp(
            self,
            member: Union[int, Member],
            group: Union[int, Group],
            Elements: Union[List[Union[ElementBase, MessageChain]], MessageChain],
            quote: Optional[Source] = None
    ) -> Optional[int]:

        """发送临时会话消息


        Args:
            group (Union[int,Group]): 对象所在的群组
            member (Union[int,Member]): 要发送的对象id或者成员对象
            Elements (list,Element): 要发送的消息类型，可以是单个类型或者一个列表
            quote (Union[int,Source]): 引用一条消息的messageId进行回复

        Returns:
            int: 一个Int类型属性，标识本条消息，用于撤回和引用回复
        """
        _chain = [(await self._element_check(_e, type_="temp")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = {
            "qq": member if isinstance(member, int) else member.id,
            "group": group if isinstance(member, int) else group.id,
            quote: quote and quote.id,
            "messageChain": _chain
        }
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="sendTempMessage",
                content=content
            )
        )
        self.logging.info(
            f"Temp{member.memberName if isinstance(member, Member) else member} <= {MessageChain(*_chain).to_str()}")
        echo = await self._raise_status(syncId=syncId)
        return echo.get("messageId")

    @error_throw
    async def recall(self, message: Union[Source, int]):
        """消息撤回

        Args:
            message (Union[Source, int]): 要撤回的消息，可以是一个Source或者消息Id
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                command="recall",
                syncId=syncId,
                content={
                    "messageId": message.id if isinstance(message, Source) else message
                }
            )
        )
        self.logging.info(f"BotRecall: {message.id if isinstance(message, Source) else message}")
        echo = await self._raise_status(syncId=syncId)
        return echo.get("msg")

    @error_throw
    async def sendNudge(
            self,
            target: Union["ElementBase", "Friend", "Member", None] = None,
            subject: Union[int, "Group", "Friend", None] = None,
            kind: Union[str, "Group", "Friend", "Stranger", None] = None,
            event_: Optional["NudgeEvent"] = None,
    ) -> None:
        """发送头像戳一戳消息，你可以只传入目标对象或者是一个事件对象

        Args:
            target (Union[ElementBase]): 戳一戳的目标, QQ号, 可以为 bot QQ号
            subject (Union[int,Group,Friend]): 戳一戳接受主体(上下文), 戳一戳信息会发送至该主体, 为群号/好友QQ号
            kind (Union[str,Group,Friend,Stranger]): 上下文类型, 可选值 Friend, Group, Stranger
            event_ (NudgeEvent): 如果直接传入该参数，则对象为该事件发起人,该参数应为NudgeEvent类型
        Returns:
            _type_:
        """
        if isinstance(target, NudgeEvent):
            event_ = target
        target = target if event_ is None else event_.fromId
        subject = subject if subject is not None else event_.subject if event_ is not None \
            else target.group if isinstance(target, Member) else target.id
        kind = kind if kind is not None else event_.subject.kind if event_ is not None \
            else target.group.type if isinstance(target, Member) else target.type
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="sendNudge",
                content={
                    "target": target,
                    "subject": subject,
                    "kind": kind
                }))
        self.logging.info(f"Bot <= NudgeEvent:{subject}")
        echo = await self._raise_status(syncId=syncId)
        return echo.get("msg")

    @error_throw
    async def fetchMessageFromId(
            self,
            messageId: int
    ) -> Optional[MessageChain]:
        """通过messageId获取消息

        Args:
            messageId (int): 获取消息的messageId

        Returns:
            Optional[MessageChain]: 包含该条消息的消息链，如果该消息未被缓存返回None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="messageFromId",
                content={
                    "id": messageId
                }
            )
        )
        message = await self._raise_status(syncId=syncId)
        return message and MessageChain(*message.get("messageChain"))

    @error_throw
    async def fetchFriendList(self) -> Optional[List[Friend]]:
        """
        获取好友列表
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="friendList"
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and [Friend(**friend) for friend in data.get("data")]

    @error_throw
    async def fetchFriendProfile(
            self,
            friend: Union[Friend, int]
    ) -> Optional[Friend]:
        """
        获取好友详细资料
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="friendProfile",
                content={
                    "target": friend if isinstance(friend, int) else friend.id
                }
            )
        )
        friend = await self._raise_status(syncId=syncId)
        return friend and FriendProfile(**friend)

    @error_throw
    async def fetchGroupList(self) -> Optional[List[Group]]:
        """
        获取群列表
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="groupList"
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and [Group(**group) for group in data.get("data")]

    @error_throw
    async def fetchMemberList(
            self,
            group: Union[Group, int]
    ) -> Optional[List[Member]]:
        """
        获取群成员列表
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="memberList",
                content={
                    "target": group if isinstance(group, int) else group.id
                }
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and [Member(**member) for member in data.get("data")]

    @error_throw
    async def fetchMemberProfile(
            self,
            group: Union[Group, int],
            member: Union[Member, int]
    ) -> Optional[MemberProfile]:
        """
        获取成员详细资料
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="memberProfile",
                content={
                    "target": group if isinstance(group, int) else group.id,
                    "memberId": member if isinstance(member, int) else member.id
                }
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and MemberProfile(**data)

    @error_throw
    async def fetchBotProfile(self) -> Optional[BotProfile]:
        """
        获取bot详细资料
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="botProfile"
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and BotProfile(**data)

    @error_throw
    async def fetchUserProfile(self, target: int) -> Optional[UserProfile]:
        """
        获取用户详细资料
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="userProfile",
                content={
                    "target": target
                }
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and UserProfile(**data)

    @error_throw
    async def fetchFileList(
            self,
            target: Union[int, Group, Friend] = None,
            dir_id: str = "",
            path: str = None,
            withDownloadInfo: bool = False,
            offset: int = 1,
            size: int = 10,
    ) -> Optional[List[File]]:
        """获取文件列表

        Args:
            dir_id (str, optional): 文件夹id, 空串为根目录. Defaults to "".
            path (str, optional): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id. Defaults to None.
            target (Union[int, Group, Friend], optional): 群聊或好友. Defaults to None.
            withDownloadInfo (bool, optional): 	是否携带下载信息，额外请求，无必要不要携带. Defaults to False.
            offset (int, optional): 分页偏移. Defaults to 1.
            size (int, optional): 分页大小. Defaults to 10.

        Returns:
            Optional[List[File]]: 一个文件对象列表
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="file_list",
                content={
                    "id": dir_id,
                    "path": path,
                    "target": target,
                    "withDownloadInfo": withDownloadInfo,
                    "offset": offset,
                    "size": size
                }
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and [File(**file) for file in data]

    @error_throw
    async def fetchFileInfo(
            self,
            target: Union[int, Group, Friend] = None,
            dir_id: str = "",
            path: str = None,
            withDownloadInfo: bool = False
    ) -> Optional[File]:
        """获取文件信息

        Args:
            dir_id (str, optional): 文件夹id, 空串为根目录. Defaults to "".
            path (str, optional): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id. Defaults to None.
            target (Union[int,Group,Friend], optional): _description_. Defaults to None.
            withDownloadInfo (bool, optional): _description_. Defaults to False.

        Returns:
            Optional[File]: 一个文件对象
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="file_info",
                content={
                    "id": dir_id,
                    "path": path,
                    "target": target,
                    "withDownloadInfo": withDownloadInfo
                }
            )
        )
        data = await self._raise_status(syncId=syncId)
        return data and File(**data)

    @error_throw
    async def fileMkdir(
            self,
            target: Union[int, Friend, Group],
            directoryName: str,
            dir_id: str = "",
            path: Optional[str] = None,
    ) -> Optional[File]:
        """创建文件夹

        Args:
            target (Union[int, Friend, Group]): 群组或好友QQ，可以是int或者对象
            directoryName (str): 新建文件夹名
            dir_id (str, optional): 父目录id,空串为根目录. Defaults to "".
            path (Optional[str], optional): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id. Defaults to None.

        Returns:
            Optional[File]: 一个文件对象
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="file_mkdir",
                content={
                    "id": dir_id,
                    "path": path,
                    "target": target,
                    "directoryName": directoryName
                }
            )
        )
        return await self._raise_status(syncId=syncId)

    @error_throw
    async def fileDelete(
            self,
            target: Union[int, Friend, Group],
            file_id: str = "",
            path: Optional[str] = None,
    ) -> None:
        """删除文件

        Args:
            target (Union[int, Friend, Group]): 群或好友QQ
            file_id (str, optional): 删除文件id. Defaults to "".
            path (Optional[str], optional): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id. Defaults to None.

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="file_delete",
                content={
                    "id": file_id,
                    "path": path,
                    "target": target,
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def fileMove(
            self,
            target: Union[int, Friend, Group],
            path: str,
            file_id: str = "",
            moveTo: str = None,
            moveToPath: str = None,
    ) -> None:
        """移动文件

        Args:
            target (Union[int, Friend, Group]): 群或好友QQ
            path (str): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id
            file_id (str, optional): 移动文件id. Defaults to "".
            moveTo (str, optional): 移动目标文件夹id. Defaults to None.
            moveToPath (str, optional): 移动目标文件路径, 文件夹允许重名, 不保证准确, 准确定位使用 moveTo. Defaults to None.

        Raises:
            ValueError: moveTo和moveToPath至少要有一个

        Returns:
            str: 状态
        """
        if moveTo is None and moveToPath is None:
            raise ValueError("必须选择移动至目标的位置")
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="file_move",
                content={
                    "id": file_id,
                    "path": path,
                    "target": target,
                    "moveTo": moveTo,
                    "moveToPath": moveToPath
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def fileRename(
            self,
            target: Union[int, Friend, Group],
            renameTo: str,
            file_id: str = "",
            path: str = None,
    ) -> None:
        """重命名文件

        Args:
            target (Union[int, Friend, Group]): 群号或好友QQ号
            path (str): 文件夹路径, 文件夹允许重名, 不保证准确, 准确定位使用 id
            renameTo (str): 新文件名
            file_id (str, optional): 重命名文件id. Defaults to "".

        Returns:
            str: 
        """
        await self.ws.send_json(
            wrap_data_json(
                command="file_rename",
                content={
                    "id": file_id,
                    "path": path,
                    "target": target,
                    "renameTo": renameTo
                }
            )
        )
        return None

    @error_throw
    async def deleteFriend(
            self,
            friend: Union[int, Friend],
    ) -> None:
        """删除好友

        Args:
            friend (Union[int, Friend]): 删除好友的QQ号码

        Returns:
            str: 
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="deleteFriend",
                content={
                    "target": friend
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def mute(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
            time: Optional[int],
    ) -> None:
        """禁言群成员

        Args:
            group (Union[int, Group]): 指定群
            member (Union[int, Member]): 指定群员
            time (Optional[int]): 禁言时长，单位为秒，最多30天，默认为0

        Returns:
            str: 
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="mute",
                content={
                    "target": group,
                    "memberId": member,
                    "time": time
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def unmute(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
    ) -> None:
        """解除群成员禁言

        Args:
            group (Union[int, Group]): 指定群
            member (Union[int, Member]): 指定群员

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="unmute",
                content={
                    "target": group,
                    "memberId": member
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def kick(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
            msg: str = "",
    ) -> None:
        """移除群成员

        Args:
            group (Union[int, Group]): 指定群的群
            member (Union[int, Member]): 指定群员
            msg (str, optional): 信息. Defaults to "".

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="kick",
                content={
                    "target": group,
                    "memberId": member,
                    "msg": msg,
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def quit(
            self,
            group: Union[int, Group]
    ) -> None:
        """退出群聊

        Args:
            group (Union[int, Group]): 退出的群

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="quit",
                content={
                    "target": group
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def muteAll(
            self,
            group: Union[int, Group],
    ) -> None:
        """全体禁言

        Args:
            group (Union[int, Group]): 指定群

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="muteAll",
                content={
                    "target": group,
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def unmuteAll(
            self,
            group: Union[int, Group]
    ) -> None:
        """解除全体禁言


        Args:
            group (Union[int, Group]): 指定群

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="unmuteAll",
                content={
                    "target": group if isinstance(group, int) else group.id,
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def setEssence(
            self,
            messageId: Union[int, Source]
    ) -> None:
        """设置群精华消息

        Args:
            messageId (Union[int, Source]): 精华消息的message

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="setEssence",
                content={
                    "target": messageId if isinstance(messageId, int) else messageId.id
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def fetchGroupConfig(
            self,
            group: Union[int, Group],
    ) -> Optional[GroupConfig]:
        """获取群设置

        Args:
            group (Union[int, Group]): 指定群的群号

        Returns:
            Optional[GroupConfig]: 一个群设置对象
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="groupConfig",
                subCommand="get",
                content={
                    "target": group
                }
            )
        )
        config = await self._raise_status(syncId=syncId)
        return config and GroupConfig(**config)

    @error_throw
    async def setGroupConfig(
            self,
            group: Union[int, Group],
            config: Union[Dict, GroupConfig] = None
    ) -> None:
        """修改群设置

        Args:
            group (Union[int, Group]): 	指定群
            config (Union[Dict, GroupConfig], optional): 群设置. Defaults to None.

        Returns:
            str: _description_
        """
        if isinstance(config, GroupConfig):
            config = GroupConfig.__dict__
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="groupConfig",
                subCommand="set",
                content={
                    "target": group,
                    "config": config
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def fetchMemberInfo(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
    ) -> Optional[Member]:
        """获取群员设置

        Args:
            group (Union[int, Group]): 指定群
            member (Union[int, Member]): 指定群员

        Returns:
            Optional[Member]: 一个Member对象
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="memberInfo",
                subCommand="get",
                content={
                    "target": group,
                    "memberId": member
                }
            )
        )
        info = await self._raise_status(syncId=syncId)
        return info and Member(**info)

    @error_throw
    async def setMemberInfo(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
            info: Union[Dict, MemberInfo]
    ) -> None:
        """修改群员设置

        Args:
            group (Union[int, Group]): 指定群
            member (Union[int, Member]): 指定群员
            info (Union[Dict, MemberInfo]): 群员设置对象或者字典

        Returns:
            None
        """
        if isinstance(info, MemberInfo):
            info = MemberInfo.elements
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="memberInfo",
                subCommand="update",
                content={
                    "target": group,
                    "memberId": member,
                    "info": info
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def setMemberAdmin(
            self,
            group: Union[int, Group],
            member: Union[int, Member],
            assign: bool,
    ) -> None:
        """修改群员管理员

        Args:
            group (Union[int, Group]): 指定群
            member (Union[int, Member]): 指定群员
            assign (bool): 是否设置为管理员

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="memberAdmin",
                content={
                    "target": group,
                    "memberId": member,
                    "assign": assign
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    @error_throw
    async def fetchAnnouncement(
            self,
            group: Union[int, Group],
            offset: Optional[int] = None,
            size: Optional[int] = None,
    ) -> List[Announcement]:
        """获取群公告

        Args:
            group (Union[int, Group]): 指定群
            offset (Optional[int], optional): 分页参数. Defaults to None.
            size (Optional[int], optional): 分页参数. Defaults to None.

        Returns:
            List[Announcement]: 群公告对象
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="anno_list",
                content={
                    "id": group,
                    "offset": offset,
                    "size": size
                }
            )
        )
        anno_list = await self._raise_status(syncId=syncId)
        return anno_list and [Announcement(**anno) for anno in anno_list]

    @error_throw
    async def publishAnnouncement(
            self,
            group: Union[int, Group],
            content: str,
            sendToNewMember: bool = False,
            pinned: bool = False,
            showEditCard: bool = False,
            showPopup: bool = False,
            requireConfirmation: bool = False,
            image: Optional[Image] = None,
            imageUrl: Optional[str] = None
    ) -> Optional[Announcement]:
        """此方法向指定群发布群公告
        Args:
            group          	    群组，可以是int也可以是群组对象
            content         	公告内容
            sendToNewMember    	是否发送给新成员
            pinned          	是否置顶
            showEditCard       	是否显示群成员修改群名片的引导
            showPopup       	是否自动弹出
            requireConfirmation	是否需要群成员确认
            image        	    公告图片对象
            imageUrl            公告图片url,本地图片请使用karas.elements.Image对象

        Returns:
            包含群公告对象的列表
        """
        if isinstance(image, Image):
            await self.uploadMultipart(image, type_="group")
            imageUrl = image.url
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="anno_publish",
                content={
                    "target": group,
                    "content": content,
                    "sendToNewMember": sendToNewMember,
                    "pinned": pinned,
                    "showEditCard": showEditCard,
                    "showPopup": showPopup,
                    "requireConfirmation": requireConfirmation,
                    "imageUrl": imageUrl
                }
            )
        )
        anno = await self._raise_status(syncId=syncId)
        return anno and Announcement(**anno)

    @error_throw
    async def deleteAnnouncement(
            self,
            group: Union[int, Group],
            fid: int
    ) -> None:
        """删除群公告

        Args:
            group (Union[int, Group]): 指定群
            fid (int): 群公告id

        Returns:
            None
        """
        syncId = self.namespace.gen()
        await self.ws.send_json(
            wrap_data_json(
                syncId=syncId,
                command="anno_delete",
                content={
                    "id": group,
                    "fid": fid
                }
            )
        )
        await self._raise_status(syncId=syncId)
        return None

    async def add_task(self, coro: Coroutine, name: str = None, callback: Callable = None, *_, **__) -> str:
        """向Yurine运行的loop中添加一个task"""
        if not inspect.iscoroutine(coro):
            raise ValueError(f"{coro} is not coroutine")
        if name is None:
            name = self.namespace.gen()
        _task = self.loop.create_task(coro, name=name)
        self._tasks[name] = _task
        self.logging.info(f"add task <task-{name}>")
        if callback:
            self.logging.info(f"add task <task-{name}> callback {callback.__name__}")
            _task.add_done_callback(callback)
        return name

    async def get_task(self, name: str) -> Optional[asyncio.Task]:
        if name not in self._tasks:
            return None
        return self._tasks[name]

    async def pop_task(self, name: str) -> Optional[asyncio.Task]:
        if name not in self._tasks:
            return None
        return self._tasks.pop(name)

    async def cancel_task(self, name: str) -> None:
        _task = await self.pop_task(name)
        if _task:
            await self._raise_task_cancel(_task)

    async def _raise_task_cancel(self, _task: asyncio.Task) -> None:
        """取消已经添加的的任务"""
        if not _task.cancelled():
            _task.cancel()
            try:
                await _task
            except asyncio.CancelledError:
                self.logging.info(f"canceled <task {_task.get_name()}>")

    async def _raise_status(self, data: Optional[Dict] = None, syncId: str = None) -> Optional[Dict]:
        try:
            while 1:
                await asyncio.sleep(.1)
                _json_data = data or (syncId and self._receiveData.pop(syncId, None)) or await self.ws.receive_json()
                if _json_data.get("syncId") and _json_data.get("syncId") == "-1":
                    await self._receiver(_json_data)
                    continue
                break
        except RuntimeError:
            return await self._raise_status(data=data, syncId=syncId)
        self.logging.debug(f"recv data {_json_data}")
        _data = _json_data.get("data")
        _status_code = _json_data.get("code") or (_data and _data.get("code"))
        _exception = status_code_exception.get(_status_code or 0)
        if _exception is not None:
            raise _exception(_data.get("msg"))
        return _json_data.get("data") or _data or (_data and _data.get("msg")) or _json_data

    def run_forever(self) -> None:
        """挂起"""
        self.logging.debug("run_forever")
        if not self._is_running:
            self.start()
        if not self._receiver_is_running:
            self.loop.create_task(self._receiver())
            self.logging.info(f"receiver created")
        try:
            self.loop.run_forever()
        except Exception:
            self.logging.info("Bot closing...")
            raise
        finally:
            self.close()

    def start(self) -> Optional["Yurine"]:
        self.logging.debug("running function start")
        if self._is_running:
            return None
        self.logging.info(f"initialization......")
        _code = self.loop.run_until_complete(self._initialization())
        self.logging.debug(f"initialization {_code}")
        self._is_running = True
        return self

    async def astart(self) -> Optional["Yurine"]:
        self.logging.debug("running function start")
        if self._is_running:
            return None
        self.logging.info(f"initialization......")
        _code = await self._initialization()
        self.logging.debug(f"initialization {_code}")
        self._is_running = True
        return self

    def close(self) -> None:
        """关闭"""
        if self.loop.is_closed():
            return
        self.stop()
        try:
            self.loop.close()
        except RuntimeError:
            pass
        self.logging.debug(f"loop closed {self.loop.is_closed()}")

    async def aclose(self) -> None:
        """关闭"""
        if self.loop.is_closed():
            return
        await self.stop()
        try:
            self.loop.close()
        except RuntimeError:
            pass
        self.logging.debug(f"loop closed  {self.loop.is_closed()}")

    async def stop(self) -> int:
        """停止所有运行中的事件"""
        for _task in asyncio.all_tasks(self.loop):
            self.logging.debug(f"try canceling <task {id(_task)}>")
            await self._raise_task_cancel(_task)
        if self.ws is not None and not self.ws.closed:
            await self.ws.close()
            self.logging.info(f"websocket closed")
        if self.session is not None and not self.session.closed:
            # await self._release()
            await self.session.close()
            self.logging.info("Session closed")
        return 0

    # def __del__(self):
    #     self.close()

    def __enter__(self):
        self.logging.debug("enter")
        if not self._is_running:
            self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self._is_running = False
        # self.close()
        self.logging.debug("exit")

    async def __aenter__(self):
        self.logging.debug("aenter")
        if not self._is_running:
            await self.astart()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # self._is_running = False
        # await self.aclose()
        self.logging.debug("aexit")
