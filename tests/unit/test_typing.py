import subprocess
import sys

def test_mypy():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            "mypy.ini",
            "kiteconnect",
        ],
        check=False,
    )
