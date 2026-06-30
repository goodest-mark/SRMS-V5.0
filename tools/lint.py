import compileall

ok = compileall.compile_dir(".",quiet=1)

print("SUCCESS" if ok else "FAILED")
