import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import laisee_generic_router
from .views_api import laisee_api_router
from .views_lnurl import laisee_lnurl_router

laisee_ext: APIRouter = APIRouter(prefix="/laisee", tags=["laisee"])
laisee_ext.include_router(laisee_generic_router)
laisee_ext.include_router(laisee_api_router)
laisee_ext.include_router(laisee_lnurl_router)

laisee_static_files = [
    {
        "path": "/laisee/static",
        "name": "laisee_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def laisee_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as exc:
            logger.warning(exc)


def laisee_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task("ext_laisee", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "laisee_ext",
    "laisee_start",
    "laisee_static_files",
    "laisee_stop",
]
