# miniPy — Limitations

> Status: prototype. The implementation is intentionally small and pragmatic — it favors getting a working end-to-end pipeline (lexer → parser → semantic checks → transpile / interpreter) rather than completeness or production-ready guarantees.

---

## 1. Language features not implemented or incomplete

- Modules / imports
  - There is no module system or import mechanism. All code is single-file; cross-file compilation, package namespaces or circular imports are not supported.

- Types and type system
  - No static types or type inference. All values are dynamically typed.
  - No separate type checking pass; semantic analysis only checks simple things (undeclared variables).

- Standard library
  - Only a tiny built-in surface is provided (e.g., `print`). No rich stdlib (collections, file I/O, math, etc.) is bundled.

- Data structures
  - No lists, dictionaries, sets, tuples (beyond possibly mapping to Python later). Only numbers and strings are supported.
  - No comprehensions or generator expressions.

- Advanced syntax
  - No decorators, context managers (`with`), class definitions or object-oriented features.
  - No list or dict literals (yet), no slicing, no attribute access on objects.

- Function features
  - No default parameter values, no keyword arguments, no varargs (`*args`, `**kwargs`).
  - No method binding or classes; function values are simple closures.

- Concurrency / async
  - No support for threads, async/await, or event loops.

---

## 2. Semantic and scoping limitations

- Limited semantic checks
  - Semantic analysis only detects undeclared variable usage in a basic way and manages function scopes. Many other semantic checks (argument arity, unreachable code, type errors) are not implemented.

- Scoping model simplified
  - The implementation follows Python-like rules (function-level scope, no block scope) but subtle corner cases (e.g., `nonlocal`/`global`) are not implemented.

- Forward-declarations & order sensitivity
  - Functions can be referenced before definition (allowed), but more complex forward-reference scenarios (e.g., mutually recursive non-function values) may be unsupported.

---

## 3. Runtime and behavioral differences

- Differences from CPython semantics
  - Although the transpiler emits Python AST, it does not guarantee perfect semantic parity in all edge cases. Small differences in evaluation order or operator semantics may exist until fully exercised by tests.
  - The interpreter backend is an independent implementation; differences between transpiled execution and interpreter execution are possible (though tests aim to keep them consistent).

- Numeric model
  - Uses Python numeric types (int / float) without any explicit overflow or fixed-width behavior. No integer-only optimization or custom numeric types.

- Recursion limits
  - Transpiled code uses CPython call stack; deep recursion will hit Python's recursion limit. The interpreter similarly uses recursion and Python exceptions for return-unwinding.

---

## 4. Security and safety

- Arbitrary code execution
  - The transpiler emits Python AST and calls `compile()`/`exec()` to run code. That runs arbitrary Python and will execute any code the user wrote. Do NOT run untrusted code with the transpiler backend in an unprotected environment.
  - The interpreter is safer but still executes arbitrary Python builtins (e.g., `print`) and may invoke Python callables; it is not a hardened sandbox.

- No sandboxing / restricted builtins
  - There is no built-in sandboxing layer or allowlist/denylist for builtins. Hardening would require replacing `__builtins__` or executing inside a secured VM.

---

## 5. Tooling and developer-experience gaps

- Diagnostics
  - Parsing and semantic errors report line/column information, but messages are terse and not localized. Tracebacks from transpiled code are full Python tracebacks and may look unfamiliar to miniPy users.
  - No error code system, no suggestions, and limited source-context formatting (basic caret printing).

- Debugging
  - No integrated debugger. While tracebacks reference `.mpy` source lines, stepping, breakpoints, or source maps are not provided.

- Packaging / multi-file projects
  - No build system for multi-file projects, modules, or packaging conventions.

- Tests & coverage
  - Few automated tests exist; many edge cases are not covered.

---

## 6. Performance

- Interpreter is slow
  - The AST-walking interpreter is meant for correctness testing and is not optimized. It is considerably slower than CPython for equivalent logic.

- Transpiler relies on CPython
  - While faster than the interpreter, the transpiled code's performance depends on CPython. No optimizations (constant folding, dead code elimination, inlining) are performed in the compiler.

---

## 7. Compatibility

- Python version expectations
  - The tooling assumes Python 3.9+ (for `ast.unparse` convenience and certain AST fields). It may work on slightly older Python versions, but some features (unparsing, end_lineno behavior) may differ.

---

## 8. Error recovery and robustness

- Parser does not attempt recovery
  - On a syntax error, parsing aborts and the program halts. There is no attempt to recover and continue parsing to show multiple errors in one pass.

- Limited validation
  - Many invalid programs may pass initial checks but fail at runtime with Python exceptions; the compiler does not proactively find all such issues.

---

## 9. Multi-user / production limitations

- No REPL multi-session state management beyond single runs.
- No concurrency or server-side execution primitives.
- Not intended for production use or untrusted execution.