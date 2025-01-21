from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar('T', bound='Serializable')


JsonValue = str | int | float | bool | list['JsonValue'] | dict[str, 'JsonValue']
JsonArray = list[JsonValue]
JsonDict = dict[str, Any]
JsonType = JsonValue | JsonArray | JsonDict


class Serializable(ABC):
    @abstractmethod
    def to_dict(self) -> JsonDict:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], data: JsonDict) -> T:
        pass
