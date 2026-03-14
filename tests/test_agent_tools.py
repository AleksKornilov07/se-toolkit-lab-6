import subprocess
import json

def test_list_files_tool():

    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki?"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    assert "tool_calls" in data