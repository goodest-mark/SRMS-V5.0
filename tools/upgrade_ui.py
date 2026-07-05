from pathlib import Path
import subprocess

ROOT = Path(".")

SKIP = {
    "venv",
    ".git",
    "__pycache__",
    "legacy",
    "dist",
    "build"
}

REPLACEMENTS = [
    (
        "Table(",
        "Table(",
        "from ui.tables import Table"
    ),
    (
        "PrimaryButton(",
        "PrimaryButton(",
        "from ui.buttons import PrimaryButton"
    ),
]

def should_skip(path):
    return any(x in path.parts for x in SKIP)

def add_import(text, imp):
    if imp in text:
        return text

    lines = text.splitlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if (
            line.startswith("import ")
            or line.startswith("from ")
            or line.strip() == ""
        ):
            idx += 1
        else:
            break

    lines.insert(idx, imp)
    return "\n".join(lines)

updated = 0

for f in ROOT.rglob("*.py"):

    if should_skip(f):
        continue

    txt = f.read_text(encoding="utf8")

    original = txt

    for old,new,imp in REPLACEMENTS:
        if old in txt:
            txt = txt.replace(old,new)
            txt = add_import(txt,imp)

    if txt == original:
        continue

    backup = f.with_suffix(".py.bak")
    backup.write_text(original,encoding="utf8")

    f.write_text(txt,encoding="utf8")

    r = subprocess.run(
        ["python","-m","py_compile",str(f)],
        capture_output=True
    )

    if r.returncode:
        print("FAILED:",f)
        backup.replace(f)
    else:
        backup.unlink()
        updated += 1
        print("OK:",f)

print()
print("Updated",updated,"files safely.")
