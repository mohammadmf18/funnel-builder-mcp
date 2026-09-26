# Funnel Builder — أداة ذكاء اصطناعي لبناء الفنلات التسويقية

نظام بناء فنلات تسويقية (Sales Funnels) يقدر أي نموذج ذكاء اصطناعي يستخدمه كـ "أداة":
يشتغل مع **Claude عبر MCP** ومع **أي نموذج يدعم OpenAI-style Function Calling** (GPT وغيره)
من نفس الكود بالضبط، بدون تكرار.

## الفكرة

```
core.py        ← المنطق الأساسي (قاعدة بيانات SQLite + توليد صفحات HTML)
schemas.py      ← مصدر واحد لتعريف الأدوات (اسم + وصف + مخطط JSON)
mcp_server.py   ← يعرض نفس الأدوات لـ Claude عبر MCP
api_server.py   ← يعرض نفس الأدوات كـ REST API بصيغة OpenAI Function Calling
templates.py    ← يولّد صفحات HTML فعلية عند النشر
```

كل أداة (create_funnel, add_landing_page...) معرّفة مرة وحدة في `schemas.py`،
وتُستخدم من الاثنين (MCP و OpenAI) — عشان لو غيّرت أو ضفت أداة، تنعكس بكل مكان تلقائيًا.

## الأدوات المتاحة

| الأداة | الوظيفة |
|---|---|
| `create_funnel` | ينشئ فنل جديد |
| `list_funnels` | يسرد كل الفنلات |
| `get_funnel` | يجيب تفاصيل فنل مع صفحاته |
| `delete_funnel` | يحذف فنل |
| `add_landing_page` | يضيف صفحة هبوط |
| `add_optin_page` | يضيف صفحة تحصيل إيميلات |
| `add_sales_page` | يضيف صفحة عرض/بيع |
| `add_checkout_page` | يضيف صفحة دفع |
| `add_upsell_page` | يضيف عرض إضافي بعد الشراء |
| `add_thankyou_page` | يضيف صفحة شكر |
| `update_page` | يحدّث محتوى صفحة موجودة |
| `connect_email_sequence` | يربط تسلسل إيميلات تلقائي |
| `record_event` | يسجّل حدث (زيارة/تسجيل/شراء) للتحليلات |
| `get_funnel_analytics` | يرجّع إحصائيات الفنل |
| `publish_funnel` | ينشر الفنل كصفحات HTML فعلية |

## التركيب

```bash
python -m venv venv
source venv/bin/activate      # على ويندوز: venv\Scripts\activate
pip install -r requirements.txt
```

## الاستخدام مع Claude (عن طريق MCP)

1. افتح إعدادات Claude Desktop: `claude_desktop_config.json`
2. ضيف السيرفر:

```json
{
  "mcpServers": {
    "funnel-builder": {
      "command": "python",
      "args": ["/المسار-الكامل-للمشروع/funnel-builder-mcp/mcp_server.py"]
    }
  }
}
```

3. أعد تشغيل Claude Desktop. الآن تقدر تقول لـ Claude مباشرة:
   > "ابنيلي فنل لبيع كورس أونلاين، صفحة هبوط، صفحة تحصيل إيميلات، وصفحة دفع"

## الاستخدام مع OpenAI (GPT) — طريقتين

**أ) مباشرة بدون سيرفر (أسهل للتجربة):**

```bash
export OPENAI_API_KEY="sk-..."
python example_openai_client.py
```

**ب) عن طريق REST API (لو تبي تفصل السيرفر عن العميل):**

```bash
uvicorn api_server:app --reload --port 8000
```

ثم من أي عميل:
```bash
curl http://localhost:8000/tools                  # قائمة الأدوات
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "create_funnel", "arguments": {"name": "فنل تجريبي", "goal": "بيع كورس"}}'
```

## قاعدة البيانات

كل البيانات تُخزّن في `funnels.db` (SQLite) — يُنشأ تلقائيًا أول مرة تشغّل فيها أي سيرفر.
تقدر تغيّر مكانه بمتغيّر البيئة `FUNNEL_DB_PATH`.

## النشر (Publish)

عند استدعاء `publish_funnel`، يتولّد مجلد `generated_sites/{funnel_id}/` فيه ملف HTML فعلي
لكل صفحة داخل الفنل (landing.html, optin.html...)، جاهزة للرفع على أي استضافة.

## التوسعة

- إضافة أداة جديدة = دالة جديدة في `core.py` + سطر واحد في `schemas.py` (`TOOLS`).
- تلقائيًا تظهر في MCP و OpenAI API بدون أي كود إضافي.
- لدمج بوابة دفع حقيقية (Stripe) أو خدمة إيميل حقيقية (Mailchimp)، أضف الاستدعاء الفعلي
  داخل `add_checkout_page` / `connect_email_sequence` في `core.py`.

## الترخيص

MIT
