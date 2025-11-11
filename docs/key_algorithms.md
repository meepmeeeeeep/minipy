# miniPy — Key Algorithms

## 1. Token recognition (Lexer)
- Implementation: `minipy/lexer.py`
- Strategy: Reuse Python's `tokenize.generate_tokens()` to produce tokens (NAME, NUMBER, STRING, OP, NEWLINE, INDENT, DEDENT, EOF). Each yielded token is wrapped into a small Token(tuple) with type, value, lineno and col.
- Why: Python's `tokenize` already implements robust indentation rules, string escapes and line handling — reusing it avoids subtle edge cases.
- Algorithm steps:
  1. Feed source to `tokenize.generate_tokens`.
  2. Map Python token types to miniPy token types.
  3. Yield Token(type, value, lineno, col) for parser consumption.
- Complexity: O(n) in source length (single pass).
- Notes: INDENT/DEDENT are preserved so parser sees indentation-based blocks reliably.

## 2. Parsing (Recursive-descent)
- Implementation: `minipy/parser.py`
- Strategy: Hand-written recursive-descent parser with separated functions for each precedence level:
  - expression -> comparison -> arith -> term -> factor
  - Statement-level parsing recognizes assignment, if/elif/else, while, def, return and expression-statements.
  - Block handling: expects INDENT, statement+, DEDENT.
- Algorithm steps (summary):
  - Use a token stream with `pos` and `current` pointer.
  - Provide `accept`/`expect` helpers to match tokens.
  - Build AST nodes (dataclasses) with lineno/col metadata at creation.
  - Expression parsing: each function consumes operators at its precedence and constructs BinaryOpNode chains (left-associative).
- Complexity: O(t) where t is the number of tokens (single pass over tokens, with backtracking minimized).
- Error handling: raise `ParserError` on unexpected tokens; parser preserves source position for error diagnostics.

## 3. Semantic analysis and symbol table
- Implementation: `minipy/semantic.py`
- Strategy: Scoped symbol table implemented as a stack of dictionaries:
  - `scopes` list with push (enter) and pop (exit) operations.
  - Module-level scope and each function body gets a new scope.
  - If/while blocks do NOT create new scopes (assignments inside blocks are visible at the enclosing function/module scope).
- Key checks:
  - Undefined identifier usage — `lookup` searches from current scope upward.
  - Function definitions: insert the function name before analyzing body (to allow recursion).
  - Function parameters: declared in the function scope prior to analyzing the body.
- Algorithm steps:
  1. Walk AST recursively.
  2. On Assignment: analyze RHS, then `insert(name)` in current scope.
  3. On Identifier: verify `lookup(name)` true else raise `CompilerError`.
  4. On FunctionDef: `insert(name)` in outer scope, then `enter()` a new scope, insert params, analyze body, `exit()`.
- Complexity: O(n) in AST node count; lookup is O(s) in worst-case number of nested scopes (usually small).
- Notes: This simple approach is sufficient for undeclared-variable detection; future improvements could add type info or multi-pass analyses.

## 4. Code generation → CPython AST
- Implementation: `minipy/codegen_pyast.py`
- Strategy: AST visitor that maps miniPy nodes to Python `ast` nodes:
  - Number/String -> `ast.Constant`
  - Identifier -> `ast.Name` (Load/Store contexts)
  - Binary operations -> `ast.BinOp` or `ast.Compare` depending on operator
  - Assignment -> `ast.Assign`
  - If/Elif/Else -> nested `ast.If` chain built so elifs and else attach correctly
  - FunctionDef -> `ast.FunctionDef` with `ast.arguments`
  - Return -> `ast.Return`, Call -> `ast.Call` (expression) and wrapped in `ast.Expr` for statement contexts
- Important details:
  - Preserve `lineno`, `col_offset`, `end_lineno`, `end_col_offset` on generated nodes so Python tracebacks match `.mpy` lines.
  - Use `ast.fix_missing_locations(module)` before `compile`.
- Complexity: O(n) in AST nodes to traverse and emit Python AST.
- Safety: `exec()` runs generated Python code; for untrusted code consider restricting `__builtins__`.
- Notes: This approach benefits from CPython performance and standard library; later backends (LLVM, native) could reuse the same AST/IR.

## 5. Interpreter (AST-walking)
- Implementation: `minipy/interpreter.py`
- Strategy: Evaluate AST with an environment stack and closures:
  - `env_stack`: list of dicts representing nested lexical environments.
  - Function values captured by `FunctionValue` that stores params, body, and a captured env (closure).
  - `Return` is implemented by raising a `ReturnException` to unwind to the caller.
  - Builtins (e.g., `print`) are provided in the global environment.
- Algorithm steps:
  1. Evaluate statements top-down in current env.
  2. For function calls: resolve function value, create new env based on captured env + parameter bindings, push, execute body, pop.
  3. For expressions: recursively evaluate subexpressions.
- Complexity: Depends on program; interpreter overhead per node visit is modest but slower than CPython bytecode.
- Use: Great for testing semantics and quick debugging.

## 6. Error handling algorithms
- Parse errors: immediate raise `ParserError` with node/token info.
- Semantic errors: raise or report `CompilerError` with lineno/col; CLI prints snippet with caret when possible.
- Runtime errors:
  - Interpreter: exceptions surfaced with messages that include lineno.
  - Transpiled: rely on Python traceback; because compiled code uses `.mpy` filename and preserved lineno, tracebacks point to miniPy source.

## 7. Complexity summary
- Lexing: O(n) in source bytes.
- Parsing: O(t) tokens → O(n) where n = tokens or AST nodes.
- Semantic analysis: O(n) with scope lookups O(depth_of_scopes) each.
- Code generation: O(n) transform to Python AST.
- Execution:
  - Interpreter: O(n * cost_per_node) runtime overhead.
  - Transpiled: performance determined by CPython execution of generated code.

## 8. Future algorithmic improvements
- Constant folding & simple local optimizations during codegen (one-pass AST rewrite).
- IR form (SSA) for more advanced optimizations and potential LLVM backend.
- Type inference / gradual typing with flow analysis for earlier error detection.
- Tail-call optimization or trampolining for recursion-heavy examples (if desired).
- JIT via Cranelift/LLJIT or emitting to LLVM IR for native performance.
- More advanced error recovery in parser (synchronization to continue multiple errors).