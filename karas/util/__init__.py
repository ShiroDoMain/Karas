from karas.permission import PermissionEnum


class MetaBase(type):
    def __new__(mcs, name, bases, namespace):
        if not namespace.get("type"):
            namespace["type"] = name
        return super().__new__(mcs, name, bases, namespace)


class BaseModel(metaclass=MetaBase):
    type: str

    def __init__(self, **kws) -> None:
        for _k, _v in kws.items():
            _k = _k if _k != "from" else "From"
            _type = self.__annotations__.get(_k)
            try:
                if _type and _v is not None and not isinstance(_v, _type):
                    _v = _type(**_v) \
                        if _k not in ("origin","current") else PermissionEnum[_v].value if _k != "messageChain" else _type(*_v)
            except:
                print(_k, ":", _v, "=>", _type)
                print(self.__annotations__)
                raise
            setattr(self, _k, _v)

    @classmethod
    def parse(cls, *args, **kwargs) -> "BaseModel":
        _params = [(_K, _V) for _K, _V in kwargs.items()]
        _arg_mapper = filter(lambda x: x if x[0] in kwargs.keys() and x[0] != "type" else None, _params)
        _filted = {_K: _V for _K, _V in filter(lambda x: x is not None, _arg_mapper)}
        _obj = cls(**_filted)
        return _obj

    def __str__(self) -> str:
        return self.__dict__.__str__()
