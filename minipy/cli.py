# CLI for minipy: improved error printing for parse/semantic/runtime errors
import sys
import ast
import traceback
from pathlib import Path

from .parser import parse, ParserError
from .semantic import SemanticAnalyzer, CompilerError
from .codegen_pyast import PyASTCodeGen
from .interpreter import Interpreter

def pretty_print_source_error(path, lineno, col, message):
    path = Path(path)
    try:
        lines = path.read_text().splitlines()
        if 1 <= lineno <= len(lines):
            line = lines[lineno - 1]
            print(f"{path}:{lineno}:{col}: {message}")
            print(line)
            caret = " " * max(col, 0) + "^"
            print(caret)
        else:
            print(f"{path}:{lineno}:{col}: {message}")
    except Exception:
        print(f"{path}:{lineno}:{col}: {message}")

def run_file(path, emit_py=False, backend="transpile"):
    source_path = Path(path)
    source_text = source_path.read_text()
    try:
        root = parse(source_text)
    except ParserError as e:
        # ParserError messages currently include context; print and exit
        print(f"Parse error: {e}")
        return 1

    analyzer = SemanticAnalyzer()
    try:
        ok = analyzer.analyze(root)
    except CompilerError as ce:
        # analyze() may raise CompilerError
        print(f"Semantic error: {ce}")
        return 1

    if not ok:
        print("Semantic errors detected. Aborting.")
        return 1

    if backend == "interpret":
        try:
            interp = Interpreter()
            interp.run(root)
            return 0
        except Exception as e:
            # interpreter exceptions often include line info in message
            print(f"Runtime error (interpreter): {e}")
            return 1

    # transpile backend
    codegen = PyASTCodeGen(source_filename=str(source_path))
    module = codegen.generate(root)

    if emit_py:
        try:
            py_source = ast.unparse(module)
        except Exception:
            import astor
            py_source = astor.to_source(module)
        out_path = source_path.with_suffix(".generated.py")
        out_path.write_text(py_source)
        print(f"Wrote generated Python to {out_path}")

    try:
        compiled = compile(module, filename=str(source_path), mode='exec')
        globals_dict = {}
        exec(compiled, globals_dict, globals_dict)
    except CompilerError as ce:
        # Semantic/compiler errors thrown during codegen or execution
        print(f"Compiler error: {ce}")
        return 1
    except Exception:
        # For runtime exceptions in the transpiled code, print a full traceback.
        # The compiled code used filename=source_path, so tracebacks will point to the .mpy file and lines.
        print("Runtime error (transpiled code):")
        traceback.print_exc()
        return 1

    return 0

def main(argv):
    if len(argv) < 2:
        print("Usage: python -m minipy.cli file.mpy [--emit-py] [--backend=transpile|interpret]")
        return 1
    path = argv[1]
    emit_py = "--emit-py" in argv
    backend = "transpile"
    for a in argv[2:]:
        if a.startswith("--backend="):
            backend = a.split("=",1)[1]
    return run_file(path, emit_py=emit_py, backend=backend)

if __name__ == "__main__":
    sys.exit(main(sys.argv))