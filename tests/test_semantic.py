"""
Automated unit tests for the VCL Semantic Analyzer.
Tests symbol resolution, scope isolation, type consistency, and diagnostic generation.
"""

import pytest
from backend.lexer import Lexer
from backend.parser import Parser
from backend.semantic import SemanticAnalyzer
from backend.errors import DiagnosticStage, DiagnosticSeverity


def analyze_source(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    sym_table, diagnostics = analyzer.analyze(program)
    return sym_table, diagnostics


def test_valid_declarations_and_symbols():
    source = "let x = 10; let y = 20.5; let flag = true;"
    sym_table, diagnostics = analyze_source(source)

    assert len(diagnostics) == 0
    sym_x = sym_table.lookup("x")
    sym_y = sym_table.lookup("y")
    sym_flag = sym_table.lookup("flag")

    assert sym_x is not None and sym_x.type_name == "int"
    assert sym_y is not None and sym_y.type_name == "float"
    assert sym_flag is not None and sym_flag.type_name == "bool"


def test_undeclared_identifier_in_expression():
    source = "let x = y + 10;"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.stage == DiagnosticStage.SEMANTIC
    assert "Undeclared identifier 'y'" in d.message
    assert d.line == 1


def test_assignment_to_undeclared_variable():
    source = "z = 42;"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert "Cannot assign to undeclared identifier 'z'" in d.message


def test_duplicate_declaration_in_same_scope():
    source = "let a = 10;\nlet a = 20;"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert "Duplicate declaration of identifier 'a'" in d.message
    assert d.line == 2


def test_arithmetic_on_boolean_error():
    source = "let res = true + 5;"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) >= 1
    assert any("cannot be applied to boolean" in d.message for d in diagnostics)


def test_if_condition_non_boolean():
    source = "let x = 10;\nif (x + 5) { print(1); }"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) >= 1
    assert any("must evaluate to a boolean" in d.message for d in diagnostics)


def test_block_scope_variable_isolation():
    # Variable 'inner' declared inside block should not be accessible in outer scope
    source = "{\n  let inner = 100;\n}\nprint(inner);"
    _, diagnostics = analyze_source(source)

    assert len(diagnostics) == 1
    assert "Undeclared identifier 'inner'" in diagnostics[0].message
