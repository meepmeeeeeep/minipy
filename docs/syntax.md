# miniPy — Syntax Reference

This document covers lexical rules, grammar (EBNF-style), operator precedence, examples, and how to run programs with the provided CLI.

---

## Quick start: run a file
- Transpile and run (default):
  ```
  python -m minipy.cli path/to/file.mpy
  ```
- Interpret (AST-walking backend):
  ```
  python -m minipy.cli path/to/file.mpy --backend=interpret
  ```
- Emit generated Python source for inspection:
  ```
  python -m minipy.cli path/to/file.mpy --emit-py
  ```

---

## Lexical elements

- Whitespace and indentation
  - Indentation defines blocks (like Python). The lexer uses Python's `tokenize`, so valid indentation follows the same rules as Python: mix tabs and spaces is discouraged.
  - Blocks use INDENT / DEDENT tokens; statement terminator is newline.

- Comments
  - Single-line comments start with `#` and extend to end-of-line.
    Example:
    ```
    # This is a comment
    ```

- Identifiers
  - Names begin with a letter or underscore, followed by letters, digits, or underscores:
    ```
    foo, _bar, my_var2
    ```

- Keywords
  - `if`, `elif`, `else`, `while`, `def`, `return`, `print` (print is a builtin function)

- Literals
  - Numbers: integers and decimals. Example: `42`, `3.14`
  - Strings: single or double quoted; escapes follow Python literal rules (the parser uses Python literal parsing to interpret STRING token text).
    Example:
    ```
    "hello\nworld"
    'single-quoted'
    ```

- Operators and punctuation
  - Arithmetic: `+ - * /`
  - Comparisons: `== != < <= > >=`
  - Assignment: `=`
  - Parentheses: `( )`
  - Comma: `,`
  - Colon: `:` (used after `if`, `elif`, `else`, `while`, `def`)

---

## Grammar (EBNF-style)

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

function_call
::= identifier '(' arg_list? ')'

arg_list
::= expression (',' expression)*

parameter_list
::= identifier (',' identifier)*

block
::= INDENT statement+ DEDENT

Notes:
- `number` is a numeric literal token (integer or float).
- `string` is a STRING token (quoted literal).
- INDENT/DEDENT/NEWLINE tokens are supplied by the lexer via Python's tokenize module.

---

## Operator precedence (highest → lowest)
1. Parentheses: `( ... )`
2. Factor: literals, identifiers, function calls
3. Multiplicative: `*`, `/`
4. Additive: `+`, `-`
5. Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`

All binary operators in this language are left-associative (e.g., `a - b - c` parsed as `(a - b) - c`).

---

## Statements & examples

- Assignment:
  ```
  x = 10
  y = x + 2
  ```

- If / Elif / Else:
  ```mpy
  if x == 0:
      print("zero")
  elif x == 1:
      print("one")
  else:
      print("other")
  ```

- While loop:
  ```mpy
  i = 0
  s = 0
  while i < 5:
      s = s + i
      i = i + 1
  print(s)
  ```

- Function definition and return:
  ```mpy
  def sum2(a, b):
      return a + b

  print(sum2(2, 3))
  ```

- Nested functions and closures:
  ```mpy
  def make_adder(x):
      def add(y):
          return x + y
      return add

  add5 = make_adder(5)
  print(add5(3))  # prints 8
  ```

- Recursion:
  ```mpy
  def fact(n):
      if n == 0:
          return 1
      else:
          return n * fact(n - 1)

  print(fact(5))  # prints 120
  ```

- Strings and concatenation:
  ```mpy
  s = "Hello, miniPy!"
  print(s)
  print("Hi, " + "you")
  ```

---

## Example file: complete mini program

```mpy
# example.mpy
def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

print(fib(6))
```

Run:
```
python -m minipy.cli example.mpy
# Expected output:
# 8
```

---

## Error reporting & debugging tips

- Parse errors
  - If syntax is invalid, the parser raises a `ParserError`. The CLI prints a compact parse message.

- Semantic errors
  - Undeclared variable use is flagged by the SemanticAnalyzer (message includes "Use of undeclared variable 'name' at line X"). The CLI will abort execution when semantic checks fail.

- Runtime errors
  - Interpreter backend: the CLI will print "Runtime error (interpreter):" plus the exception message (often includes line number).
  - Transpiled backend: the CLI prints a full Python traceback. Because the code generator preserves `lineno`/`col_offset` and compiles with the `.mpy` filename, tracebacks point to the original source lines.

- For detailed inspection of the transpiled code:
  ```
  python -m minipy.cli path/to/file.mpy --emit-py
  ```
  This writes `file.generated.py` next to the source; you can open and run it with CPython to reproduce behavior.

---

## Restrictions, gotchas & best practices

- Indentation: be consistent. The lexer relies on Python rules; mixing tabs and spaces can cause tokenization errors.
- No block scope: assignments inside `if`/`while` are visible in the surrounding function/module scope (like Python).
- Builtins: currently only a small set of builtins exist (e.g., `print`). Avoid relying on other Python builtins unless you inspect the generated code and builtins provided by the interpreter.
- Security: transpiler uses `exec()` on generated Python. Do not run untrusted miniPy programs with transpiler backend on a shared system without sandboxing.
- Limitations: see `docs/limitations_summary.md` for a short list of missing features and known gaps (lists, dicts, default args, imports).

---

## Tests and examples

- The repository includes `examples/` with many `.mpy` files exercising features.
- Use `run_examples.py` to run the example suite:
  ```
  python run_examples.py            # run transpile backend and print outputs
  python run_examples.py --backend interpret
  python run_examples.py --backend all
  python run_examples.py --emit
  ```

---

## Extending syntax

If you want to add features, here are common extension points:
- Add new literal types (booleans, list/dict) in the lexer and ast_nodes.
- Extend parser factor/term rules to include the new constructs.
- Update semantic analyzer for new scoping or typing rules.
- Provide codegen mapping to Python ast and interpreter eval implementations.

---

## Reference summary

- File extension: `.mpy`
- Entrypoint: `minipy.cli` module
- Execution backends: `transpile` (default), `interpret`
- Use `--emit-py` to see generated Python
- See `examples/` and `run_examples.py` for sample programs and test harness.