import sys
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv(".env.agent.secret")
load_dotenv(".env.docker.secret")

API_KEY = os.getenv("LLM_API_KEY")
API_BASE = os.getenv("LLM_API_BASE")
MODEL = os.getenv("LLM_MODEL")
LMS_API_KEY = os.getenv("LMS_API_KEY")
AGENT_API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE
)

PROJECT_ROOT = Path.cwd()

tool_calls_log = []
source_reference = "unknown"


def safe_path(path):
    p = (PROJECT_ROOT / path).resolve()
    # Use case-insensitive comparison for Windows compatibility
    if not str(p).lower().startswith(str(PROJECT_ROOT).lower()):
        raise Exception("Access outside project directory")
    return p


def list_files(path):
    global source_reference
    try:
        p = safe_path(path)

        if not p.exists():
            return "Path does not exist"

        source_reference = path
        entries = os.listdir(p)
        return "\n".join(entries)

    except Exception as e:
        return str(e)


def read_file(path):
    global source_reference
    try:
        p = safe_path(path)

        if not p.exists():
            return "File does not exist"

        source_reference = path
        return p.read_text()

    except Exception as e:
        return str(e)


def query_api(method, path, body=None, auth=True):
    """Call the backend API with authentication.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path (e.g., /items/)
        body: Optional JSON request body as string
        auth: Whether to include Authorization header (default True)

    Returns:
        JSON string with status_code and body
    """
    try:
        url = f"{AGENT_API_BASE_URL}{path}"
        headers = {
            "Content-Type": "application/json"
        }
        
        if auth and LMS_API_KEY:
            headers["Authorization"] = f"Bearer {LMS_API_KEY}"

        if body:
            response = requests.request(method, url, headers=headers, data=body)
        else:
            response = requests.request(method, url, headers=headers)

        return json.dumps({
            "status_code": response.status_code,
            "body": response.text
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


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
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the backend API. Use for live data like item counts, analytics, status codes. ALWAYS use for questions about counts, analytics, or API status codes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "description": "HTTP method (GET, POST, PUT, DELETE)"},
                    "path": {"type": "string", "description": "API endpoint path (e.g., /items/)"},
                    "body": {"type": "string", "description": "Optional JSON request body as string"},
                    "auth": {"type": "boolean", "description": "Include Authorization header (default true). Set false to test unauthenticated access."}
                },
                "required": ["method", "path"]
            }
        }
    }
]


def execute_tool(name, args):

    if name == "list_files":
        result = list_files(**args)

    elif name == "read_file":
        result = read_file(**args)

    elif name == "query_api":
        result = query_api(**args)

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
                "You are a system agent. Answer questions using tools efficiently.\n\n"
                "Tools: list_files, read_file, query_api\n\n"
                "Tool Selection (CRITICAL):\n"
                "- Wiki/documentation questions -> list_files('wiki'), then read_file on specific file\n"
                "- Backend/router questions -> list_files('backend/app/routers'), then answer\n"
                "- Code/framework questions -> read_file('pyproject.toml')\n"
                "- Status code questions -> query_api with auth=false for 'without auth'\n"
                "- Count/data/analytics -> query_api\n"
                "- Architecture -> read docker-compose.yml, Dockerfile\n\n"
                "Rules:\n"
                "- Use full paths: 'backend/app/routers' not just 'routers'\n"
                "- Maximum 3-4 tool calls, then answer\n"
                "- Include exact keywords from files in answer\n"
                "- Set source to the last file read\n"
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
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                result = execute_tool(name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })

                tool_count += 1

            continue

        else:
            answer = msg.content or ""

            output = {
                "answer": answer,
                "source": source_reference,
                "tool_calls": tool_calls_log
            }

            print(json.dumps(output))

            return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "answer": f"Error: {str(e)}",
            "source": "unknown",
            "tool_calls": tool_calls_log
        }), file=sys.stdout)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)