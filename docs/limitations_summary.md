# miniPy — Limitations (Summary)

- Small feature set: only numbers and strings are supported. No lists, dicts, tuples, classes, decorators, comprehensions, or async/await.
- Function limitations: no default parameters, no keyword args, no varargs (`*args` / `**kwargs`), no methods or class support; functions are simple closures only.
- No modules/imports: single-file programs only; no package or import system.
- Minimal semantic checks: only basic undeclared-variable detection and function-scope handling. No arity checking, no type checking, no advanced semantic analyses.
- Potential semantic differences vs. Python: subtle differences may exist; interpreter and transpiled backends may diverge on edge cases until more tests are added.
- No sandboxing: the transpiler compiles to Python and uses `exec()` — do not run untrusted code without isolating it (separate process/container or a hardened sandbox).
- Limited diagnostics and tooling: terse error messages, little error recovery, no integrated debugger or REPL, and sparse automated tests / CI.
- Performance: the AST-walking interpreter is slow (for testing/debugging). The transpiled backend relies on CPython and has no compiler optimizations (no constant folding, inlining, etc.).
- Recursion and runtime limits: deep recursion subject to Python recursion limits; no tail-call optimization.
- Packaging & multi-file projects: no build system for multi-file projects; packaging is minimal.

Quick mitigations / next steps (suggested)
- Run untrusted code inside a sandboxed process/container or restrict builtins before executing transpiled code.
- Improve semantic checks (argument arity, basic types) and expand automated tests to reduce divergence between backends.
- Add data structures (lists/dicts) and boolean/logical operators next; later consider small optimizations (constant folding) and a richer standard library.