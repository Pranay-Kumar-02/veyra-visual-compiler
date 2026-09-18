"""
Lexical analyzer (Scanner) for VCL (Visual Compiler Language).
Scans source code character-by-character, strictly tracking line and column numbers.
"""

from typing import List, Optional
from backend.tokens import Token, TokenType, KEYWORDS
from backend.errors import LexicalError


class Lexer:
    """
    Hand-written character-by-character lexical analyzer for VCL.
    Adheres strictly to the VCL language specification.
    """

    def __init__(self, source: str):
        self.source: str = source
        self.length: int = len(source)
        self.start_pos: int = 0
        self.current_pos: int = 0
        self.line: int = 1
        self.column: int = 1
        self.start_column: int = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """Scans the entire source and produces a list of Tokens ending with EOF."""
        self.tokens = []
        self.start_pos = 0
        self.current_pos = 0
        self.line = 1
        self.column = 1

        while not self._is_at_end():
            self.start_pos = self.current_pos
            self.start_column = self.column
            self._scan_token()

        self.tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                literal=None,
                line=self.line,
                column=self.column,
                source_pos=self.current_pos,
            )
        )
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current_pos >= self.length

    def _advance(self) -> str:
        ch = self.source[self.current_pos]
        self.current_pos += 1
        self.column += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current_pos]

    def _peek_next(self) -> str:
        if self.current_pos + 1 >= self.length:
            return "\0"
        return self.source[self.current_pos + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current_pos] != expected:
            return False
        self.current_pos += 1
        self.column += 1
        return True

    def _add_token(self, token_type: TokenType, literal: Optional[object] = None) -> None:
        lexeme = self.source[self.start_pos : self.current_pos]
        self.tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                literal=literal,
                line=self.line,
                column=self.start_column,
                source_pos=self.start_pos,
            )
        )

    def _scan_token(self) -> None:
        ch = self._advance()

        # Whitespace handling
        if ch in (" ", "\r", "\t"):
            return
        if ch == "\n":
            self.line += 1
            self.column = 1
            return

        # Delimiters
        if ch == "(":
            self._add_token(TokenType.LPAREN)
        elif ch == ")":
            self._add_token(TokenType.RPAREN)
        elif ch == "{":
            self._add_token(TokenType.LBRACE)
        elif ch == "}":
            self._add_token(TokenType.RBRACE)
        elif ch == ";":
            self._add_token(TokenType.SEMICOLON)
        elif ch == ",":
            self._add_token(TokenType.COMMA)

        # Arithmetic operators
        elif ch == "+":
            self._add_token(TokenType.PLUS)
        elif ch == "-":
            self._add_token(TokenType.MINUS)
        elif ch == "*":
            self._add_token(TokenType.STAR)
        elif ch == "/":
            self._add_token(TokenType.SLASH)
        elif ch == "%":
            self._add_token(TokenType.PERCENT)

        # Relational & Assignment operators
        elif ch == "=":
            if self._match("="):
                self._add_token(TokenType.EQ_EQ)
            else:
                self._add_token(TokenType.ASSIGN)
        elif ch == "!":
            if self._match("="):
                self._add_token(TokenType.BANG_EQ)
            else:
                self._add_token(TokenType.BANG)
        elif ch == "<":
            if self._match("="):
                self._add_token(TokenType.LESS_EQ)
            else:
                self._add_token(TokenType.LESS)
        elif ch == ">":
            if self._match("="):
                self._add_token(TokenType.GREATER_EQ)
            else:
                self._add_token(TokenType.GREATER)

        # Logical operators
        elif ch == "&":
            if self._match("&"):
                self._add_token(TokenType.AND_AND)
            else:
                raise LexicalError(
                    message="Unexpected single '&'. Expected logical '&&'.",
                    line=self.line,
                    column=self.start_column,
                    hint="In VCL, logical AND is written as '&&'.",
                )
        elif ch == "|":
            if self._match("|"):
                self._add_token(TokenType.OR_OR)
            else:
                raise LexicalError(
                    message="Unexpected single '|'. Expected logical '||'.",
                    line=self.line,
                    column=self.start_column,
                    hint="In VCL, logical OR is written as '||'.",
                )

        # Number literals (Integer & Float)
        elif ch.isdigit():
            self._scan_number()

        # Identifiers & Keywords
        elif ch.isalpha() or ch == "_":
            self._scan_identifier()

        else:
            raise LexicalError(
                message=f"Invalid character '{ch}' in source.",
                line=self.line,
                column=self.start_column,
                hint=f"Character '{ch}' is not part of the VCL alphabet.",
            )

    def _scan_number(self) -> None:
        is_float = False
        while self._peek().isdigit():
            self._advance()

        # Check for fractional part
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()  # Consume '.'
            while self._peek().isdigit():
                self._advance()

            # Check if there is an illegal second dot
            if self._peek() == ".":
                raise LexicalError(
                    message="Malformed floating-point literal with multiple decimal points.",
                    line=self.line,
                    column=self.column,
                    hint="Numbers must contain at most one decimal point.",
                )

        lexeme = self.source[self.start_pos : self.current_pos]
        if is_float:
            self._add_token(TokenType.FLOAT, float(lexeme))
        else:
            self._add_token(TokenType.INTEGER, int(lexeme))

    def _scan_identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        lexeme = self.source[self.start_pos : self.current_pos]
        token_type = KEYWORDS.get(lexeme)

        if token_type is not None:
            if token_type == TokenType.TRUE:
                self._add_token(TokenType.BOOLEAN, True)
            elif token_type == TokenType.FALSE:
                self._add_token(TokenType.BOOLEAN, False)
            else:
                self._add_token(token_type)
        else:
            self._add_token(TokenType.IDENTIFIER, lexeme)
