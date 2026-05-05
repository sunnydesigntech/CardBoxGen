"""CardBoxGen package API."""

from .api import generate_svg
from .models import BoxParams, GenerationResult, WarningMsg
from .version import __version__

__all__ = ["__version__", "BoxParams", "GenerationResult", "WarningMsg", "generate_svg"]
