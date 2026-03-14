# Task 2 Plan — Documentation Agent

## Goal
Extend the agent from Task 1 so it can read project documentation using tools.

The agent will implement an agentic loop:
1. Send the user question and tool schemas to the LLM.
2. If the LLM returns tool_calls, execute them.
3. Append the tool results as messages.
4. Send the updated conversation back to the LLM.
5. Repeat until the model returns a final answer.

Maximum 10 tool calls per request.

## Tools

### list_files
Lists files and directories.

Parameters:
- path (string)

Returns:
newline-separated list of files.

Security:
Path must stay inside the project directory.

### read_file
Reads a file from the repository.

Parameters:
- path (string)

Returns:
file content.

Security:
Prevent `../` traversal.

## Agentic loop

The loop:

User question → LLM → tool_calls? → execute tools → send result → repeat.

Stop conditions:
- LLM returns text message
- 10 tool calls reached

## Output JSON

The agent prints:

{
  "answer": "...",
  "source": "...",
  "tool_calls": []
}

## System prompt strategy

The model should:
1. Use list_files to discover wiki files
2. Use read_file to inspect relevant files
3. Extract the answer
4. Return the source path and section anchor

Example source:

wiki/git-workflow.md#resolving-merge-conflicts