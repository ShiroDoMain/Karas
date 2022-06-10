from enum import Enum


class Permission:
    type: str

    def __init__(self, *args, **kwargs) -> None:
        pass

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self):
            return False
        return self.type == __o if isinstance(__o, str) else self.type == __o.type

    def __str__(self) -> str:
        return self.type


class AdministartorPermission(Permission):
    type: str = "ADMINISTRATOR"


class OwnerPermission(Permission):
    type: str = "OWNER"


class MemberPermission(Permission):
    type: str = "MEMBER"


class PermissionEnum(Enum):
    ADMINISTRATOR: "AdministartorPermission" = AdministartorPermission
    OWNER: "OwnerPermission" = OwnerPermission
    MEMBER: "MemberPermission" = MemberPermission
