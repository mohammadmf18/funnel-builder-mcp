"""
templates.py
مولّد HTML بسيط لكل نوع صفحة داخل الفنل. بدون أي اعتماديات خارجية.
"""

BASE_STYLE = """
<style>
  body { font-family: -apple-system, Tahoma, Arial, sans-serif; max-width: 720px; margin: 60px auto; padding: 0 20px; background:#fafafa; color:#1a1a1a; direction: rtl; text-align: right; }
  h1 { font-size: 2rem; margin-bottom: .3em; }
  .sub { color:#555; font-size: 1.1rem; margin-bottom: 1.5em; }
  .cta { display:inline-block; padding: 14px 28px; background:#111; color:#fff; text-decoration:none; border-radius: 8px; font-weight:bold; }
  .price { font-size: 1.8rem; font-weight:bold; margin: 1em 0; }
  ul { line-height: 1.9; }
  .card { background:#fff; padding: 30px; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,.06); }
</style>
"""


def _wrap(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ar"><head><meta charset="utf-8"><title>{title}</title>{BASE_STYLE}</head>
<body><div class="card">{body}</div></body></html>"""


def render_page_html(funnel_name: str, page: dict) -> str:
    ptype = page["type"]
    content = page.get("content", {})
    headline = page.get("headline") or funnel_name

    if ptype == "landing":
        body = f"""
        <h1>{headline}</h1>
        <p class="sub">{content.get('subheadline','')}</p>
        <a class="cta" href="#">{content.get('cta_text','ابدأ الآن')}</a>
        """
    elif ptype == "optin":
        body = f"""
        <h1>{headline}</h1>
        <p class="sub">{content.get('offer_description','')}</p>
        <p><strong>{content.get('incentive','')}</strong></p>
        <input type="email" placeholder="بريدك الإلكتروني" style="padding:10px;width:100%;margin-bottom:10px;border-radius:6px;border:1px solid #ccc">
        <a class="cta" href="#">احصل عليه الآن</a>
        """
    elif ptype == "sales":
        benefits = "".join(f"<li>{b}</li>" for b in content.get("benefits", []))
        body = f"""
        <h1>{headline}</h1>
        <ul>{benefits}</ul>
        <div class="price">{content.get('price','')} {content.get('currency','')}</div>
        <a class="cta" href="#">اشترِ الآن</a>
        """
    elif ptype == "checkout":
        body = f"""
        <h1>{headline}</h1>
        <div class="price">{content.get('price','')} {content.get('currency','')}</div>
        <p>أدخل بيانات الدفع لإتمام الطلب.</p>
        <a class="cta" href="#">تأكيد الدفع</a>
        """
    elif ptype == "upsell":
        body = f"""
        <h1>{headline}</h1>
        <p class="sub">عرض لمرة واحدة فقط بعد الشراء</p>
        <div class="price">{content.get('price','')} {content.get('currency','')}</div>
        <a class="cta" href="#">نعم، أضفه لطلبي</a>
        """
    else:  # thankyou
        body = f"""
        <h1>{headline}</h1>
        <p class="sub">{content.get('message','نشكرك على ثقتك.')}</p>
        """

    return _wrap(headline, body)
