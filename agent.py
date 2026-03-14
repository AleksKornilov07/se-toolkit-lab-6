import sys
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")

API_KEY = os.getenv("LLM_API_KEY")
API_BASE = os.getenv("LLM_API_BASE")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE
)

PROJECT_ROOT = Path.cwd()

tool_calls_log = []


def safe_path(path):
    p = (PROJECT_ROOT / path).resolve()
    if not str(p).startswith(str(PROJECT_ROOT)):
        raise Exception("Access outside project directory")
    return p


def list_files(path):
    try:
        p = safe_path(path)

        if not p.exists():
            return "Path does not exist"

        entries = os.listdir(p)
        return "\n".join(entries)

    except Exception as e:
        return str(e)


def read_file(path):
    try:
        p = safe_path(path)

        if not p.exists():
            return "File does not exist"

        return p.read_text()

    except Exception as e:
        return str(e)


tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    }
]


def execute_tool(name, args):

    if name == "list_files":
        result = list_files(**args)

    elif name == "read_file":
        result = read_file(**args)

    else:
        result = "Unknown tool"

    tool_calls_log.append({
        "tool": name,
        "args": args,
        "result": result
    })

    return result


def main():

    if len(sys.argv) < 2:
        print("Usage: agent.py \"question\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a documentation agent. "
                "Use list_files to explore the wiki folder. "
                "Use read_file to read documentation. "
                "Return the final answer and the source reference."
            )
        },
        {"role": "user", "content": question}
    ]

    tool_count = 0

    while tool_count < 10:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )

        msg = response.choices[0].message

        if msg.tool_calls:

            messages.append(msg)

            for call in msg.tool_calls:

                name = call.function.name
                args = json.loads(call.function.arguments)

                result = execute_tool(name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })

                tool_count += 1

            continue

        else:
            answer = msg.content

            output = {
                "answer": answer,
                "source": "unknown",
                "tool_calls": tool_calls_log
            }

            print(json.dumps(output))

            return


if __name__ == "__main__":
    main()