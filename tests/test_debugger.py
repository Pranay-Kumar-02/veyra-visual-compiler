"""
Unit tests for the Step-by-Step Debugger and Execution Tracer.
Validates event ordering, variable snapshot integrity, branch decision tracking,
output accumulation, and runtime error capture.
"""

import pytest
from backend.lexer import Lexer
from backend.parser import Parser
from backend.semantic import SemanticAnalyzer
from backend.symbol_table import SymbolTable
from backend.debugger import TracedInterpreter
from backend.errors import RuntimeCompilerError


def parse_and_validate(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    sym_table = SymbolTable()
    analyzer = SemanticAnalyzer(sym_table)
    sym_table, diags = analyzer.analyze(ast)
    assert not any(d.severity.value == "ERROR" for d in diags)
    return ast, sym_table


def test_debugger_event_sequence_and_variables():
    source = """
    let x = 10;
    let y = 20;
    let z = x + y;
    print(z);
    """
    ast, sym_table = parse_and_validate(source)
    debugger = TracedInterpreter(sym_table)
    output, _, trace = debugger.interpret_with_trace(ast)

    assert output == ["30"]
    assert trace.completed_normally is True
    assert trace.total_steps == 6  # start, x=10, y=20, z=x+y, print(z), completed

    events = trace.events
    assert events[0].event_type == "start"

    # Step 1: x = 10
    ev1 = events[1]
    assert ev1.event_type == "var_declare"
    assert ev1.changed_variable == "x"
    assert "x" in ev1.variables
    assert ev1.variables["x"]["value"] == 10

    # Step 2: y = 20
    ev2 = events[2]
    assert ev2.event_type == "var_declare"
    assert ev2.changed_variable == "y"
    assert "x" in ev2.variables
    assert "y" in ev2.variables
    assert ev2.variables["y"]["value"] == 20

    # Step 3: z = x + y
    ev3 = events[3]
    assert ev3.event_type == "var_declare"
    assert ev3.changed_variable == "z"
    assert ev3.variables["z"]["value"] == 30

    # Step 4: print(z)
    ev4 = events[4]
    assert ev4.event_type == "print"
    assert ev4.output_so_far == ["30"]

    # Step 5: completed
    assert events[5].event_type == "completed"


def test_debugger_assignment_mutation():
    source = """
    let counter = 1;
    counter = counter + 5;
    print(counter);
    """
    ast, sym_table = parse_and_validate(source)
    debugger = TracedInterpreter(sym_table)
    output, _, trace = debugger.interpret_with_trace(ast)

    assert output == ["6"]
    # Check that assignment event records changed variable
    assign_event = [e for e in trace.events if e.event_type == "assignment"][0]
    assert assign_event.changed_variable == "counter"
    assert assign_event.variables["counter"]["value"] == 6


def test_debugger_branch_decision_tracking():
    source = """
    let score = 85;
    if (score >= 50) {
        print(1);
    } else {
        print(0);
    }
    """
    ast, sym_table = parse_and_validate(source)
    debugger = TracedInterpreter(sym_table)
    output, _, trace = debugger.interpret_with_trace(ast)

    assert output == ["1"]
    branch_event = [e for e in trace.events if e.event_type == "branch_decision"][0]
    assert branch_event.branch_info["evaluated_result"] is True
    assert branch_event.branch_info["branch_taken"] == "Then"

    # Now test with score < 50 taking Else branch
    source_else = """
    let score = 30;
    if (score >= 50) {
        print(1);
    } else {
        print(0);
    }
    """
    ast2, sym_table2 = parse_and_validate(source_else)
    debugger2 = TracedInterpreter(sym_table2)
    output2, _, trace2 = debugger2.interpret_with_trace(ast2)

    assert output2 == ["0"]
    branch_event2 = [e for e in trace2.events if e.event_type == "branch_decision"][0]
    assert branch_event2.branch_info["evaluated_result"] is False
    assert branch_event2.branch_info["branch_taken"] == "Else"


def test_debugger_runtime_error_event():
    source = """
    let a = 10;
    let b = 0;
    let c = a / b;
    """
    ast, sym_table = parse_and_validate(source)
    debugger = TracedInterpreter(sym_table)

    with pytest.raises(RuntimeCompilerError) as exc_info:
        debugger.interpret_with_trace(ast)

    # Check that an error event was recorded in trace_events before raising
    events = debugger.trace_events
    err_event = events[-1]
    assert err_event.event_type == "runtime_error"
    assert "Division by zero" in err_event.description
    assert err_event.error is not None
    assert "Division by zero" in err_event.error["message"]


def test_debugger_repeatable_independent_sessions():
    source1 = "let a = 1; print(a);"
    source2 = "let b = 2; print(b);"

    ast1, sym1 = parse_and_validate(source1)
    ast2, sym2 = parse_and_validate(source2)

    debugger = TracedInterpreter()
    out1, _, trace1 = debugger.interpret_with_trace(ast1)
    assert out1 == ["1"]
    assert "a" in trace1.events[1].variables
    assert "b" not in trace1.events[1].variables

    out2, _, trace2 = debugger.interpret_with_trace(ast2)
    assert out2 == ["2"]
    assert "b" in trace2.events[1].variables
    assert "a" not in trace2.events[1].variables
