import json

from bolt11 import decode as decode_bolt11
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from lnbits.core.services import create_invoice, pay_invoice
from lnurl import (
    CallbackUrl,
    LightningInvoice,
    LnurlErrorResponse,
    LnurlPayActionResponse,
    LnurlPayMetadata,
    LnurlPayResponse,
    LnurlSuccessResponse,
    LnurlWithdrawResponse,
    MilliSatoshi,
)
from pydantic import parse_obj_as

from .crud import (
    claim_laisee_for_withdrawal,
    get_laisee_by_hash,
    revert_laisee_withdrawal_claim,
)

laisee_lnurl_router = APIRouter(prefix="/api/v1/lnurl")


@laisee_lnurl_router.get(
    "/pay-cb/{unique_hash}",
    name="laisee.api_lnurl_pay_callback",
    response_class=JSONResponse,
)
async def api_lnurl_pay_callback(
    request: Request,
    unique_hash: str,
    amount: int = Query(...),
) -> LnurlErrorResponse | LnurlPayActionResponse:
    laisee = await get_laisee_by_hash(unique_hash)
    if not laisee:
        return LnurlErrorResponse(reason="Laisee not found.")

    if laisee.is_paid:
        return LnurlErrorResponse(reason="This laisee is already funded.")

    min_msat = laisee.min_sats * 1000
    max_msat = laisee.max_sats * 1000

    if amount < min_msat:
        return LnurlErrorResponse(
            reason=f"Amount too small. Minimum is {laisee.min_sats} sats."
        )
    if amount > max_msat:
        return LnurlErrorResponse(
            reason=f"Amount too large. Maximum is {laisee.max_sats} sats."
        )

    metadata = LnurlPayMetadata(json.dumps([["text/plain", laisee.title]]))
    payment = await create_invoice(
        wallet_id=laisee.wallet,
        amount=int(amount / 1000),
        memo=laisee.title,
        unhashed_description=metadata.encode(),
        extra={"tag": "laisee", "laisee_id": laisee.id},
    )
    invoice = parse_obj_as(LightningInvoice, LightningInvoice(payment.bolt11))
    # disposable=False: wallet should keep the LNURL – same QR becomes a withdraw link
    return LnurlPayActionResponse(pr=invoice, disposable=False)


@laisee_lnurl_router.get(
    "/withdraw-cb/{unique_hash}",
    name="laisee.api_lnurl_withdraw_callback",
    response_class=JSONResponse,
)
async def api_lnurl_withdraw_callback(
    unique_hash: str,
    k1: str,
    pr: str,
) -> LnurlErrorResponse | LnurlSuccessResponse:
    laisee = await get_laisee_by_hash(unique_hash)
    if not laisee:
        return LnurlErrorResponse(reason="Laisee not found.")

    if not laisee.is_paid:
        return LnurlErrorResponse(reason="This laisee has not been funded yet.")

    if laisee.is_withdrawn:
        return LnurlErrorResponse(reason="This laisee has already been withdrawn.")

    if laisee.k1 != k1:
        return LnurlErrorResponse(reason="Invalid k1.")

    bolt11 = decode_bolt11(pr)
    if not bolt11.amount_msat:
        return LnurlErrorResponse(reason="Zero-amount invoices are not supported.")

    # allow a small tolerance for routing fee rounding (within 1 sat)
    expected_msat = laisee.paid_amount * 1000
    if abs(bolt11.amount_msat - expected_msat) > 1000:
        return LnurlErrorResponse(
            reason=(
                f"Wrong amount. Expected {laisee.paid_amount} sats, "
                f"got {bolt11.amount_msat // 1000} sats."
            )
        )

    # Atomically claim the withdrawal before touching the Lightning network.
    # Only one concurrent request can win this UPDATE; the rest get False here
    # and are turned away before any payment is attempted.
    claimed = await claim_laisee_for_withdrawal(laisee.id)
    if not claimed:
        return LnurlErrorResponse(reason="This laisee has already been withdrawn.")

    try:
        await pay_invoice(
            wallet_id=laisee.wallet,
            payment_request=pr,
            max_sat=laisee.paid_amount,
            extra={"tag": "laisee_withdraw", "laisee_id": laisee.id},
        )
    except Exception as exc:
        # Payment failed — revert so the recipient can try again.
        await revert_laisee_withdrawal_claim(laisee.id)
        return LnurlErrorResponse(reason=f"Withdrawal failed: {exc!s}")

    return LnurlSuccessResponse()


@laisee_lnurl_router.get(
    "/{unique_hash}",
    name="laisee.api_lnurl_response",
    response_class=JSONResponse,
)
async def api_lnurl_response(
    request: Request, unique_hash: str
) -> LnurlPayResponse | LnurlWithdrawResponse | LnurlErrorResponse:
    laisee = await get_laisee_by_hash(unique_hash)
    if not laisee:
        return LnurlErrorResponse(reason="Laisee not found.")

    if laisee.is_withdrawn:
        return LnurlErrorResponse(reason="This laisee has already been withdrawn.")

    if laisee.is_paid:
        # Switch to LNURL-Withdraw mode
        url = str(
            request.url_for(
                "laisee.api_lnurl_withdraw_callback", unique_hash=unique_hash
            )
        )
        callback_url = parse_obj_as(CallbackUrl, url)
        return LnurlWithdrawResponse(
            callback=callback_url,
            k1=laisee.k1,
            minWithdrawable=MilliSatoshi(laisee.paid_amount * 1000),
            maxWithdrawable=MilliSatoshi(laisee.paid_amount * 1000),
            defaultDescription=laisee.title,
        )

    # LNURL-Pay mode
    url = str(
        request.url_for("laisee.api_lnurl_pay_callback", unique_hash=unique_hash)
    )
    callback_url = parse_obj_as(CallbackUrl, url)
    metadata = LnurlPayMetadata(json.dumps([["text/plain", laisee.title]]))
    return LnurlPayResponse(
        callback=callback_url,
        minSendable=MilliSatoshi(laisee.min_sats * 1000),
        maxSendable=MilliSatoshi(laisee.max_sats * 1000),
        metadata=metadata,
    )
