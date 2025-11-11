# miniPy — Language Grammar and Implementation Overview

## Grammar (EBNF-style, updated)

program
::= statement*

statement
::= assignment | if_stmt | while_stmt | function_def | return_stmt | expression_stmt

assignment
::= identifier '=' expression

if_stmt
::= 'if' expression ':' block ('elif' expression ':' block)* ('else' ':' block)?

while_stmt
::= 'while' expression ':' block

function_def
::= 'def' identifier '(' parameter_list? ')' ':' block

return_stmt
::= 'return' expression?

expression_stmt
::= expression

expression
::= comparison

comparison
::= arith (('==' | '!=' | '<' | '<=' | '>' | '>=') arith)*

arith
::= term (('+' | '-') term)*

term
::= factor (('*' | '/') factor)*

factor
::= number | string | identifier | '(' expression ')' | function_call

block
::= INDENT statement+ DEDENT

parameter_list
::= identifier (',' identifier)*

Notes:
- number: integer or decimal literal (tokenized as NUMBER).
- string: quoted string literal (tokenized as STRING; supports Python-like escapes).
- INDENT / DEDENT / NEWLINE tokens are produced by the lexer using Python's tokenize module to match indentation behavior reliably.
- The grammar supports function calls, recursion, closures, arithmetic, and comparisons.

## AST node set (conceptual)
- Program (body: list[Node])
- NumberNode (value)
- StringNode (value)
- IdentifierNode (name)
- BinaryOpNode (left, operator, right)
- AssignmentNode (name, value)
- IfNode (condition, then_body, elifs, else_body)
- WhileNode (condition, body)
- FunctionDefNode (name, params, body)
- ReturnNode (value)
- CallNode (func, args)

Each AST node carries source position metadata: lineno and col (and optionally end_lineno/end_col when the codegen sets those).

## Key Components and Files

- Lexer
  - File: minipy/lexer.py
  - Responsibility: tokenize source using Python's `tokenize.generate_tokens(...)` to produce tokens including NAME, NUMBER, STRING, OP, NEWLINE, INDENT, DEDENT, EOF. Produces Token(type, value, lineno, col).
  - Notes: Using `tokenize` ensures INDENT/DEDENT behavior matches Python's rules.

- Parser
  - File: minipy/parser.py
  - Responsibility: recursive-descent parser that consumes tokens and builds the AST nodes described above. It attaches lineno/col to AST nodes for diagnostics.
  - Error: raises ParserError on unexpected tokens or syntax problems.

- AST node definitions
  - File: minipy/ast_nodes.py
  - Responsibility: dataclass definitions for all AST node types (NumberNode, StringNode, IdentifierNode, BinaryOpNode, AssignmentNode, IfNode, WhileNode, FunctionDefNode, ReturnNode, CallNode, Program).

- Semantic Analyzer / Symbol Table
  - File: minipy/semantic.py
  - Responsibility:
    - Manage symbol tables and scopes (function-level lexical scope; module scope).
    - Enforce semantic checks like "use of undeclared variable".
    - Insert function names and parameters into the symbol table on definition.
  - Important rule: if/while blocks are not creating new scopes (assignments inside them declare names visible in the enclosing function/module scope), matching Python semantics.

- Code Generator (transpiler to CPython AST)
  - File: minipy/codegen_pyast.py
  - Responsibility:
    - Convert miniPy AST nodes to Python ast.* nodes (ast.Module, ast.FunctionDef, ast.Assign, ast.If, ast.While, ast.BinOp, ast.Compare, ast.Call, ast.Constant, ast.Return).
    - Preserve source positions: set lineno, col_offset, end_lineno, end_col_offset when possible so Python tracebacks point into the original `.mpy` file.
    - Ensure expression contexts receive ast.expr nodes (e.g., ast.Call) and statement contexts receive ast.stmt (wrap calls in ast.Expr when needed).
    - Output: an ast.Module; CLI compiles with compile(module, filename=source_path, mode='exec').

- Interpreter (AST-walking backend)
  - File: minipy/interpreter.py
  - Responsibility: direct evaluation of AST nodes for testing and debugging. Implements:
    - Lexical closures via FunctionValue capturing an environment dict.
    - Return handling via internal ReturnException to unwind call frames.
    - Builtin bindings (e.g., print).
  - Use case: faster to inspect semantics and for unit tests.

- CLI / Runner
  - File: minipy/cli.py
  - Responsibility: entry point that ties pipeline together:
    - read source -> parse -> semantic analyze -> run backend (interpret or transpile & exec)
    - flags: --emit-py to write generated Python file; --backend to choose backend.
    - Error printing: pretty prints parse and semantic errors; prints tracebacks for runtime exceptions from transpiled code.

## Error Handling Design

- ParserError (raised by parser)
  - Thrown on syntax errors. CLI prints a short message and aborts.

- CompilerError / SemanticAnalyzer errors
  - Thrown or reported when semantic checks fail (e.g., undeclared variable). CLI prints a compact message and aborts before execution.

- Runtime errors
  - Interpreter: raises Python exceptions with messages that include the node's lineno when applicable. CLI reports "Runtime error (interpreter): <message>".
  - Transpiled code: Python traceback is printed as-is. Because we compile the generated ast with the original `.mpy` filename and set lineno/col_offset, tracebacks point at the original source line.

- Diagnostics
  - Parse/semantic errors include source snippet printing with a caret (CLI helper pretty_print_source_error).
  - Transpiled runtime tracebacks already include .mpy file/line info.

## Implementation notes / gotchas

- INDENT/DEDENT: using Python's tokenize avoids many corner cases; keep the code that consumes INDENT/DEDENT tokens in sync with parser expectations (block() expects an INDENT then statements then a DEDENT).
- Function scope: the semantic analyzer creates a new scope when entering a FunctionDef; it does not create scopes for if/while blocks.
- Calls vs statements: codegen must return ast.Call objects for expression positions and ast.Expr(value=ast.Call(...)) for statement positions.
- Line/column info: set both start and end positions (lineno/col_offset and end_lineno/end_col_offset) to avoid invalid AST ranges on some Python versions.
- Safety: exec(compiled_code) runs Python code; consider restricting builtins for untrusted code or run in sandbox if needed.

## Mapping to repository layout

```
minipy/
├── __init__.py
├── ast_nodes.py
├── lexer.py
├── parser.py
├── semantic.py
├── codegen_pyast.py
├── interpreter.py
└── cli.py
examples/
├── *.mpy
run_examples.py
README.md
docs/
└── language.md   # this file
```