from time import time
from karas.util import BaseModel
from karas.elements import ElementBase
from karas.elements import MessageElementEnum
from typing import List, Dict, Optional, Union


class MessageChain(BaseModel):
    def __init__(self, *chain) -> None:
        self._data = chain
        for _element in chain:
            _element_type = _element.get("type")
            _attr_obj = Quote(**_element) if _element_type == "Quote" \
                else Forward(**_element) if _element_type == "Forward" \
                else MessageElementEnum[_element_type].value(**_element)
            if hasattr(self, _element_type):
                getattr(self, _element_type).append(_attr_obj)
            else:
                setattr(self, _element_type, [_attr_obj])

    def parse_to_json(self) -> list:
        """
        将消息链内部的消息对象转换成可发送的数组形式
        """
        _elements = []
        for attr in self.__dict__.keys():
            if attr == "Source" or attr.startswith("_"):
                continue
            _elements += [_e.elements for _e in self.fetch(attr)]
        return _elements

    def fetch(self, element: Union[str, "ElementBase"]) -> Optional[List["ElementBase"]]:
        """从消息链中取出指定类型的消息对象列表

        Args:
            element (Union[str, ElementBase]): 指定的消息类型

        Returns:
            List[ElementBase]: 一个包含了指定消息类型的消息对象列表,如果不存在则返回None
        """
        return getattr(self, element if isinstance(element, str) else element.type, None)

    def fetchone(self, element: Union["ElementBase", str]) -> Optional["ElementBase"]:
        """从消息链中取出指定类型的第一个消息对象

        Args:
            element (Union[ElementBase,str]): 指定要取出的消息对象

        Returns:
            Optional[ElementBase]: 消息链中的第一个指定消息对象，不存在则返回None
        """
        _element = element if isinstance(element, str) else element.type
        return (self.has(_element) or None) and getattr(self, _element, None)[0]

    def has(self, element: Union[str, "ElementBase"]) -> bool:
        """判断消息链中是否存在该类型的消息对象

        Args:
            element (Union[str,ElementBase]): 要判断的消息对象，可以是原对象或者字符串

        Returns:
            bool: 一个普通的Boolean
        """
        return hasattr(self, element if isinstance(element, str) else element.type)

    def has_all(self, *element: Union["ElementBase", str, List]) -> bool:
        """判断消息链中是否包含所有指定消息类型

        Returns:
            bool: 如果消息链中含有所有指定的消息类型返回true, 反之返回false
        """
        return all((self.has(_e) for _e in element))

    def has_any(self, *element: Union["ElementBase", str, List]) -> bool:
        """判断消息链中是否至少包含一个指定消息类型

        Returns:
            bool: 如果消息链中至少含有一个指定的消息类型返回true, 反之返回false
        """
        return any((self.has(_e) for _e in element))

    def to_str(self) -> str:
        """将消息链的内容以str方式返回

        Returns:
            str: 一个表示消息链的字符串
        """
        return "".join([str(_e) for _e in self._get_elements() if _e.type != "Source"])

    def to_text(self) -> str:
        """获取消息链中的文本消息

        Returns:
            _type_: 一个只有文本消息类型的str
        """
        return self.fetch("Plain") and "".join([_plain.text for _plain in self.fetch("Plain")])

    def _get_elements(self) -> List[ElementBase]:
        _elements = []
        _chain = (_V for _K, _V in self.__dict__.items()
                  if not _K.startswith("_"))
        for _e in _chain:
            _elements += _e
        return _elements

    def __str__(self) -> str:
        return f"".join([_e.__str__() for _e in self._get_elements()])


class Quote(ElementBase):
    id: int
    groupId: int
    senderId: int
    targetId: int
    origin: MessageChain

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "Quote"


class node(ElementBase):
    senderId: int
    time: int
    senderName: str
    messageChain: MessageChain
    messageId: int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Forward(ElementBase):
    nodeList: List[node]

    def __init__(self, **kws):
        self._data = kws
        self.nodeList = list(node(**content)
                             for content in kws.get("nodeList"))
        self.type = "Forward"

    # @property
    # def elements(self) -> Dict[Any, Any]:
    #     self._data["type"] = "Forward"
    #     return self._data

    @classmethod
    def _build(cls, _senders, _messages) -> List:
        _build_lst = []
        _len = len(_messages)
        for s, m in zip(_senders, _messages):
            _senderId, _senderName = s.popitem()
            _build_lst.append(
                {
                    "senderId": _senderId,
                    "time": int(time()-_len),
                    "senderName": _senderName,
                    "messageChain": [e.elements for e in m] if isinstance(m, List) else m.parse_to_json()
                }
            )
            _len -= 1
        return _build_lst

    @classmethod
    def build(cls, senders: List[Dict[int, str]], messages: List[Union[MessageChain, List[ElementBase]]]) -> "Forward":
        """Args:

            sender:发送者列表，长度应当与消息列表一致或者为1,格式为[{id,name}] 

                例: [{123,"senderName1"},{234:"senderName2"}]

            messages:消息列表,格式为[[消息元素]]

                例:[[Plain("哼哼")],[Plain("啊啊啊啊啊"),Image("xxx")]]
        """
        if len(senders) != len(messages) and len(senders) != 1:
            raise ValueError
        if len(senders) == 1:
            sender = senders.pop()
            senders = [sender.copy() for _ in range(len(messages))]
        return cls(**{"nodeList": cls._build(senders, messages)})
