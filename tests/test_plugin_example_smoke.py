import subprocess
import sys
from pathlib import Path


def test_plugin_example_smoke() -> None:
    script_path = Path(__file__).resolve().parents[1] / "examples" / "plugins" / "basic_plugins.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Hello, Ada!" in result.stdout
    assert "Goodbye, Linus." in result.stdout
