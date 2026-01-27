from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Type, Any


T = TypeVar("T")


class _SingletonMeta(type):
    """Metaclass for singleton pattern implementation."""

    _instances: dict[type, object] = {}

    def __getitem__(cls, item: Type[T]) -> T:
        """Get singleton instance for the given type.

        Args:
            item: The type of the singleton instance to retrieve.

        Returns:
            The singleton instance.

        Raises:
            KeyError: If the instance for the given type is not found.
        """
        if item not in cls._instances:
            raise KeyError(f"{item} not found in {cls.__name__}")
        return cls._instances[item]

    def get(cls, item: Type[T]) -> T | None:
        try:
            return cls[item]
        except KeyError:
            return None

    def set(cls, type: Type[T], instance: Any) -> T:
        """Set singleton instance for the given type.

        Args:
            type: The type of the singleton instance to set.
            instance: The instance to set.

        Returns:
            The set instance.
        """
        cls._instances[type] = instance


class Singleton(metaclass=_SingletonMeta):
    """Base class for singleton objects."""

    pass
