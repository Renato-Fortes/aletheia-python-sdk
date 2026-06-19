"""Tests for the Aletheia Python SDK.

Run:  pip install respx pytest && pytest tests/ -v
"""

import pytest
import respx
import httpx

from aletheia import (
    Aletheia,
    ClearanceResponse,
    CreatorsListResponse,
    LicenseRecord,
    VerifyResponse,
)
from aletheia.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

BASE = "https://api.aletheiarights.com"

# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    return Aletheia(api_key="ak_live_testkey1234567890", base_url=BASE)


# ── aletheia.clear() ───────────────────────────────────────────────────────────


class TestClear:
    @respx.mock
    def test_cleared_status(self, client):
        cert = {
            "certificate_id": "cert-uuid-001",
            "verification_url": f"{BASE}/verify/cert-uuid-001",
        }
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(200, json={
                "status": "cleared",
                "license_id": "lic-uuid-001",
                "compliance_record_id": "cert-uuid-001",
                "certificate": cert,
                "cleared_at": "2026-06-15T10:00:00Z",
                "creator": "Sarah Collins",
                "amount_charged": 10.0,
                "creator_payout": 8.5,
                "platform_fee": 1.5,
            })
        )
        result = client.clear("Sarah Collins", "commercial_ad", amount=10.0)

        assert isinstance(result, ClearanceResponse)
        assert result.is_cleared is True
        assert result.is_escrow is False
        assert result.is_unresolved is False
        assert result.license_id == "lic-uuid-001"
        assert result.creator == "Sarah Collins"
        assert result.amount_charged == 10.0
        assert result.creator_payout == 8.5
        assert result.platform_fee == 1.5
        assert result.verification_url == f"{BASE}/verify/cert-uuid-001"

    @respx.mock
    def test_escrow_status(self, client):
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(200, json={
                "status": "escrow",
                "escrow_id": "escrow-uuid-002",
                "compliance_record_id": "comp-uuid-002",
                "message": "Creator is registered but pending approval. Payment held in escrow.",
                "estimated_resolution": "72 hours",
            })
        )
        result = client.clear("Pending Creator", "voiceover")

        assert result.is_escrow is True
        assert result.escrow_id == "escrow-uuid-002"
        assert result.estimated_resolution == "72 hours"
        assert result.compliance_record_id == "comp-uuid-002"

    @respx.mock
    def test_unresolved_status(self, client):
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(200, json={
                "status": "unresolved",
                "clearance_attempt_id": "att-uuid-003",
                "compliance_record_id": "gf-uuid-003",
                "message": "Creator not found.",
                "options": [
                    {"type": "suggest_alternatives", "endpoint": "GET /v1/creators"},
                ],
            })
        )
        result = client.clear("Unknown Creator", "podcast")

        assert result.is_unresolved is True
        assert result.clearance_attempt_id == "att-uuid-003"
        assert len(result.options) == 1

    @respx.mock
    def test_optional_params_sent(self, client):
        route = respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(200, json={"status": "cleared"})
        )
        client.clear(
            "Sarah Collins",
            "commercial_ad",
            creator_id="creator-uuid",
            generation_id="gen-abc",
            amount=15.0,
        )
        body = route.calls[0].request.read()
        import json
        payload = json.loads(body)
        assert payload["creator_id"] == "creator-uuid"
        assert payload["generation_id"] == "gen-abc"
        assert payload["amount"] == 15.0

    @respx.mock
    def test_auth_error(self, client):
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            client.clear("Sarah Collins", "commercial_ad")

    @respx.mock
    def test_rate_limit_error(self, client):
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(429, json={"detail": "Rate limit exceeded"})
        )
        with pytest.raises(RateLimitError):
            client.clear("Sarah Collins", "commercial_ad")

    @respx.mock
    def test_validation_error(self, client):
        respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(422, json={"detail": "Invalid use_type"})
        )
        with pytest.raises(ValidationError):
            client.clear("Sarah Collins", "bad_use_type")

    @respx.mock
    def test_api_key_sent_in_header(self, client):
        route = respx.post(f"{BASE}/v1/clear").mock(
            return_value=httpx.Response(200, json={"status": "cleared"})
        )
        client.clear("Sarah Collins", "commercial_ad")
        assert route.calls[0].request.headers.get("x-api-key") == "ak_live_testkey1234567890"


# ── aletheia.get_license() ─────────────────────────────────────────────────────


