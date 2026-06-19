"""Aletheia Rights SDK — official Python client for api.aletheiarights.com."""

from ._client import Aletheia
from .exceptions import (
    AletheiaAPIError,
    AletheiaError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import (
    ClearanceResponse,
    Creator,
    CreatorsListResponse,
    LicenseRecord,
    VerifyResponse,
)

__version__ = "0.2.0"
__all__ = [
    "Aletheia",
    # exceptions
    "AletheiaError",
    "AletheiaAPIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    # models
    "ClearanceResponse",
    "Creator",
    "CreatorsListResponse",
    "LicenseRecord",
    "VerifyResponse",
]
