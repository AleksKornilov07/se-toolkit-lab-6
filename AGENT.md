## Tools

The agent uses two tools:

### list_files
Lists files in the repository.

### read_file
Reads documentation files.

## Agentic loop

1. Send question to LLM
2. LLM decides tool calls
3. Execute tools
4. Feed results back to LLM
5. Repeat until final answer