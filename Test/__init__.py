from abc import ABC
from enum import Enum
import inspect
import graia.application.message.chain
class Test:
    a:int
    b:int

class A(Test):
    def __init__(self) -> None:
        print(self.__annotations__)

a = A()