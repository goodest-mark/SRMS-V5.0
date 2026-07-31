import py_compile

from common import python_files


ok = True
for file in python_files():
    try:
        py_compile.compile(str(file), doraise=True)
    except py_compile.PyCompileError as error:
        print(error)
        ok = False

print("SUCCESS" if ok else "FAILED")
