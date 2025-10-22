"""pytest-depper: Smart test selection based on code dependencies.

Only run the tests you need by analyzing AST-level code dependencies.
"""

__version__ = "0.1.0"

from .analyzer import DependencyAnalyzer
from .plugin import pytest_configure, pytest_collection_modifyitems

__all__ = ["DependencyAnalyzer", "pytest_configure", "pytest_collection_modifyitems"]
