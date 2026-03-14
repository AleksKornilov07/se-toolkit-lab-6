import subprocess
import json

def test_read_file_tool():

    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    assert "answer" in data
    assert "source" in data