# Recursive-descent parser for miniPy (updated: support STRING tokens)
from .lexer import tokenize_source, Token
from .ast_nodes import *
from typing import List
import ast as _pyast  # used for safe literal parsing of string tokens

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, source_text):
        self.tokens = list(tokenize_source(source_text))
        self.pos = 0
        self.current = self.tokens[0] if self.tokens else Token("EOF", "", 0, 0)

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = Token("EOF", "", 0, 0)

    def accept(self, typ, val=None):
        if self.current.type == typ and (val is None or self.current.value == val):
            tok = self.current
            self.advance()
            return tok
        return None

    def expect(self, typ, val=None):
        tok = self.accept(typ, val)
        if not tok:
            raise ParserError(f"Expected {typ} {val}, got {self.current}")
        return tok

    def parse(self):
        stmts = []
        while self.current.type != "EOF":
            if self.current.type == "NEWLINE":
                self.advance()
                continue
            stmts.append(self.statement())
        return Program(body=stmts)

    def statement(self):
        if self.current.type == "NAME" and self.current.value == "if":
            return self.if_stmt()
        if self.current.type == "NAME" and self.current.value == "while":
            return self.while_stmt()
        if self.current.type == "NAME" and self.current.value == "def":
            return self.function_def()
        if self.current.type == "NAME" and self.current.value == "return":
            return self.return_stmt()
        # assignment or expression statement
        if self.current.type == "NAME":
            # peek next token to see if assignment
            tok = self.current
            next_tok = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
            if next_tok and next_tok.type == "OP" and next_tok.value == "=":
                return self.assignment()
        # otherwise expression statement (likely function call)
        expr = self.expression()
        # accept optional NEWLINE
        if self.current.type == "NEWLINE":
            self.advance()
        return expr  # expression statements are CallNodes typically

    def assignment(self):
        name_tok = self.expect("NAME")
        eq = self.expect("OP", "=")
        val = self.expression()
        if self.current.type == "NEWLINE":
            self.advance()
        return AssignmentNode(name=name_tok.value, value=val, lineno=name_tok.lineno, col=name_tok.col)

    def if_stmt(self):
        if_tok = self.expect("NAME", "if")
        cond = self.expression()
        # expect colon (OP :)
        self.expect("OP", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        then_body = self.block()
        elifs = []
        else_body = None
        while self.current.type == "NAME" and self.current.value == "elif":
            self.advance()
            econd = self.expression()
            self.expect("OP", ":")
            self.expect("NEWLINE")
            self.expect("INDENT")
            ebody = self.block()
            elifs.append((econd, ebody))
        if self.current.type == "NAME" and self.current.value == "else":
            self.advance()
            self.expect("OP", ":")
            self.expect("NEWLINE")
            self.expect("INDENT")
            else_body = self.block()
        return IfNode(condition=cond, then_body=then_body, elifs=elifs, else_body=else_body, lineno=if_tok.lineno, col=if_tok.col)

    def while_stmt(self):
        while_tok = self.expect("NAME", "while")
        cond = self.expression()
        self.expect("OP", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        body = self.block()
        return WhileNode(condition=cond, body=body, lineno=while_tok.lineno, col=while_tok.col)

    def function_def(self):
        def_tok = self.expect("NAME", "def")
        name_tok = self.expect("NAME")
        self.expect("OP", "(")
        params = []
        if not (self.current.type == "OP" and self.current.value == ")"):
            # parse parameter list
            p = self.expect("NAME")
            params.append(p.value)
            while self.accept("OP", ","):
                p = self.expect("NAME")
                params.append(p.value)
        self.expect("OP", ")")
        self.expect("OP", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        body = self.block()
        return FunctionDefNode(name=name_tok.value, params=params, body=body, lineno=def_tok.lineno, col=def_tok.col)

    def return_stmt(self):
        ret_tok = self.expect("NAME", "return")
        if self.current.type != "NEWLINE":
            val = self.expression()
        else:
            val = None
        if self.current.type == "NEWLINE":
            self.advance()
        return ReturnNode(value=val, lineno=ret_tok.lineno, col=ret_tok.col)

    def block(self):
        stmts = []
        while not (self.current.type == "DEDENT" or self.current.type == "EOF"):
            if self.current.type == "NEWLINE":
                self.advance()
                continue
            stmts.append(self.statement())
        self.expect("DEDENT")
        return stmts

    # Expressions (precedence)
    # expression -> comparison
    # comparison -> arith ( ( '==' | '!=' | '<' | '<=' | '>' | '>=' ) arith )*
    # arith -> term (('+' | '-') term)*
    # term -> factor (('*' | '/') factor)*
    # factor -> NUMBER | STRING | IDENTIFIER | '(' expression ')' | function_call

    def expression(self):
        return self.comparison()

    def comparison(self):
        node = self.arith()
        while self.current.type == "OP" and self.current.value in ("==", "!=", "<", "<=", ">", ">="):
            op = self.current.value
            self.advance()
            right = self.arith()
            node = BinaryOpNode(left=node, operator=op, right=right, lineno=node.lineno, col=node.col)
        return node

    def arith(self):
        node = self.term()
        while self.current.type == "OP" and self.current.value in ("+", "-"):
            op = self.current.value
            self.advance()
            right = self.term()
            node = BinaryOpNode(left=node, operator=op, right=right, lineno=node.lineno, col=node.col)
        return node

    def term(self):
        node = self.factor()
        while self.current.type == "OP" and self.current.value in ("*", "/"):
            op = self.current.value
            self.advance()
            right = self.factor()
            node = BinaryOpNode(left=node, operator=op, right=right, lineno=node.lineno, col=node.col)
        return node

    def factor(self):
        tok = self.current
        if tok.type == "NUMBER":
            self.advance()
            return NumberNode(value=float(tok.value) if '.' in tok.value else int(tok.value), lineno=tok.lineno, col=tok.col)
        if tok.type == "STRING":
            # use Python literal parsing to handle escapes properly
            val = _pyast.literal_eval(tok.value)
            self.advance()
            return StringNode(value=val, lineno=tok.lineno, col=tok.col)
        if tok.type == "NAME":
            # could be function call or identifier
            # peek for '('
            next_tok = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
            if next_tok and next_tok.type == "OP" and next_tok.value == "(":
                return self.call()
            self.advance()
            return IdentifierNode(name=tok.value, lineno=tok.lineno, col=tok.col)
        if tok.type == "OP" and tok.value == "(":
            self.advance()
            node = self.expression()
            self.expect("OP", ")")
            return node
        raise ParserError(f"Unexpected token in factor: {tok}")

    def call(self):
        name_tok = self.expect("NAME")
        self.expect("OP", "(")
        args = []
        if not (self.current.type == "OP" and self.current.value == ")"):
            args.append(self.expression())
            while self.accept("OP", ","):
                args.append(self.expression())
        self.expect("OP", ")")
        return CallNode(func=IdentifierNode(name=name_tok.value, lineno=name_tok.lineno, col=name_tok.col), args=args, lineno=name_tok.lineno, col=name_tok.col)

# convenience parse function
def parse(source_text):
    p = Parser(source_text)
    return p.parse()