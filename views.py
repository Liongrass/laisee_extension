from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

laisee_generic_router = APIRouter()


def laisee_renderer():
    return template_renderer(["laisee/templates"])


@laisee_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return laisee_renderer().TemplateResponse(
        "laisee/index.html",
        {"request": request, "user": user.json()},
    )
