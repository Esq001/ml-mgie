"""Abstract base class for tax form parsers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """Base class that all form-specific parsers must implement."""

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Return True if this parser can handle the given text."""
        ...

    @abstractmethod
    def parse(self, text: str, source_file: str) -> Any:
        """Parse the text and return the appropriate data model."""
        ...
