import asyncio
import inspect
import traceback
from typing import Optional, Union
import aiohttp
from aiohttp.web_exceptions import HTTPRequestTimeout
from functools import wraps
from karas.sender import ReceptorBase
from karas.exceptions import BotBaseException, ConnectException, FunctionException


def error_throw(func):
    @wraps(func)
    async def _wrapper(obj, *args, **kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                return await func(obj, *args, **kwargs)
            else:
                return func(obj, *args, **kwargs)
        except ConnectException as ce:
            obj.logging.error(f"cannot connect host {obj.host},try again")
            for step in range(1, 11):
                obj.logging.warning(f"try connect {obj.host} {step}/10")
                try:
                    return await func(obj, *args, **kwargs)
                except ConnectException:
                    await asyncio.sleep(8)
                except Exception:
                    traceback.print_exc()
                    await asyncio.sleep(5)
            obj.logging.error("connect fail, closing...")
            exc_ = traceback.format_exc()
            obj.logging.error(exc_)
            await obj.stop()
            raise ce
        except FunctionException:
            obj.logging.error("Function Error")
            exc_ = traceback.format_exc()
            obj.logging.error(exc_)
            pass
        except BotBaseException as be:
            exc_ = traceback.format_exc()
            obj.logging.error(exc_)
            raise be
        except HTTPRequestTimeout:
            exc_ = traceback.format_exc()
            obj.logging.error(exc_)
            raise
        except Exception:
            exc_ = traceback.format_exc()
            obj.logging.error(exc_)
            raise

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
        content = {_K: _V.id if isinstance(
            _V, ReceptorBase) else _V for _K, _V in content.items()}
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
