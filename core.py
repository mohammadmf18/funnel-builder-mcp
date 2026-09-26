"""
core.py
المنطق الأساسي لبناء وإدارة الفنلات (Funnels).
مستقل تمامًا عن أي بروتوكول (MCP أو OpenAI) — كل من الطبقتين ينادي هذي الدوال.
"""

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from email_validator import validate_email, EmailNotValidError
from validation import validate, validate_content, TEXT, PRICE, EMAILS
from typing import Optional

from db import get_conn, init_db, new_id, row_to_dict, _now
from templates import render_page_html

init_db()

VALID_PAGE_TYPES = {"landing", "optin", "sales", "checkout", "upsell", "thankyou"}


# ---------------------------------------------------------------------------
# الفنلات
# ---------------------------------------------------------------------------

def create_funnel(name: str, goal: str = "") -> dict:
    validate({**TEXT, "minLength": 1, "pattern": r"\S"}, name)
    validate(TEXT, goal)
    fid = new_id("funnel")
    now = _now()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funnels (id, name, goal, status, created_at, updated_at) VALUES (?, ?, ?, 'draft', ?, ?)",
            (fid, name, goal, now, now),
        )
    return {"funnel_id": fid, "name": name, "goal": goal, "status": "draft"}


def list_funnels() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM funnels ORDER BY created_at DESC").fetchall()
    return [row_to_dict(r) for r in rows]


def get_funnel(funnel_id: str) -> dict:
    with get_conn() as conn:
        f = conn.execute("SELECT * FROM funnels WHERE id = ?", (funnel_id,)).fetchone()
        if not f:
            raise ValueError(f"funnel {funnel_id} غير موجود")
        pages = conn.execute(
            "SELECT * FROM pages WHERE funnel_id = ? ORDER BY order_index ASC", (funnel_id,)
        ).fetchall()
        sequences = conn.execute(
            "SELECT * FROM email_sequences WHERE funnel_id = ?", (funnel_id,)
        ).fetchall()

    funnel = row_to_dict(f)
    funnel["pages"] = [
        {**row_to_dict(p), "content": json.loads(p["content_json"])} for p in pages
    ]
    funnel["email_sequences"] = [
        {**row_to_dict(s), "emails": json.loads(s["emails_json"])} for s in sequences
    ]
    return funnel


