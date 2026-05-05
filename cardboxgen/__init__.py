"""CardBoxGen package API."""

from .api import generate_svg
from .models import BoxParams, GenerationResult, ValidationResult, WarningMsg
from .validation import validate_template_params
from .version import __version__

__all__ = ["__version__", "BoxParams", "GenerationResult", "ValidationResult", "WarningMsg", "generate_svg", "validate_template_params"]
