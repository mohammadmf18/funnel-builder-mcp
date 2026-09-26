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

MODEL = "gpt-4o"


def run(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    tools = schemas.to_openai_functions()

    while True:
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
            arguments = json.loads(tool_call.function.arguments)
            print(f"[تنفيذ أداة] {name}({arguments})")

            try:
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


if __name__ == "__main__":
    run(
        "ابنيلي فنل اسمه 'كورس التسويق الرقمي'، هدفه بيع كورس أونلاين بسعر 499 ريال. "
        "ضيف له صفحة هبوط جذابة، وصفحة تحصيل إيميلات مع هدية كتاب مجاني، "
        "وصفحة بيع تشرح 3 فوائد، وصفحة دفع، ثم انشر الفنل."
    )
