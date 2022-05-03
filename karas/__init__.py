from aiohttp import ClientSession
import asyncio
from typing import List, Optional, Union, AsyncGenerator
from .chain import MessageChain
from .Sender import Friend, Group, Member, Stranger, ReceptorBase
from .messages import MessageBase
from .event import Auto_Switch_Event, EventBase, RequestEvent, Event, NudgeEvent
from .elements import ElementBase, File, FlashImage, Image, Plain, Source, Voice, FriendProfile, MemberProfile, \
    BotProfile, UserProfile
from .exceptions import InvalidArgumentError, VerifyError
from .util.Logger import Logging
from .util.network import error_throw, URL_Route, wrap_data_json


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

    @classmethod
    async def event_parse(cls, original: dict, _logger: Logging = None) -> AsyncGenerator:
        # print(f"\nOriginal:{original}\n")
        _event: Union[MessageBase, Event] = Auto_Switch_Event.parse_json(**original)
        isBotEvent = yield _event
        _logger.info(_event)
        if isBotEvent:
            _logger.info(_event.__str__())
        elif _event:
            await cls.executor(_event)
        yield

    @classmethod
    async def bot_event(cls, _event: dict):
        # bot触发的事件
        _event: MessageBase = Auto_Switch_Event.parse_json(**_event)
        return _event

    @classmethod
    async def executor(cls, message: Union["MessageBase", "EventBase"]) -> Optional[str]:
        if cls.listeners.get(message.type) is None:
            return
        for listener in cls.listeners.get(message.type):
            _message_dict = message.__dict__
            _func_params = listener.__annotations__

            _reversed = {_v if isinstance(type, type(_v)) else type(_v): _k for _k, _v in _message_dict.items()}
            _types = [v if isinstance(type, type(v)) else type(v) for v in _message_dict.values()]
            _o = {}
            for k, t in _func_params.items():
                if t in _types:
                    _o[k] = _message_dict[_reversed[t]]
            await listener(**_o)


