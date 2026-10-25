# VEYRA VISUAL COMPILER — FINAL REVIEW 3 DEMONSTRATION GUIDE

This guide provides a short, structured, and reproducible walkthrough for the Final Review 3 evaluation of the Veyra Visual Compiler.

---

## 1. Quick Start Commands

```bash
# Terminal 1: Start the Flask Backend Server
python app.py
# Server starts at http://127.0.0.1:5000

# Terminal 2 (Optional for verification): Run Full Automated Test Suite
python -m pytest -v
# Verified: 87 passed in 0.52s
```

Open your browser to: **`http://127.0.0.1:5000`**

---

## 2. Step-by-Step Demonstration Script

### Part 1: Integrated Workspace & Flagship Compilation (Baseline)
1. In the top navigation bar, ensure the preset selector is set to **`Phase 3 Flagship: CFG & Optimization`**.
2. Notice the VCL code in the editor:
   ```vcl
   let score = 20;
   let bonus = 5;
   let result = score + bonus * 2;

   if (result >= 30) {
       print(result);
   } else {
       print(0);
   }
   ```
3. Click the **Run** button (or press `Ctrl + Enter`).
4. In the tab bar, click **`AST`**:
   - Inspect the interactive AST showing typed `Program`, `VarDeclaration`, `BinaryExpression`, `IfStatement`, and branches.
5. Click **`3AC / IR`**:
   - Inspect the emitted linear Three-Address Code with explicit temporaries (`t1`, `t2`, `t3`), conditional branches (`if_false`), and labels (`L1:`, `L2:`).

---

### Part 2: Control Flow Graph (CFG) Visualization
1. Click the **`CFG (4)`** tab in the inspector pane.
2. Observe the derived Control Flow Graph:
   - **`B0 [ENTRY]`**: Contains straight-line instructions up to the conditional branch `if_false t3 goto L1`.
   - **Outgoing Directed Edges from B0**:
     - Red pill: `False Branch -> B2` (branch taken when condition is false)
     - Green pill: `True Branch -> B1` (fall-through to Then branch)
   - **`B1`**: Contains the Then-body (`print result`, `goto L2`). Outgoing edge: `Goto -> B3`.
   - **`B2`**: Contains label `L1:` and the Else-body (`print 0`). Outgoing edge: `Fall-through -> B3`.
   - **`B3 [EXIT]`**: Contains merge label `L2:`.
3. Click on any block card (e.g. `B0` or `B1`):
   - Notice the **Block Inspector** panel on the right updates to show Block ID, Reachability (`Reachable from Entry`), Predecessors, Successors, and detailed instruction types.

---

### Part 3: Intermediate-Code Optimization Pipeline
1. Click the **`Optimizer (-2)`** tab in the inspector pane.
2. Review the top summary cards:
   - **Original 3AC Instructions:** 12
   - **Optimized 3AC Instructions:** 10
   - **Instructions Eliminated:** 2
   - **Transformations Applied:** 10
3. Compare the side-by-side columns:
   - **Left:** Original 3AC with temporaries `t1 = bonus * 2`, `t2 = score + t1`, etc.
   - **Right:** Optimized 3AC where constants are folded (`result = 30`, `t3 = true`), and unused temporaries `t1` and `t2` are eliminated.
4. Scroll through the **Transformation Log** on the right:
   - Point out discrete passes: **Constant Propagation**, **Constant Folding**, and **Dead Code Elimination**.
   - Use the dropdown filter to isolate specific passes (e.g. filter by "Constant Folding").

---

### Part 4: Step-by-Step Runtime Debugger
1. Click the **`Debugger (7)`** tab in the inspector pane.
2. Notice the control bar: `Reset`, `Step Back`, `Play`, `Step Next`, `To End`, and the timeline slider.
3. Click **`Step Next`** sequentially:
   - **Step 1:** Program starts.
   - **Step 2:** `let score = 20` $\rightarrow$ Variables watch window shows `score: int = 20`.
   - **Step 3:** `let bonus = 5` $\rightarrow$ Variables watch window adds `bonus: int = 5`.
   - **Step 4:** `let result = score + bonus * 2` $\rightarrow$ Notice the code editor highlights **Line 3**. Variables watch window highlights `result (UPDATED)` with value `30`.
   - **Step 5:** `IfStatement` branch decision $\rightarrow$ Green banner appears: `Condition evaluated to true -> Taking Then branch`.
   - **Step 6:** `print(result)` $\rightarrow$ Console output terminal snapshot adds `> 30`.
   - **Step 7:** Program finishes normally.
4. Click **`Step Back`**:
   - Scrub backward to previous steps. Notice the variable state reverts immediately without re-executing any code, demonstrating deterministic state snapshotting.

---

### Part 5: Diagnostics & Error Handling
1. In the preset selector at the top left, choose **`Diagnostic: Syntax Recovery Error`**.
2. Source displays: `let x = 10 + ;`. Click **Run**.
3. Notice the status pill turns red: `● 1 Error`.
4. Click the **`Diagnostics (1)`** tab:
   - Displays: `Syntax Error at Line 1, Column 14: Unexpected token ';' in expression`.
   - Helpful recovery hint: `Expected a literal, variable name, or '(' expression`.
   - Editor highlights line 1 with error styling.
5. In the preset selector, switch to **`Diagnostic: Division by Zero`** (`let z = 10 / 0; print(z);`).
6. Click **Run**:
   - Demonstrates that 3AC is generated, but the runtime interpreter traps the division by zero and reports a structured Runtime Error.

---

### Part 6: Automated Test Verification
Run in your terminal:
```bash
python -m pytest -v
```
**Expected Outcome:**
- 87 passed in ~0.52s.
- 100% pass rate across lexer, parser, semantics, symbol table, 3AC, CFG, optimizer, debugger, and integration suites.
