import asyncio

from lnbits.core.models import Payment
from lnbits.tasks import register_invoice_listener
from loguru import logger

from .crud import mark_laisee_paid


async def wait_for_paid_invoices():
    invoice_queue: asyncio.Queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_laisee")

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment) -> None:
    if not payment.extra or payment.extra.get("tag") != "laisee":
        return

    laisee_id = payment.extra.get("laisee_id")
    if not laisee_id:
        logger.error("Laisee: invoice paid but no laisee_id in extra.")
        return

    # payment.amount is in millisatoshis; convert to sats
    paid_amount_sats = abs(payment.amount) // 1000

    laisee = await mark_laisee_paid(laisee_id, payment.payment_hash, paid_amount_sats)
    if laisee:
        logger.info(
            f"Laisee {laisee_id} funded with {paid_amount_sats} sats "
            f"(payment_hash={payment.payment_hash})."
        )
    else:
        logger.warning(f"Laisee {laisee_id} not found or already paid.")