class Yurine(object):
    """
    Yurine:
        负责服务器的连接，Karas的调度
    """

    def __init__(
            self,
            host: str,
            port: int,
            qq: int,
            verifyKey: str,
            loop: asyncio.BaseEventLoop = None,
            karas: Karas = None,
            protocol: str = "ws",
            sessionKey: str = None,
            session: ClientSession = None,
            loggerLevel: str = "INFO"
    ) -> None:
        self.url = f"{protocol}://{host}:{port}"
        self.protocol = protocol
        self.account = qq
        self.verifyKey = verifyKey
        self.sessionKey = sessionKey
        self.session = session

        self.offline = False

        self.route = URL_Route(self.url)
        self.logging = Logging(loggerLevel, qq)
        self.loop = loop or asyncio.get_event_loop()
        self.karas = karas or Karas

    @error_throw
    async def _initialization(self) -> None:
        """初始化"""
        self.logging.debug(f"URL:  {self.url}")
        if not self.session:
            self.session = ClientSession(loop=self.loop)
            await self._connect()
            self.logging.info("Account verify success")
            self.logging.debug(f"got verifyKey {self.sessionKey}")

            # async with self.session.post(
            #         "/bind",
            #         json={
            #             "qq": self.account,
            #             "sessionKey": self.sessionKey
            #         }
            # ) as _bind_response:
            #     _bind_response.raise_for_status()
            #     _bind_msg = await _bind_response.json()
            #     self.logging.debug(f"accout bind response {_bind_msg}")
            #     if _bind_msg.get("msg") == "success":
            #         self.logging.info("Account bind success")
            #         self.session.headers["sessionKey"] = self.sessionKey

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
            except Exception as e:
                self.logging.warning("connect reset, retry...")
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(3)

    @error_throw
    async def _connect(self) -> Optional[int]:
        """
        向服务器发起 WebSocket 连接
        :return 返回连接是否成功
        :raise VerifyError
        """
        self.logging.debug(f"connect websocket server {self.url}")
        self.ws = await self.session.ws_connect(
            url=self.route("all"),
            headers={
                "verifyKey": self.verifyKey,
                "qq": str(self.account)
            }
        )
        _verify_response: dict = await self.ws.receive_json()
        self.logging.debug(f"verify key {_verify_response}")
        _verify_data: dict = _verify_response.get("data")
        if _verify_data.get("code") != 0:
            raise VerifyError
        self.sessionKey: str = _verify_data.get("session")
        self.loop.create_task(self._ping())
        return 0

    @error_throw
    async def _receiver(self) -> None:
        """事件监听器"""
        while True:
            _receive_data: dict = await self.ws.receive_json()
            if _receive_data.get("syncId") == "-1":
                _parser = self.karas.event_parse(_receive_data["data"], self.logging)
                _event = await _parser.__anext__()
                await _parser.asend(self.account == _event.event.fromId) \
                    if isinstance(_event, Event) else await _parser.asend(False)

    def listen(self, registerEvent: Union[str, "EventBase", "MessageBase"]):
        """事件装饰器
        Args:
            registerEvent (str, Event, Message): 要监听的事件或者消息类型

        Returns:
            None: NoReturn
        """
        if registerEvent:
            registerEvent = registerEvent if isinstance(registerEvent, str) else registerEvent.type

        def register_decorator(Callable):
            def register_wrapper(*args, **kwargs):
                self.logging.debug(f"register listener [{Callable.__name__}] for Event[{registerEvent}]")
                if Karas.listeners.get(registerEvent):
                    Karas.listeners.get(registerEvent).apeend(Callable)
                else:
                    Karas.listeners[registerEvent] = [Callable, ]

            return register_wrapper()

        return register_decorator

    @error_throw
    async def accept(self, requestEvent: "RequestEvent", message: str = None) -> None:
        requestEvent.message = message
        await self.ws.send_json(
            wrap_data_json(
                syncId="accept",
                command=requestEvent.command,
                content=requestEvent.accept
            )
        )

    @error_throw
    async def uploadMultipart(self, obj: Union["Voice", "File", "Image", "FlashImage"], type: str) -> None:
        async with self.session.post(
                self.route(f"upload{obj.type}"),
                data={
                    "sessionKey": self.sessionKey,
                    "type": type,
                    obj.ftype: open(obj.file, "rb") if isinstance(obj.file, str) else obj.file
                }
        ) as _response:
            _response_json = await _response.json()
            obj(**_response_json)

    async def _element_check(self, element: "ElementBase", type: str):
        if isinstance(element, (Image, Voice, File, FlashImage)):
            await self.uploadMultipart(element, type=type)
        return element.elements

    @error_throw
    async def sendGroup(
            self, group: Union[int, "Group"],
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
        _chain = [(await self._element_check(_e, type="group")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = {
            "group": group if isinstance(group, int) else group.id,
            "quote": quote.id,
            "messageChain": _chain
        }
        await self.ws.send_json(
            wrap_data_json(
                syncId="sendGroupMessage",
                command="sendGroupMessage",
                content=content
            ))
        self.logging.info(f"Bot => {[str(_e) for _e in _chain]}")
        echo = await self.ws.receive_json()
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
        _chain = [(await self._element_check(_e, type="friend")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = await _build_content_json("target", friend, quote, _chain)
        await self.ws.send_json(
            wrap_data_json(
                syncId="sendFriendMessage",
                command="sendFriendMessage",
                content=content
            )
        )
        self.logging.info(f"Bot => {[str(_e) for _e in _chain]}")
        echo = await self.ws.receive_json()
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
        _chain = [(await self._element_check(_e, type="temp")) for _e in Elements] \
            if not isinstance(Elements, MessageChain) else Elements.parse_to_json()
        content = {
            "qq": member if isinstance(member, int) else member.id,
            "group": group if isinstance(member, int) else group.id,
            quote: quote and quote.id,
            "messageChain": _chain
        }
        await self.ws.send_json(
            wrap_data_json(
                syncId="sendTempMessage",
                command="sendTempMessage",
                content=content
            )
        )
        echo = await self.ws.receive_json()
        return echo.get("messageId")

    @error_throw
    async def recall(self, message: Union[Source, int]):
        await self.ws.send_json(
            wrap_data_json(
                command="recall",
                syncId="recall",
                content={
                    "messageId": message.id if isinstance(message, Source) else message
                }
            )
        )

    @error_throw
    async def sendNudge(
            self,
            target: Union[int, "ElementBase", "Friend", "Member", None] = None,
            subject: Union[int, "Group", "Friend", None] = None,
            kind: Union[str, "Group", "Friend", "Stranger", None] = None,
            nudgeEvent: "NudgeEvent" = None,
    ) -> None:
        """发送头像戳一戳消息

        Args:
            nudgeEvent:(Event): 戳一戳事件的主体，不为None时则对发出此事件的对象发送戳一戳
            target (Union[int,ElementBase]): 戳一戳的目标, QQ号, 可以为 bot QQ号
            subject (Union[int,Group,Friend]): 戳一戳接受主体(上下文), 戳一戳信息会发送至该主体, 为群号/好友QQ号
            kind (Union[str,Group,Friend,Stranger]): 上下文类型, 可选值 Friend, Group, Stranger

        Returns:
            _type_: 不知道会返回什么，不返回了，反正也没什么意义
        """
        target = target if target is not None else nudgeEvent.fromId
        subject = subject if nudgeEvent is None else nudgeEvent.subject.id \
            if subject is None else target.group.id if isinstance(target, Member) else target.id
        kind = kind if nudgeEvent is None else nudgeEvent.subject.kind \
            if kind is None else target.group.type if isinstance(target, Member) else target.type
        await self.ws.send_json(
            wrap_data_json(
                syncId="sendNudge",
                command="sendNudge",
                content={
                    "target": target if isinstance(target, int) else target.id,
                    "subject": subject if isinstance(subject, int) else subject.id,
                    "kind": kind if isinstance(kind, str) else kind.type
                }))
        echo: dict = await self.ws.receive_json()
        if echo.get("data").get("code") != 0:
            self.logging.error(f"{echo}")
        return echo.get("data").get("code")

    async def fetchFriendList(self) -> Optional[List[Friend]]:
        """
        获取好友列表
        """
        await self.ws.send_json(
            wrap_data_json(
                command="friendList"
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and [Friend(**friend) for friend in data.get("data")]

    async def fetchFriendProfile(self, friend: Union[Friend, int]) -> Optional[Friend]:
        """
        获取好友详细资料
        """
        await self.ws.send_json(
            wrap_data_json(
                command="friendProfile",
                content={
                    "target": friend if isinstance(friend, int) else friend.id
                }
            )
        )
        echo = await self.ws.receive_json()
        friend = echo.get("data")
        return friend and FriendProfile(**friend)

    async def fetchGroupList(self) -> Optional[List[Group]]:
        """
        获取群列表
        """
        await self.ws.send_json(
            wrap_data_json(
                command="groupList"
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and [Group(**group) for group in data.get("data")]

    async def fetchMemberList(self, group: [Group, int]) -> Optional[List[Member]]:
        """
        获取群成员列表
        """
        await self.ws.send_json(
            wrap_data_json(
                command="memberList",
                content={
                    "target": group if isinstance(group, int) else group.id
                }
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and [Member(**member) for member in data.get("data")]

    async def fetchMemberProfile(self, group: Union[Group, int], member: [Member, int]) -> Optional[MemberProfile]:
        """
        获取成员详细资料
        """
        await self.ws.send_json(
            wrap_data_json(
                command="memberProfile",
                content={
                    "target": group if isinstance(group, int) else group.id,
                    "memberId": member if isinstance(member, int) else member.id
                }
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and MemberProfile(**data)

    async def fetchBotProfile(self) -> Optional[BotProfile]:
        """
        获取bot详细资料
        """
        await self.ws.send_json(
            wrap_data_json(
                command="botProfile"
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and BotProfile(**data)

    async def fetchUserProfile(self, target: int) -> Optional[UserProfile]:
        """
        获取用户详细资料
        """
        await self.ws.send_json(
            wrap_data_json(
                command="userProfile",
                content={
                    "target": target
                }
            )
        )
        echo = await self.ws.receive_json()
        data = echo.get("data")
        return data and UserProfile(**data)

    async def _raise_task_cancel(self, _task: asyncio.Task) -> None:
        """取消当前事件循环中的任务"""
        if not _task.cancelled():
            _task.cancel()
            try:
                await _task
            except asyncio.CancelledError:
                self.logging.debug(f"cancel <task {id(_task)}>")
                ...

    def run_forever(self) -> None:
        """挂起"""
        self.loop.run_until_complete(self._initialization())
        self.loop.create_task(self._receiver())
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.logging.info("Bot close...")
            raise
        finally:
            self.close()

    def start(self):
        pass

    def close(self):
        """关闭"""
        if self.loop.is_closed():
            return
        self.loop.run_until_complete(self.stop())
        self.loop.close()
        self.logging.debug(f"loop closed is  {self.loop.is_closed()}")

    async def stop(self):
        """停止所有运行中的事件"""
        for _task in asyncio.all_tasks(self.loop):
            self.logging.debug(f"try canceling <task {id(_task)}>")
            await self._raise_task_cancel(_task)
        if not self.ws.closed:
            await self.ws.close()
            self.logging.info(f"websocket closed")
        if not self.session.closed:
            # await self._release()
            await self.session.close()
            self.logging.info("Session closed")
        return 0

    async def __aenter__(self):
        self.logging.debug("enter service")
        await self._initialization()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.logging.debug("exit service")
        await self.stop()
        self.logging.info("exiting...")

    def __enter__(self):
        self.loop.run_until_complete(self._initialization())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
