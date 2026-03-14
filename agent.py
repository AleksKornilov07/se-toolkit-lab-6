import sys
import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load agent environment
load_dotenv(".env.agent.secret")

API_KEY = os.getenv("LLM_API_KEY")
API_BASE = os.getenv("LLM_API_BASE")
MODEL = os.getenv("LLM_MODEL")

if not API_KEY or not API_BASE or not MODEL:
    print("Missing LLM configuration", file=sys.stderr)
    sys.exit(1)

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE,
)

def main():
    if len(sys.argv) < 2:
        print("Usage: agent.py \"question\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    start = time.time()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question},
            ],
            timeout=60,
        )

        answer = response.choices[0].message.content.strip()

        output = {
            "answer": answer,
            "tool_calls": []
        }

        print(json.dumps(output))

    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        sys.exit(1)

    if time.time() - start > 60:
        print("Timeout exceeded", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()