import ctypes
import logging
import os
import sys
import time
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional, Union


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
        ctypes.windll.kernel32.SetConsoleTextAttribute(
            handle, cls.RED.value | cls.GREEN.value | cls.BLUE.value)


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

    def __init__(
            self,
            level: Union[str, int],
            botId: int,
            description: str = "bot",
            filename: str = None,
            logFile: bool = False,
            recordLevel: str = None
    ) -> None:
        self.description = description
        self.logging = logging.getLogger()
        self.level = level.upper() if isinstance(level, str) else level
        self.logging.setLevel(level=self.level)
        self.botId = botId
        self.handle = logging.StreamHandler()
        self.handle.setLevel(level=self.level)
        self._logFile = logFile
        self.filename = filename
        self._callbacks = {}
        self._recordLevel = (recordLevel and recordLevel.upper()) or self.level
        if logFile:
            if self.filename is None and not os.path.exists("logs"):
                os.mkdir("logs")
        self.logging.addHandler(hdlr=self.handle)
        self._level = {
            "INFO": 0,
            "DEBUG": 1,
            "WARNING": 0,
            "ERROR": 0
        }
        self._logLv = self._level[self._recordLevel]

    @property
    def callbacks(self) -> List:
        return list(self._callbacks.keys())

    def addCallback(self, callback: Callable, namespace: Optional[str] = None, *args, **kwargs) -> None:
        """add a callback
        Args:
            callback(logText:str, logLevel:str,*args, **kwargs)
            namespace(None, str): callback name

        """
        namespace = namespace or callback.__name__
        self._callbacks[namespace] = (callback, args, kwargs)

    def removeCallback(self, callback: Union[str, Callable]) -> bool:
        """remove callback, return false if not found"""
        namespace = callback if isinstance(
            callback, str) else callback.__name__
        if namespace not in self.callbacks:
            return False
        del self._callbacks[namespace]
        return True

    def _write(self, text, _localtime) -> None:
        with open(self.filename or time.strftime("logs/%Y-%m-%d.log", _localtime), "a") as f:
            f.write(text + "\n")

    def format_time(self, msg: str, name: str, qq: int, level: str, _color: str = ""):
        current_time = time.localtime()
        color = _color if _color else ""
        color_end = '\033[0m' if color else ""
        _log = f"{time.strftime('%Y-%m-%d %H:%M:%S', current_time)}" \
               f"-[{level}]-{name or self.description}/{qq or self.botId}: {msg} "
        _format = f"{color}{_log}{color_end}"
        if self.callbacks:
            for cb, args, kws in self._callbacks.values():
                cb(_log, level, *args, **kws)
        if self._level[level] <= self._logLv and self._logFile:
            self._write(_log, current_time)
        return _format

    @os_check("BLUE")
    def debug(self, msg, name: str = None, qq: int = None, _color: str = "", *args):
        self.logging.debug(self.format_time(
            msg=msg, name=name, qq=qq, level="DEBUG", _color=_color), *args)

    @os_check("GREEN")
    def info(self, msg, name: str = None, qq: int = None, _color: str = "", *args):
        self.logging.info(self.format_time(msg=msg, name=name,
                                           qq=qq, level="INFO", _color=_color), *args)

    @os_check("YELLOW")
    def warning(self, msg, name: str = None, qq: int = None, _color: str = "", *args):
        self.logging.warning(self.format_time(
            msg=msg, name=name, qq=qq, level="WARNING", _color=_color), *args)

    @os_check("RED")
    def error(self, msg, name: str = None, qq: int = None, _color: str = "", *args):
        self.logging.error(self.format_time(
            msg=msg, name=name, qq=qq, level="ERROR", _color=_color), *args)
