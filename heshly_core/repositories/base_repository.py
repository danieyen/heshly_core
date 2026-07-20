from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract repository interface.

    All repository implementations
    (Memory, ERPNext, PostgreSQL, etc.)
    must implement these methods.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Create or update an entity.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, entity_id: str) -> T | None:
        """
        Retrieve a single entity.
        """
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[T]:
        """
        Return all entities.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity.

        Returns True if deleted,
        otherwise False.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check whether an entity exists.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """
        Return total number of entities.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """
        Remove every entity.
        """
        raise NotImplementedError