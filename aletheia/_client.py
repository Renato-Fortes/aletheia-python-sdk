from __future__ import annotations

from typing import Optional

import httpx

from .exceptions import (
    AletheiaAPIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import ClearanceResponse, LicenseRecord, VerifyResponse
from .resources import CreatorsResource

_SDK_VERSION = "0.1.0"
_USER_AGENT = f"aletheia-python/{_SDK_VERSION}"


class Aletheia:
    """Synchronous client for the Aletheia Rights API.

    Usage::

        client = Aletheia(api_key="ak_live_...")
        result = client.clear("Sarah Collins", "commercial_ad", amount=10.00)

    The client can also be used as a context manager::

        with Aletheia(api_key="ak_live_...") as client:
            result = client.clear("Sarah Collins", "commercial_ad")
    """

    DEFAULT_BASE_URL = "https://api.aletheiarights.com"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

        _common_headers = {
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }

        self._http = httpx.Client(
            timeout=timeout,
            headers={**_common_headers, "X-API-Key": api_key, "Content-Type": "application/json"},
        )

        # Separate client for the public /verify/* endpoint — no auth header.
        self._public_http = httpx.Client(
            timeout=timeout,
            headers=_common_headers,
        )

        self.creators = CreatorsResource(self)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text or f"HTTP {response.status_code}"

        sc = response.status_code
        if sc == 401:
            raise AuthenticationError(detail)
        if sc == 404:
            raise NotFoundError(detail)
        if sc == 422:
            raise ValidationError(detail)
        if sc == 429:
            raise RateLimitError(detail)
        raise AletheiaAPIError(sc, detail)

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        resp = self._http.get(self._url(path), params=params)
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, json: dict) -> dict:
        resp = self._http.post(self._url(path), json=json)
        self._raise_for_status(resp)
        return resp.json()

    def _public_get(self, path: str) -> dict:
        resp = self._public_http.get(self._url(path))
        self._raise_for_status(resp)
        return resp.json()

    # ── Public API ─────────────────────────────────────────────────────────────

    def clear(
        self,
        creator_name: str,
        use_type: str,
        *,
        creator_id: Optional[str] = None,
        generation_id: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> ClearanceResponse:
        """POST /v1/clear — clear commercial rights for a voice creator.

        Args:
            creator_name:  Full name of the voice creator.
            use_type:      One of: commercial_ad, voiceover, podcast, video, other.
            creator_id:    Optional UUID of a registered creator (speeds up lookup).
            generation_id: Optional ID of the AI-generated audio asset.
            amount:        Override the creator's default rate (USD, positive).

        Returns:
            ClearanceResponse with status "cleared", "escrow", or "unresolved".
        """
        body: dict = {"creator_name": creator_name, "use_type": use_type}
        if creator_id is not None:
            body["creator_id"] = creator_id
        if generation_id is not None:
            body["generation_id"] = generation_id
        if amount is not None:
            body["amount"] = amount

        data = self._post("/v1/clear", json=body)
        return ClearanceResponse.from_dict(data)

    def get_license(self, license_id: str) -> LicenseRecord:
        """GET /v1/licenses/{license_id} — retrieve a clearance record.

        Args:
            license_id: UUID of the clearance / license record.

        Returns:
            LicenseRecord with full payment and status details.
        """
        data = self._get(f"/v1/licenses/{license_id}")
        return LicenseRecord.from_dict(data)

    def verify(self, certificate_id: str) -> VerifyResponse:
        """GET /verify/{certificate_id} — publicly verify a compliance certificate.

        This endpoint is unauthenticated; no API key is sent. Anyone can call it
        to confirm a certificate is genuine.

        Args:
            certificate_id: UUID from the compliance_record_id / certificate field.

        Returns:
            VerifyResponse with valid=True/False and the certificate document.
        """
        data = self._public_get(f"/verify/{certificate_id}")
        return VerifyResponse.from_dict(data)

    def list_licenses(self):
        """List all licenses for this API key.

        Not yet implemented — available in v0.2.0.
        """
        raise NotImplementedError("Available in v0.2.0")

    # ── Context manager ────────────────────────────────────────────────────────

    def __enter__(self) -> Aletheia:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        self._http.close()
        self._public_http.close()

    def __repr__(self) -> str:
        prefix = self._api_key[:16] + "..." if len(self._api_key) > 16 else self._api_key
        return f"Aletheia(api_key={prefix!r}, base_url={self._base_url!r})"
