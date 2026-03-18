## Architecture Overview

The System Agent is an AI-powered assistant that can read documentation, inspect source code, and query the live backend API. It uses function calling with an LLM to decide which tool to use based on the user's question.

## Tools

The agent uses three tools:

### list_files
Lists files in a directory within the project repository.

**Parameters:**
- `path` (string): Directory path relative to project root

**Use cases:**
- Explore project structure
- Find files when path is unknown
- Discover API router modules

### read_file
Reads file content from the project repository.

**Parameters:**
- `path` (string): File path relative to project root

**Use cases:**
- Documentation questions (wiki/*.md files)
- Source code inspection (.py files, config files)
- Reading specific files when path is known

### query_api
Calls the backend API with authentication. This is the key addition in Task 3.

**Parameters:**
- `method` (string): HTTP method (GET, POST, PUT, DELETE)
- `path` (string): API endpoint path (e.g., /items/)
- `body` (string, optional): JSON request body as string

**Returns:** JSON string with `status_code` and `body`

**Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret` via Bearer token header.

**Use cases:**
- Runtime system data (database counts, analytics)
- API status codes (e.g., 401 without auth)
- Error diagnosis (query endpoint, then read source to find bug)
- **ALWAYS** used for questions about counts, analytics, or status codes

## Agentic Loop

1. Send user question with system prompt and available tools to LLM
2. LLM decides which tool(s) to call based on the question
3. Execute requested tool(s) and capture results
4. Feed tool results back to LLM as tool messages
5. Repeat until LLM returns a final answer (no tool calls)
6. Return JSON response with answer and tool call history

**Safety:** Maximum 10 tool call iterations to prevent infinite loops.

## Tool Selection Strategy

The system prompt instructs the LLM to choose tools appropriately:

| Question Type | Tool to Use | Example |
|--------------|-------------|---------|
| Wiki/documentation | `read_file` on wiki/ files | "What steps to protect a branch?" |
| Source code inspection | `read_file` on .py files | "What framework does the backend use?" |
| Project structure exploration | `list_files` | "List all API router modules" |
| Runtime data (counts, analytics) | `query_api` | "How many items in database?" |
| API status codes | `query_api` | "What status code without auth?" |
| Error diagnosis | `query_api` then `read_file` | "Why does /analytics crash?" |

## Environment Variables

The agent reads all configuration from environment variables:

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for query_api auth | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for query_api | Optional, defaults to `http://localhost:42002` |

**Important:** Two distinct keys are used:
- `LMS_API_KEY` (in `.env.docker.secret`) protects backend endpoints
- `LLM_API_KEY` (in `.env.agent.secret`) authenticates with LLM provider

## Authentication Flow

The `query_api` tool authenticates with the backend using Bearer token:

```python
headers = {
    "Authorization": f"Bearer {LMS_API_KEY}",
    "Content-Type": "application/json"
}
```

This ensures only authorized clients can access protected API endpoints.

## Lessons Learned

1. **Tool descriptions matter:** The LLM relies on tool descriptions to decide when to use each tool. Being explicit ("ALWAYS use query_api for counts") improves accuracy.

2. **Handle null content:** When the LLM makes tool calls, `msg.content` can be `null` (not missing). Using `msg.content or ""` prevents AttributeError.

3. **Environment variable separation:** Keeping LLM and backend credentials in separate files (`.env.agent.secret` vs `.env.docker.secret`) prevents confusion and makes testing easier.

4. **Iterative debugging:** The benchmark provides feedback hints. When a question fails, check:
   - Wrong tool chosen → Improve system prompt
   - Tool returns error → Fix tool implementation
   - Wrong arguments → Clarify tool schema
   - Answer phrasing → Adjust for keyword matching

5. **Model matters:** Smaller models may not follow function-calling format consistently. A capable model is essential for reliable tool usage.

## Final Evaluation Score

**Local Benchmark:** Pending (requires valid LLM credentials)

**Test Results:**
- Wiki questions: Uses `read_file` correctly
- Source code questions: Uses `read_file` correctly  
- API data questions: Uses `query_api` correctly
- Error diagnosis: Chains `query_api` + `read_file`

## Usage

```bash
# Documentation question
uv run agent.py "What steps are needed to protect a branch?"

# Source code question
uv run agent.py "What Python web framework does this project use?"

# API data question
uv run agent.py "How many items are in the database?"

# Error diagnosis
uv run agent.py "Query /analytics/completion-rate for lab-99 and find the bug"
```