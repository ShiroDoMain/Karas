from enum import Enum
import logging
import ctypes, sys
import time
from typing import Union


class WindowsCMD(Enum):
    # Windows CMD text colors
    BLACK = 0x00  # black.
    DARKBLUE = 0x01  # dark blue.
    DARKGREEN = 0x02  # dark green.
    DARKSKYBLUE = 0x03  # dark skyblue.
    DARKRED = 0x04  # dark red.
    DARKPINK = 0x05  # dark pink.
    DARKYELLOW = 0x06  # dark yellow.
    DARKWHITE = 0x07  # dark white.
    DARKGRAY = 0x08  # dark gray.
    BLUE = 0x09  # blue.
    GREEN = 0x0a  # green.
    SKYBLUE = 0x0b  # skyblue.
    RED = 0x0c  # red.
    PINK = 0x0d  # pink.
    YELLOW = 0x0e  # yellow.
    WHITE = 0x0f  # white.

    @classmethod
    def set_color(cls, handle, color):
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)

    @classmethod
    def reset(cls, handle):
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, cls.RED.value | cls.GREEN.value | cls.BLUE.value)


class UnixShell(Enum):
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def os_check(color):
    def decorator(func):
        def check(*args, **kwargs):
            if sys.platform == "win32":
                std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
                WindowsCMD.set_color(std_out_handle, WindowsCMD[color].value)
                _res = func(*args, **kwargs)
                WindowsCMD.reset(std_out_handle)
            else:
                _res = func(_color=UnixShell[color].value, *args, **kwargs)
            return _res

        return check

    return decorator


class Logging:

    def __init__(self, loggerLevel: Union[str, int], botId: int) -> None:
        self.logging = logging.getLogger()
        self.logging.setLevel(loggerLevel.upper())
        self.botId = botId
        self.handle = logging.StreamHandler()
        self.handle.setLevel(loggerLevel.upper())
        self.logging.addHandler(self.handle)

    def format_time(self, msg: str, name: str, qq: int, level: str, _color: str = ""):
        current_time = time.localtime()
        color = _color if _color else ""
        color_end = '\033[0m' if color else ""
        return f"{color}{time.strftime('%Y-%M-%d %H:%m:%S', current_time)}-[{level}]-{name}/{qq or self.botId}: {msg}{color_end}"

    @os_check("BLUE")
    def debug(self, msg, name: str = "bot", qq: int = None, _color: str = ""):
        self.logging.debug(self.format_time(msg=msg, name=name, qq=qq, level="DEBUG", _color=_color))

    @os_check("GREEN")
    def info(self, msg, name: str = "bot", qq: int = None, _color: str = ""):
        self.logging.info(self.format_time(msg=msg, name=name, qq=qq, level="INFO", _color=_color))

    @os_check("YELLOW")
    def warning(self, msg, name: str = "bot", qq: int = None, _color: str = ""):
        self.logging.warning(self.format_time(msg=msg, name=name, qq=qq, level="WARNING", _color=_color))

    @os_check("RED")
    def error(self, msg, name: str = "bot", qq: int = None, _color: str = ""):
        self.logging.error(self.format_time(msg=msg, name=name, qq=qq, level="ERROR", _color=_color))
