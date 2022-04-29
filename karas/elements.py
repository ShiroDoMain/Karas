from enum import Enum
from typing import Any, BinaryIO, Dict, Optional, Union

from .util import BaseModel


class ElementBase(BaseModel):
    type: str

    @property
    def elements(self) -> Dict[Any, Any]:
        return {_K: _V for _K, _V in self.__dict__.items() if _V is not None}

    def __str__(self) -> str:
        return f"{self.type}:{[str(_v) for _v in self.__dict__.values()]}"


class At(ElementBase):
    type: str = "At"
    target: int
    display: str


class AtAll(ElementBase):
    type: str = "At"


class Face(ElementBase):
    type: str = "Face"
    faceId: int
    name: str


class Plain(ElementBase):
    type: str = "Plain"
    text: str

    def __str__(self) -> str:
        return self.text


class Source(ElementBase):
    type: str = "Source"
    id: int
    time: int


class Image(ElementBase):
    type: str = "Image"
    imageId: str
    url: str
    path: str
    base64: str

    def __init__(self, file: Union[str, BinaryIO, bytes, None] = None, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ftype = "img"
        # self.type = "Image"
        self.file = file

    def __str__(self) -> str:
        return f"[图片:{self.imageId}]"

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.imageId = kwds.get("imageId")
        self.url = kwds.get("url")


class FlashImage(Image):
    type: str = "FlashImage"
    imageId: str
    url: str
    path: str
    base64: str


class Voice(ElementBase):
    type: str = "Voice"
    voiceId: str
    url: str
    path: Optional[str]
    base64: Optional[str]
    length: int

    def __init__(self, file: Union[str, BinaryIO, bytes, None] = None, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ftype = "voice"
        self.type = "Voice"
        self.file = file

    def __str__(self) -> str:
        return f"[语音:{self.voiceId}]"

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.voiceId = kwds.get("voiceId")
        self.url = kwds.get("url")


class Xml(ElementBase):
    type: str = "Xml"
    xml: str


class Json(ElementBase):
    type: str = "Json"
    json: str


class App(ElementBase):
    type: str = "App"
    content: str


class Poke(ElementBase):
    """
    Poke: 戳一戳
    ShowLove: 比心
    Like: 点赞
    Heartbroken: 心碎
    SixSixSix: 666
    FangDaZhao: 放大招

    Args:
        ElementBase (_type_): _description_
    """
    type: str = "Poke"
    name: str


class Dice(ElementBase):
    type: str = "Dice"
    value: int


class MarketFace(ElementBase):
    """目前商城表情仅支持接收和转发，不支持构造发送"""
    type: str = "MarketFace"
    id: int
    name: str


class MusicShare(ElementBase):
    """
    kind	str	类型
    title	str	标题
    summary	str	概括
    jumpUrl	str	跳转路径
    pictureUrl	str	封面路径
    musicUrl	str	音源路径
    brief	str	简介

    Args:
        ElementBase (_type_): _description_
    """
    type: str = "MusicShare"
    kind: str
    title: str
    summary: str
    jumpUrl: str
    pictureUrl: str
    musicUrl: str
    brief: str


class File(ElementBase):
    type: str = "File"
    id: int
    name: str
    size: int


class MiraiCode(ElementBase):
    type: str = "MiraiCode"
    code: str


class MessageElementEnum(Enum):
    At: "At" = At
    AtAll: "AtAll" = AtAll
    Face: "Face" = Face
    Source: "Source" = Source
    Plain: "Plain" = Plain
    Image: "Image" = Image
    FlashImage: "FlashImage" = FlashImage
    Voice: "Voice" = Voice
    Xml: "Xml" = Xml
    Json: "Json" = Json
    App: "App" = App
    Poke: "Poke" = Poke
    Dice: "Dice" = Dice
    MarketFace: "MarketFace" = MarketFace
    MusicShare: "MusicShare" = MusicShare
    File: "File" = File
    MiraiCode: "MiraiCode" = MiraiCode
