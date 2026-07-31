from pathlib import Path


# Tools run as standalone scripts, so importing a top-level project module is
# unreliable: Python places ``tools/`` rather than the repository root first.
ROOT = Path(__file__).resolve().parents[1]

def python_files():
    for f in ROOT.rglob("*.py"):
        p = str(f)
        if any(x in p for x in (
            "venv",
            "__pycache__",
            ".git",
            "legacy",
            "build",
            "dist"
        )):
            continue
        yield f
