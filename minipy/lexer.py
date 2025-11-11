# Lexer: wraps Python's tokenize to produce tokens for our parser.
import tokenize
from io import StringIO
from collections import namedtuple

Token = namedtuple("Token", ["type", "value", "lineno", "col"])

def tokenize_source(source_text):
    """
    Yield Token(type, value, lineno, col) for our parser.
    Uses Python's tokenize to get INDENT/DEDENT/NAME/NUMBER/OP tokens.
    """
    src = StringIO(source_text)
    gen = tokenize.generate_tokens(src.readline)
    for tok_type, tok_str, start, end, _ in gen:
        lineno, col = start
        if tok_type == tokenize.NUMBER:
            yield Token("NUMBER", tok_str, lineno, col)
        elif tok_type == tokenize.NAME:
            yield Token("NAME", tok_str, lineno, col)
        elif tok_type == tokenize.STRING:
            # simple string token support if needed later
            yield Token("STRING", tok_str, lineno, col)
        elif tok_type == tokenize.NEWLINE:
            yield Token("NEWLINE", tok_str, lineno, col)
        elif tok_type == tokenize.INDENT:
            yield Token("INDENT", tok_str, lineno, col)
        elif tok_type == tokenize.DEDENT:
            yield Token("DEDENT", tok_str, lineno, col)
        elif tok_type == tokenize.OP:
            yield Token("OP", tok_str, lineno, col)
        elif tok_type == tokenize.ENDMARKER:
            yield Token("EOF", "", lineno, col)
        else:
            # ignore other tokens (NL, COMMENT)
            continue