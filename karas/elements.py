from enum import Enum
from typing import Any, BinaryIO, Dict, Optional, Union

from karas.permission import Permission

from karas.util import BaseModel


class ElementBase(BaseModel):
    type: str

    @property
    def elements(self) -> Dict[Any, Any]:
        return {_K: _V for _K, _V in self.__dict__.items() if _V is not None}

    def __str__(self) -> str:
        return f"{self.type}:{[str(_v) for _v in self.__dict__.values()]}"


class At(ElementBase):
    target: int
    display: str

    def __init__(self, target: int, **kwargs):
        self.type: str = "At"
        self.target = target
        super().__init__(**kwargs)


class AtAll(ElementBase):
    def __init__(self, **kwargs):
        self.type: str = "AtAll"
        super().__init__(**kwargs)


class Face(ElementBase):
    faceId: int
    name: str

    def __init__(self, **kwargs):
        self.type: str = "Face"
        super().__init__(**kwargs)


class Plain(ElementBase):
    text: str

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.type: str = "Plain"
        self.text = text

    def __str__(self) -> str:
        return self.text


class Source(ElementBase):
    id: int
    time: int

    def __init__(self, **kwargs):
        self.type: str = "Source"
        super().__init__(**kwargs)


class Image(ElementBase):
    imageId: str
    url: str
    path: str
    base64: str

    def __init__(self, file: Union[str, BinaryIO, bytes, None] = None, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.type: str = "Image"
        self.ftype = "img"
        self.file = file

    def __str__(self) -> str:
        return f"[图片:{self.imageId}]"

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.imageId = kwds.get("imageId")
        self.url = kwds.get("url")


class FlashImage(ElementBase):
    imageId: str
    url: str
    path: str
    base64: str

    def __init__(self, file: Union[str, BinaryIO, bytes, None] = None, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.type: str = "FlashImage"
        self.ftype = "img"
        self.file = file

    def __str__(self) -> str:
        return f" [闪照:{self.imageId}]"

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.imageId = kwds.get("imageId")
        self.url = kwds.get("url")

class Voice(ElementBase):
    voiceId: str
    url: str
    path: Optional[str]
    base64: Optional[str]
    length: int

    def __init__(self, file: Union[str, BinaryIO, bytes, None] = None, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.type: str = "Voice"
        self.ftype = "voice"
        self.type = "Voice"
        self.file = file

    def __str__(self) -> str:
        return f" [语音:{self.voiceId}]"

    def __call__(self, *args: Any, **kwds: Any) -> None:
        self.voiceId = kwds.get("voiceId")
        self.url = kwds.get("url")


class Xml(ElementBase):
    xml: str

    def __init__(self, **kwargs):
        self.type: str = "Xml"
        super().__init__(**kwargs)


class Json(ElementBase):
    json: str

    def __init__(self, **kwargs):
        self.type: str = "Json"
        super().__init__(**kwargs)


class App(ElementBase):
    def __init__(self, **kwargs):
        self.type: str = "App"
        super().__init__(**kwargs)

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
    name: str

    def __init__(self, **kwargs):
        self.type: str = "Poke"
        super().__init__(**kwargs)


class Dice(ElementBase):
    value: int

    def __init__(self, **kwargs):
        self.type: str = "Dice"
        super().__init__(**kwargs)


class MarketFace(ElementBase):
    """目前商城表情仅支持接收和转发，不支持构造发送"""

    id: int
    name: str

    def __init__(self, **kwargs):
        self.type: str = "MarketFace"
        super().__init__(**kwargs)


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

    kind: str
    title: str
    summary: str
    jumpUrl: str
    pictureUrl: str
    musicUrl: str
    brief: str

    def __init__(self, **kwargs):
        self.type: str = "MusicShare"
        super().__init__(**kwargs)


class FileDownloadInfo(ElementBase):
    """
    sha1    str	文件sha1校验
    md5	str	文件md5校验
    url	str	文件下载url


    Args:
        ElementBase (_type_): _description_
    """
    sha1: str
    md5: str
    downloadTimes: int
    uploaderId: int
    uploadTime: int
    lastModifyTime: int
    url: str


class UploaderInfo(ElementBase):
    id: int
    name: str
    permission: Permission


class File(ElementBase):
    """
    name    str         	文件名  
    id	    str	            文件ID  
    parent	File	        文件对象, 递归类型. null 为存在根目录  
    contact	UploaderInfo	群信息或好友信息  
    contact	UploaderInfo	群信息或好友信息  
    isFile	bool    	    是否文件  
    isDictionary	bool	是否文件夹(弃用)  
    isDirectory	    bool    	是否文件夹  
    """
    id: str
    name: str
    size: int
    path: str
    parent: Optional["File"]
    contact: FileDownloadInfo
    isFile: bool
    isDictionary: bool
    isDirectory: bool
    downloadInfo: FileDownloadInfo


    def __init__(self, file:Union[str,bytes, BinaryIO, None] = None, path: str = "", parent = None, **kwargs):
        self.type: str = "File"
        self.file = file
        self.path = path
        self.parent = parent and File(**parent)
        super().__init__(**kwargs)
    
    def __str__(self) -> str:
        return f" File[{self.id}]"


class MiraiCode(ElementBase):
    def __init__(self, **kwargs):
        self.type: str = "MiraiCode"
        super().__init__(**kwargs)

    code: str


class Profile(BaseModel):
    nickname: str
    email: str
    age: int
    level: int
    sign: str
    sex: str


class FriendProfile(Profile):
    """好友资料"""


class MemberProfile(ElementBase):
    """成员资料"""


class UserProfile(ElementBase):
    """用户资料"""


class BotProfile(ElementBase):
    """Bot资料"""


class GroupConfig(ElementBase):
    """
    name            	群名

    announcement	    群公告
    
    confessTalk         是否开启坦白说
    
    allowMemberInvite	是否允许群员邀请
    
    autoApprove	        是否开启自动审批入群
    
    anonymousChat	    是否允许匿名聊天
    
    """
    name: str
    announcement: str
    confessTalk: bool
    allowMemberInvite: bool
    autoApprove: bool
    anonymousChat: bool

    def __init__(
        self,
        name: str = None,
        announcement: str = None,
        confessTalk: bool = None,
        allowMemberInvite: bool = None,
        autoApprove: bool = None,
        anonymousChat: bool = None,
        **kws,
    ) -> None:
        super().__init__(**kws)
        self.name = name
        self.announcement = announcement
        self.confessTalk = confessTalk
        self.allowMemberInvite = allowMemberInvite
        self.autoApprove = autoApprove
        self.anonymousChat = anonymousChat


class MemberInfo(ElementBase):
    name: str
    specialTitle: str

    def __init__(self, **kws) -> None:
        super().__init__(**kws)


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
