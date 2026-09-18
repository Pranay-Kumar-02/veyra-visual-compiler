"""
Automated unit tests for the VCL Lexer.
Tests lexical tokenization, literal types, line/column tracking, and error handling.
"""

import pytest
from backend.tokens import TokenType
from backend.lexer import Lexer
from backend.errors import LexicalError


def test_tokenize_keywords():
    source = "let if else print true false"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert [t.type for t in tokens] == [
        TokenType.LET,
        TokenType.IF,
        TokenType.ELSE,
        TokenType.PRINT,
        TokenType.BOOLEAN,
        TokenType.BOOLEAN,
        TokenType.EOF,
    ]
    assert tokens[4].literal is True
    assert tokens[5].literal is False


def test_tokenize_identifiers_and_literals():
    source = "let count = 42; let pi = 3.1415;"
    tokens = Lexer(source).tokenize()

    assert tokens[0].type == TokenType.LET
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].lexeme == "count"
    assert tokens[2].type == TokenType.ASSIGN
    assert tokens[3].type == TokenType.INTEGER
    assert tokens[3].literal == 42
    assert tokens[4].type == TokenType.SEMICOLON

    assert tokens[5].type == TokenType.LET
    assert tokens[6].type == TokenType.IDENTIFIER
    assert tokens[6].lexeme == "pi"
    assert tokens[7].type == TokenType.ASSIGN
    assert tokens[8].type == TokenType.FLOAT
    assert tokens[8].literal == 3.1415
    assert tokens[9].type == TokenType.SEMICOLON


def test_tokenize_all_operators():
    source = "+ - * / % == != < > <= >= && || ! ="
    tokens = Lexer(source).tokenize()

    expected_types = [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.EQ_EQ,
        TokenType.BANG_EQ,
        TokenType.LESS,
        TokenType.GREATER,
        TokenType.LESS_EQ,
        TokenType.GREATER_EQ,
        TokenType.AND_AND,
        TokenType.OR_OR,
        TokenType.BANG,
        TokenType.ASSIGN,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types


def test_tokenize_delimiters():
    source = "( ) { } ; ,"
    tokens = Lexer(source).tokenize()
    expected = [
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.COMMA,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_line_and_column_tracking():
    source = "let x = 10;\nlet y = 20;"
    tokens = Lexer(source).tokenize()

    # First line: let x = 10;
    assert tokens[0].line == 1 and tokens[0].column == 1  # let
    assert tokens[1].line == 1 and tokens[1].column == 5  # x
    assert tokens[2].line == 1 and tokens[2].column == 7  # =
    assert tokens[3].line == 1 and tokens[3].column == 9  # 10

    # Second line: let y = 20;
    assert tokens[5].line == 2 and tokens[5].column == 1  # let
    assert tokens[6].line == 2 and tokens[6].column == 5  # y
    assert tokens[7].line == 2 and tokens[7].column == 7  # =
    assert tokens[8].line == 2 and tokens[8].column == 9  # 20


def test_lexical_error_invalid_character():
    source = "let x = @10;"
    with pytest.raises(LexicalError) as exc_info:
        Lexer(source).tokenize()
    err = exc_info.value
    assert "Invalid character '@'" in err.message
    assert err.line == 1
    assert err.column == 9


def test_lexical_error_single_ampersand():
    source = "let valid = true & false;"
    with pytest.raises(LexicalError) as exc_info:
        Lexer(source).tokenize()
    err = exc_info.value
    assert "Unexpected single '&'" in err.message


def test_lexical_error_single_pipe():
    source = "let valid = true | false;"
    with pytest.raises(LexicalError) as exc_info:
        Lexer(source).tokenize()
    err = exc_info.value
    assert "Unexpected single '|'" in err.message


def test_lexical_error_multiple_decimals():
    source = "let n = 12.34.56;"
    with pytest.raises(LexicalError) as exc_info:
        Lexer(source).tokenize()
    err = exc_info.value
    assert "multiple decimal points" in err.message
