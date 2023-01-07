from enum import Enum
from karas.util import BaseModel


class Permission:
    type: str

    def __init__(self, *args, **kwargs) -> None:
        pass

    def __eq__(self, __o: BaseModel) -> bool:
        if isinstance(__o, self.__class__):
            return __o.type.upper() == self.type.upper()
        return self.type == __o if isinstance(__o, str) else self.type == __o.type

    def __str__(self) -> str:
        return self.type


class AdministratorPermission(Permission):
    type: str = "ADMINISTRATOR"


class OwnerPermission(Permission):
    type: str = "OWNER"


class MemberPermission(Permission):
    type: str = "MEMBER"


class PermissionEnum(Enum):
    ADMINISTRATOR: "AdministratorPermission" = AdministratorPermission
    OWNER: "OwnerPermission" = OwnerPermission
    MEMBER: "MemberPermission" = MemberPermission
