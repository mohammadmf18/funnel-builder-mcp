"""Authenticated management API and public funnel pages / lead collection."""
import hmac
import os
import re
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field

import core
import schemas

app = FastAPI(title="Funnel Builder API", version="1.1.0")


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LeadSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page_id: str = Field(pattern=r"^page_[0-9a-f]{12}$")
    email: EmailStr = Field(max_length=254)


def require_api_key(request: Request):
    expected = os.environ.get("FUNNEL_API_KEY", "")
    if not expected:
        raise HTTPException(503, "Set FUNNEL_API_KEY to enable the management API")
    supplied = request.headers.get("authorization", "")
    if not hmac.compare_digest(supplied.encode(), f"Bearer {expected}".encode()):
        raise HTTPException(401, "Invalid API key", headers={"WWW-Authenticate": "Bearer"})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if request.url.path.startswith("/sites/"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools", dependencies=[Depends(require_api_key)])
def get_tools():
    return {"tools": schemas.to_openai_functions()}


@app.post("/tools/call", dependencies=[Depends(require_api_key)])
def call_tool(call: ToolCall):
    try:
        return {"result": schemas.call_tool(call.name, call.arguments)}
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


def published_funnel(funnel_id):
    if not re.fullmatch(r"funnel_[0-9a-f]{12}", funnel_id):
        raise HTTPException(404, "Funnel not found")
    try:
        funnel = core.get_funnel(funnel_id)
    except ValueError as exc:
        raise HTTPException(404, "Funnel not found") from exc
    if funnel["status"] != "published" or not funnel["pages"]:
        raise HTTPException(404, "Funnel not published")
    return funnel


def visitor(request):
    value = request.cookies.get("funnel_visitor", "")
    return value if re.fullmatch(r"[0-9a-f]{32}", value) else uuid.uuid4().hex


def set_visitor(response, request, funnel_id, visitor_id):
    response.set_cookie("funnel_visitor", visitor_id, max_age=60 * 60 * 24 * 30,
                        path=f"/sites/{funnel_id}/", httponly=True,
                        secure=request.url.scheme == "https", samesite="lax")
    return response


@app.get("/sites/{funnel_id}/")
def entry(funnel_id: str):
    funnel = published_funnel(funnel_id)
    return RedirectResponse(f"/sites/{funnel_id}/{funnel['pages'][0]['slug']}.html", status_code=302)


@app.get("/sites/{funnel_id}/funnel.js")
def script(funnel_id: str):
    published_funnel(funnel_id)
    path = core.site_root() / funnel_id / "funnel.js"
    if not path.is_file():
        raise HTTPException(404, "Asset not found; republish the funnel")
    return FileResponse(path, media_type="application/javascript")


@app.get("/sites/{funnel_id}/{slug}.html")
def page(funnel_id: str, slug: str, request: Request):
    funnel = published_funnel(funnel_id)
    current = next((p for p in funnel["pages"] if p["slug"] == slug), None)
    if not current or not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
        raise HTTPException(404, "Page not found")
    path = core.site_root() / funnel_id / f"{slug}.html"
    if not path.is_file():
        raise HTTPException(404, "Page not published")
    visitor_id = visitor(request)
    core.record_event(funnel_id, "visit", current["id"], visitor_id=visitor_id)
    return set_visitor(FileResponse(path, media_type="text/html"), request, funnel_id, visitor_id)


@app.post("/sites/{funnel_id}/leads")
def lead(funnel_id: str, submission: LeadSubmission, request: Request):
    published_funnel(funnel_id)
    visitor_id = visitor(request)
    try:
        result = core.submit_lead(funnel_id, submission.page_id, str(submission.email), visitor_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return set_visitor(JSONResponse(result), request, funnel_id, visitor_id)
