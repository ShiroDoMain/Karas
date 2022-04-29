#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/1/18 14:41
# @Author  : Shiro
# @File    : exceptions.py
# @Software: PyCharm
class AccountError(Exception):
    """Account Error"""
    pass


class VerifyError(Exception):
    """Verify Error"""
    pass


class SessionError(Exception):
    """Session Error"""
    pass


class VerifyKeyError(Exception):
    """VerifyKey Error"""
    pass


class InvalidArgumentError(Exception):
    """InvalidArgument"""
    pass
