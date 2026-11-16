"""Local REST API for AI Sales Funnel Builder.
Bind only to loopback by default. No public authentication is implemented.
"""
import os
import secrets
from typing import Any
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import schemas

app = FastAPI(title="AI Sales Funnel Builder API", version="1.1.0")

class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

def _authorized(key: str | None):
    expected = os.environ.get("FUNNEL_API_KEY")
    if not expected or not key or not secrets.compare_digest(expected, key):
        raise HTTPException(status_code=401, detail="Set FUNNEL_API_KEY and supply X-API-Key")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tools")
def get_tools(x_api_key: str | None = Header(default=None)):
    _authorized(x_api_key)
    return {"tools": schemas.to_openai_functions()}

@app.post("/tools/call")
def call_tool(call: ToolCall, x_api_key: str | None = Header(default=None)):
    _authorized(x_api_key)
    try:
        return {"result": schemas.call_tool(call.name, call.arguments)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TypeError as exc:
        raise HTTPException(status_code=422, detail="Invalid tool arguments")
