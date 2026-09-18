# Contributing to Veyra Visual Compiler

Thank you for your interest in contributing to **Veyra Visual Compiler**! Veyra is an interactive compiler engineering environment designed to make intermediate compiler representations inspectable, observable, and educational without sacrificing technical rigor.

We welcome contributions from compiler engineers, programming language enthusiasts, and software developers.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

---

## Development Workflow

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- `pytest` for automated test execution
- Modern web browser (Chrome, Firefox, Edge, Safari)

### 2. Local Setup
```bash
# Clone repository
git clone https://github.com/Pranay-Kumar-02/veyra-visual-compiler.git
cd veyra-visual-compiler

# Create and activate virtual environment
python -m venv .venv

# Windows (Command Prompt / PowerShell)
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Test Suite
Before making any changes, verify that all existing tests pass:
```bash
python -m pytest tests/ -v
```

### 4. Running the Web Workspace
```bash
python app.py
```
Open `http://127.0.0.1:5000` to interact with the local development build.

---

## Architecture Overview

When contributing to compiler phases, maintain strict separation of concerns across modules:

- **Lexer & Tokens** (`backend/tokens.py`, `backend/lexer.py`):
  - Hand-written character scanning.
  - Every token must preserve line, column, and character offset coordinates.
- **AST Nodes** (`backend/ast_nodes.py`):
  - Typed dataclasses/classes implementing `to_dict()` for recursive JSON serialization consumed by the visualizer.
- **Parser** (`backend/parser.py`):
  - Hand-written recursive descent.
  - Maintain operator precedence levels and proper error recovery boundaries.
- **Symbol Table & Scopes** (`backend/symbol_table.py`):
  - Hierarchical parent-pointer scope stack.
- **Semantic Analyzer** (`backend/semantic.py`):
  - Static validation pass: identifier resolution, duplicate declaration checks, and type compatibility.
- **Interpreter** (`backend/interpreter.py`):
  - Tree-walking evaluation executing the AST directly (not raw text).
- **Diagnostics** (`backend/errors.py`):
  - All errors must subclass `VeyraCompilerException` and carry `stage`, `message`, `line`, `column`, `severity`, and optional `hint`.

---

## Guidelines for Adding Language Features (Phase 2 Roadmap)

If you plan to implement features targeted for Phase 2 (e.g., loops, functions, or richer types):

1. **Update Language Grammar**: Document changes in EBNF and update `README.md`.
2. **Tokenization**: Add new `TokenType` entries and update `Lexer._scan_token()` / keyword tables.
3. **AST Node System**: Define typed AST node classes with rich `to_dict()` metadata.
4. **Parsing**: Implement recursive descent parsing with appropriate precedence.
5. **Semantic Validation**: Add scope resolution and type checking rules.
6. **Execution**: Implement interpreter evaluation in `Interpreter.execute()` / `Interpreter.evaluate()`.
7. **Testing**: Add dedicated unit tests in `tests/` covering both valid programs and error boundaries.

---

## Submitting Pull Requests

1. **Fork the Repository** and create a feature branch (`git checkout -b feat/your-feature-name`).
2. **Ensure Code Quality**:
   - Follow PEP 8 style guidelines.
   - Include type annotations where useful.
   - Write clear docstrings for new public functions and classes.
3. **Run Tests**:
   - All tests must pass: `python -m pytest tests/ -v`
   - Add new tests for any added functionality.
4. **Commit & Push**:
   - Use conventional commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
5. **Open a Pull Request**:
   - Clearly explain the problem solved or feature added.
   - Link any related issues.
