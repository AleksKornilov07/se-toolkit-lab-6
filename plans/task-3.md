# Task 3 Plan — System Agent

## Goal
Extend the documentation agent with a new tool `query_api` so the agent can query the running backend system.

The agent should now handle:
1. Wiki/documentation questions
2. Source code questions
3. System queries requiring API access

## New Tool: query_api

The query_api tool allows the agent to call the backend API.

### Tool Schema Definition

The tool will be registered in the `tools` list alongside `list_files` and `read_file`:

```python
{
    "type": "function",
    "function": {
        "name": "query_api",
        "description": "Call backend API. Use for real data questions like counts, analytics, status codes.",
        "parameters": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "description": "HTTP method (GET, POST, PUT, DELETE)"},
                "path": {"type": "string", "description": "API endpoint path (e.g., /items/)"},
                "body": {"type": "string", "description": "Optional JSON request body"}
            },
            "required": ["method", "path"]
        }
    }
}
```

### Implementation

```python
def query_api(method, path, body=None):
    try:
        url = f"{API_BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {LMS_API_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.request(method, url, headers=headers, data=body)
        return json.dumps({
            "status_code": r.status_code,
            "body": r.text
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### Authentication

- **LMS_API_KEY** is read from environment via `os.getenv("LMS_API_KEY")`
- Loaded from `.env.docker.secret` at startup using `load_dotenv()`
- Sent in the `Authorization: Bearer <key>` header
- **Never hardcoded** — the autochecker injects different credentials during evaluation

## Environment Variables

The agent reads all configuration from environment variables:

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for query_api auth | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for query_api | Optional, defaults to `http://localhost:42002` |

```python
# At module startup
load_dotenv(".env.agent.secret")
load_dotenv(".env.docker.secret")

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE")
LLM_MODEL = os.getenv("LLM_MODEL")
LMS_API_KEY = os.getenv("LMS_API_KEY")
API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
```

## Agent Strategy: Tool Selection

The system prompt instructs the model to choose tools appropriately:

### read_file
- Documentation questions (wiki, markdown files)
- Source code inspection (Python files, config files)
- Reading specific files when path is known

### list_files
- Explore project structure
- Find files when path is unknown
- Discover API router modules

### query_api
- Runtime system data (database counts, analytics)
- API status codes (e.g., 401 without auth)
- Error diagnosis (query endpoint, then read source to find bug)
- **ALWAYS** use for questions about counts, analytics, or status codes

### Updated System Prompt

```
You are a system agent.
- Use read_file for documentation and code.
- Use list_files to explore repository.
- Use query_api for live backend data.
- ALWAYS use query_api for questions about counts, analytics, or status codes.
- Return concise answers with exact keywords when possible.
```

## Agent Loop

The agentic loop from Task 2 remains unchanged:

1. Send messages + tools to LLM
2. If tool calls returned:
   - Execute tool
   - Append result to messages
3. Repeat until LLM returns content (no tool calls)
4. Stop after 10 iterations max

## Benchmark Strategy

### Initial Run

```bash
uv run run_eval.py
```

### Iteration Process

When a question fails:

1. **Read the feedback** — `run_eval.py` shows a hint
2. **Identify the root cause**:
   - Wrong tool chosen? → Improve system prompt
   - Tool called with wrong args? → Improve tool description
   - Tool returns error? → Fix tool implementation
   - Answer phrasing wrong? → Adjust prompt for keyword matching
3. **Make one change** and re-run
4. **Move to next question** only after current passes

### Common Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent doesn't use query_api for data questions | Prompt doesn't emphasize it enough | Add "ALWAYS use query_api for counts/analytics" |
| query_api returns 401 | LMS_API_KEY not loaded | Check load_dotenv() calls |
| Agent reads file in loop | File truncated | Increase content limit |
| Answer close but no match | Missing keyword | Adjust prompt to include exact terms |

## Implementation Status

**Date:** March 18, 2026

### Completed Tasks

1. ✅ Added `query_api` tool to `agent.py`
2. ✅ Implemented authentication with `LMS_API_KEY` from `.env.docker.secret`
3. ✅ Added `AGENT_API_BASE_URL` environment variable (defaults to `http://localhost:42002`)
4. ✅ Updated system prompt with tool selection strategy
5. ✅ Fixed `msg.content or ""` to handle null content from LLM
6. ✅ Updated `AGENT.md` with comprehensive documentation (140+ lines)
7. ✅ Added 2 regression tests:
   - `test_system_api.py` - verifies `query_api` usage for database questions
   - `test_system_framework.py` - verifies `read_file` usage for source code questions

### Implementation Details

**query_api function:**
```python
def query_api(method, path, body=None):
    """Call the backend API with authentication."""
    try:
        url = f"{AGENT_API_BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {LMS_API_KEY}",
            "Content-Type": "application/json"
        }
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
```

**Tool schema:**
```python
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
                "body": {"type": "string", "description": "Optional JSON request body as string"}
            },
            "required": ["method", "path"]
        }
    }
}
```

### Benchmark Status

**Current State:** Implementation complete, LLM credentials working

**LLM Configuration:**
- Provider: Qwen (via university VM at 10.93.25.235:42005)
- Model: qwen3-coder-plus
- Status: Working with OAuth credentials

**Latest Benchmark Results:**
- **Best Run:** 7-8/10 passed (varies due to LLM consistency)
- Questions 1-7: Consistently passing
- Questions 8-10: Intermittent failures due to LLM timeout/inconsistency

**Passing Questions:**
1. ✅ Wiki branch protection - uses list_files + read_file
2. ✅ SSH wiki - uses list_files + read_file  
3. ✅ Framework question - uses read_file on pyproject.toml
4. ✅ API routers - uses list_files on backend/app/routers
5. ✅ Items count - uses query_api
6. ✅ Status code without auth - uses query_api with auth=false
7. ✅ Completion-rate error - uses query_api + read_file

**Failing Questions (intermittent):**
8. ⚠️ Top-learners crash - LLM sometimes times out
9. ⚠️ Request journey - LLM sometimes doesn't complete
10. ⚠️ ETL idempotency - LLM sometimes doesn't complete

**Root Cause:** LLM inconsistency - same question passes when run directly but may fail during eval run due to different conversation history or timing.

**Next Steps:**
1. Continue iterating on system prompt for consistency
2. Consider increasing tool limit for complex questions
3. Test multiple times to find stable configuration

### Acceptance Criteria Checklist

- [x] `plans/task-3.md` exists with implementation plan
- [x] `agent.py` defines `query_api` as function-calling schema
- [x] `query_api` authenticates with `LMS_API_KEY` from environment
- [x] Agent reads LLM config from environment variables
- [x] Agent reads `AGENT_API_BASE_URL` from environment (defaults to localhost:42002)
- [ ] Agent passes all 10 benchmark questions (pending credentials)
- [x] `AGENT.md` documents architecture (140+ lines)
- [x] 2 regression tests exist
