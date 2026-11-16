"""Simple, escaped static HTML prototypes for funnel pages."""
from html import escape

BASE_STYLE = """
<style>
body {font-family:system-ui,Tahoma,Arial,sans-serif;max-width:760px;margin:56px auto;padding:0 20px;background:#f5f6fa;color:#171923;direction:rtl;text-align:right}
.card{background:white;padding:32px;border-radius:16px;box-shadow:0 5px 25px #10182812}
h1{font-size:2rem} .sub{color:#475467;line-height:1.7}.cta{display:inline-block;padding:13px 22px;background:#4338ca;color:white;border-radius:9px;text-decoration:none;font-weight:700}
.price{font-size:1.6rem;font-weight:700;margin:22px 0} li{margin:8px 0}
input{padding:11px;max-width:100%;border:1px solid #ccc;border-radius:8px}
.notice{background:#fff7ed;padding:12px;border-radius:8px;color:#9a3412;font-size:.9rem}
</style>
"""

def clean(value):
    return escape(str(value if value is not None else ""), quote=True)

def _wrap(title, body):
    return f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{clean(title)}</title>{BASE_STYLE}</head><body><main class="card">{body}</main></body></html>'

def render_page_html(funnel_name, page):
    ptype = page["type"]
    c = page.get("content") or {}
    headline = clean(page.get("headline") or funnel_name)
    if ptype == "landing":
        body = f'<h1>{headline}</h1><p class="sub">{clean(c.get("subheadline"))}</p><a class="cta" href="optin.html">{clean(c.get("cta_text") or "ابدأ الآن")}</a>'
    elif ptype == "optin":
        body = f'<h1>{headline}</h1><p class="sub">{clean(c.get("offer_description"))}</p><p>{clean(c.get("incentive"))}</p><label>البريد الإلكتروني <input type="email" disabled placeholder="example@email.com"></label><p class="notice">نموذج تجريبي: ربط جمع الإيميلات غير متوفر.</p>'
    elif ptype == "sales":
        benefits = "".join(f'<li>{clean(x)}</li>' for x in (c.get("benefits") or []))
        body = f'<h1>{headline}</h1><ul>{benefits}</ul><div class="price">{clean(c.get("price"))} {clean(c.get("currency"))}</div><a class="cta" href="checkout.html">عرض صفحة الدفع التجريبية</a>'
    elif ptype == "checkout":
        body = f'<h1>{headline}</h1><div class="price">{clean(c.get("price"))} {clean(c.get("currency"))}</div><p class="notice">صفحة توضيحية فقط؛ لا توجد معالجة مدفوعات.</p>'
    elif ptype == "upsell":
        body = f'<h1>{headline}</h1><div class="price">{clean(c.get("price"))} {clean(c.get("currency"))}</div><p class="notice">عرض إضافي تجريبي؛ لا يمكن الشراء من هذه الصفحة.</p>'
    else:
        body = f'<h1>{headline}</h1><p class="sub">{clean(c.get("message") or "نشكرك على ثقتك.")}</p>'
    return _wrap(page.get("headline") or funnel_name, body)
