from app_paths import ROOT

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
