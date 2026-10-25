"""
Unit tests for Control Flow Graph (CFG) construction and analysis.
Validates basic block leader identification, edge resolution, reachability,
validation error detection, and back-edge detection.
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
    LabelInstruction,
    JumpInstruction,
    JumpIfFalseInstruction,
    PrintInstruction,
)
from backend.cfg import CFGBuilder, ControlFlowGraph


def compile_to_ir(source: str) -> IRProgram:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    sym_table = SymbolTable()
    analyzer = SemanticAnalyzer(sym_table)
    sym_table, diags = analyzer.analyze(ast)
    assert not any(d.severity.value == "ERROR" for d in diags)
    return IRGenerator().generate(ast)


def test_cfg_empty_program():
    builder = CFGBuilder()
    cfg = builder.build(IRProgram(instructions=[], temp_count=0, label_count=0))
    assert cfg.blocks == []
    assert cfg.edges == []
    assert cfg.entry_block_id is None
    assert cfg.validation_errors == []


def test_cfg_straight_line():
    source = """
    let a = 10;
    let b = 20;
    let c = a + b;
    print(c);
    """
    ir_prog = compile_to_ir(source)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    # In straight-line code with no jumps or labels, there is exactly 1 basic block
    assert len(cfg.blocks) == 1
    assert cfg.blocks[0].is_entry is True
    assert cfg.blocks[0].is_exit is True
    assert cfg.blocks[0].reachable is True
    assert len(cfg.edges) == 0
    assert len(cfg.blocks[0].instructions) == 5  # a=10, b=20, t1=a+b, c=t1, print c


def test_cfg_if_else_branching():
    source = """
    let score = 85;
    if (score >= 50) {
        print(1);
    } else {
        print(0);
    }
    """
    ir_prog = compile_to_ir(source)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    # Blocks:
    # B0 (Entry): score=85, t1=score>=50, if_false t1 goto L1
    # B1 (Then): print 1, goto L2
    # B2 (Else): L1:, print 0
    # B3 (Merge/Exit): L2:
    assert len(cfg.blocks) >= 3
    assert cfg.entry_block_id == "B0"
    assert all(b.reachable for b in cfg.blocks)

    # Verify conditional edges from B0
    b0 = cfg.get_block("B0")
    assert b0 is not None
    assert len(b0.successors) == 2

    # Edges should include 'false' (branch to else) and 'true' (fallthrough to then)
    b0_edges = [e for e in cfg.edges if e.from_block == "B0"]
    edge_types = {e.edge_type for e in b0_edges}
    assert "false" in edge_types
    assert "true" in edge_types

    # Then block should have unconditional jump to Merge block
    then_block = cfg.get_block("B1")
    assert then_block is not None
    then_edges = [e for e in cfg.edges if e.from_block == "B1"]
    assert any(e.edge_type == "unconditional" for e in then_edges)


def test_cfg_if_without_else():
    source = """
    let x = 10;
    if (x > 5) {
        print(x);
    }
    let y = 20;
    """
    ir_prog = compile_to_ir(source)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    assert cfg.entry_block_id == "B0"
    assert all(b.reachable for b in cfg.blocks)
    # Check that B0 branches to the end label if false, or falls through if true
    b0_edges = [e for e in cfg.edges if e.from_block == "B0"]
    assert len(b0_edges) == 2


def test_cfg_unreachable_block_and_reachability():
    # Construct an IR with an unreachable block manually
    instructions = [
        CopyInstruction(result="x", source="10"),
        JumpInstruction(target="L_EXIT"),
        # Dead code block below
        CopyInstruction(result="dead_var", source="999"),
        PrintInstruction(value="dead_var"),
        # Exit label
        LabelInstruction(name="L_EXIT"),
        PrintInstruction(value="x"),
    ]
    ir_prog = IRProgram(instructions=instructions, temp_count=0, label_count=1)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    # Leaders:
    # 0: x = 10 (leader 1)
    # 2: dead_var = 999 (immediately follows jump)
    # 4: L_EXIT: (jump target)
    # So 3 basic blocks:
    # B0: x = 10, goto L_EXIT
    # B1: dead_var = 999, print dead_var
    # B2: L_EXIT:, print x
    assert len(cfg.blocks) == 3
    b0 = cfg.get_block("B0")
    b1 = cfg.get_block("B1")
    b2 = cfg.get_block("B2")

    assert b0.reachable is True
    assert b1.reachable is False  # B1 is unreachable from entry B0!
    assert b2.reachable is True   # B2 is reachable via goto L_EXIT


def test_cfg_invalid_target_validation():
    # Construct an IR with a jump to non-existent label
    instructions = [
        CopyInstruction(result="x", source="5"),
        JumpInstruction(target="NON_EXISTENT_LABEL"),
        PrintInstruction(value="x"),
    ]
    ir_prog = IRProgram(instructions=instructions, temp_count=0, label_count=0)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    assert len(cfg.validation_errors) > 0
    assert not cfg.to_dict()["is_valid"]
    assert any("NON_EXISTENT_LABEL" in err for err in cfg.validation_errors)


def test_cfg_back_edge_detection():
    # Construct an IR with a backward jump to an earlier label
    instructions = [
        LabelInstruction(name="LOOP_HEAD"),
        CopyInstruction(result="i", source="1"),
        JumpInstruction(target="LOOP_HEAD"),
    ]
    ir_prog = IRProgram(instructions=instructions, temp_count=0, label_count=1)
    builder = CFGBuilder()
    cfg = builder.build(ir_prog)

    assert len(cfg.edges) == 1
    edge = cfg.edges[0]
    assert edge.is_backedge is True