class TestGetLicense:
    @respx.mock
    def test_returns_license_record(self, client):
        respx.get(f"{BASE}/v1/licenses/lic-uuid-001").mock(
            return_value=httpx.Response(200, json={
                "id": "lic-uuid-001",
                "status": "cleared",
                "creator_name": "Sarah Collins",
                "use_type": "commercial_ad",
                "amount_charged": 10.0,
                "platform_fee": 1.5,
                "creator_payout": 8.5,
                "stripe_payment_intent_id": "pi_test_123",
                "generation_id": "gen-abc",
                "created_at": "2026-06-15T10:00:00Z",
                "cleared_at": "2026-06-15T10:00:05Z",
            })
        )
        result = client.get_license("lic-uuid-001")

        assert isinstance(result, LicenseRecord)
        assert result.id == "lic-uuid-001"
        assert result.status == "cleared"
        assert result.creator_name == "Sarah Collins"
        assert result.amount_charged == 10.0
        assert result.stripe_payment_intent_id == "pi_test_123"

    @respx.mock
    def test_not_found_raises(self, client):
        respx.get(f"{BASE}/v1/licenses/bad-uuid").mock(
            return_value=httpx.Response(404, json={"detail": "License not found"})
        )
        with pytest.raises(NotFoundError):
            client.get_license("bad-uuid")

    @respx.mock
    def test_api_key_sent_in_header(self, client):
        route = respx.get(f"{BASE}/v1/licenses/lic-uuid-001").mock(
            return_value=httpx.Response(200, json={
                "id": "lic-uuid-001",
                "status": "cleared",
                "creator_name": "Test",
                "use_type": "voiceover",
                "amount_charged": 10.0,
                "platform_fee": 1.5,
                "creator_payout": 8.5,
                "created_at": "2026-06-15T10:00:00Z",
            })
        )
        client.get_license("lic-uuid-001")
        assert route.calls[0].request.headers.get("x-api-key") == "ak_live_testkey1234567890"


# ── aletheia.creators.list() ───────────────────────────────────────────────────


class TestCreatorsList:
    @respx.mock
    def test_returns_creators_list(self, client):
        respx.get(f"{BASE}/v1/creators").mock(
            return_value=httpx.Response(200, json={
                "creators": [
                    {"id": "c1", "name": "Sarah Collins", "rate_per_use": 10.0, "currency": "USD"},
                    {"id": "c2", "name": "James Reed", "rate_per_use": 15.0, "currency": "USD"},
                ],
                "total": 2,
            })
        )
        result = client.creators.list()

        assert isinstance(result, CreatorsListResponse)
        assert result.total == 2
        assert result.creators[0].name == "Sarah Collins"
        assert result.creators[1].rate_per_use == 15.0

    @respx.mock
    def test_query_params_forwarded(self, client):
        route = respx.get(f"{BASE}/v1/creators").mock(
            return_value=httpx.Response(200, json={"creators": [], "total": 0})
        )
        client.creators.list(category="voice", min_rate=5.0, max_rate=20.0)

        url_str = str(route.calls[0].request.url)
        assert "category=voice" in url_str
        assert "min_rate=5.0" in url_str
        assert "max_rate=20.0" in url_str

    @respx.mock
    def test_no_params_when_none(self, client):
        route = respx.get(f"{BASE}/v1/creators").mock(
            return_value=httpx.Response(200, json={"creators": [], "total": 0})
        )
        client.creators.list()
        # No query string appended
        assert "?" not in str(route.calls[0].request.url)

    @respx.mock
    def test_empty_list(self, client):
        respx.get(f"{BASE}/v1/creators").mock(
            return_value=httpx.Response(200, json={"creators": [], "total": 0})
        )
        result = client.creators.list(min_rate=9999.0)
        assert result.total == 0
        assert result.creators == []

    @respx.mock
    def test_api_key_sent_in_header(self, client):
        route = respx.get(f"{BASE}/v1/creators").mock(
            return_value=httpx.Response(200, json={"creators": [], "total": 0})
        )
        client.creators.list()
        assert route.calls[0].request.headers.get("x-api-key") == "ak_live_testkey1234567890"


# ── aletheia.verify() ──────────────────────────────────────────────────────────


class TestVerify:
    @respx.mock
    def test_valid_certificate(self, client):
        respx.get(f"{BASE}/verify/cert-uuid-001").mock(
            return_value=httpx.Response(200, json={
                "valid": True,
                "certificate": {
                    "certificate_id": "cert-uuid-001",
                    "version": "1.0",
                    "issued_by": "Aletheia Rights",
                },
                "record_type": "license_certificate",
            })
        )
        result = client.verify("cert-uuid-001")

        assert isinstance(result, VerifyResponse)
        assert result.valid is True
        assert result.record_type == "license_certificate"
        assert result.certificate["certificate_id"] == "cert-uuid-001"

    @respx.mock
    def test_invalid_certificate(self, client):
        respx.get(f"{BASE}/verify/nonexistent").mock(
            return_value=httpx.Response(200, json={
                "valid": False,
                "certificate": None,
                "record_type": None,
            })
        )
        result = client.verify("nonexistent")
        assert result.valid is False
        assert result.certificate is None

    @respx.mock
    def test_no_api_key_sent(self, client):
        """verify() must NOT send the X-API-Key header — it is a public endpoint."""
        route = respx.get(f"{BASE}/verify/cert-uuid-001").mock(
            return_value=httpx.Response(200, json={"valid": True})
        )
        client.verify("cert-uuid-001")
        assert "x-api-key" not in route.calls[0].request.headers

    @respx.mock
    def test_escrow_hold_record_type(self, client):
        respx.get(f"{BASE}/verify/escrow-uuid-002").mock(
            return_value=httpx.Response(200, json={
                "valid": True,
                "certificate": {"attempt_id": "escrow-uuid-002"},
                "record_type": "escrow_hold",
            })
        )
        result = client.verify("escrow-uuid-002")
        assert result.record_type == "escrow_hold"


