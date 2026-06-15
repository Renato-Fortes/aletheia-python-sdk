# Aletheia Python SDK

Official Python SDK for the [Aletheia Rights](https://aletheiarights.com) API — clear AI voice rights and pay creators instantly.

## Installation

```bash
pip install aletheia-rights
```

Requires Python 3.9+ and `httpx`.

## Quick start

```python
from aletheia import Aletheia

client = Aletheia(api_key="ak_live_...")

# Clear rights for a voice creator
result = client.clear("Sarah Collins", "commercial_ad", amount=10.00)

if result.is_cleared:
    print(f"License ID: {result.license_id}")
    print(f"Verify at:  {result.verification_url}")
elif result.is_escrow:
    print(f"Payment held in escrow — {result.estimated_resolution}")
elif result.is_unresolved:
    print(f"Creator not found. Attempt logged: {result.clearance_attempt_id}")
```

## Methods

### `client.clear(creator_name, use_type, *, creator_id=None, generation_id=None, amount=None)`

Clears commercial rights for a voice creator. Posts to `POST /v1/clear`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `creator_name` | str | ✓ | Full name of the voice creator |
| `use_type` | str | ✓ | One of: `commercial_ad`, `voiceover`, `podcast`, `video`, `other` |
| `creator_id` | str | | UUID of a registered creator (speeds up lookup) |
| `generation_id` | str | | ID of the AI-generated audio asset |
| `amount` | float | | Override the creator's default rate (USD) |

Returns a `ClearanceResponse` with `.is_cleared`, `.is_escrow`, `.is_unresolved` convenience properties.

---

### `client.get_license(license_id)`

Retrieves a clearance record. Maps to `GET /v1/licenses/{license_id}`.

```python
license = client.get_license("lic-uuid")
print(license.status, license.creator_name, license.amount_charged)
```

---

### `client.creators.list(*, category=None, min_rate=None, max_rate=None)`

Lists approved voice creators. Maps to `GET /v1/creators`.

```python
creators = client.creators.list(category="voice", min_rate=5, max_rate=50)
for c in creators.creators:
    print(c.name, c.rate_per_use, c.currency)
```

---

### `client.verify(certificate_id)`

Publicly verifies a compliance certificate. Maps to `GET /verify/{certificate_id}`. **No API key required** — this endpoint is open so anyone can confirm a certificate is genuine.

```python
cert = client.verify("cert-uuid")
print(cert.valid, cert.record_type)  # True, "license_certificate"
```

---

### `client.list_licenses()`

Not yet implemented — raises `NotImplementedError("Available in v0.2.0")`.

## Response models

| Model | Returned by |
|---|---|
| `ClearanceResponse` | `clear()` |
| `LicenseRecord` | `get_license()` |
| `CreatorsListResponse` | `creators.list()` |
| `VerifyResponse` | `verify()` |

## Error handling

```python
from aletheia import (
    AuthenticationError,   # 401 — invalid API key
    NotFoundError,         # 404 — resource not found
    RateLimitError,        # 429 — slow down
    ValidationError,       # 422 — bad request body
    AletheiaAPIError,      # any other HTTP error
)

try:
    result = client.clear("Sarah Collins", "commercial_ad")
except AuthenticationError:
    print("Check your API key")
except RateLimitError:
    print("Rate limited — retry later")
```

## Context manager

```python
with Aletheia(api_key="ak_live_...") as client:
    result = client.clear("Sarah Collins", "voiceover")
```

## Running tests

```bash
pip install respx pytest
pytest tests/ -v
```

## License

MIT
