# Task 1 Plan — Call an LLM from Code

## Goal
Create a Python CLI agent (`agent.py`) that:
1. Accepts a user question as a command line argument
2. Sends the question to an LLM using the OpenAI-compatible Chat Completions API
3. Returns a structured JSON response:
   {
     "answer": "...",
     "tool_calls": []
   }

## LLM Provider
Provider: Qwen Code API  
Model: qwen3-coder-plus

Reasons:
- OpenAI compatible API
- Free daily quota (1000 requests)
- No credit card required
- Works from Russia

Configuration will be stored in `.env.agent.secret`:
- LLM_API_KEY
- LLM_API_BASE
- LLM_MODEL

## Agent Architecture

agent.py will:

1. Parse CLI arguments
2. Load environment variables from `.env.agent.secret`
3. Create an OpenAI client pointing to the configured base URL
4. Send the question to the model
5. Extract the model response
6. Output JSON to stdout

Debug logging goes to stderr.

## Response format

Output:

{
  "answer": "LLM response text",
  "tool_calls": []
}

Rules:
- Valid JSON only
- Printed as a single line
- No extra logs in stdout

## Timeout
The request must complete within 60 seconds.

## Testing

One regression test:

tests/test_agent.py

Test will:
1. Run `agent.py` via subprocess
2. Capture stdout
3. Parse JSON
4. Verify fields:
   - answer
   - tool_calls

## Files created

plans/task-1.md  
agent.py  
AGENT.md  
tests/test_agent.py