def delete_funnel(funnel_id: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM funnels WHERE id = ?", (funnel_id,))
        if cur.rowcount == 0:
            raise ValueError(f"funnel {funnel_id} غير موجود")
    shutil.rmtree(site_root() / funnel_id, ignore_errors=True)
    return {"funnel_id": funnel_id, "deleted": True}


# ---------------------------------------------------------------------------
# الصفحات
# ---------------------------------------------------------------------------

def _add_page(funnel_id: str, page_type: str, headline: str, content: dict, slug: Optional[str] = None) -> dict:
    if page_type not in VALID_PAGE_TYPES:
        raise ValueError(f"نوع صفحة غير معروف: {page_type}. الأنواع المسموحة: {sorted(VALID_PAGE_TYPES)}")

    validate(TEXT, headline)
    validate_content(page_type, content)
    if slug is not None and not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
        raise ValueError("slug غير صالح")
    with get_conn() as conn:
        f = conn.execute("SELECT id FROM funnels WHERE id = ?", (funnel_id,)).fetchone()
        if not f:
            raise ValueError(f"funnel {funnel_id} غير موجود")

        count = conn.execute(
            "SELECT COUNT(*) c FROM pages WHERE funnel_id = ?", (funnel_id,)
        ).fetchone()["c"]

        pid = new_id("page")
        now = _now()
        final_slug = slug or f"{page_type}-{count + 1}"

        conn.execute(
            """INSERT INTO pages (id, funnel_id, type, order_index, slug, headline, content_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, funnel_id, page_type, count, final_slug, headline, json.dumps(content, ensure_ascii=False), now, now),
        )
        conn.execute("UPDATE funnels SET updated_at = ? WHERE id = ?", (now, funnel_id))

    return {"page_id": pid, "funnel_id": funnel_id, "type": page_type, "slug": final_slug, "order_index": count}


def add_landing_page(funnel_id: str, headline: str, subheadline: str = "", cta_text: str = "ابدأ الآن") -> dict:
    return _add_page(funnel_id, "landing", headline, {"subheadline": subheadline, "cta_text": cta_text})


def add_optin_page(funnel_id: str, headline: str, offer_description: str, incentive: str = "") -> dict:
    return _add_page(funnel_id, "optin", headline, {"offer_description": offer_description, "incentive": incentive})


def add_sales_page(funnel_id: str, headline: str, benefits: list, price: float, currency: str = "SAR") -> dict:
    return _add_page(funnel_id, "sales", headline, {"benefits": benefits, "price": price, "currency": currency})


def add_checkout_page(funnel_id: str, product_name: str, price: float, currency: str = "SAR", checkout_url: str = "") -> dict:
    return _add_page(
        funnel_id, "checkout", f"إتمام الشراء: {product_name}",
        {"product_name": product_name, "price": price, "currency": currency, "checkout_url": checkout_url},
    )


def add_upsell_page(funnel_id: str, product_name: str, price: float, headline: str = "", currency: str = "SAR", checkout_url: str = "") -> dict:
    headline = headline or f"عرض خاص: {product_name}"
    return _add_page(funnel_id, "upsell", headline, {"product_name": product_name, "price": price, "currency": currency, "checkout_url": checkout_url})


def add_thankyou_page(funnel_id: str, headline: str = "شكرًا لك!", message: str = "") -> dict:
    return _add_page(funnel_id, "thankyou", headline, {"message": message})


def update_page(page_id: str, headline: Optional[str] = None, content: Optional[dict] = None) -> dict:
    with get_conn() as conn:
        p = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if not p:
            raise ValueError(f"page {page_id} غير موجودة")
        new_headline = headline if headline is not None else p["headline"]
        merged_content = json.loads(p["content_json"])
        validate(TEXT, new_headline)
        if content is not None:
            validate_content(p["type"], content)
            merged_content.update(content)
        validate_content(p["type"], merged_content)
        conn.execute(
            "UPDATE pages SET headline = ?, content_json = ?, updated_at = ? WHERE id = ?",
            (new_headline, json.dumps(merged_content, ensure_ascii=False), _now(), page_id),
        )
    return {"page_id": page_id, "headline": new_headline, "content": merged_content}


# ---------------------------------------------------------------------------
# قوائم الإيميل
# ---------------------------------------------------------------------------

def connect_email_sequence(funnel_id: str, list_name: str, emails: list) -> dict:
    """
    يحفظ مسودة تسلسل رسائل فقط؛ لا يرسل أو يجدول رسائل.
    """
    validate(TEXT, list_name)
    validate(EMAILS, emails)
    with get_conn() as conn:
        f = conn.execute("SELECT id FROM funnels WHERE id = ?", (funnel_id,)).fetchone()
        if not f:
            raise ValueError(f"funnel {funnel_id} غير موجود")
        sid = new_id("seq")
        conn.execute(
            "INSERT INTO email_sequences (id, funnel_id, list_name, emails_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (sid, funnel_id, list_name, json.dumps(emails, ensure_ascii=False), _now()),
        )
    return {"sequence_id": sid, "funnel_id": funnel_id, "list_name": list_name, "emails_count": len(emails), "status": "draft", "sending_enabled": False}


# ---------------------------------------------------------------------------
# الأحداث والتحليلات
# ---------------------------------------------------------------------------

def record_event(funnel_id: str, event_type: str, page_id: Optional[str] = None, value: float = 0, visitor_id: Optional[str] = None) -> dict:
    valid_events = {"visit", "optin", "purchase", "upsell_purchase"}
    if event_type not in valid_events:
        raise ValueError(f"نوع حدث غير معروف: {event_type}. الأنواع المسموحة: {sorted(valid_events)}")
    validate(PRICE, value)
    eid = new_id("evt")
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM funnels WHERE id = ?", (funnel_id,)).fetchone():
            raise ValueError("الفنل غير موجود")
        if page_id is not None and not conn.execute("SELECT id FROM pages WHERE id = ? AND funnel_id = ?", (page_id, funnel_id)).fetchone():
            raise ValueError("الصفحة لا تنتمي لهذا الفنل")
        conn.execute(
            "INSERT INTO events (id, funnel_id, page_id, event_type, value, created_at, visitor_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (eid, funnel_id, page_id, event_type, value, _now(), visitor_id),
        )
    return {"event_id": eid, "funnel_id": funnel_id, "event_type": event_type}


def get_funnel_analytics(funnel_id: str) -> dict:
    get_funnel(funnel_id)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT event_type, COUNT(DISTINCT CASE WHEN event_type = 'visit' THEN COALESCE(visitor_id, id) ELSE id END) c, COALESCE(SUM(value), 0) total_value FROM events WHERE funnel_id = ? GROUP BY event_type",
            (funnel_id,),
        ).fetchall()

    stats = {r["event_type"]: {"count": r["c"], "total_value": r["total_value"]} for r in rows}
    visits = stats.get("visit", {}).get("count", 0)
    optins = stats.get("optin", {}).get("count", 0)
    purchases = stats.get("purchase", {}).get("count", 0)

    return {
        "funnel_id": funnel_id,
        "visits": visits,
        "optins": optins,
        "purchases": purchases,
        "revenue": stats.get("purchase", {}).get("total_value", 0) + stats.get("upsell_purchase", {}).get("total_value", 0),
        "optin_rate": round(optins / visits, 4) if visits else 0,
        "conversion_rate": round(purchases / visits, 4) if visits else 0,
        "raw": stats,
    }


# ---------------------------------------------------------------------------
# النشر (توليد صفحات HTML فعلية)
# ---------------------------------------------------------------------------

def site_root() -> Path:
    return Path(os.environ.get("FUNNEL_OUTPUT_DIR", Path(__file__).parent / "generated_sites")).resolve()


def publish_funnel(funnel_id: str) -> dict:
    funnel = get_funnel(funnel_id)
    if not funnel["pages"]:
        raise ValueError("أضف صفحة واحدة على الأقل قبل النشر")
    root = site_root()
    root.mkdir(parents=True, exist_ok=True)
    site_dir = root / funnel_id
    generated = []
    # Render everything before replacing any live files.
    with tempfile.TemporaryDirectory(dir=root) as staging:
        shutil.copyfile(Path(__file__).parent / "funnel.js", Path(staging) / "funnel.js")
        for index, page in enumerate(funnel["pages"]):
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", page["slug"]):
                raise ValueError("slug غير صالح")
            validate_content(page["type"], page["content"])
            next_page = funnel["pages"][index + 1] if index + 1 < len(funnel["pages"]) else None
            next_url = f"{next_page['slug']}.html" if next_page else None
            html = render_page_html(funnel["name"], page, next_url)
            Path(staging, f"{page['slug']}.html").write_text(html, encoding="utf-8")
            generated.append({"page_id": page["id"], "slug": page["slug"], "file": str(site_dir / f"{page['slug']}.html")})
        site_dir.mkdir(exist_ok=True)
        for file in Path(staging).iterdir():
            os.replace(file, site_dir / file.name)
    with get_conn() as conn:
        conn.execute("UPDATE funnels SET status = 'published', updated_at = ? WHERE id = ?", (_now(), funnel_id))
    return {"funnel_id": funnel_id, "status": "published", "output_dir": str(site_dir),
            "site_path": f"/sites/{funnel_id}/", "pages": generated,
            "note": "الرابط يعمل عند تشغيل api_server؛ الملفات وحدها لا تحفظ الاشتراكات"}


def submit_lead(funnel_id: str, page_id: str, email: str, visitor_id: str) -> dict:
    try:
        normalized = validate_email(email, check_deliverability=False).normalized.casefold()
    except EmailNotValidError as exc:
        raise ValueError("البريد الإلكتروني غير صالح") from exc
    funnel = get_funnel(funnel_id)
    if funnel["status"] != "published":
        raise ValueError("الفنل غير منشور")
    pages = funnel["pages"]
    index = next((i for i, page in enumerate(pages) if page["id"] == page_id and page["type"] == "optin"), None)
    if index is None:
        raise ValueError("صفحة التسجيل غير موجودة في هذا الفنل")
    if not (site_root() / funnel_id / f"{pages[index]['slug']}.html").is_file():
        raise ValueError("صفحة التسجيل غير منشورة")
    with get_conn() as conn:
        inserted = conn.execute(
            "INSERT OR IGNORE INTO leads (id, funnel_id, page_id, email, created_at) VALUES (?, ?, ?, ?, ?)",
            (new_id("lead"), funnel_id, page_id, normalized, _now()),
        ).rowcount
        if inserted:
            conn.execute(
                "INSERT INTO events (id, funnel_id, page_id, event_type, value, created_at, visitor_id) VALUES (?, ?, ?, 'optin', 0, ?, ?)",
                (new_id("evt"), funnel_id, page_id, _now(), visitor_id),
            )
    next_page = pages[index + 1] if index + 1 < len(pages) else None
    if next_page and not (site_root() / funnel_id / f"{next_page['slug']}.html").is_file():
        next_page = None
    return {"ok": True, "next_url": f"/sites/{funnel_id}/{next_page['slug']}.html" if next_page else None}


def list_leads(funnel_id: str, limit: int = 100, offset: int = 0) -> dict:
    get_funnel(funnel_id)
    validate({"type": "integer", "minimum": 1, "maximum": 1000}, limit)
    validate({"type": "integer", "minimum": 0}, offset)
    with get_conn() as conn:
        rows = conn.execute("SELECT id, page_id, email, created_at FROM leads WHERE funnel_id = ? ORDER BY created_at, id LIMIT ? OFFSET ?", (funnel_id, limit, offset)).fetchall()
    return {"funnel_id": funnel_id, "leads": [row_to_dict(row) for row in rows]}
