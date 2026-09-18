"""
Automated unit tests for the VCL Parser.
Tests recursive-descent parsing, operator precedence, AST construction, and syntax error diagnostics.
"""

import pytest
from backend.lexer import Lexer
from backend.parser import Parser
from backend.errors import SyntaxError
from backend.ast_nodes import (
    Program,
    VarDeclaration,
    Assignment,
    PrintStatement,
    IfStatement,
    BinaryExpression,
    Literal,
    Identifier,
)


def parse_source(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def test_parse_sample_program():
    source = "let x = 10 + 5 * 2; print(x);"
    program = parse_source(source)

    assert len(program.statements) == 2
    stmt1 = program.statements[0]
    stmt2 = program.statements[1]

    # Statement 1: let x = 10 + 5 * 2;
    assert isinstance(stmt1, VarDeclaration)
    assert stmt1.name == "x"
    # Precedence check: '+' must be at the root of binary expression, '*' below it
    assert isinstance(stmt1.initializer, BinaryExpression)
    assert stmt1.initializer.operator == "+"
    assert isinstance(stmt1.initializer.left, Literal)
    assert stmt1.initializer.left.value == 10

    mult_expr = stmt1.initializer.right
    assert isinstance(mult_expr, BinaryExpression)
    assert mult_expr.operator == "*"
    assert mult_expr.left.value == 5
    assert mult_expr.right.value == 2

    # Statement 2: print(x);
    assert isinstance(stmt2, PrintStatement)
    assert isinstance(stmt2.expression, Identifier)
    assert stmt2.expression.name == "x"


def test_parenthesized_expression_precedence():
    source = "let res = (10 + 5) * 2;"
    program = parse_source(source)
    stmt = program.statements[0]

    assert isinstance(stmt, VarDeclaration)
    assert isinstance(stmt.initializer, BinaryExpression)
    assert stmt.initializer.operator == "*"
    assert isinstance(stmt.initializer.left, BinaryExpression)
    assert stmt.initializer.left.operator == "+"


def test_relational_and_logical_precedence():
    source = "let cond = x > 5 && y <= 10 || z == 20;"
    program = parse_source(source)
    stmt = program.statements[0]

    # Logical OR has lower precedence than AND
    assert isinstance(stmt.initializer, BinaryExpression)
    assert stmt.initializer.operator == "||"
    assert stmt.initializer.left.operator == "&&"


def test_assignment_statement():
    source = "counter = counter + 1;"
    program = parse_source(source)
    stmt = program.statements[0]

    assert isinstance(stmt, Assignment)
    assert stmt.target == "counter"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.operator == "+"


def test_if_else_statement():
    source = "if (x > 0) { print(1); } else { print(0); }"
    program = parse_source(source)
    stmt = program.statements[0]

    assert isinstance(stmt, IfStatement)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.else_branch is not None


def test_syntax_error_missing_semicolon():
    source = "let x = 10\nprint(x);"
    with pytest.raises(SyntaxError) as exc_info:
        parse_source(source)
    err = exc_info.value
    assert "Expected ';'" in err.message


def test_syntax_error_missing_initializer():
    source = "let x;"
    with pytest.raises(SyntaxError) as exc_info:
        parse_source(source)
    err = exc_info.value
    assert "Expected '='" in err.message


def test_syntax_error_unclosed_parenthesis():
    source = "let x = (10 + 5;"
    with pytest.raises(SyntaxError) as exc_info:
        parse_source(source)
    err = exc_info.value
    assert "Expected ')'" in err.message
