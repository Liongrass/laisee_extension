from datetime import datetime, timezone
from typing import Optional

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateLaiseeData, Laisee

db = Database("ext_laisee")


async def create_laisee(data: CreateLaiseeData, wallet_id: str) -> Laisee:
    laisee = Laisee(
        id=urlsafe_short_hash()[:22],
        wallet=wallet_id,
        title=data.title,
        min_sats=data.min_sats,
        max_sats=data.max_sats,
        unique_hash=urlsafe_short_hash(),
        k1=urlsafe_short_hash(),
        memo=data.memo,
        created_at=datetime.now(timezone.utc),
    )
    await db.insert("laisee.laisees", laisee)
    return laisee


async def get_laisee(laisee_id: str) -> Optional[Laisee]:
    return await db.fetchone(
        "SELECT * FROM laisee.laisees WHERE id = :id",
        {"id": laisee_id},
        Laisee,
    )


async def get_laisee_by_hash(unique_hash: str) -> Optional[Laisee]:
    return await db.fetchone(
        "SELECT * FROM laisee.laisees WHERE unique_hash = :hash",
        {"hash": unique_hash},
        Laisee,
    )


async def get_laisees(wallet_ids: list[str]) -> list[Laisee]:
    if not wallet_ids:
        return []
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM laisee.laisees WHERE wallet IN ({q}) ORDER BY created_at DESC",
        model=Laisee,
    )


async def update_laisee(laisee: Laisee) -> Laisee:
    await db.update("laisee.laisees", laisee)
    return laisee


async def delete_laisee(laisee_id: str) -> None:
    await db.execute(
        "DELETE FROM laisee.laisees WHERE id = :id",
        {"id": laisee_id},
    )


async def mark_laisee_paid(
    laisee_id: str, payment_hash: str, paid_amount_sats: int
) -> Optional[Laisee]:
    laisee = await get_laisee(laisee_id)
    if not laisee or laisee.is_paid:
        return laisee
    laisee.is_paid = True
    laisee.payment_hash = payment_hash
    laisee.paid_amount = paid_amount_sats
    laisee.paid_at = datetime.now(timezone.utc)
    return await update_laisee(laisee)


async def mark_laisee_withdrawn(laisee_id: str) -> Optional[Laisee]:
    laisee = await get_laisee(laisee_id)
    if not laisee or laisee.is_withdrawn:
        return laisee
    laisee.is_withdrawn = True
    laisee.withdrawn_at = datetime.now(timezone.utc)
    return await update_laisee(laisee)
