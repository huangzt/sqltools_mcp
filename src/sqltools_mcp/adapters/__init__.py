"""Database adapters package."""

from .base import DatabaseAdapter
from .factory import get_adapter

__all__ = ["DatabaseAdapter", "get_adapter"]
