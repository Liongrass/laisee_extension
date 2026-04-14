from datetime import datetime, timezone
from typing import Optional

from fastapi import Query
from pydantic import BaseModel, Field


class CreateLaiseeData(BaseModel):
    title: str
    wallet: Optional[str] = None
    min_sats: int = Query(1, ge=1)
    max_sats: int = Query(1, ge=1)
    memo: Optional[str] = None


class Laisee(BaseModel):
    id: str
    wallet: str
    title: str
    min_sats: int
    max_sats: int
    unique_hash: str
    k1: str
    is_paid: bool = False
    is_withdrawn: bool = False
    payment_hash: Optional[str] = None
    paid_amount: int = 0  # sats actually paid; used as withdraw amount
    memo: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    paid_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    lnurl: Optional[str] = Field(
        default=None,
        no_database=True,
        deprecated=True,
        description=(
            "Deprecated: dynamically generate on the client side. "
            "Example: lnurlp://${host}/laisee/api/v1/lnurl/${unique_hash}"
        ),
    )
    lnurl_url: Optional[str] = Field(
        default=None,
        no_database=True,
        description="Raw LNURL callback URL (use for QR code generation)",
    )

    @property
    def state(self) -> str:
        if self.is_withdrawn:
            return "withdrawn"
        if self.is_paid:
            return "funded"
        return "unfunded"
