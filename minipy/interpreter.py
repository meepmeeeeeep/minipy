# Simple AST-walking interpreter for miniPy (updated to support strings)
from .ast_nodes import *
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class FunctionValue:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # captured environment (lexical)

class Interpreter:
    def __init__(self):
        self.global_env = {}
        # provide a basic builtin
        self.global_env["print"] = print

    def run(self, program: Program):
        self.env_stack = [self.global_env]
        for s in program.body or []:
            self.eval_stmt(s)

    def current_env(self):
        return self.env_stack[-1]

    def push_env(self, newenv=None):
        if newenv is None:
            newenv = {}
        self.env_stack.append(newenv)

    def pop_env(self):
        self.env_stack.pop()

    def eval_stmt(self, node):
        method = getattr(self, f'eval_{type(node).__name__}', None)
        if method:
            return method(node)
        raise NotImplementedError(f"No eval for {type(node).__name__}")

    def eval_AssignmentNode(self, node: AssignmentNode):
        v = self.eval_expr(node.value)
        # assign in current env
        self.current_env()[node.name] = v
        return None

    def eval_NumberNode(self, node: NumberNode):
        return node.value

    def eval_StringNode(self, node: StringNode):
        return node.value

    def eval_IdentifierNode(self, node: IdentifierNode):
        # lookup lexical
        for s in reversed(self.env_stack):
            if node.name in s:
                return s[node.name]
        raise NameError(f"Name '{node.name}' not found (line {node.lineno})")

    def eval_BinaryOpNode(self, node: BinaryOpNode):
        l = self.eval_expr(node.left)
        r = self.eval_expr(node.right)
        if node.operator == '+':
            return l + r
        if node.operator == '-':
            return l - r
        if node.operator == '*':
            return l * r
        if node.operator == '/':
            return l / r
        if node.operator == '==':
            return l == r
        if node.operator == '!=':
            return l != r
        if node.operator == '<':
            return l < r
        if node.operator == '<=':
            return l <= r
        if node.operator == '>':
            return l > r
        if node.operator == '>=':
            return l >= r
        raise RuntimeError(f"Unknown operator {node.operator}")

    def eval_CallNode(self, node: CallNode):
        # resolve function value
        if isinstance(node.func, IdentifierNode):
            fn = None
            for s in reversed(self.env_stack):
                if node.func.name in s:
                    fn = s[node.func.name]
                    break
            if fn is None:
                raise NameError(f"Function '{node.func.name}' not found (line {node.lineno})")
        else:
            fn = self.eval_expr(node.func)
        args = [self.eval_expr(a) for a in node.args or []]
        # builtin python call
        if callable(fn) and not isinstance(fn, FunctionValue):
            return fn(*args)
        # user-defined function
        if isinstance(fn, FunctionValue):
            newenv = dict(fn.env)  # shallow copy captured outer env
            # params binding
            for i, p in enumerate(fn.params):
                newenv[p] = args[i] if i < len(args) else None
            # push env and execute
            self.push_env(newenv)
            try:
                for s in fn.body or []:
                    self.eval_stmt(s)
            except ReturnException as re:
                self.pop_env()
                return re.value
            self.pop_env()
            return None
        raise RuntimeError("Not callable")

    def eval_FunctionDefNode(self, node: FunctionDefNode):
        # capture current env for lexical closure
        func = FunctionValue(params=node.params or [], body=node.body or [], env=dict(self.current_env()))
        # bind function name in current env
        self.current_env()[node.name] = func
        return None

    def eval_ReturnNode(self, node: ReturnNode):
        val = self.eval_expr(node.value) if node.value is not None else None
        raise ReturnException(val)

    def eval_IfNode(self, node: IfNode):
        cond = self.eval_expr(node.condition)
        if cond:
            self.push_env(dict(self.current_env()))
            for s in node.then_body or []:
                self.eval_stmt(s)
            self.pop_env()
            return
        for cond_node, body in node.elifs or []:
            if self.eval_expr(cond_node):
                self.push_env(dict(self.current_env()))
                for s in body:
                    self.eval_stmt(s)
                self.pop_env()
                return
        if node.else_body:
            self.push_env(dict(self.current_env()))
            for s in node.else_body:
                self.eval_stmt(s)
            self.pop_env()

    def eval_WhileNode(self, node: WhileNode):
        while self.eval_expr(node.condition):
            self.push_env(dict(self.current_env()))
            for s in node.body or []:
                self.eval_stmt(s)
            self.pop_env()

    # expression helper
    def eval_expr(self, node):
        method = getattr(self, f'eval_{type(node).__name__}', None)
        if method:
            return method(node)
        raise NotImplementedError(f"No eval for expr {type(node).__name__}")