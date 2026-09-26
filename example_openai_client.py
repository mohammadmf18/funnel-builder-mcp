"""
example_openai_client.py
مثال يوضح كيف يستخدم GPT (عبر OpenAI SDK) أدوات الفنل بيلدر مباشرة،
بدون المرور على api_server.py — عن طريق استدعاء schemas.call_tool محليًا.

قبل التشغيل:
    pip install openai
    export OPENAI_API_KEY="sk-..."

تشغيل:
    python example_openai_client.py
"""

import json
import os
from openai import OpenAI

import schemas

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")


def run(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    tools = schemas.to_openai_functions()

    for _ in range(12):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print("\n--- الرد النهائي ---")
            print(msg.content)
            return

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            print(f"[تنفيذ أداة] {name}")

            try:
                arguments = json.loads(tool_call.function.arguments)
                result = schemas.call_tool(name, arguments)
            except Exception as e:
                result = {"error": str(e)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("تجاوز التنفيذ 12 جولة من استدعاء الأدوات")


if __name__ == "__main__":
    run(
        "ابنيلي فنل اسمه 'أخبار التسويق الرقمي'، هدفه جمع الاشتراكات. "
        "ضيف صفحة هبوط ثم صفحة تسجيل إيميل ثم صفحة شكر، وانشر الفنل. "
        "وضّح أن تشغيل api_server مطلوب لفتح الرابط وحفظ الاشتراكات."
    )
