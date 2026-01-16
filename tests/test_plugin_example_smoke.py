import os
import subprocess
import sys
from pathlib import Path


def test_plugin_example_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "examples" / "plugins" / "basic_plugins.py"

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_pythonpath = str(repo_root / "src")
    env["PYTHONPATH"] = (
        f"{repo_pythonpath}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else repo_pythonpath
    )
    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Hello, Ada!" in result.stdout
    assert "Goodbye, Linus." in result.stdout
