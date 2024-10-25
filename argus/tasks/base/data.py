from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, TypeVar, Union

# Define JSON value types
JsonValue = Union[str, int, float, bool, List['JsonValue'], Dict[str, 'JsonValue']]

# Define JSON array
JsonArray = List[JsonValue]

# Define JSON object
JsonObject = Dict[str, JsonValue]

# Define the overall JSON type
JsonType = Union[JsonValue, JsonArray, JsonObject]


class JsonSerializable(ABC):
    @abstractmethod
    def to_json_data(self) -> JsonType:
        """Return a dictionary representation of the object for JSON serialization."""
        pass


T = TypeVar('T', bound=JsonSerializable)
