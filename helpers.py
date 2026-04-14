from fastapi import Request
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
