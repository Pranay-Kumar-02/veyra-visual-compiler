"""
Token specifications, data structures, and management utilities for VCL.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class TokenType(Enum):
    # Keywords
    LET = "let"
    IF = "if"
    ELSE = "else"
    PRINT = "print"
    TRUE = "true"
    FALSE = "false"

    # Arithmetic Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"

    # Relational Operators
    EQ_EQ = "=="
    BANG_EQ = "!="
    LESS = "<"
    GREATER = ">"
    LESS_EQ = "<="
    GREATER_EQ = ">="

    # Logical Operators
    AND_AND = "&&"
    OR_OR = "||"
    BANG = "!"

    # Assignment Operator
    ASSIGN = "="

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    SEMICOLON = ";"
    COMMA = ","

    # Literals
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"

    # Identifiers
    IDENTIFIER = "IDENTIFIER"

    # Control & End-Of-File
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.name


# Mapping for keyword recognition
KEYWORDS: Dict[str, TokenType] = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "print": TokenType.PRINT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}


class TokenCategory(Enum):
    KEYWORD = "Keyword"
    ARITHMETIC_OP = "Arithmetic Operator"
    RELATIONAL_OP = "Relational Operator"
    LOGICAL_OP = "Logical Operator"
    ASSIGNMENT_OP = "Assignment Operator"
    DELIMITER = "Delimiter"
    LITERAL = "Literal"
    IDENTIFIER = "Identifier"
    CONTROL = "Control"


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Optional[Any]
    line: int
    column: int
    source_pos: int

    @property
    def category(self) -> TokenCategory:
        t = self.type
        if t in (TokenType.LET, TokenType.IF, TokenType.ELSE, TokenType.PRINT, TokenType.TRUE, TokenType.FALSE):
            return TokenCategory.KEYWORD
        if t in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            return TokenCategory.ARITHMETIC_OP
        if t in (TokenType.EQ_EQ, TokenType.BANG_EQ, TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ):
            return TokenCategory.RELATIONAL_OP
        if t in (TokenType.AND_AND, TokenType.OR_OR, TokenType.BANG):
            return TokenCategory.LOGICAL_OP
        if t == TokenType.ASSIGN:
            return TokenCategory.ASSIGNMENT_OP
        if t in (TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE, TokenType.SEMICOLON, TokenType.COMMA):
            return TokenCategory.DELIMITER
        if t in (TokenType.INTEGER, TokenType.FLOAT, TokenType.BOOLEAN):
            return TokenCategory.LITERAL
        if t == TokenType.IDENTIFIER:
            return TokenCategory.IDENTIFIER
        return TokenCategory.CONTROL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.name,
            "lexeme": self.lexeme,
            "literal": self.literal,
            "line": self.line,
            "column": self.column,
            "source_pos": self.source_pos,
            "category": self.category.value,
        }

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.lexeme}', line={self.line}, col={self.column})"


class TokenManager:
    """
    Abstractions for storing, inspecting, categorizing, and serializing token streams.
    """

    def __init__(self, tokens: Optional[List[Token]] = None):
        self.tokens: List[Token] = tokens or []

    def add(self, token: Token) -> None:
        self.tokens.append(token)

    def to_list(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.tokens]

    def count_by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for t in self.tokens:
            cat = t.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def __len__(self) -> int:
        return len(self.tokens)

    def __getitem__(self, index: int) -> Token:
        return self.tokens[index]