# ── aletheia.list_licenses() ───────────────────────────────────────────────────


class TestListLicenses:
    def test_raises_not_implemented(self, client):
        with pytest.raises(NotImplementedError):
            client.list_licenses()


# ── aletheia.clear_by_audio() ──────────────────────────────────────────────────


class TestClearByAudio:
    @respx.mock
    def test_match_cleared(self, client, tmp_path):
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

        respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(200, json={
                "status": "cleared",
                "license_id": "lic-audio-001",
                "compliance_record_id": "cert-audio-001",
                "creator": "Sarah Collins",
                "amount_charged": 10.0,
                "creator_payout": 8.5,
                "platform_fee": 1.5,
                "auto_matched": True,
                "fingerprint_confidence": 0.92,
                "fingerprint_scope": "output_audio_only",
                "fingerprint_disclaimer": "Voice matching analyzes the submitted audio output only.",
                "cleared_at": "2026-06-19T10:00:00Z",
            })
        )
        result = client.clear_by_audio(str(wav_file), "commercial_ad", amount=10.0)

        assert isinstance(result, ClearanceResponse)
        assert result.is_cleared is True
        assert result.auto_matched is True
        assert result.fingerprint_confidence == 0.92
        assert result.fingerprint_scope == "output_audio_only"
        assert result.fingerprint_disclaimer is not None
        assert result.license_id == "lic-audio-001"
        assert result.creator == "Sarah Collins"

    @respx.mock
    def test_no_match_response(self, client, tmp_path):
        wav_file = tmp_path / "other.wav"
        wav_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

        respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(200, json={
                "status": "no_match",
                "message": "No enrolled creator matched the submitted audio above the confidence threshold.",
                "options": [
                    {"type": "clear_by_name", "endpoint": "POST /v1/clear"},
                    {"type": "enroll_voice", "note": "Enroll via POST /v1/creators/{id}/enroll-voice"},
                ],
            })
        )
        result = client.clear_by_audio(str(wav_file), "voiceover")

        assert result.status == "no_match"
        assert result.is_cleared is False
        assert len(result.options) == 2
        assert result.fingerprint_confidence is None
        assert result.auto_matched is None

    def test_file_not_found_raises(self, client):
        with pytest.raises((FileNotFoundError, OSError)):
            client.clear_by_audio("/nonexistent/path/audio.wav", "commercial_ad")

    @respx.mock
    def test_auth_error(self, client, tmp_path):
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

        respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            client.clear_by_audio(str(wav_file), "commercial_ad")

    @respx.mock
    def test_optional_fields_sent_in_multipart(self, client, tmp_path):
        wav_file = tmp_path / "sample.wav"
        wav_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

        route = respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(200, json={"status": "no_match", "message": "no match"})
        )
        client.clear_by_audio(
            str(wav_file),
            "podcast",
            generation_id="gen-xyz",
            amount=25.0,
        )
        body = route.calls[0].request.content
        assert b"gen-xyz" in body
        assert b"25.0" in body
        assert b"podcast" in body

    @respx.mock
    def test_api_key_sent_in_header(self, client, tmp_path):
        wav_file = tmp_path / "test.wav"
        wav_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

        route = respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(200, json={"status": "no_match"})
        )
        client.clear_by_audio(str(wav_file), "video")
        assert route.calls[0].request.headers.get("x-api-key") == "ak_live_testkey1234567890"

    @respx.mock
    def test_mp3_mime_type(self, client, tmp_path):
        mp3_file = tmp_path / "sample.mp3"
        mp3_file.write_bytes(b"\xff\xfb\x90\x00" * 10)

        route = respx.post(f"{BASE}/v1/clear-by-audio").mock(
            return_value=httpx.Response(200, json={"status": "no_match"})
        )
        client.clear_by_audio(str(mp3_file), "commercial_ad")
        ct = route.calls[0].request.headers.get("content-type", "")
        assert "multipart/form-data" in ct


# ── Client construction ────────────────────────────────────────────────────────


class TestClientConstruction:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="api_key is required"):
            Aletheia(api_key="")

    def test_context_manager(self):
        with Aletheia(api_key="ak_live_test", base_url=BASE) as c:
            assert c._api_key == "ak_live_test"

    def test_repr(self):
        c = Aletheia(api_key="ak_live_testkey1234567890", base_url=BASE)
        assert "ak_live_testkey1..." in repr(c)

    def test_creators_resource_attached(self):
        c = Aletheia(api_key="ak_live_test", base_url=BASE)
        from aletheia.resources import CreatorsResource
        assert isinstance(c.creators, CreatorsResource)

    def test_custom_base_url_trailing_slash_stripped(self):
        c = Aletheia(api_key="ak_live_test", base_url="https://example.com/")
        assert c._base_url == "https://example.com"
