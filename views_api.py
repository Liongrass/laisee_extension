from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from lnbits.core.crud import get_user
from lnbits.core.models import SimpleStatus, WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key

from .crud import create_laisee, delete_laisee, get_laisee, get_laisees
from .helpers import create_lnurl
from .models import CreateLaiseeData, Laisee

laisee_api_router = APIRouter(prefix="/api/v1")


@laisee_api_router.get("/laisees", status_code=HTTPStatus.OK)
async def api_list_laisees(
    request: Request,
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[Laisee]:
    wallet_ids = [key_info.wallet.id]
    if all_wallets:
        user = await get_user(key_info.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    laisees = await get_laisees(wallet_ids)
    for laisee in laisees:
        try:
            lnurl = create_lnurl(laisee, request)
            laisee.lnurl = str(lnurl.bech32)
            laisee.lnurl_url = str(lnurl.url)
        except ValueError:
            pass
    return laisees


@laisee_api_router.get("/laisees/{laisee_id}", status_code=HTTPStatus.OK)
async def api_get_laisee(
    request: Request,
    laisee_id: str,
    key_info: WalletTypeInfo = Depends(require_invoice_key),
) -> Laisee:
    laisee = await get_laisee(laisee_id)
    if not laisee:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Laisee not found."
        )
    if laisee.wallet != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your laisee."
        )
    try:
        lnurl = create_lnurl(laisee, request)
        laisee.lnurl = str(lnurl.bech32)
        laisee.lnurl_url = str(lnurl.url)
    except ValueError:
        pass
    return laisee


@laisee_api_router.post("/laisees", status_code=HTTPStatus.CREATED)
async def api_create_laisee(
    request: Request,
    data: CreateLaiseeData,
    key_info: WalletTypeInfo = Depends(require_admin_key),
) -> Laisee:
    if data.min_sats > data.max_sats:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="min_sats cannot be greater than max_sats.",
        )
    if not data.wallet:
        data.wallet = key_info.wallet.id

    laisee = await create_laisee(data, data.wallet)
    try:
        lnurl = create_lnurl(laisee, request)
        laisee.lnurl = str(lnurl.bech32)
        laisee.lnurl_url = str(lnurl.url)
    except ValueError:
        pass
    return laisee


@laisee_api_router.delete("/laisees/{laisee_id}", status_code=HTTPStatus.OK)
async def api_delete_laisee(
    laisee_id: str,
    key_info: WalletTypeInfo = Depends(require_admin_key),
) -> SimpleStatus:
    laisee = await get_laisee(laisee_id)
    if not laisee:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Laisee not found."
        )
    if laisee.wallet != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your laisee."
        )
    await delete_laisee(laisee_id)
    return SimpleStatus(success=True, message="Laisee deleted.")
