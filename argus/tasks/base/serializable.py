from typing import Any, TypeVar, cast

T = TypeVar('T', bound='Serializable')


JsonValue = str | int | float | bool | list['JsonValue'] | dict[str, 'JsonValue']
JsonArray = list[JsonValue]
JsonDict = dict[str, Any]
JsonType = JsonValue | JsonArray | JsonDict


class Serializable:

    registry: dict[str, type['Serializable']] = {}

    def __init_subclass__(cls, **kwargs):
        '''Auto-register subclasses for correct deserialization.'''
        super().__init_subclass__(**kwargs)
        cls.registry[cls.__name__] = cls

    def to_dict(self) -> JsonDict:
        return {'__class__': self.__class__.__name__}

    @staticmethod
    def serialize_parameters(data: JsonDict) -> JsonDict:
        return data

    @classmethod
    def from_dict(cls: type[T], data: JsonDict) -> T:
        class_name = data.pop('__class__', None)
        if class_name is None:
            return cls(**cls.serialize_parameters(data))
        subclass = cls.registry.get(class_name)
        if subclass is None:
            raise ValueError(f'Unknown class: {class_name}')
        subclass_type = cast(type[T], subclass)
        return subclass_type.from_dict(data)
