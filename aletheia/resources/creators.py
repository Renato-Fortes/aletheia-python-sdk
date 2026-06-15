from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..models import CreatorsListResponse

if TYPE_CHECKING:
    from .._client import Aletheia


class CreatorsResource:
    def __init__(self, client: Aletheia):
        self._client = client

    def list(
        self,
        *,
        category: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
    ) -> CreatorsListResponse:
        """GET /v1/creators — list approved voice creators.

        Args:
            category: Filter by category keyword (matched against creator name).
            min_rate:  Minimum rate per use (USD).
            max_rate:  Maximum rate per use (USD).
        """
        params: dict = {}
        if category is not None:
            params["category"] = category
        if min_rate is not None:
            params["min_rate"] = min_rate
        if max_rate is not None:
            params["max_rate"] = max_rate

        data = self._client._get("/v1/creators", params=params or None)
        return CreatorsListResponse.from_dict(data)
