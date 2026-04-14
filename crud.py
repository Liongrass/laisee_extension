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
    placeholders = ",".join(f":w{i}" for i in range(len(wallet_ids)))
    values = {f"w{i}": w for i, w in enumerate(wallet_ids)}
    return await db.fetchall(
        f"SELECT * FROM laisee.laisees WHERE wallet IN ({placeholders}) ORDER BY created_at DESC",
        values,
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


async def claim_laisee_for_withdrawal(laisee_id: str) -> bool:
    """Atomically flip is_withdrawn to TRUE only if it is currently FALSE.

    Returns True if this call won the race (exactly one row updated), False if
    another concurrent request already claimed the withdrawal.  Callers must
    revert via revert_laisee_withdrawal_claim() if the subsequent pay_invoice
    call fails, so the envelope can be retried.
    """
    result = await db.execute(
        "UPDATE laisee.laisees "
        "SET is_withdrawn = TRUE, withdrawn_at = :now "
        "WHERE id = :id AND is_withdrawn = FALSE AND is_paid = TRUE",
        {"id": laisee_id, "now": datetime.now(timezone.utc)},
    )
    # db.execute returns the affected-row count (int) for UPDATE statements
    return result == 1


async def revert_laisee_withdrawal_claim(laisee_id: str) -> None:
    """Undo a claim made by claim_laisee_for_withdrawal when pay_invoice fails.

    This re-opens the envelope for a retry.  Only call this on a confirmed
    payment failure — never after a successful payment.
    """
    await db.execute(
        "UPDATE laisee.laisees "
        "SET is_withdrawn = FALSE, withdrawn_at = NULL "
        "WHERE id = :id",
        {"id": laisee_id},
    )
