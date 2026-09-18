# Veyra Visual Compiler

> **Academic Project Title**: *Interactive Visual Compiler with Step-by-Step AST and Symbol Table Visualization*  
> **Target Language**: VCL (*Visual Compiler Language*)  
> **Status**: **Phase 1 Complete** (~35% foundational vertical slice)

[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask_3.1-000000.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-38_Passing-10b981.svg?style=flat&logo=pytest&logoColor=white)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular_Compiler-38bdf8.svg?style=flat)](#compiler-pipeline--architecture)

---

## 1. Problem Statement & Solution

### The Problem
Compiler design education often presents compilation as an impenetrable black box: source code enters, and machine code or errors emerge. Students and engineers struggle to visualize how character streams become lexical tokens, how recursive-descent parsing constructs Abstract Syntax Trees (ASTs), how symbol tables track lexical scopes and variable bindings, and how semantic analysis intercepts bugs before code execution.

### The Solution
**Veyra Visual Compiler** turns the compilation pipeline inside-out. Built with production-grade engineering principles, Veyra exposes every phase of compilation through an interactive developer-tool interface. Developers can inspect token streams, interact with collapsible AST hierarchies, review live symbol tables across nested scopes, and analyze source-located diagnostics in real-time.

---

## 2. Compiler Pipeline & Architecture

Veyra executes a hand-written, real compilation pipeline from source text to evaluation. No regex-based fake parsing or hardcoded token streams are used.

```
+-------------------------------------------------------------------------------+
|                             VCL Source Code                                   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 1. Lexical Analyzer (Character-by-character scanner with line/col tracking)   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 2. Token Stream & TokenManager (Categorization & source coordinates)          |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 3. Recursive-Descent Parser (Operator precedence & typed AST construction)     |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 4. Abstract Syntax Tree (Hierarchical AST Nodes with source locations)        |
+-------------------------------------------------------------------------------+
                         |                                 |
                         v                                 v
+---------------------------------------+  +------------------------------------+
| 5. Semantic Analyzer                  |  | 6. AST Interpreter                 |
| - Undeclared identifier checks        |  | - Evaluates AST expressions        |
| - Duplicate declaration checks        |  | - Evaluates conditionals & blocks  |
| - Type compatibility validation       |  | - Detects runtime errors (div by 0)|
| - Scope-aware identifier resolution   |  | - Buffers stdout program output    |
+---------------------------------------+  +------------------------------------+
                         \                                 /
                          \                               /
                           v                             v
+-------------------------------------------------------------------------------+
| 7. Hierarchical Symbol Table (Scopes, types, runtime values, line:col)        |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 8. Structured Diagnostics Engine & REST API (Flask)                           |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 9. Interactive IDE Frontend (Tokens, Visual AST, Symbol Table, Output)        |
+-------------------------------------------------------------------------------+
```

---

## 3. VCL Language Specification (Source of Truth)

Veyra compiles **VCL** (*Visual Compiler Language*), adhering strictly to the formal academic specification:

### Keywords
```
let    if    else    print    true    false
```

### Arithmetic Operators
```
+      -     *       /        %
```

### Relational Operators
```
==     !=    <       >        <=      >=
```

### Logical Operators
```
&&     ||    !
```

### Assignment & Delimiters
```
=      (     )       {        }       ;       ,
```

### Literals & Identifiers
- **Integer**: Sequences of digits `[0-9]+`
- **Float**: Decimal numbers `[0-9]+\.[0-9]+`
- **Boolean**: `true` or `false`
- **Identifier**: `[A-Za-z_][A-Za-z0-9_]*`

### Formal Grammar (Phase 1)
```ebnf
Program        ::= Statement* EOF
Statement      ::= VarDecl | Assignment | PrintStmt | IfStmt | BlockStmt
VarDecl        ::= "let" IDENTIFIER "=" Expression ";"
Assignment     ::= IDENTIFIER "=" Expression ";"
PrintStmt      ::= "print" "(" Expression ")" ";"
IfStmt         ::= "if" "(" Expression ")" Statement ("else" Statement)?
BlockStmt      ::= "{" Statement* "}"

Expression     ::= LogicalOr
LogicalOr      ::= LogicalAnd ( "||" LogicalAnd )*
LogicalAnd     ::= Equality ( "&&" Equality )*
Equality       ::= Relational ( ( "==" | "!=" ) Relational )*
Relational     ::= Additive ( ( "<" | ">" | "<=" | ">=" ) Additive )*
Additive       ::= Multiplicative ( ( "+" | "-" ) Multiplicative )*
Multiplicative ::= Unary ( ( "*" | "/" | "%" ) Unary )*
Unary          ::= ( "!" | "-" ) Unary | Primary
Primary        ::= INTEGER | FLOAT | BOOLEAN | IDENTIFIER | "(" Expression ")"
```

---

## 4. Phase 1 Scope vs Phase 2/3 Roadmap

### Implemented in Phase 1 (Foundational Vertical Slice ~35%)
- [x] **Character Scanner**: Hand-written lexer tracking 1-indexed line and column positions.
- [x] **Token System**: Structured `Token` dataclass with `TokenType` and `TokenCategory`.
- [x] **Recursive-Descent Parser**: Complete operator precedence climbing (`||` down to unary and primary).
- [x] **Typed AST Hierarchy**: `Program`, `VarDeclaration`, `Assignment`, `PrintStatement`, `IfStatement`, `BlockStatement`, `BinaryExpression`, `UnaryExpression`, `Literal`, `Identifier`.
- [x] **Hierarchical Symbol Table**: Parent-pointer scope stack tracking symbol name, inferred type, evaluated value, scope level, and declaration location.
- [x] **Semantic Analysis**: Undeclared variables, duplicate declarations in the same scope, assignment checks, and basic type compatibility.
- [x] **AST Interpreter**: Tree-walking evaluation of arithmetic, logic, assignments, branching, stdout buffering, and runtime division-by-zero detection.
- [x] **Structured Diagnostics**: No raw tracebacks. Clean source-coordinate errors for Lexical, Syntax, Semantic, and Runtime stages.
- [x] **REST API**: Flask backend providing `/api/compile`, `/api/examples`, `/api/health`.
- [x] **Interactive Web UI**: Modern dark IDE with line numbers, interactive collapsible AST visualizer, symbol table viewer, token cards, and stdout console.
- [x] **Automated Test Suite**: 38 tests across lexer, parser, semantic analyzer, interpreter, and end-to-end integration.

### Planned for Phase 2 & 3
- [ ] **Functions & Procedures**: Parameter bindings, call stack, return values, recursion.
- [ ] **Looping Constructs**: `while` and `for` iterations with control flow graphs.
- [ ] **Intermediate Representation (IR)**: Three-Address Code (3AC) generation and visualization.
- [ ] **Bytecode Virtual Machine**: Stack-based bytecode compiler and virtual machine execution.
- [ ] **Control Flow Graph (CFG)**: Visual block-and-edge graphs for basic blocks.
- [ ] **Optimization Passes**: Constant folding, dead code elimination, and algebraic simplification visualizer.
- [ ] **Step-by-Step Debugger**: Interactive execution stepping through AST nodes in the browser.

---

## 5. Project Directory Structure

```
veyra-visual-compiler/
├── backend/
│   ├── __init__.py           # Package exports
│   ├── tokens.py             # TokenType, Token dataclass, TokenManager
│   ├── errors.py             # Diagnostic model & compiler exceptions
│   ├── lexer.py              # Character-by-character scanner
│   ├── ast_nodes.py          # Typed AST node hierarchy with serializers
│   ├── parser.py             # Recursive-descent hand-written parser
│   ├── symbol_table.py       # Hierarchical scope & symbol tracking
│   ├── semantic.py           # Semantic validation & type analysis
│   ├── interpreter.py        # Tree-walking AST evaluator
│   └── compiler.py           # Unified compilation orchestrator
│
├── frontend/
│   ├── index.html            # Workspace layout & inspection suite
│   ├── style.css             # Dark IDE design system & styles
│   └── app.js                # Interactive AST tree & real-time client
│
├── examples/
│   ├── arithmetic.vcl        # Baseline precedence demonstration
│   ├── conditions.vcl        # If-else branching demonstration
│   ├── scope.vcl             # Block scoping & mutations
│   └── errors.vcl            # Semantic diagnostics demonstration
│
├── tests/
│   ├── __init__.py
│   ├── test_lexer.py         # Lexer unit tests
│   ├── test_parser.py        # Parser & precedence unit tests
│   ├── test_semantic.py      # Semantic analysis unit tests
│   ├── test_interpreter.py   # AST interpreter unit tests
│   └── test_integration.py   # Full pipeline integration tests
│
├── app.py                    # Flask application & REST API server
├── requirements.txt          # Python dependencies
├── .gitignore                # Repository ignore rules
└── README.md                 # Project documentation
```

---

## 6. Installation & Quickstart

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- pip package manager

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/Pranay-Kumar-02/veyra-visual-compiler.git
cd veyra-visual-compiler
python -m pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```
Expected output:
```
tests/test_integration.py::test_end_to_end_sample_program PASSED
tests/test_interpreter.py::test_eval_sample_program_returns_twenty PASSED
...
============================== 38 passed in 0.26s ==============================
```

### 3. Launch the Veyra Web Workspace
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 7. Sample VCL Program & Execution

### Sample Input (`examples/arithmetic.vcl`)
```vcl
let x = 10 + 5 * 2;
print(x);
```

### 1. Token Stream
```
[Keyword: let] [Identifier: x] [Assign: =] [Int: 10] [Op: +] [Int: 5] [Op: *] [Int: 2] [Delim: ;]
[Keyword: print] [Delim: (] [Identifier: x] [Delim: )] [Delim: ;]
```

### 2. AST Representation
```
Program
├── VarDeclaration (let x)
│   └── BinaryExpression (+)
│       ├── Literal (10)
│       └── BinaryExpression (*)
│           ├── Literal (5)
│           └── Literal (2)
└── PrintStatement (print())
    └── Identifier (x)
```

### 3. Symbol Table State
| Identifier | Inferred Type | Evaluated Value | Scope Level | Declaration Location |
| :--- | :--- | :--- | :--- | :--- |
| `x` | `int` | `20` | `global (lvl 0)` | Line 1, Column 1 |

### 4. Output
```
20
```

---

## 8. Diagnostic System

Veyra guarantees that no raw Python tracebacks are ever presented to the user. Errors across all compiler stages produce structured diagnostics:

```
[Syntax Error] Expected ';' after declaration of 'x'.
  --> Line 1, Column 19
  Hint: VCL requires semicolons at the end of declarations.
```

```
[Semantic Error] Duplicate declaration of identifier 'a' in the same scope.
  --> Line 2, Column 1
  Hint: Identifier 'a' was already declared at line 1.
```

```
[Runtime Error] Division by zero encountered during execution.
  --> Line 1, Column 14
  Hint: Ensure divisor expression does not evaluate to 0.
```

---

## 9. Diagnostic Metrics Notice

Stage timing durations displayed in the output tab (`Pipeline Duration`) are intended strictly for developer diagnostic visibility and educational inspection of compilation phases. They do not constitute formal performance benchmarks.

---

## 10. License & Academic Attribution

Developed as a Compiler Design Laboratory project:  
*Interactive Visual Compiler with Step-by-Step AST and Symbol Table Visualization*.  
Licensed under the MIT License.
