"""Escaped Arabic HTML pages. Public forms use the same-origin funnel API."""
from html import escape

BASE_STYLE = """
<style>
*{box-sizing:border-box} body{font-family:Tahoma,Arial,sans-serif;max-width:720px;margin:60px auto;padding:0 20px;background:#fafafa;color:#1a1a1a;direction:rtl;text-align:right;line-height:1.7}
h1{font-size:2rem;line-height:1.4}.sub{color:#555;font-size:1.1rem}.cta{display:inline-block;padding:14px 28px;background:#111;color:#fff;text-decoration:none;border:0;border-radius:8px;font:inherit;cursor:pointer}.cta:disabled{opacity:.5;cursor:wait}.price{font-size:1.8rem;font-weight:bold;margin:1em 0}.card{background:#fff;padding:30px;border-radius:12px;box-shadow:0 1px 6px #0001}input{font:inherit;padding:12px;width:100%;margin:10px 0 20px;border-radius:6px;border:1px solid #777}label{display:block}.notice{padding:12px;background:#f3f3f3;border-radius:6px}#result{min-height:1.7em}@media(max-width:480px){body{margin:24px auto}.card{padding:20px}h1{font-size:1.6rem}}
</style>
"""


def text(value):
    return escape(str(value), quote=True)


def render_page_html(funnel_name: str, page: dict, next_url: str | None = None) -> str:
    ptype = page["type"]
    content = page.get("content", {})
    headline = text(page.get("headline") or funnel_name)
    body = f"<h1>{headline}</h1>"

    def cta(label):
        return f'<a class="cta" href="{text(next_url)}">{text(label)}</a>' if next_url else '<p class="notice">هذه آخر صفحة في المسار.</p>'

    if ptype == "landing":
        body += f'<p class="sub">{text(content.get("subheadline", ""))}</p>'
        body += cta(content.get("cta_text", "ابدأ الآن"))
    elif ptype == "optin":
        body += f'''<p class="sub">{text(content.get("offer_description", ""))}</p>
<p><strong>{text(content.get("incentive", ""))}</strong></p>
<form id="lead-form" data-endpoint="/sites/{text(page['funnel_id'])}/leads" data-page-id="{text(page['id'])}">
<label for="email">بريدك الإلكتروني</label>
<input id="email" name="email" type="email" autocomplete="email" maxlength="254" required dir="ltr">
<button class="cta" type="submit">سجّل الآن</button>
<p id="result" role="status" aria-live="polite"></p>
</form><noscript>فعّل JavaScript لإرسال بيانات التسجيل.</noscript>
<script src="funnel.js" defer></script>'''
    elif ptype == "sales":
        body += "<ul>" + "".join(f"<li>{text(item)}</li>" for item in content.get("benefits", [])) + "</ul>"
        body += f'<div class="price">{text(content.get("price", ""))} {text(content.get("currency", ""))}</div>'
        body += cta("متابعة الشراء")
    elif ptype in {"checkout", "upsell"}:
        body += f'<p>{text(content.get("product_name", ""))}</p><div class="price">{text(content.get("price", ""))} {text(content.get("currency", ""))}</div>'
        # Defense in depth for direct renderer use; core also validates this URL.
        from validation import validate_content
        validate_content(ptype, content)
        url = content.get("checkout_url")
        if url:
            body += f'<a class="cta" href="{text(url)}" rel="noreferrer">الانتقال إلى الدفع الآمن</a>'
        else:
            body += '<p class="notice">الدفع غير متاح حاليًا؛ لم يتم إعداد رابط الدفع.</p>'
    else:
        body += f'<p class="sub">{text(content.get("message", "نشكرك على ثقتك."))}</p>'
    return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{headline}</title>{BASE_STYLE}</head>
<body><main class="card">{body}</main></body></html>'''
