import inspect
from typing import Awaitable, Callable, Optional, Union
import sys
import aiohttp
import traceback
from functools import wraps

from karas.Sender import ReceptorBase


def error_throw(func:Awaitable):
    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                _response = await func(*args, **kwargs)
            else:
                _response = func(*args, **kwargs)
        except Exception as e:
            # _,_,tb = sys.exc_info()
            # traceback.print_tb(tb,limit=10)
            raise
        else:
            return _response
    return _wrapper
    

def echo_receiver(ws: aiohttp.ClientWebSocketResponse, _return: str = None):
    def wrapper(func):
        @wraps(func)
        async def decorator(*args, **kwargs):
            await func(*args, **kwargs)
            response = await ws.receive_json()
            return _return and response.get(_return)
        return decorator
    return wrapper


def wrap_data_json(
        command: str, syncId: Union[int, str] = None,
        subCommand: Optional[str] = None,
        content: dict = None) -> dict:
    """包装数据格式

    Args:
        command (str): 命令字
        syncId (Optional[int], optional): 消息同步的字段. Defaults to None.
        subCommand (Optional[str], optional): 子命令字, 可空. Defaults to None.
        content (dict, optional): 命令的数据对象, 与通用接口定义相同. Defaults to None.

    Returns:
        dict: _description_
    """
    if content is not None:
        content = {_K:_V.id if isinstance(_V,ReceptorBase) else _V for _K,_V in content.items()}
    return {
        "syncId": syncId,
        "command": command,
        "subCommand": subCommand,
        "content": content
    }


class URL_Route:
    url_gen: str

    def __init__(self, url_gen: str) -> None:
        self.url_gen = url_gen if url_gen.endswith("/") else url_gen + "/"

    def __call__(self, *args) -> str:
        return self.url_gen + "/".join(args)
