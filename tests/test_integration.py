"""
End-to-end integration tests for the Veyra Visual Compiler pipeline.
Validates end-to-end transitions: Source -> Tokens -> AST -> Symbol Table -> Diagnostics -> Output.
"""

import pytest
from backend.compiler import VeyraCompiler


@pytest.fixture
def compiler():
    return VeyraCompiler()


def test_end_to_end_sample_program(compiler):
    source = "let x = 10 + 5 * 2;\nprint(x);"
    result = compiler.compile(source)

    assert result.success is True
    assert result.output == "20"
    assert result.output_lines == ["20"]
    assert len(result.diagnostics) == 0

    # Verify stages executed
    assert result.stages_executed == ["Lexer", "Parser", "Semantic Analysis", "Interpreter"]

    # Verify token manager stream
    assert len(result.tokens) > 0
    assert result.tokens[0]["lexeme"] == "let"
    assert result.tokens[0]["category"] == "Keyword"

    # Verify AST structure
    assert result.ast is not None
    assert result.ast["node_type"] == "Program"
    assert len(result.ast["children"]) == 2

    # Verify Symbol Table
    assert len(result.symbol_table) == 1
    sym = result.symbol_table[0]
    assert sym["name"] == "x"
    assert sym["type"] == "int"
    assert sym["value"] == "20"
    assert sym["scope"] == "global"


def test_end_to_end_lexical_error(compiler):
    source = "let bad = #invalid;"
    result = compiler.compile(source)

    assert result.success is False
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag["stage"] == "Lexical Error"
    assert "Invalid character" in diag["message"]
    assert result.stages_executed == []  # Halted at lexer


def test_end_to_end_syntax_error(compiler):
    source = "let x = ;"
    result = compiler.compile(source)

    assert result.success is False
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag["stage"] == "Syntax Error"
    assert "Unexpected token ';'" in diag["message"]
    assert "Lexer" in result.stages_executed
    assert "Parser" not in result.stages_executed  # Failed during parsing


def test_end_to_end_semantic_error(compiler):
    source = "let a = 10;\nlet a = 20;"
    result = compiler.compile(source)

    assert result.success is False
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag["stage"] == "Semantic Error"
    assert "Duplicate declaration" in diag["message"]
    assert "Interpreter" not in result.stages_executed


def test_end_to_end_runtime_error(compiler):
    source = "let num = 50;\nlet err = num / 0;"
    result = compiler.compile(source)

    assert result.success is False
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag["stage"] == "Runtime Error"
    assert "Division by zero" in diag["message"]
    assert "Interpreter" not in result.stages_executed or "Semantic Analysis" in result.stages_executed


def test_end_to_end_nested_scope_and_conditionals(compiler):
    source = """
    let base = 100;
    let multiplier = 2;
    let result = 0;
    if (multiplier > 1) {
        result = base * multiplier;
    } else {
        result = base;
    }
    print(result);
    """
    result = compiler.compile(source)
    assert result.success is True
    assert result.output == "200"
