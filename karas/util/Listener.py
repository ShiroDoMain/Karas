from typing import Type, List


class Listener:
    type: str


class Listeners:
    listeners: List[Type[Listener]]
