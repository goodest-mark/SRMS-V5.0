import os

os.system("python tools/fix_imports.py")
os.system("python tools/lint.py")
os.system("python app.py")
