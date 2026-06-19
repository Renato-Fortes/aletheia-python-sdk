from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ClearanceResponse:
    """Returned by aletheia.clear() and aletheia.clear_by_audio()."""

    status: str  # "cleared" | "escrow" | "unresolved" | "no_match"
    license_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    certificate: Optional[dict] = None
    certificate_pdf_url: Optional[str] = None
    cleared_at: Optional[str] = None
    creator: Optional[str] = None
    amount_charged: Optional[float] = None
    creator_payout: Optional[float] = None
    platform_fee: Optional[float] = None
    message: Optional[str] = None
    escrow_id: Optional[str] = None
    estimated_resolution: Optional[str] = None
    clearance_attempt_id: Optional[str] = None
    options: Optional[List[dict]] = None
    # Audio fingerprint fields (present when status comes from clear_by_audio)
    fingerprint_confidence: Optional[float] = None
    auto_matched: Optional[bool] = None
    fingerprint_scope: Optional[str] = None
    fingerprint_disclaimer: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> ClearanceResponse:
        return cls(
            status=data["status"],
            license_id=data.get("license_id"),
            compliance_record_id=data.get("compliance_record_id"),
            certificate=data.get("certificate"),
            certificate_pdf_url=data.get("certificate_pdf_url"),
            cleared_at=data.get("cleared_at"),
            creator=data.get("creator"),
            amount_charged=data.get("amount_charged"),
            creator_payout=data.get("creator_payout"),
            platform_fee=data.get("platform_fee"),
            message=data.get("message"),
            escrow_id=data.get("escrow_id"),
            estimated_resolution=data.get("estimated_resolution"),
            clearance_attempt_id=data.get("clearance_attempt_id"),
            options=data.get("options"),
            fingerprint_confidence=data.get("fingerprint_confidence"),
            auto_matched=data.get("auto_matched"),
            fingerprint_scope=data.get("fingerprint_scope"),
            fingerprint_disclaimer=data.get("fingerprint_disclaimer"),
        )

    @property
    def is_cleared(self) -> bool:
        return self.status == "cleared"

    @property
    def is_escrow(self) -> bool:
        return self.status == "escrow"

    @property
    def is_unresolved(self) -> bool:
        return self.status == "unresolved"

    @property
    def verification_url(self) -> Optional[str]:
        """Convenience accessor for the certificate verification URL."""
        if self.certificate:
            return self.certificate.get("verification_url")
        return None


@dataclass
class Creator:
    id: str
    name: str
    rate_per_use: float
    currency: str

    @classmethod
    def from_dict(cls, data: dict) -> Creator:
        return cls(
            id=data["id"],
            name=data["name"],
            rate_per_use=data["rate_per_use"],
            currency=data["currency"],
        )


@dataclass
class CreatorsListResponse:
    """Returned by aletheia.creators.list()."""

    creators: List[Creator]
    total: int

    @classmethod
    def from_dict(cls, data: dict) -> CreatorsListResponse:
        return cls(
            creators=[Creator.from_dict(c) for c in data.get("creators", [])],
            total=data.get("total", 0),
        )


@dataclass
class LicenseRecord:
    """Returned by aletheia.get_license()."""

    id: str
    status: str
    creator_name: str
    use_type: str
    amount_charged: float
    platform_fee: float
    creator_payout: float
    stripe_payment_intent_id: Optional[str] = None
    generation_id: Optional[str] = None
    created_at: Optional[str] = None
    cleared_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> LicenseRecord:
        return cls(
            id=data["id"],
            status=data["status"],
            creator_name=data["creator_name"],
            use_type=data["use_type"],
            amount_charged=data["amount_charged"],
            platform_fee=data["platform_fee"],
            creator_payout=data["creator_payout"],
            stripe_payment_intent_id=data.get("stripe_payment_intent_id"),
            generation_id=data.get("generation_id"),
            created_at=data.get("created_at"),
            cleared_at=data.get("cleared_at"),
        )


@dataclass
class VerifyResponse:
    """Returned by aletheia.verify()."""

    valid: bool
    certificate: Optional[dict] = None
    record_type: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> VerifyResponse:
        return cls(
            valid=data["valid"],
            certificate=data.get("certificate"),
            record_type=data.get("record_type"),
        )
