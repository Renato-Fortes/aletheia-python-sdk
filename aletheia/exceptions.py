class AletheiaError(Exception):
    """Base exception for all Aletheia SDK errors."""


class AletheiaAPIError(AletheiaError):
    """Raised for non-2xx HTTP responses."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class AuthenticationError(AletheiaError):
    """Raised when the API key is invalid or missing (HTTP 401)."""


class NotFoundError(AletheiaError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class RateLimitError(AletheiaError):
    """Raised when the rate limit is exceeded (HTTP 429)."""


class ValidationError(AletheiaError):
    """Raised when the server rejects the request body (HTTP 422)."""
