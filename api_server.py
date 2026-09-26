"""
api_server.py
REST API يعرض نفس أدوات الفنل بيلدر، بصيغة متوافقة مع OpenAI Function Calling.
يصلح لأي نموذج ذكاء اصطناعي يدعم استدعاء أدوات عبر HTTP (GPT، Gemini، نماذج محلية...).

تشغيل محلي:
    uvicorn api_server:app --reload --port 8000

نقاط الوصول:
    GET  /tools                -> قائمة الأدوات بصيغة OpenAI functions
    POST /tools/call           -> تنفيذ أداة معينة {"name": "...", "arguments": {...}}
    GET  /health                -> فحص الحالة
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

import schemas

app = FastAPI(title="Funnel Builder API", version="1.0.0")


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools")
def get_tools():
    """يرجّع تعريفات الأدوات بصيغة OpenAI Function Calling الجاهزة للاستخدام مباشرة."""
    return {"tools": schemas.to_openai_functions()}


@app.post("/tools/call")
def call_tool(call: ToolCall):
    try:
        result = schemas.call_tool(call.name, call.arguments)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TypeError as e:
        raise HTTPException(status_code=422, detail=f"مدخلات غير صحيحة: {e}")
