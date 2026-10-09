from fastapi import Request
from lnbits.core.services import fee_reserve_total
from lnurl import Lnurl
from lnurl import encode as lnurl_encode

from .models import Laisee


def create_lnurl(laisee: Laisee, req: Request) -> Lnurl:
    url = req.url_for("laisee.api_lnurl_response", unique_hash=laisee.unique_hash)
    try:
        return lnurl_encode(str(url))
    except Exception as exc:
        raise ValueError(
            f"Error creating LNURL with url: `{url!s}`. "
            "Check your webserver proxy configuration."
        ) from exc


def withdrawable_sats(amount_sats: int, deduct_fees: bool) -> int:
    """Sats a recipient may withdraw from an envelope holding `amount_sats`.

    With deduct_fees, the LNbits fee reserve (routing fee limit + service fee)
    is held back inside the envelope. The reserve grows with the amount, so
    paying out `amount - reserve(amount)` never debits more than `amount`.
    """
    if not deduct_fees:
        return amount_sats
    amount_msat = amount_sats * 1000
    return max(0, (amount_msat - fee_reserve_total(amount_msat)) // 1000)
