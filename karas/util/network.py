from typing import Optional, Union


def error_throw(func):
    async def wrapper(*args, **kwargs):
        try:
            _response = await func(*args, **kwargs)
        except Exception as e:
            raise e
        else:
            return _response

    return wrapper


def send_json(
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
    return {
        "syncId": syncId,
        "command": command,
        "subCommand": subCommand,
        "content": {} if content is None else content
    }


class URL_Route:
    url_gen: str

    def __init__(self, url_gen: str) -> None:
        self.url_gen = url_gen if url_gen.endswith("/") else url_gen + "/"

    def __call__(self, *args) -> str:
        return self.url_gen + "/".join(args)
