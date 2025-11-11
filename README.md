# miniPy

miniPy is a small educational language and prototype compiler implemented in Python.
The project provides two backends:

- Transpiler → CPython AST: converts miniPy programs to Python `ast.Module`, compiles, and executes them (fast, uses CPython runtime).
- Interpreter: an AST-walking interpreter backend useful for testing and debugging language semantics.

This repository contains a working end-to-end pipeline: lexer (using Python's `tokenize`), parser, AST nodes, basic semantic analysis, a code generator to the Python AST, an AST interpreter, CLI, and a set of example programs.

## Status
This is a prototype. Core features implemented:
- Indentation-based blocks (INDENT / DEDENT)
- Assignments, expressions, binary arithmetic (+, -, *, /)
- Comparison operators (==, !=, <, <=, >, >=)
- If / elif / else
- While loops
- Function definitions, calls, recursion, lexical closures
- Return statements
- String literals and concatenation with `+`
- Basic semantic checking for undeclared variables (simple symbol table)
- Clearer error handling and tracebacks that point to the original `.mpy` files
- Two execution backends: transpile (default) and interpret

## Requirements
- Python 3.9+ recommended (code uses `ast.unparse` where available)
- No other system dependencies required to run the prototype. Optional dev dependencies: `pytest`, `astor` (fallback for older Pythons).

## Quick install (development)
1. Clone or place the project folder on your machine so it contains `minipy/` and example files.
2. Create and activate a virtual environment (recommended):
   - Unix / macOS:
     ```
     python -m venv .venv
     source .venv/bin/activate
     ```
   - Windows (cmd.exe):
     ```
     python -m venv .venv
     .venv\Scripts\activate
     ```
3. Install the package in editable/development mode:
   ```
   python -m pip install -e .
   ```
   This makes the `minipy` package importable as a module and allows running the CLI as `python -m minipy.cli`.

If you prefer to run without installing, ensure your shell's current working directory is the project root and use:
- On cmd.exe:
  ```
  set PYTHONPATH=.
  python -m minipy.cli examples/example.mpy
  ```
- On PowerShell:
  ```
  $env:PYTHONPATH = "."
  python -m minipy.cli examples/example.mpy
  ```

## CLI usage
The main entrypoint is `minipy/cli.py` and is exposed as a module:

- Run a single `.mpy` file (transpile backend, default):
  ```
  python -m minipy.cli path/to/file.mpy
  ```

- Emit generated Python source (writes `file.generated.py` next to the source):
  ```
  python -m minipy.cli path/to/file.mpy --emit-py
  ```

- Choose interpretation instead of transpiling:
  ```
  python -m minipy.cli path/to/file.mpy --backend=interpret
  ```

- Help / usage:
  ```
  python -m minipy.cli
  ```

## Example programs
Example `.mpy` files live in the `examples/` directory. A few highlights:

- `examples/example.mpy` (factorial, while loop, prints)
  Expected output:
  ```
  120
  10
  ```

- `examples/print_string.mpy`
  Expected:
  ```
  Hello, miniPy!
  Hello, world
  ```

- `examples/closure_test.mpy` — tests lexical closures
  Expected:
  ```
  8
  ```

- `examples/error_semantic.mpy` — demonstrates a semantic error (undeclared variable)
  Expected: semantic error printed and non-zero exit.

- `examples/error_runtime.mpy` — demonstrates runtime traceback (e.g., division by zero)
  Expected: a Python traceback printed with `.mpy` filename and line number.

## Running the example suite
A runner script is provided to exercise the examples and do basic verification:

```
python run_examples.py             # run transpile backend
python run_examples.py --backend interpret
python run_examples.py --backend all   # compare transpile vs interpreter
python run_examples.py --emit         # also write generated .generated.py files
```

`run_examples.py` checks expected stdout for positive cases and checks that error cases return non-zero and contain indicative messages.

## Error handling & diagnostics
- Parse errors: `Parse error: ...` is printed with a short message.
- Semantic errors: printed by the semantic analyzer; the CLI aborts execution when semantic checks fail.
- Runtime errors:
  - Interpreter backend: prints "Runtime error (interpreter): <message>".
  - Transpiled backend: prints a full Python traceback. Because the transpiler copies `lineno`/`col_offset` and compiles with the original `.mpy` filename, tracebacks point to the correct `.mpy` file and line.
- If you want prettier diagnostics (snippets + caret, color), that can be added as a small utility to parse tracebacks and show file context.

## Development notes & file layout
Minimal project layout:
```
.
├── minipy/
│   ├── __init__.py
│   ├── ast_nodes.py
│   ├── lexer.py
│   ├── parser.py
│   ├── semantic.py
│   ├── codegen_pyast.py
│   ├── interpreter.py
│   └── cli.py
├── examples/
│   └── *.mpy
├── example.mpy   # (top-level sample)
├── run_examples.py
└── README.md
```

## Troubleshooting
- ModuleNotFoundError: If `python -m minipy.cli` fails with `ModuleNotFoundError: No module named 'minipy'`, either:
  - Run the install step `python -m pip install -e .` from the project root, or
  - Set `PYTHONPATH=.` in the shell before running the `-m` invocation so Python can import the local package.
- If you get AST compile errors, ensure `minipy/codegen_pyast.py` is the up-to-date version that returns `ast.Call` in expression contexts and uses `ast.fix_missing_locations`, and that `end_lineno`/`end_col_offset` information is present.

## Tests & CI
The repository includes a basic runnable example test harness (`run_examples.py`); converting these to `pytest` unit tests and adding CI is a straightforward next step.