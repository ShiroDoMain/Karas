#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/1/18 14:41
# @Author  : Shiro
# @File    : exceptions.py
# @Software: PyCharm


from typing import Tuple


__all__ : Tuple[str]= (
    "BotBaseException",
    "BotMutedException",
    "BotNotFoundException",
    "FileNotFoundException",
    "InvalidArgumentException",
    "MessageTooLongException",
    "PermissionException",
    "SessionInvalidationException",
    "SessionUnauthorizedException",
    "TargetNotFoundException",
    "VerifyException",
)


class BotBaseException(Exception):
    pass


class AccountException(BotBaseException):
    """Account Exception"""
    pass


class ConnectException(BotBaseException):
    "连接错误"
    pass


class BotNotFoundException(BotBaseException):
    """指定的Bot不存在"""
    pass


class VerifyException(BotBaseException):
    """错误的verify key"""
    pass


class SessionInvalidationException(BotBaseException):
    """Session失效或不存在"""
    pass


class SessionUnauthorizedException(BotBaseException):
    """Session未认证(未激活)"""
    pass


class TargetNotFoundException(BotBaseException):
    """发送消息目标不存在(指定对象不存在)"""
    pass


class FileNotFoundException(BotBaseException):
    """指定文件不存在，出现于发送本地图片"""
    pass


class PermissionException(BotBaseException):
    """无操作权限，指Bot没有对应操作的限权"""
    pass


class BotMutedException(BotBaseException):
    """Bot被禁言，指Bot当前无法向指定群发送消息"""
    pass


class MessageTooLongException(BotBaseException):
    """消息过长"""
    pass


class InvalidArgumentException(BotBaseException):
    """错误的访问，如参数错误等"""
    pass
