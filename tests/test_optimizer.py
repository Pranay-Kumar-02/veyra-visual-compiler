"""
Comprehensive unit tests for the 3AC Intermediate Representation Optimization Pipeline.
Tests each individual pass (Folding, Propagation, Algebraic, Dead Code, Unreachable Code),
correctness safeguards (division by zero, reassignment, branch merges, valid labels),
and end-to-end optimization results.
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
    PrintInstruction,
)
from backend.optimizer import (
    ConstantFoldingPass,
    ConstantPropagationPass,
    AlgebraicSimplificationPass,
    DeadCodeEliminationPass,
    UnreachableCodeEliminationPass,
    OptimizationPipeline,
)


def compile_to_ir(source: str) -> IRProgram:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    sym_table = SymbolTable()
    analyzer = SemanticAnalyzer(sym_table)
    sym_table, diags = analyzer.analyze(ast)
    assert not any(d.severity.value == "ERROR" for d in diags)
    return IRGenerator().generate(ast)


def test_constant_folding_arithmetic():
    insts = [
        BinaryOpInstruction(result="t1", op="+", left="10", right="20"),
        BinaryOpInstruction(result="t2", op="*", left="5", right="4"),
        BinaryOpInstruction(result="t3", op="-", left="100", right="45"),
        BinaryOpInstruction(result="t4", op="/", left="20", right="4"),
        BinaryOpInstruction(result="t5", op="%", left="17", right="5"),
    ]
    pass_obj = ConstantFoldingPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 5
    assert all(isinstance(i, CopyInstruction) for i in optimized)
    assert optimized[0].source == "30"
    assert optimized[1].source == "20"
    assert optimized[2].source == "55"
    assert optimized[3].source == "5"
    assert optimized[4].source == "2"


def test_constant_folding_safeguard_zero_division():
    """Correctness safeguard: Division and modulo by zero MUST NOT be folded at compile time."""
    insts = [
        BinaryOpInstruction(result="t1", op="/", left="10", right="0"),
        BinaryOpInstruction(result="t2", op="%", left="10", right="0"),
    ]
    pass_obj = ConstantFoldingPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 0
    assert optimized[0].op == "/"
    assert optimized[0].right == "0"
    assert optimized[1].op == "%"
    assert optimized[1].right == "0"


def test_constant_folding_relational_and_logical():
    insts = [
        BinaryOpInstruction(result="t1", op=">=", left="85", right="50"),
        BinaryOpInstruction(result="t2", op="<", left="10", right="5"),
        BinaryOpInstruction(result="t3", op="==", left="5", right="5"),
        BinaryOpInstruction(result="t4", op="&&", left="true", right="false"),
        BinaryOpInstruction(result="t5", op="||", left="false", right="true"),
        UnaryOpInstruction(result="t6", op="!", operand="true"),
        UnaryOpInstruction(result="t7", op="-", operand="15"),
    ]
    pass_obj = ConstantFoldingPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 7
    assert optimized[0].source == "true"
    assert optimized[1].source == "false"
    assert optimized[2].source == "true"
    assert optimized[3].source == "false"
    assert optimized[4].source == "true"
    assert optimized[5].source == "false"
    assert optimized[6].source == "-15"


def test_constant_propagation_local():
    insts = [
        CopyInstruction(result="a", source="10"),
        CopyInstruction(result="b", source="20"),
        BinaryOpInstruction(result="t1", op="+", left="a", right="b"),
        PrintInstruction(value="a"),
    ]
    pass_obj = ConstantPropagationPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 2
    # t1 should now be 10 + 20
    assert isinstance(optimized[2], BinaryOpInstruction)
    assert optimized[2].left == "10"
    assert optimized[2].right == "20"
    # PrintInstruction should print 10
    assert isinstance(optimized[3], PrintInstruction)
    assert optimized[3].value == "10"


def test_constant_propagation_with_reassignment():
    insts = [
        CopyInstruction(result="x", source="5"),
        PrintInstruction(value="x"),  # prints 5
        CopyInstruction(result="x", source="100"),
        PrintInstruction(value="x"),  # prints 100
    ]
    pass_obj = ConstantPropagationPass()
    optimized, transforms = pass_obj.run(insts)

    assert optimized[1].value == "5"
    assert optimized[3].value == "100"


def test_algebraic_simplification():
    insts = [
        BinaryOpInstruction(result="t1", op="+", left="x", right="0"),
        BinaryOpInstruction(result="t2", op="-", left="y", right="0"),
        BinaryOpInstruction(result="t3", op="*", left="z", right="1"),
        BinaryOpInstruction(result="t4", op="*", left="w", right="0"),
        BinaryOpInstruction(result="t5", op="/", left="v", right="1"),
        BinaryOpInstruction(result="t6", op="&&", left="p", right="true"),
        BinaryOpInstruction(result="t7", op="||", left="q", right="false"),
    ]
    pass_obj = AlgebraicSimplificationPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 7
    assert optimized[0].source == "x"
    assert optimized[1].source == "y"
    assert optimized[2].source == "z"
    assert optimized[3].source == "0"
    assert optimized[4].source == "v"
    assert optimized[5].source == "p"
    assert optimized[6].source == "q"


def test_dead_code_elimination():
    insts = [
        BinaryOpInstruction(result="t1", op="*", left="5", right="2"),  # never used!
        BinaryOpInstruction(result="t2", op="+", left="10", right="20"),
        CopyInstruction(result="ans", source="t2"),  # t2 used here
        PrintInstruction(value="ans"),
    ]
    pass_obj = DeadCodeEliminationPass()
    optimized, transforms = pass_obj.run(insts)

    assert len(transforms) == 1
    # t1 eliminated
    assert not any(getattr(i, "result", None) == "t1" for i in optimized)
    # t2 preserved because ans uses it
    assert any(getattr(i, "result", None) == "t2" for i in optimized)


def test_unreachable_code_elimination_branch_folding():
    insts = [
        JumpIfFalseInstruction(condition="true", target="L1"),  # condition true, branch never taken
        PrintInstruction(value="alive"),
        JumpIfFalseInstruction(condition="false", target="L2"),  # condition false, always taken
        PrintInstruction(value="dead_after_unconditional"),
        LabelInstruction(name="L1"),
        LabelInstruction(name="L2"),
    ]
    pass_obj = UnreachableCodeEliminationPass()
    optimized, transforms = pass_obj.run(insts)

    # First jump-if-false true eliminated
    # Second converted to goto L2
    # dead instruction after goto L2 eliminated
    assert not any(isinstance(i, JumpIfFalseInstruction) for i in optimized)
    assert any(isinstance(i, JumpInstruction) and i.target == "L2" for i in optimized)
    assert not any(isinstance(i, PrintInstruction) and i.value == "dead_after_unconditional" for i in optimized)


def test_full_optimization_pipeline_on_expression():
    source = """
    let x = 10 + 5 * 2;
    print(x);
    """
    ir_prog = compile_to_ir(source)
    pipeline = OptimizationPipeline()
    result = pipeline.optimize(ir_prog)

    # In original IR:
    # t1 = 5 * 2
    # t2 = 10 + t1
    # x = t2
    # print x
    # After folding & propagation:
    # 5 * 2 = 10 -> 10 + 10 = 20 -> x = 20 -> print 20
    assert result.is_valid is True
    assert len(result.validation_errors) == 0
    assert result.metrics["optimized_count"] < result.metrics["original_count"]

    opt_text = result.optimized_ir.to_text()
    assert "20" in opt_text
    assert "print 20" in opt_text or "print x" in opt_text


def test_full_optimization_pipeline_preserves_semantics():
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
    ir_prog = compile_to_ir(source)
    pipeline = OptimizationPipeline()
    result = pipeline.optimize(ir_prog)

    assert result.is_valid is True
    # In this code: bonus * 2 = 10; score + 10 = 30; result = 30; 30 >= 30 is TRUE!
    # So if_false 30 >= 30 (true) will NOT branch to else, taking the Then branch!
    assert len(result.validation_errors) == 0
    assert result.metrics["instructions_removed"] > 0
