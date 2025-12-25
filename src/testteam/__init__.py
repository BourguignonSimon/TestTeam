"""Simple team roster management tools."""

from .storage import TeamStorage
from .cli import main

__all__ = ["TeamStorage", "main"]

