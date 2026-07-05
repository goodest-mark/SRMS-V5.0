from common import python_files

for file in python_files():

    lines = file.read_text(encoding="utf-8").splitlines()

    seen = set()

    out = []

    for line in lines:

        if line.startswith("import ") or line.startswith("from "):

            if line in seen:
                continue

            seen.add(line)

        out.append(line)

    file.write_text("\n".join(out)+"\n",encoding="utf-8")

print("Duplicate imports removed.")
