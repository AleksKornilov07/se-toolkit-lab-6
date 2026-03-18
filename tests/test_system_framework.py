import subprocess
import json

def test_framework_question():
    """Test that the agent uses read_file for source code inspection questions."""

    result = subprocess.run(
        ["uv", "run", "agent.py", "What Python web framework does this project use?"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    assert "tool_calls" in data, "Response should contain tool_calls"
    
    # Verify read_file was used (not query_api)
    tools_used = [tc.get("tool") for tc in data["tool_calls"]]
    assert "read_file" in tools_used, f"Expected read_file tool, got: {tools_used}"
    
    # Verify answer mentions FastAPI
    answer = data.get("answer", "").lower()
    assert "fastapi" in answer, f"Answer should mention FastAPI: {answer}"