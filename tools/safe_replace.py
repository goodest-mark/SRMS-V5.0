from pathlib import Path
import subprocess

ROOT = Path(".")
SKIP = {"venv",".git","__pycache__","build","dist","legacy"}

def files():
    for f in ROOT.rglob("*.py"):
        if any(x in f.parts for x in SKIP):
            continue
        yield f

old = input("Find : ")
new = input("Replace : ")

changed = 0

for f in files():

    text = f.read_text()

    if old not in text:
        continue

    backup = f.with_suffix(".py.bak")
    backup.write_text(text)

    text = text.replace(old,new)

    f.write_text(text)

    r = subprocess.run(
        ["python","-m","py_compile",str(f)],
        capture_output=True
    )

    if r.returncode != 0:
        print("FAILED:",f)
        backup.replace(f)
    else:
        backup.unlink()
        changed += 1
        print("OK:",f)

print()
print("Updated",changed,"files safely.")
