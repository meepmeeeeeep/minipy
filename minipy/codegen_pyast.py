# Convert miniPy AST to Python ast, preserving lineno/col offsets (improved elif chaining)
import ast
from .ast_nodes import *

class PyASTCodeGen:
    def __init__(self, source_filename="<string>"):
        self.source_filename = source_filename

    def generate(self, root: Program):
        module_body = []
        for stmt in root.body or []:
            py = self._stmt_or_expr(stmt)
            if isinstance(py, list):
                module_body.extend(py)
            else:
                module_body.append(py)
        module = ast.Module(body=module_body, type_ignores=[])
        ast.fix_missing_locations(module)
        return module

    def visit(self, node):
        method = getattr(self, f'visit_{type(node).__name__}', None)
        if method is None:
            raise NotImplementedError(f"No codegen for {type(node).__name__}")
        return method(node)

    # Nodes
    def visit_NumberNode(self, node):
        n = ast.Constant(value=node.value)
        self._copy_pos(n, node)
        return n

    def visit_StringNode(self, node):
        n = ast.Constant(value=node.value)
        self._copy_pos(n, node)
        return n

    def visit_IdentifierNode(self, node):
        nm = ast.Name(id=node.name, ctx=ast.Load())
        self._copy_pos(nm, node)
        return nm

    def visit_BinaryOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        arith_ops = {'+': ast.Add(), '-': ast.Sub(), '*': ast.Mult(), '/': ast.Div()}
        compare_ops_map = {
            '==': ast.Eq(),
            '!=': ast.NotEq(),
            '<': ast.Lt(),
            '<=': ast.LtE(),
            '>': ast.Gt(),
            '>=': ast.GtE(),
        }
        if node.operator in arith_ops:
            b = ast.BinOp(left=left, op=arith_ops[node.operator], right=right)
            self._copy_pos(b, node)
            return b
        elif node.operator in compare_ops_map:
            comp = ast.Compare(left=left, ops=[compare_ops_map[node.operator]], comparators=[right])
            self._copy_pos(comp, node)
            return comp
        else:
            raise NotImplementedError(f"Operator {node.operator} not supported in codegen")

    def visit_AssignmentNode(self, node):
        target = ast.Name(id=node.name, ctx=ast.Store())
        value = self.visit(node.value)
        a = ast.Assign(targets=[target], value=value)
        self._copy_pos(a, node)
        return a

    def visit_CallNode(self, node):
        # Return ast.Call (expression) for use inside expressions.
        func = self.visit(node.func) if hasattr(node, 'func') else ast.Name(id=node.name, ctx=ast.Load())
        args = [self.visit(a) for a in node.args or []]
        call = ast.Call(func=func, args=args, keywords=[])
        self._copy_pos(call, node)
        return call

    def visit_IfNode(self, node):
        test = self.visit(node.condition)
        body = [self._stmt_or_expr(s) for s in node.then_body]
        # Build the top-level If and chain elifs in order
        top_if = ast.If(test=test, body=body, orelse=[])
        current = top_if

        for cond, body_nodes in node.elifs or []:
            elif_test = self.visit(cond)
            elif_body = [self._stmt_or_expr(s) for s in body_nodes]
            new_if = ast.If(test=elif_test, body=elif_body, orelse=[])
            current.orelse = [new_if]
            current = new_if

        if node.else_body:
            # attach else body to the last If's orelse
            current.orelse = [self._stmt_or_expr(s) for s in node.else_body]

        self._copy_pos(top_if, node)
        return top_if

    def visit_WhileNode(self, node):
        test = self.visit(node.condition)
        body = [self._stmt_or_expr(s) for s in node.body]
        w = ast.While(test=test, body=body, orelse=[])
        self._copy_pos(w, node)
        return w

    def visit_FunctionDefNode(self, node):
        args = [ast.arg(arg=name) for name in (node.params or [])]
        arguments = ast.arguments(posonlyargs=[], args=args, vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
        body = [self._stmt_or_expr(s) for s in (node.body or [])]
        func = ast.FunctionDef(name=node.name, args=arguments, body=body, decorator_list=[])
        self._copy_pos(func, node)
        return func

    def visit_ReturnNode(self, node):
        val = self.visit(node.value) if node.value is not None else None
        r = ast.Return(value=val)
        self._copy_pos(r, node)
        return r

    # Helpers
    def _stmt_or_expr(self, node):
        if isinstance(node, CallNode):
            call_expr = self.visit(node)  # returns ast.Call
            expr_stmt = ast.Expr(value=call_expr)
            self._copy_pos(expr_stmt, node)
            return expr_stmt
        return self.visit(node)

    def _copy_pos(self, py_node, src_node):
        try:
            lineno = getattr(src_node, "lineno", None)
            col = getattr(src_node, "col", None) or 0
            if lineno is not None:
                setattr(py_node, "lineno", lineno)
                setattr(py_node, "col_offset", col)
                end_lineno = getattr(src_node, "end_lineno", lineno)
                end_col = getattr(src_node, "end_col", col) or col
                setattr(py_node, "end_lineno", end_lineno)
                setattr(py_node, "end_col_offset", end_col)
        except Exception:
            pass