"""
Automated unit tests for the VCL Interpreter.
Tests tree-walking evaluation, runtime execution, print buffering, and runtime exceptions.
"""

import pytest
from backend.lexer import Lexer
from backend.parser import Parser
from backend.semantic import SemanticAnalyzer
from backend.interpreter import Interpreter
from backend.errors import RuntimeCompilerError


def run_code(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    sym_table, diags = analyzer.analyze(program)
    assert len(diags) == 0, f"Unexpected semantic errors: {diags}"

    interpreter = Interpreter(sym_table)
    output, updated_table = interpreter.interpret(program)
    return output, updated_table


def test_eval_sample_program_returns_twenty():
    """
    Mandatory baseline test from specification:
    let x = 10 + 5 * 2;
    print(x);
    MUST return: 20
    """
    source = "let x = 10 + 5 * 2; print(x);"
    output, sym_table = run_code(source)

    assert output == ["20"]
    sym_x = sym_table.lookup("x")
    assert sym_x is not None
    assert sym_x.value == 20
    assert sym_x.type_name == "int"
    assert sym_x.scope_name == "global"


def test_eval_parenthesized_precedence():
    source = "let x = (10 + 5) * 2; print(x);"
    output, _ = run_code(source)
    assert output == ["30"]


def test_eval_float_arithmetic():
    source = "let a = 5.5 + 4.5; print(a);"
    output, _ = run_code(source)
    assert output == ["10"]


def test_eval_assignment_mutation():
    source = "let count = 1;\ncount = count + 10;\nprint(count);"
    output, sym_table = run_code(source)
    assert output == ["11"]
    assert sym_table.lookup("count").value == 11


def test_eval_if_else_branching():
    source = """
    let score = 85;
    if (score >= 50) {
        print(1);
    } else {
        print(0);
    }
    """
    output, _ = run_code(source)
    assert output == ["1"]

    source_false = """
    let score = 30;
    if (score >= 50) {
        print(1);
    } else {
        print(0);
    }
    """
    output_false, _ = run_code(source_false)
    assert output_false == ["0"]


def test_eval_boolean_logic():
    source = """
    let flag1 = true && false;
    let flag2 = true || false;
    let flag3 = !flag1;
    print(flag1);
    print(flag2);
    print(flag3);
    """
    output, _ = run_code(source)
    assert output == ["false", "true", "true"]


def test_runtime_error_division_by_zero():
    source = "let a = 100 / 0;"
    with pytest.raises(RuntimeCompilerError) as exc_info:
        run_code(source)
    err = exc_info.value
    assert "Division by zero" in err.message


def test_runtime_error_modulo_by_zero():
    source = "let a = 100 % 0;"
    with pytest.raises(RuntimeCompilerError) as exc_info:
        run_code(source)
    err = exc_info.value
    assert "Modulo by zero" in err.message
