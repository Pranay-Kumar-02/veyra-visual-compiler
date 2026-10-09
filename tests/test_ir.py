"""
Unit tests for the Three-Address Code (3AC) Intermediate Representation (IR) generator.
Tests operator precedence, temporaries, labels, branches, and AST immutability.
"""

import pytest
from backend.lexer import Lexer
from backend.parser import Parser
from backend.semantic import SemanticAnalyzer
from backend.symbol_table import SymbolTable
from backend.ir import (
    IRGenerator,
    IRProgram,
    CopyInstruction,
    BinaryOpInstruction,
    UnaryOpInstruction,
    LabelInstruction,
    JumpInstruction,
    JumpIfFalseInstruction,
    JumpIfTrueInstruction,
    PrintInstruction,
)


def parse_and_validate(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    sym_table = SymbolTable()
    analyzer = SemanticAnalyzer(sym_table)
    sym_table, diags = analyzer.analyze(ast)
    assert not any(d.severity.value == "ERROR" for d in diags)
    return ast


def test_ir_instruction_representations():
    copy_inst = CopyInstruction(result="x", source="t1", line=1, column=1)
    assert copy_inst.to_text() == "x = t1"
    assert copy_inst.to_dict()["kind"] == "copy"
    assert copy_inst.to_dict()["op"] == "="

    bin_inst = BinaryOpInstruction(result="t1", op="*", left="5", right="2", line=2, column=3)
    assert bin_inst.to_text() == "t1 = 5 * 2"
    assert bin_inst.to_dict()["kind"] == "binary"

    un_inst = UnaryOpInstruction(result="t2", op="-", operand="x", line=3, column=5)
    assert un_inst.to_text() == "t2 = -x"
    assert un_inst.to_dict()["kind"] == "unary"

    lbl_inst = LabelInstruction(name="L1", line=4, column=1)
    assert lbl_inst.to_text() == "L1:"
    assert lbl_inst.to_dict()["kind"] == "label"

    jmp_inst = JumpInstruction(target="L2", line=5, column=1)
    assert jmp_inst.to_text() == "goto L2"
    assert jmp_inst.to_dict()["kind"] == "jump"

    cond_false = JumpIfFalseInstruction(condition="t3", target="L1", line=6, column=1)
    assert cond_false.to_text() == "if_false t3 goto L1"
    assert cond_false.to_dict()["kind"] == "cond_jump_false"

    cond_true = JumpIfTrueInstruction(condition="t3", target="L2", line=6, column=1)
    assert cond_true.to_text() == "if_true t3 goto L2"
    assert cond_true.to_dict()["kind"] == "cond_jump_true"

    pr_inst = PrintInstruction(value="result", line=7, column=1)
    assert pr_inst.to_text() == "print result"
    assert pr_inst.to_dict()["kind"] == "print"


def test_ir_arithmetic_precedence():
    source = "let x = 10 + 5 * 2;\nprint(x);"
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    lines = [line.strip() for line in code.splitlines() if line.strip()]

    # Multiplication must happen before addition
    assert lines[0] == "t1 = 5 * 2"
    assert lines[1] == "t2 = 10 + t1"
    assert lines[2] == "x = t2"
    assert lines[3] == "print x"
    assert ir_prog.temp_count == 2
    assert ir_prog.label_count == 0


def test_ir_parenthesized_precedence():
    source = "let x = (10 + 5) * 2;\nprint(x);"
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    lines = [line.strip() for line in code.splitlines() if line.strip()]

    # Addition must happen before multiplication due to parentheses
    assert lines[0] == "t1 = 10 + 5"
    assert lines[1] == "t2 = t1 * 2"
    assert lines[2] == "x = t2"
    assert lines[3] == "print x"


def test_ir_unary_operators():
    source = "let a = 10;\nlet b = -a;\nlet c = true;\nlet d = !c;"
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    assert "t1 = -a" in code
    assert "b = t1" in code
    assert "t2 = !c" in code
    assert "d = t2" in code


def test_ir_relational_and_logical():
    source = """
    let a = 10;
    let b = 20;
    let r1 = a < b;
    let r2 = a == b;
    let r3 = r1 && r2;
    let r4 = r1 || r2;
    """
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    assert "t1 = a < b" in code
    assert "t2 = a == b" in code
    assert "t3 = r1 && r2" in code
    assert "t4 = r1 || r2" in code


def test_ir_reassignment():
    source = "let count = 0;\ncount = count + 1;\nprint(count);"
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    assert lines[0] == "count = 0"
    assert lines[1] == "t1 = count + 1"
    assert lines[2] == "count = t1"
    assert lines[3] == "print count"


def test_ir_if_else_branching():
    source = """
    let score = 20;
    let bonus = 5;
    let result = score + bonus * 2;
    if (result >= 30) {
        print(result);
    } else {
        print(0);
    }
    """
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    lines = [line.strip() for line in code.splitlines() if line.strip()]

    assert "t1 = bonus * 2" in lines
    assert "t2 = score + t1" in lines
    assert "result = t2" in lines
    assert "t3 = result >= 30" in lines
    assert "if_false t3 goto L1" in lines
    assert "print result" in lines
    assert "goto L2" in lines
    assert "L1:" in lines
    assert "print 0" in lines
    assert "L2:" in lines
    assert ir_prog.label_count == 2


def test_ir_if_without_else():
    source = """
    let x = 10;
    if (x > 5) {
        print(x);
    }
    """
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    lines = [line.strip() for line in code.splitlines() if line.strip()]

    assert "t1 = x > 5" in lines
    assert "if_false t1 goto L1" in lines
    assert "print x" in lines
    assert "L1:" in lines
    assert ir_prog.label_count == 1


def test_ir_nested_conditionals():
    source = """
    let a = 10;
    let b = 20;
    if (a > 5) {
        if (b > 15) {
            print(1);
        } else {
            print(2);
        }
    }
    """
    ast = parse_and_validate(source)
    gen = IRGenerator()
    ir_prog = gen.generate(ast)

    code = ir_prog.to_text()
    assert "if_false t1 goto L1" in code
    assert "if_false t2 goto L2" in code
    assert "goto L3" in code
    assert "L2:" in code
    assert "L3:" in code
    assert "L1:" in code
    assert ir_prog.label_count == 3


def test_ir_ast_immutability():
    source = "let x = 10 + 5 * 2;\nprint(x);"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()

    ast_dict_before = ast.to_dict()

    gen = IRGenerator()
    _ = gen.generate(ast)

    ast_dict_after = ast.to_dict()
    assert ast_dict_before == ast_dict_after


def test_ir_deterministic_counters():
    source = "let a = 1 + 2;\nlet b = 3 + 4;"
    ast = parse_and_validate(source)

    gen1 = IRGenerator()
    prog1 = gen1.generate(ast)

    gen2 = IRGenerator()
    prog2 = gen2.generate(ast)

    assert prog1.to_text() == prog2.to_text()
    assert prog1.temp_count == prog2.temp_count == 2


def test_ir_malformed_input_safety():
    gen = IRGenerator()
    prog = gen.generate(None)
    assert prog.instructions == []
    assert prog.temp_count == 0
    assert prog.label_count == 0
