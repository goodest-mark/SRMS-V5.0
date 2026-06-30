from common import python_files

OLD = input("Replace: ").strip()
NEW = input("With: ").strip()

count = 0

for file in python_files():

    text = file.read_text(encoding="utf-8")

    if OLD not in text:
        continue

    text = text.replace(OLD, NEW)

    file.write_text(text, encoding="utf-8")

    count += 1

print(f"Updated {count} files.")
