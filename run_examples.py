#!/usr/bin/env python3
"""
Run example .mpy files with minipy and show their outputs.

Usage:
    python run_examples.py                  # runs transpile backend (default) and prints outputs
    python run_examples.py --backend interpret
    python run_examples.py --backend transpile
    python run_examples.py --backend all    # run both backends and compare behavior
    python run_examples.py --emit           # also write generated .generated.py files
    python run_examples.py --quiet          # run tests but suppress printing program outputs (only summary)
"""

import subprocess
import sys
from pathlib import Path

# Each entry: (path, expected_stdout_or_None, expect_nonzero_bool, list_of_substrings_expected_in_output_or_None)
EXAMPLES = [
    ("examples/indentation_test.mpy", "11\n", False, None),
    ("examples/variables_scope.mpy", "10\n5\n", False, None),
    ("examples/conditionals.mpy", "2\n", False, None),
    ("examples/while_sum.mpy", "10\n", False, None),
    ("examples/closure_test.mpy", "8\n", False, None),
    ("examples/fib_recursion.mpy", "8\n", False, None),
    ("examples/function_args.mpy", "5\n", False, None),
    ("examples/expression_precedence.mpy", "7\n9\n", False, None),
    ("examples/print_string.mpy", "Hello, miniPy!\nHello, world\n", False, None),
    # error cases
    ("examples/error_semantic.mpy", None, True, ["undeclared", "semantic error", "semantic errors", "name 'x'"]),
    ("examples/error_runtime.mpy", None, True, ["division by zero", "zerodivisionerror"]),
]

def run_example(path, backend="transpile", emit_py=False):
    cmd = [sys.executable, "-m", "minipy.cli", path]
    if emit_py:
        cmd.append("--emit-py")
    if backend and backend != "transpile":
        cmd.append(f"--backend={backend}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + p.stderr
    return p.returncode, out

def check_result(path, rc, out, expected, expect_nonzero, substrings):
    if expect_nonzero:
        ok = (rc != 0)
        if ok and substrings:
            lower = out.lower()
            ok = any(s.lower() in lower for s in substrings)
        return ok, f"exit={rc}"
    else:
        # Normalize line endings for comparison
        got = out.replace("\r\n", "\n")
        ok = (rc == 0 and got == expected)
        return ok, f"exit={rc}, got={repr(got)}"

def print_example_output(path, out, print_output):
    # Pretty-print the program output when requested
    header = f"--- Output for {path} ---"
    if print_output:
        print(header)
        if out.strip() == "":
            print("(no output)")
        else:
            # print output as-is
            print(out, end="")
        print("-" * len(header))
    else:
        # in quiet mode do nothing
        pass

def run_all(backend="transpile", emit=False, quiet=False):
    any_fail = False
    for path, expected, expect_nonzero, substrings in EXAMPLES:
        p = Path(path)
        if not p.exists():
            print(f"[SKIP] {path} (file not found)\n")
            any_fail = True
            continue
        print(f"Running {path} ... (backend={backend})")
        if backend == "all":
            # run transpile then interpret and print both results
            rc_t, out_t = run_example(path, backend="transpile", emit_py=emit)
            rc_i, out_i = run_example(path, backend="interpret", emit_py=emit)
            ok_t, info_t = check_result(path, rc_t, out_t, expected, expect_nonzero, substrings)
            ok_i, info_i = check_result(path, rc_i, out_i, expected, expect_nonzero, substrings)
            status = "OK" if ok_t and ok_i else "FAIL"
            print(f"  -> transpile: {info_t}")
            print_example_output(path, out_t, not quiet)
            print(f"  -> interpret: {info_i}")
            print_example_output(path, out_i, not quiet)
            print(f"  -> status: {status}\n")
            if not (ok_t and ok_i):
                any_fail = True
        else:
            rc, out = run_example(path, backend=backend, emit_py=emit)
            ok, info = check_result(path, rc, out, expected, expect_nonzero, substrings)
            status = "OK" if ok else "FAIL"
            print(f"  -> {info}, status={status}")
            # Always print the program output for inspection (unless quiet)
            print_example_output(path, out, not quiet)
            # add a blank line to separate examples for readability
            print()
            if not ok:
                any_fail = True

    if any_fail:
        print("\nSome tests failed or were skipped.")
        return 2
    print("\nAll tests passed.")
    return 0

def main():
    backend = "transpile"
    emit = False
    quiet = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--backend", "-b") and i + 1 < len(args):
            backend = args[i+1]
            i += 2
            continue
        if a.startswith("--backend="):
            backend = a.split("=",1)[1]
        if a in ("--emit", "--emit-py"):
            emit = True
        if a in ("--quiet", "-q"):
            quiet = True
        i += 1

    rc = run_all(backend=backend, emit=emit, quiet=quiet)
    sys.exit(rc)

if __name__ == "__main__":
    main()