import subprocess
import json

def test_api_query():
    """Test that the agent uses query_api for database count questions."""

    result = subprocess.run(
        ["uv", "run", "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    assert "tool_calls" in data, "Response should contain tool_calls"
    
    # Verify query_api was used
    tools_used = [tc.get("tool") for tc in data["tool_calls"]]
    assert "query_api" in tools_used, f"Expected query_api tool, got: {tools_used}"
    
    # Verify answer contains a number
    answer = data.get("answer", "")
    import re
    numbers = re.findall(r"\d+", answer)
    assert len(numbers) > 0, f"Answer should contain a number: {answer}"