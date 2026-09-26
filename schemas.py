"""
schemas.py
مصدر واحد لتعريف كل الأدوات (اسم + وصف + مخطط JSON للمدخلات).
منه تُبنى:
  - أدوات MCP Server (لـ Claude)
  - Function definitions بصيغة OpenAI (لـ GPT / function calling)
حتى ما نكرر نفس الوصف في مكانين ويصير فيه تعارض لاحقًا.
"""

import core

# كل أداة: name, description, parameters (JSON Schema), func (الدالة الفعلية في core.py)
TOOLS = [
    {
        "name": "create_funnel",
        "description": "ينشئ فنل تسويقي (Sales Funnel) جديد بالاسم والهدف المحددين.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "اسم الفنل"},
                "goal": {"type": "string", "description": "هدف الفنل، مثلاً: بيع كورس أونلاين"},
            },
            "required": ["name"],
        },
        "func": core.create_funnel,
    },
    {
        "name": "list_funnels",
        "description": "يرجّع قائمة بكل الفنلات الموجودة.",
        "parameters": {"type": "object", "properties": {}},
        "func": core.list_funnels,
    },
    {
        "name": "get_funnel",
        "description": "يرجّع تفاصيل فنل معين مع كل صفحاته وقوائم الإيميل المرتبطة فيه.",
        "parameters": {
            "type": "object",
            "properties": {"funnel_id": {"type": "string"}},
            "required": ["funnel_id"],
        },
        "func": core.get_funnel,
    },
    {
        "name": "delete_funnel",
        "description": "يحذف فنل بالكامل مع كل صفحاته وبياناته.",
        "parameters": {
            "type": "object",
            "properties": {"funnel_id": {"type": "string"}},
            "required": ["funnel_id"],
        },
        "func": core.delete_funnel,
    },
    {
        "name": "add_landing_page",
        "description": "يضيف صفحة هبوط (Landing Page) لفنل موجود.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "headline": {"type": "string"},
                "subheadline": {"type": "string"},
                "cta_text": {"type": "string", "description": "نص زر الدعوة للعمل"},
            },
            "required": ["funnel_id", "headline"],
        },
        "func": core.add_landing_page,
    },
    {
        "name": "add_optin_page",
        "description": "يضيف صفحة تحصيل بيانات (Opt-in) لجمع إيميلات الزوار مقابل عرض/هدية.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "headline": {"type": "string"},
                "offer_description": {"type": "string"},
                "incentive": {"type": "string", "description": "الحافز، مثلاً: كتاب مجاني"},
            },
            "required": ["funnel_id", "headline", "offer_description"],
        },
        "func": core.add_optin_page,
    },
    {
        "name": "add_sales_page",
        "description": "يضيف صفحة عرض/بيع تشرح فوائد المنتج وسعره.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "headline": {"type": "string"},
                "benefits": {"type": "array", "items": {"type": "string"}},
                "price": {"type": "number"},
                "currency": {"type": "string", "default": "SAR"},
            },
            "required": ["funnel_id", "headline", "price"],
        },
        "func": core.add_sales_page,
    },
    {
        "name": "add_checkout_page",
        "description": "يضيف صفحة إتمام دفع لمنتج معين داخل الفنل.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "product_name": {"type": "string"},
                "price": {"type": "number"},
                "currency": {"type": "string", "default": "SAR"},
            },
            "required": ["funnel_id", "product_name", "price"],
        },
        "func": core.add_checkout_page,
    },
    {
        "name": "add_upsell_page",
        "description": "يضيف صفحة عرض إضافي (Upsell) تُعرض بعد إتمام عملية الشراء الأساسية.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "product_name": {"type": "string"},
                "price": {"type": "number"},
                "headline": {"type": "string"},
                "currency": {"type": "string", "default": "SAR"},
            },
            "required": ["funnel_id", "product_name", "price"],
        },
        "func": core.add_upsell_page,
    },
    {
        "name": "add_thankyou_page",
        "description": "يضيف صفحة شكر تظهر بعد إتمام رحلة العميل بالفنل.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "headline": {"type": "string", "default": "شكرًا لك!"},
                "message": {"type": "string"},
            },
            "required": ["funnel_id"],
        },
        "func": core.add_thankyou_page,
    },
    {
        "name": "update_page",
        "description": "يحدّث عنوان أو محتوى صفحة موجودة داخل الفنل.",
        "parameters": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "headline": {"type": "string"},
                "content": {"type": "object"},
            },
            "required": ["page_id"],
        },
        "func": core.update_page,
    },
    {
        "name": "connect_email_sequence",
        "description": "يربط تسلسل رسائل إيميل آلي (Email Sequence) بالفنل، يُرسل للمشتركين الجدد.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "list_name": {"type": "string"},
                "emails": {
                    "type": "array",
                    "description": "قائمة رسائل، كل رسالة فيها subject و body و delay_days",
                    "items": {"type": "object"},
                },
            },
            "required": ["funnel_id", "list_name", "emails"],
        },
        "func": core.connect_email_sequence,
    },
    {
        "name": "record_event",
        "description": "يسجّل حدث تتبّع (زيارة/تسجيل إيميل/شراء) لصفحة أو فنل معين، يُستخدم لحساب التحليلات.",
        "parameters": {
            "type": "object",
            "properties": {
                "funnel_id": {"type": "string"},
                "event_type": {"type": "string", "enum": ["visit", "optin", "purchase", "upsell_purchase"]},
                "page_id": {"type": "string"},
                "value": {"type": "number", "description": "القيمة المالية إن وجدت (عند الشراء)"},
            },
            "required": ["funnel_id", "event_type"],
        },
        "func": core.record_event,
    },
    {
        "name": "get_funnel_analytics",
        "description": "يرجّع إحصائيات الفنل: عدد الزيارات، نسبة التسجيل، نسبة التحويل، والإيرادات.",
        "parameters": {
            "type": "object",
            "properties": {"funnel_id": {"type": "string"}},
            "required": ["funnel_id"],
        },
        "func": core.get_funnel_analytics,
    },
    {
        "name": "publish_funnel",
        "description": "ينشر الفنل: يولّد صفحات HTML فعلية لكل صفحة داخل الفنل ويحفظها كملفات جاهزة.",
        "parameters": {
            "type": "object",
            "properties": {"funnel_id": {"type": "string"}},
            "required": ["funnel_id"],
        },
        "func": core.publish_funnel,
    },
]

TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


def to_openai_functions() -> list:
    """يحوّل TOOLS إلى صيغة Function Calling المتوافقة مع OpenAI."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in TOOLS
    ]


def call_tool(name: str, arguments: dict):
    """منفذ عام يستدعي أي أداة بالاسم — تستخدمه طبقتا MCP و OpenAI API."""
    if name not in TOOLS_BY_NAME:
        raise ValueError(f"أداة غير معروفة: {name}")
    return TOOLS_BY_NAME[name]["func"](**arguments)
