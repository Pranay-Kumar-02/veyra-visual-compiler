/**
 * Veyra Visual Compiler — Interactive Frontend Client Application
 * Connects directly to backend compiler API to render real Tokens, AST,
 * Symbol Table, Diagnostics, and Output.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const codeEditor = document.getElementById('codeEditor');
  const lineNumbers = document.getElementById('lineNumbers');
  const cursorPos = document.getElementById('cursorPos');
  const docStats = document.getElementById('docStats');
  const compilerStatus = document.getElementById('compilerStatus');
  const btnCompile = document.getElementById('btnCompile');
  const btnReset = document.getElementById('btnReset');
  const btnClear = document.getElementById('btnClear');
  const exampleSelect = document.getElementById('exampleSelect');

  // Tabs
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  // Inspector Panels
  const astContainer = document.getElementById('astContainer');
  const btnExpandAst = document.getElementById('btnExpandAst');
  const btnCollapseAst = document.getElementById('btnCollapseAst');
  const symbolsTbody = document.getElementById('symbolsTbody');
  const symbolBadge = document.getElementById('symbolBadge');
  const tokensContainer = document.getElementById('tokensContainer');
  const tokenBadge = document.getElementById('tokenBadge');
  const tokenFilterBar = document.getElementById('tokenFilterBar');
  const diagnosticsContainer = document.getElementById('diagnosticsContainer');
  const diagBadge = document.getElementById('diagBadge');
  const diagSummary = document.getElementById('diagSummary');
  const programOutput = document.getElementById('programOutput');

  // Metrics
  const metricTokens = document.getElementById('metricTokens');
  const metricSymbols = document.getElementById('metricSymbols');
  const metricDiags = document.getElementById('metricDiags');
  const metricDuration = document.getElementById('metricDuration');

  // Pipeline Stepper Steps
  const stages = {
    lexer: document.getElementById('stage-lexer'),
    parser: document.getElementById('stage-parser'),
    semantic: document.getElementById('stage-semantic'),
    interpreter: document.getElementById('stage-interpreter'),
  };

  // State
  let currentTokens = [];
  let currentTokenFilter = 'all';

  const DEFAULT_PROGRAM = `let x = 10 + 5 * 2;\nprint(x);`;

  // ---------------------------------------------------------------------------
  // Editor Utilities & Line Numbers
  // ---------------------------------------------------------------------------

  function updateLineNumbers() {
    const lines = codeEditor.value.split('\n');
    lineNumbers.innerHTML = lines.map((_, i) => i + 1).join('<br>');
    const charCount = codeEditor.value.length;
    docStats.textContent = `${lines.length} lines, ${charCount} chars`;
  }

  function updateCursorPos() {
    const selStart = codeEditor.selectionStart;
    const textBefore = codeEditor.value.substring(0, selStart);
    const lines = textBefore.split('\n');
    const line = lines.length;
    const col = lines[lines.length - 1].length + 1;
    cursorPos.textContent = `Ln ${line}, Col ${col}`;
  }

  codeEditor.addEventListener('input', () => {
    updateLineNumbers();
    updateCursorPos();
  });

  codeEditor.addEventListener('keyup', updateCursorPos);
  codeEditor.addEventListener('click', updateCursorPos);

  codeEditor.addEventListener('scroll', () => {
    lineNumbers.scrollTop = codeEditor.scrollTop;
  });

  // Handle Tab key in editor
  codeEditor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = codeEditor.selectionStart;
      const end = codeEditor.selectionEnd;
      codeEditor.value = codeEditor.value.substring(0, start) + '    ' + codeEditor.value.substring(end);
      codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
      updateLineNumbers();
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runCompiler();
    }
  });

  // ---------------------------------------------------------------------------
  // Tab Switching
  // ---------------------------------------------------------------------------

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabButtons.forEach((b) => b.classList.remove('active'));
      tabContents.forEach((c) => c.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // ---------------------------------------------------------------------------
  // Compiler Pipeline Execution & API
  // ---------------------------------------------------------------------------

  async function runCompiler() {
    const source = codeEditor.value;
    setCompilerStatus('compiling', 'Compiling...');
    resetPipelineStepper();

    try {
      const response = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, run_interpreter: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const data = await response.json();
      renderCompilerResults(data);
    } catch (err) {
      console.error('Compiler invocation error:', err);
      setCompilerStatus('error', 'API Request Failed');
      renderFatalError(err.message);
    }
  }

  function setCompilerStatus(statusClass, text) {
    const dot = compilerStatus.querySelector('.status-dot');
    const label = compilerStatus.querySelector('.status-text');
    dot.className = `status-dot ${statusClass}`;
    label.textContent = text;
  }

  function resetPipelineStepper() {
    Object.values(stages).forEach((el) => {
      el.className = 'stage-step';
    });
  }

  function updatePipelineStepper(stagesExecuted, success, diagnostics) {
    resetPipelineStepper();
    const executed = stagesExecuted || [];

    if (executed.includes('Lexer')) stages.lexer.classList.add('success');
    if (executed.includes('Parser')) stages.parser.classList.add('success');
    if (executed.includes('Semantic Analysis')) stages.semantic.classList.add('success');
    if (executed.includes('Interpreter')) stages.interpreter.classList.add('success');

    if (!success && diagnostics && diagnostics.length > 0) {
      const firstStage = diagnostics[0].stage;
      if (firstStage === 'Lexical Error') stages.lexer.className = 'stage-step error';
      else if (firstStage === 'Syntax Error') stages.parser.className = 'stage-step error';
      else if (firstStage === 'Semantic Error') stages.semantic.className = 'stage-step error';
      else if (firstStage === 'Runtime Error') stages.interpreter.className = 'stage-step error';
    }
  }

  // ---------------------------------------------------------------------------
  // Result Rendering
  // ---------------------------------------------------------------------------

  function renderCompilerResults(result) {
    updatePipelineStepper(result.stages_executed, result.success, result.diagnostics);

    if (result.success) {
      setCompilerStatus('ready', 'Compilation Succeeded');
    } else {
      setCompilerStatus('error', 'Compilation Errors');
    }

    // 1. AST View
    renderAst(result.ast);

    // 2. Symbol Table View
    renderSymbolTable(result.symbol_table);

    // 3. Tokens View
    currentTokens = result.tokens || [];
    renderTokens(currentTokens);

    // 4. Diagnostics View
    renderDiagnostics(result.diagnostics);

    // 5. Output & Metrics View
    renderOutputAndMetrics(result);
  }

  // ---------------------------------------------------------------------------
  // AST Visualizer Rendering
  // ---------------------------------------------------------------------------

  function renderAst(astData) {
    if (!astData) {
      astContainer.innerHTML = '<div class="empty-state">No AST generated. Fix parsing errors to view tree.</div>';
      return;
    }

    astContainer.innerHTML = '';
    const rootTree = document.createElement('div');
    rootTree.className = 'ast-tree';
    rootTree.appendChild(buildAstNodeElement(astData));
    astContainer.appendChild(rootTree);
  }

  function buildAstNodeElement(node) {
    const container = document.createElement('div');
    container.className = 'ast-node';

    const card = document.createElement('div');
    card.className = 'ast-card';

    // Badge color determination
    let badgeClass = 'badge-stmt';
    const type = node.node_type || '';
    if (type === 'Program') badgeClass = 'badge-program';
    else if (type.includes('Declaration')) badgeClass = 'badge-decl';
    else if (type.includes('Assignment')) badgeClass = 'badge-assign';
    else if (type.includes('Binary')) badgeClass = 'badge-binary';
    else if (type.includes('Literal')) badgeClass = 'badge-literal';
    else if (type.includes('Identifier')) badgeClass = 'badge-id';

    const hasChildren = node.children && node.children.length > 0;

    let toggleHtml = '';
    if (hasChildren) {
      toggleHtml = '<span class="ast-toggle">▼</span>';
    }

    card.innerHTML = `
      ${toggleHtml}
      <span class="node-badge ${badgeClass}">${node.node_type}</span>
      <span class="ast-node-label">${escapeHtml(node.label || node.node_type)}</span>
      <span class="ast-node-meta">Ln ${node.line}:${node.column}</span>
    `;

    container.appendChild(card);

    if (hasChildren) {
      const childrenWrapper = document.createElement('div');
      childrenWrapper.className = 'ast-children';

      node.children.forEach((child) => {
        childrenWrapper.appendChild(buildAstNodeElement(child));
      });

      container.appendChild(childrenWrapper);

      // Collapsible functionality
      card.addEventListener('click', (e) => {
        e.stopPropagation();
        const isCollapsed = childrenWrapper.classList.toggle('collapsed');
        const toggle = card.querySelector('.ast-toggle');
        if (toggle) toggle.textContent = isCollapsed ? '▶' : '▼';
      });
    }

    return container;
  }

  btnExpandAst.addEventListener('click', () => {
    astContainer.querySelectorAll('.ast-children').forEach((el) => {
      el.classList.remove('collapsed');
    });
    astContainer.querySelectorAll('.ast-toggle').forEach((t) => (t.textContent = '▼'));
  });

  btnCollapseAst.addEventListener('click', () => {
    astContainer.querySelectorAll('.ast-children').forEach((el) => {
      el.classList.add('collapsed');
    });
    astContainer.querySelectorAll('.ast-toggle').forEach((t) => (t.textContent = '▶'));
  });

  // ---------------------------------------------------------------------------
  // Symbol Table Rendering
  // ---------------------------------------------------------------------------

  function renderSymbolTable(symbols) {
    const list = symbols || [];
    symbolBadge.textContent = list.length;

    if (list.length === 0) {
      symbolsTbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No symbols active in symbol table.</td></tr>';
      return;
    }

    symbolsTbody.innerHTML = list
      .map((s) => {
        let typeClass = 'type-unknown';
        if (s.type === 'int') typeClass = 'type-int';
        else if (s.type === 'float') typeClass = 'type-float';
        else if (s.type === 'bool') typeClass = 'type-bool';

        return `
          <tr>
            <td><strong>${escapeHtml(s.name)}</strong></td>
            <td><span class="type-pill ${typeClass}">${escapeHtml(s.type)}</span></td>
            <td><span class="val-pill">${escapeHtml(String(s.value))}</span></td>
            <td><span class="scope-pill">${escapeHtml(s.scope)} (lvl ${s.scope_level})</span></td>
            <td>Ln ${s.line}, Col ${s.column}</td>
          </tr>
        `;
      })
      .join('');
  }

  // ---------------------------------------------------------------------------
  // Token Stream Rendering & Filtering
  // ---------------------------------------------------------------------------

  function renderTokens(tokens) {
    const list = tokens || [];
    tokenBadge.textContent = list.length;

    let filtered = list;
    if (currentTokenFilter !== 'all') {
      if (currentTokenFilter === 'Operator') {
        filtered = list.filter((t) => t.category.includes('Operator'));
      } else {
        filtered = list.filter((t) => t.category.includes(currentTokenFilter));
      }
    }

    if (filtered.length === 0) {
      tokensContainer.innerHTML = '<div class="empty-state">No matching tokens found for active filter.</div>';
      return;
    }

    tokensContainer.innerHTML = filtered
      .map((t, idx) => {
        return `
          <div class="token-card" title="${escapeHtml(t.category)}">
            <div class="token-header">
              <span class="token-type">${escapeHtml(t.type)}</span>
              <span class="token-idx">#${t.source_pos}</span>
            </div>
            <div class="token-lexeme">${escapeHtml(t.lexeme || 'EOF')}</div>
            <div class="token-footer">
              <span>${escapeHtml(t.category)}</span>
              <span>Ln ${t.line}:${t.column}</span>
            </div>
          </div>
        `;
      })
      .join('');
  }

  tokenFilterBar.addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-pill')) {
      tokenFilterBar.querySelectorAll('.filter-pill').forEach((p) => p.classList.remove('active'));
      e.target.classList.add('active');
      currentTokenFilter = e.target.dataset.filter;
      renderTokens(currentTokens);
    }
  });

  // ---------------------------------------------------------------------------
  // Diagnostics Rendering
  // ---------------------------------------------------------------------------

  function renderDiagnostics(diagnostics) {
    const list = diagnostics || [];
    diagBadge.textContent = list.length;
    if (list.length > 0) {
      diagBadge.classList.add('has-errors');
      diagSummary.textContent = `${list.length} issue(s) detected`;
    } else {
      diagBadge.classList.remove('has-errors');
      diagSummary.textContent = '0 issues detected';
    }

    if (list.length === 0) {
      diagnosticsContainer.innerHTML = `
        <div class="empty-state success-empty">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <span>No diagnostics or errors detected. Program is clean.</span>
        </div>
      `;
      return;
    }

    diagnosticsContainer.innerHTML = list
      .map((d) => {
        const isWarn = d.severity === 'WARNING';
        return `
          <div class="diag-card ${isWarn ? 'diag-warning' : ''}">
            <div class="diag-header">
              <span class="diag-stage">${escapeHtml(d.stage)}</span>
              <span class="diag-loc">Line ${d.line}, Column ${d.column}</span>
            </div>
            <div class="diag-message">${escapeHtml(d.message)}</div>
            ${d.hint ? `<div class="diag-hint">💡 Hint: ${escapeHtml(d.hint)}</div>` : ''}
          </div>
        `;
      })
      .join('');

    // If compilation failed with diagnostics, auto-switch to Diagnostics tab for immediate visibility
    if (list.length > 0) {
      const diagTabBtn = document.getElementById('tabBtnDiagnostics');
      if (diagTabBtn) diagTabBtn.click();
    }
  }

  // ---------------------------------------------------------------------------
  // Output & Metrics Rendering
  // ---------------------------------------------------------------------------

  function renderOutputAndMetrics(result) {
    if (result.output) {
      programOutput.textContent = result.output;
    } else if (result.success) {
      programOutput.textContent = '[Program completed with no output]';
    } else {
      programOutput.textContent = '[Execution halted due to compiler errors. See Diagnostics tab.]';
    }

    const m = result.metrics || {};
    metricTokens.textContent = m.token_count || 0;
    metricSymbols.textContent = m.symbol_count || 0;
    metricDiags.textContent = m.diagnostic_count || 0;
    metricDuration.textContent = `${m.diagnostic_pipeline_duration_ms || 0.0} ms`;
  }

  function renderFatalError(message) {
    programOutput.textContent = `[Fatal Application Error]: ${message}`;
    diagnosticsContainer.innerHTML = `
      <div class="diag-card">
        <div class="diag-stage">Internal Server Error</div>
        <div class="diag-message">${escapeHtml(message)}</div>
      </div>
    `;
    diagBadge.textContent = '1';
    diagBadge.classList.add('has-errors');
  }

  // ---------------------------------------------------------------------------
  // Presets & Controls
  // ---------------------------------------------------------------------------

  btnCompile.addEventListener('click', runCompiler);

  btnReset.addEventListener('click', () => {
    codeEditor.value = DEFAULT_PROGRAM;
    updateLineNumbers();
    updateCursorPos();
    runCompiler();
  });

  btnClear.addEventListener('click', () => {
    codeEditor.value = '';
    updateLineNumbers();
    updateCursorPos();
    runCompiler();
  });

  // Example presets
  const presets = {
    'arithmetic.vcl': `let x = 10 + 5 * 2;\nprint(x);`,
    'conditions.vcl': `let score = 85;\nlet threshold = 50;\n\nif (score >= threshold) {\n    print(1);\n} else {\n    print(0);\n}`,
    'scope.vcl': `let a = 10;\nlet b = 20;\nlet total = 0;\n\n{\n    let factor = 3;\n    total = (a + b) * factor;\n}\n\nprint(total);`,
    'errors.vcl': `let valid = 10;\nlet valid = 20;\nprint(undeclared_variable);`,
  };

  exampleSelect.addEventListener('change', () => {
    const key = exampleSelect.value;
    if (presets[key]) {
      codeEditor.value = presets[key];
      updateLineNumbers();
      updateCursorPos();
      runCompiler();
    }
  });

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initial boot
  updateLineNumbers();
  updateCursorPos();
  runCompiler();
});
