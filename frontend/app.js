/**
 * Veyra Visual Compiler — Editorial Developer Workspace Client
 * Fully data-driven client with CodeMirror editor integration,
 * D3.js interactive SVG AST tree visualization, and source synchronization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ---------------------------------------------------------------------------
  // 1. CodeMirror Custom Mode for VCL & Initialization
  // ---------------------------------------------------------------------------

  if (typeof CodeMirror !== 'undefined') {
    CodeMirror.defineMode('vcl', () => {
      const keywords = {
        'let': true,
        'if': true,
        'else': true,
        'print': true,
        'true': 'boolean',
        'false': 'boolean',
      };

      return {
        startState: () => ({ inString: false }),
        token: (stream, state) => {
          if (stream.eatSpace()) return null;

          // Numbers (Integer and Float)
          if (stream.match(/^[0-9]+(\.[0-9]+)?/)) {
            return 'number';
          }

          // Identifiers and Keywords
          if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/)) {
            const word = stream.current();
            if (keywords[word] === 'boolean') return 'boolean';
            if (keywords[word]) return 'keyword';
            return 'variable';
          }

          // Operators
          if (stream.match(/^(==|!=|<=|>=|&&|\|\||[+\-*\/%!=<>])/)) {
            return 'operator';
          }

          // Delimiters
          if (stream.match(/^[(){};,]/)) {
            return 'punctuation';
          }

          stream.next();
          return null;
        },
      };
    });
  }

  const editorTextarea = document.getElementById('sourceCode');
  let editor = null;

  if (typeof CodeMirror !== 'undefined') {
    editor = CodeMirror.fromTextArea(editorTextarea, {
      mode: 'vcl',
      theme: 'vcl',
      lineNumbers: true,
      matchBrackets: true,
      styleActiveLine: true,
      tabSize: 4,
      indentWithTabs: false,
      extraKeys: {
        'Tab': (cm) => {
          cm.replaceSelection('    ', 'end');
        },
        'Ctrl-Enter': () => runCompiler(),
        'Cmd-Enter': () => runCompiler(),
      },
    });

    editor.on('cursorActivity', updateCursorDisplay);
    editor.on('change', updateDocLength);
  }

  function updateCursorDisplay() {
    if (!editor) return;
    const pos = editor.getCursor();
    document.getElementById('cursorPos').textContent = `Ln ${pos.line + 1}, Col ${pos.ch + 1}`;
  }

  function updateDocLength() {
    if (!editor) return;
    const count = editor.lineCount();
    document.getElementById('docLength').textContent = `${count} ${count === 1 ? 'line' : 'lines'}`;
  }

  // ---------------------------------------------------------------------------
  // 2. DOM Elements & State
  // ---------------------------------------------------------------------------

  const btnRun = document.getElementById('btnRun');
  const btnResetCode = document.getElementById('btnResetCode');
  const presetSelect = document.getElementById('presetSelect');
  const pipelineStatusText = document.getElementById('pipelineStatusText');

  // Tabs & Views
  const navTabs = document.querySelectorAll('.nav-tab');
  const viewPanels = document.querySelectorAll('.view-panel');

  // Inspector Elements
  const countSymbols = document.getElementById('countSymbols');
  const countIr = document.getElementById('countIr');
  const countTokens = document.getElementById('countTokens');
  const countDiagnostics = document.getElementById('countDiagnostics');
  const tbodySymbols = document.getElementById('tbodySymbols');
  const tbodyTokens = document.getElementById('tbodyTokens');
  const diagnosticsList = document.getElementById('diagnosticsList');
  const diagStatusSummary = document.getElementById('diagStatusSummary');
  const outputTerminal = document.getElementById('outputTerminal');
  const execStatusPill = document.getElementById('execStatusPill');

  // IR Elements
  const irContainer = document.getElementById('irContainer');
  const irEmptyState = document.getElementById('irEmptyState');
  const irCodeWrapper = document.getElementById('irCodeWrapper');
  const irLineNumbers = document.getElementById('irLineNumbers');
  const irCodeContent = document.getElementById('irCodeContent');
  const irErrorState = document.getElementById('irErrorState');
  const irErrorMessage = document.getElementById('irErrorMessage');
  const btnCopyIr = document.getElementById('btnCopyIr');

  // Telemetry
  const telTokens = document.getElementById('telTokens');
  const telSymbols = document.getElementById('telSymbols');
  const telIr = document.getElementById('telIr');
  const telDiags = document.getElementById('telDiags');
  const telDuration = document.getElementById('telDuration');

  // D3 Viewport & Controls
  const astD3Viewport = document.getElementById('astD3Viewport');
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnZoomFit = document.getElementById('btnZoomFit');
  const astControls = document.getElementById('astControls');

  // Pipeline Steps
  const pipelineSteps = {
    src: document.getElementById('step-src'),
    lex: document.getElementById('step-lex'),
    parse: document.getElementById('step-parse'),
    ast: document.getElementById('step-ast'),
    sem: document.getElementById('step-sem'),
    sym: document.getElementById('step-sym'),
    ir: document.getElementById('step-ir'),
    exec: document.getElementById('step-exec'),
  };

  // State
  let activeTokens = [];
  let tokenCategoryFilter = 'all';
  let activeSymbols = [];
  let activeIrCode = '';
  let d3Svg = null;
  let d3Zoom = null;
  let currentAstData = null;
  let errorLineMarks = [];

  const PRESET_PROGRAMS = {
    'phase2_demo.vcl': `let score = 20;\nlet bonus = 5;\nlet result = score + bonus * 2;\n\nif (result >= 30) {\n    print(result);\n} else {\n    print(0);\n}`,
    'arithmetic.vcl': `let x = 10 + 5 * 2;\nprint(x);`,
    'conditions.vcl': `let score = 85;\nlet threshold = 50;\n\nif (score >= threshold) {\n    print(1);\n} else {\n    print(0);\n}`,
    'scope.vcl': `let a = 10;\nlet b = 20;\nlet total = 0;\n\n{\n    let factor = 3;\n    total = (a + b) * factor;\n}\n\nprint(total);`,
    'errors.vcl': `let valid = 10;\nlet valid = 20;\nprint(undeclared_variable);`,
  };

  // ---------------------------------------------------------------------------
  // 3. Tab Switching
  // ---------------------------------------------------------------------------

  navTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const view = tab.dataset.view;
      navTabs.forEach((t) => t.classList.remove('active'));
      viewPanels.forEach((p) => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(`view${capitalize(view)}`);
      if (targetPanel) targetPanel.classList.add('active');

      // Show/hide AST controls
      if (view === 'ast') {
        astControls.style.display = 'flex';
        if (currentAstData) renderD3Ast(currentAstData);
      } else {
        astControls.style.display = 'none';
      }
    });
  });

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  // ---------------------------------------------------------------------------
  // 4. Resizable Split Panes
  // ---------------------------------------------------------------------------

  const paneResizer = document.getElementById('paneResizer');
  const paneEditor = document.getElementById('paneEditor');
  let isDragging = false;

  paneResizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    paneResizer.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const containerWidth = document.getElementById('workbench').offsetWidth;
    const newWidth = Math.max(280, Math.min(containerWidth - 320, e.clientX));
    paneEditor.style.flex = `0 0 ${newWidth}px`;
    if (editor) editor.refresh();
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      paneResizer.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      if (editor) editor.refresh();
    }
  });

  // ---------------------------------------------------------------------------
  // 5. Compiler API Orchestration
  // ---------------------------------------------------------------------------

  async function runCompiler() {
    const source = editor ? editor.getValue() : editorTextarea.value;
    clearErrorHighlights();
    setPipelineRunning();

    try {
      const response = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, run_interpreter: true }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const result = await response.json();
      renderExecutionResults(result);
    } catch (err) {
      console.error('Compiler invocation failure:', err);
      renderFatalFailure(err.message);
    }
  }

  function setPipelineRunning() {
    pipelineStatusText.textContent = 'Compiling...';
    Object.values(pipelineSteps).forEach((el) => {
      el.className = 'flow-step';
    });
    pipelineSteps.src.classList.add('passed');
  }

  function updatePipelineJourney(stagesExecuted, success, diagnostics) {
    const executed = stagesExecuted || [];
    pipelineSteps.src.classList.add('passed');

    if (executed.includes('Lexer')) pipelineSteps.lex.classList.add('passed');
    if (executed.includes('Parser')) {
      pipelineSteps.parse.classList.add('passed');
      pipelineSteps.ast.classList.add('passed');
    }
    if (executed.includes('Semantic Analysis')) {
      pipelineSteps.sem.classList.add('passed');
      pipelineSteps.sym.classList.add('passed');
    }
    if (executed.includes('IR Generation')) {
      if (pipelineSteps.ir) pipelineSteps.ir.classList.add('passed');
    }
    if (executed.includes('Interpreter')) pipelineSteps.exec.classList.add('passed');

    if (!success && diagnostics && diagnostics.length > 0) {
      const errStage = diagnostics[0].stage;
      if (errStage === 'Lexical Error') pipelineSteps.lex.className = 'flow-step failed';
      else if (errStage === 'Syntax Error') pipelineSteps.parse.className = 'flow-step failed';
      else if (errStage === 'Semantic Error') pipelineSteps.sem.className = 'flow-step failed';
      else if (errStage === 'Runtime Error') pipelineSteps.exec.className = 'flow-step failed';
    }
  }

  function clearErrorHighlights() {
    if (editor) {
      errorLineMarks.forEach((mark) => mark.clear());
      errorLineMarks = [];
      editor.eachLine((line) => {
        editor.removeLineClass(line, 'background', 'cm-error-line');
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 6. Result Rendering
  // ---------------------------------------------------------------------------

  function renderExecutionResults(result) {
    updatePipelineJourney(result.stages_executed, result.success, result.diagnostics);

    if (result.success) {
      pipelineStatusText.textContent = 'Compiled Successfully';
    } else {
      pipelineStatusText.textContent = 'Diagnostics Emitted';
    }

    // 1. AST View
    currentAstData = result.ast;
    renderD3Ast(result.ast);

    // 2. Symbol Table View
    activeSymbols = result.symbol_table || [];
    renderSymbolGrid(activeSymbols);

    // 3. Intermediate Representation (3AC) View
    renderIr(result.ir, result.ir_code, result.success, result.diagnostics);

    // 4. Token Stream View
    activeTokens = result.tokens || [];
    renderTokenGrid(activeTokens);

    // 5. Diagnostics View
    renderDiagnostics(result.diagnostics);

    // 6. Output View & Telemetry
    renderOutputAndTelemetry(result);
  }

  // ---------------------------------------------------------------------------
  // 7. D3.js Hierarchical SVG AST Visualizer
  // ---------------------------------------------------------------------------

  function renderD3Ast(astData) {
    if (!astData) {
      astD3Viewport.innerHTML = '<div class="empty-msg">No AST generated. Correct syntax errors to inspect syntax tree.</div>';
      return;
    }

    astD3Viewport.innerHTML = '';
    const width = astD3Viewport.clientWidth || 600;
    const height = astD3Viewport.clientHeight || 500;

    const svg = d3
      .select('#astD3Viewport')
      .append('svg')
      .attr('class', 'ast-svg')
      .attr('width', '100%')
      .attr('height', '100%');

    d3Svg = svg;

    const g = svg.append('g').attr('class', 'ast-content');

    d3Zoom = d3
      .zoom()
      .scaleExtent([0.2, 2.5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(d3Zoom);

    // Convert raw AST to D3 hierarchy
    const root = d3.hierarchy(astData, (d) => d.children);

    // Calculate tree layout dimensions
    const nodeWidth = 140;
    const nodeHeight = 54;
    const levelSeparation = 70;

    const treeLayout = d3
      .tree()
      .nodeSize([nodeWidth + 24, nodeHeight + levelSeparation]);

    treeLayout(root);

    // Draw connecting Bezier curves
    const linkGenerator = d3
      .linkVertical()
      .x((d) => d.x)
      .y((d) => d.y);

    g.selectAll('.ast-link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'ast-link')
      .attr('d', (d) => {
        return `M${d.source.x},${d.source.y + nodeHeight / 2}
                C${d.source.x},${(d.source.y + d.target.y) / 2}
                 ${d.target.x},${(d.source.y + d.target.y) / 2}
                 ${d.target.x},${d.target.y - nodeHeight / 2}`;
      });

    // Draw Node Groups
    const nodes = g
      .selectAll('.ast-node-group')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'ast-node-group')
      .attr('transform', (d) => `translate(${d.x},${d.y})`)
      .on('click', (event, d) => {
        event.stopPropagation();
        // Highlight active node in SVG
        g.selectAll('.ast-node-group').classed('selected', false);
        d3.select(event.currentTarget).classed('selected', true);

        // Highlight in CodeMirror
        if (editor && d.data.line) {
          highlightSourceCoordinate(d.data.line, d.data.column);
        }
      });

    // Node Box
    nodes
      .append('rect')
      .attr('class', 'ast-node-rect')
      .attr('x', -nodeWidth / 2)
      .attr('y', -nodeHeight / 2)
      .attr('width', nodeWidth)
      .attr('height', nodeHeight);

    // Node Badge (Node Type)
    nodes
      .append('text')
      .attr('class', 'ast-node-badge')
      .attr('y', -nodeHeight / 2 + 15)
      .text((d) => truncate(d.data.node_type, 18));

    // Node Primary Value / Operator
    nodes
      .append('text')
      .attr('class', 'ast-node-text')
      .attr('y', 4)
      .text((d) => truncate(d.data.label || d.data.node_type, 16));

    // Node Coordinates
    nodes
      .append('text')
      .attr('class', 'ast-node-meta')
      .attr('y', nodeHeight / 2 - 9)
      .text((d) => (d.data.line ? `Ln ${d.data.line}:${d.data.column}` : ''));

    // Initial center zoom
    fitAstView(root, width, height);
  }

  function fitAstView(root, width, height) {
    if (!d3Svg || !d3Zoom || !root) return;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    root.descendants().forEach((d) => {
      if (d.x < minX) minX = d.x;
      if (d.x > maxX) maxX = d.x;
      if (d.y < minY) minY = d.y;
      if (d.y > maxY) maxY = d.y;
    });

    const treeW = (maxX - minX) + 160;
    const treeH = (maxY - minY) + 120;
    const scale = Math.min(1.2, Math.max(0.4, Math.min((width - 40) / treeW, (height - 40) / treeH)));
    const centerX = width / 2 - ((minX + maxX) / 2) * scale;
    const centerY = 40 - minY * scale;

    d3Svg.transition().duration(400).call(
      d3Zoom.transform,
      d3.zoomIdentity.translate(centerX, centerY).scale(scale)
    );
  }

  function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len - 1) + '…' : str;
  }

  btnZoomIn.addEventListener('click', () => {
    if (d3Svg && d3Zoom) d3Svg.transition().duration(200).call(d3Zoom.scaleBy, 1.25);
  });

  btnZoomOut.addEventListener('click', () => {
    if (d3Svg && d3Zoom) d3Svg.transition().duration(200).call(d3Zoom.scaleBy, 0.8);
  });

  btnZoomFit.addEventListener('click', () => {
    if (currentAstData) renderD3Ast(currentAstData);
  });

  function highlightSourceCoordinate(line, col) {
    if (!editor) return;
    const lineIndex = Math.max(0, line - 1);
    editor.setCursor({ line: lineIndex, ch: Math.max(0, (col || 1) - 1) });
    editor.focus();

    // Pulse line
    editor.addLineClass(lineIndex, 'background', 'cm-error-line');
    setTimeout(() => {
      editor.removeLineClass(lineIndex, 'background', 'cm-error-line');
    }, 1200);
  }

  // ---------------------------------------------------------------------------
  // 8. Symbol Table Data Grid
  // ---------------------------------------------------------------------------

  function renderSymbolGrid(symbols) {
    countSymbols.textContent = symbols.length;
    if (!symbols || symbols.length === 0) {
      tbodySymbols.innerHTML = '<tr><td colspan="5" class="empty-msg">No active symbols recorded.</td></tr>';
      return;
    }

    const filterVal = (document.getElementById('filterSymbolsInput').value || '').toLowerCase();
    const filtered = symbols.filter((s) => s.name.toLowerCase().includes(filterVal));

    if (filtered.length === 0) {
      tbodySymbols.innerHTML = '<tr><td colspan="5" class="empty-msg">No matching symbols found.</td></tr>';
      return;
    }

    tbodySymbols.innerHTML = filtered
      .map((s) => {
        const typeClass = `pill-type-${s.type || 'int'}`;
        return `
          <tr>
            <td><strong>${escapeHtml(s.name)}</strong></td>
            <td><span class="grid-pill ${typeClass}">${escapeHtml(s.type)}</span></td>
            <td><strong>${escapeHtml(String(s.value))}</strong></td>
            <td><span class="grid-pill pill-scope">${escapeHtml(s.scope)}</span></td>
            <td>Ln ${s.line}, Col ${s.column}</td>
          </tr>
        `;
      })
      .join('');
  }

  document.getElementById('filterSymbolsInput').addEventListener('input', () => {
    renderSymbolGrid(activeSymbols);
  });

  // ---------------------------------------------------------------------------
  // 9. Token Stream Inspector Grid
  // ---------------------------------------------------------------------------

  function renderTokenGrid(tokens) {
    countTokens.textContent = tokens.length;
    if (!tokens || tokens.length === 0) {
      tbodyTokens.innerHTML = '<tr><td colspan="5" class="empty-msg">No tokens scanned.</td></tr>';
      return;
    }

    let filtered = tokens;
    if (tokenCategoryFilter !== 'all') {
      if (tokenCategoryFilter === 'Operator') {
        filtered = tokens.filter((t) => t.category && t.category.includes('Operator'));
      } else {
        filtered = tokens.filter((t) => t.category && t.category.includes(tokenCategoryFilter));
      }
    }

    if (filtered.length === 0) {
      tbodyTokens.innerHTML = '<tr><td colspan="5" class="empty-msg">No tokens match category filter.</td></tr>';
      return;
    }

    tbodyTokens.innerHTML = filtered
      .map((t, idx) => {
        return `
          <tr>
            <td style="color: var(--text-muted);">${idx + 1}</td>
            <td style="color: var(--sem-blue); font-weight: 500;">${escapeHtml(t.type)}</td>
            <td><code>${escapeHtml(t.lexeme || 'EOF')}</code></td>
            <td><span class="grid-pill pill-scope">${escapeHtml(t.category)}</span></td>
            <td>Ln ${t.line}:${t.column}</td>
          </tr>
        `;
      })
      .join('');
  }

  document.getElementById('tokenFilterRow').addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-btn')) {
      document.querySelectorAll('#tokenFilterRow .filter-btn').forEach((b) => b.classList.remove('active'));
      e.target.classList.add('active');
      tokenCategoryFilter = e.target.dataset.cat;
      renderTokenGrid(activeTokens);
    }
  });

  // ---------------------------------------------------------------------------
  // 10. Diagnostics Console & Editor Error Sync
  // ---------------------------------------------------------------------------

  function renderDiagnostics(diagnostics) {
    const list = diagnostics || [];
    countDiagnostics.textContent = list.length;

    if (list.length > 0) {
      countDiagnostics.classList.add('has-errors');
      diagStatusSummary.textContent = `${list.length} issue(s) detected`;
    } else {
      countDiagnostics.classList.remove('has-errors');
      diagStatusSummary.textContent = '0 issues detected';
    }

    if (list.length === 0) {
      diagnosticsList.innerHTML = `
        <div class="diag-clean-state">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <span>No compilation diagnostics. The program parsed, validated, and executed cleanly.</span>
        </div>
      `;
      return;
    }

    diagnosticsList.innerHTML = list
      .map((d) => {
        return `
          <div class="diag-item" data-line="${d.line}" data-col="${d.column}" title="Click to navigate to source line">
            <div class="diag-meta-row">
              <span class="diag-stage-tag">${escapeHtml(d.stage)}</span>
              <span class="diag-loc-tag">Line ${d.line}, Column ${d.column}</span>
            </div>
            <div class="diag-msg">${escapeHtml(d.message)}</div>
            ${d.hint ? `<div class="diag-hint-box">${escapeHtml(d.hint)}</div>` : ''}
          </div>
        `;
      })
      .join('');

    // Highlight error lines in editor
    if (editor) {
      list.forEach((d) => {
        if (d.line > 0) {
          const lineIndex = d.line - 1;
          editor.addLineClass(lineIndex, 'background', 'cm-error-line');
        }
      });
    }

    // Attach click jump to diagnostic cards
    document.querySelectorAll('.diag-item').forEach((item) => {
      item.addEventListener('click', () => {
        const line = parseInt(item.dataset.line, 10);
        const col = parseInt(item.dataset.col, 10);
        if (line > 0) highlightSourceCoordinate(line, col);
      });
    });

    // Auto-switch to Diagnostics tab on error
    const tabDiag = document.getElementById('tabDiagnostics');
    if (tabDiag) tabDiag.click();
  }

  // ---------------------------------------------------------------------------
  // 11. Output & Telemetry
  // ---------------------------------------------------------------------------

  function renderOutputAndTelemetry(result) {
    if (result.output) {
      outputTerminal.textContent = result.output;
      execStatusPill.textContent = 'Status: Program Output Captured';
      execStatusPill.style.color = 'var(--accent)';
    } else if (result.success) {
      outputTerminal.textContent = '[Execution finished with no output]';
      execStatusPill.textContent = 'Status: Normal Exit (Code 0)';
      execStatusPill.style.color = 'var(--text-dim)';
    } else {
      outputTerminal.textContent = '[Execution halted due to compilation diagnostics. Inspect Diagnostics tab.]';
      execStatusPill.textContent = 'Status: Compilation Error';
      execStatusPill.style.color = 'var(--sem-error)';
    }

    const m = result.metrics || {};
    telTokens.textContent = m.token_count || 0;
    telSymbols.textContent = m.symbol_count || 0;
    if (telIr) telIr.textContent = m.ir_instruction_count || 0;
    telDiags.textContent = m.diagnostic_count || 0;
    telDuration.textContent = `${m.diagnostic_pipeline_duration_ms || 0.0} ms`;
  }

  // ---------------------------------------------------------------------------
  // 11b. Three-Address Code (3AC) Intermediate Representation Rendering
  // ---------------------------------------------------------------------------

  function renderIr(irData, irCode, success, diagnostics) {
    activeIrCode = irCode || '';

    if (irData && irData.instructions && irData.instructions.length > 0) {
      if (countIr) countIr.textContent = irData.instruction_count || irData.instructions.length;
      if (telIr) telIr.textContent = irData.instruction_count || irData.instructions.length;

      if (irEmptyState) irEmptyState.style.display = 'none';
      if (irErrorState) irErrorState.style.display = 'none';
      if (irCodeWrapper) irCodeWrapper.style.display = 'flex';

      const rawLines = irCode.split('\n');
      const lineNums = rawLines.map((_, idx) => idx + 1).join('\n');
      if (irLineNumbers) irLineNumbers.textContent = lineNums;

      if (irCodeContent) irCodeContent.innerHTML = formatIrSyntax(rawLines);
    } else if (!success) {
      if (countIr) countIr.textContent = '0';
      if (telIr) telIr.textContent = '0';
      if (irCodeWrapper) irCodeWrapper.style.display = 'none';
      if (irEmptyState) irEmptyState.style.display = 'none';
      if (irErrorState) irErrorState.style.display = 'flex';

      const diagMsg = (diagnostics && diagnostics.length > 0)
        ? `${diagnostics[0].stage}: ${diagnostics[0].message}`
        : 'Compilation halted prior to IR generation due to diagnostic errors.';
      if (irErrorMessage) irErrorMessage.textContent = diagMsg;
    } else {
      if (countIr) countIr.textContent = '0';
      if (telIr) telIr.textContent = '0';
      if (irCodeWrapper) irCodeWrapper.style.display = 'none';
      if (irErrorState) irErrorState.style.display = 'none';
      if (irEmptyState) irEmptyState.style.display = 'flex';
    }
  }

  function formatIrSyntax(lines) {
    return lines
      .map((line) => {
        const trimmed = line.trim();
        if (!trimmed) return '';
        const isIndent = line.startsWith('  ');
        const prefix = isIndent ? '  ' : '';

        // Label line (e.g. L1:)
        if (trimmed.endsWith(':')) {
          return `${prefix}<span class="ir-label">${escapeHtml(trimmed)}</span>`;
        }

        // Branching lines (e.g. goto L2, if_false t1 goto L1)
        if (trimmed.startsWith('goto ')) {
          const parts = trimmed.split(' ');
          return `${prefix}<span class="ir-branch">${parts[0]}</span> <span class="ir-label">${escapeHtml(parts[1])}</span>`;
        }
        if (trimmed.startsWith('if_false ') || trimmed.startsWith('if_true ')) {
          const parts = trimmed.split(' ');
          return `${prefix}<span class="ir-branch">${parts[0]}</span> <span class="ir-temp">${escapeHtml(parts[1])}</span> <span class="ir-branch">${parts[2]}</span> <span class="ir-label">${escapeHtml(parts[3])}</span>`;
        }

        // Print line (e.g. print result)
        if (trimmed.startsWith('print ')) {
          const parts = trimmed.split(' ');
          return `${prefix}<span class="ir-print">${parts[0]}</span> <span class="ir-temp">${escapeHtml(parts.slice(1).join(' '))}</span>`;
        }

        // Assignment / Binary / Unary (e.g. t1 = 5 * 2, x = t2)
        if (trimmed.includes(' = ')) {
          const eqIdx = trimmed.indexOf(' = ');
          const target = trimmed.substring(0, eqIdx);
          const expr = trimmed.substring(eqIdx + 3);

          const targetHtml = /^t\d+$/.test(target)
            ? `<span class="ir-temp">${escapeHtml(target)}</span>`
            : `<span class="ir-var">${escapeHtml(target)}</span>`;

          const exprTokens = expr
            .split(' ')
            .map((tok) => {
              if (/^t\d+$/.test(tok)) return `<span class="ir-temp">${escapeHtml(tok)}</span>`;
              if (['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'].includes(tok)) {
                return `<span class="ir-op">${escapeHtml(tok)}</span>`;
              }
              return escapeHtml(tok);
            })
            .join(' ');

          return `${prefix}${targetHtml} <span class="ir-op">=</span> ${exprTokens}`;
        }

        return `${prefix}${escapeHtml(trimmed)}`;
      })
      .join('\n');
  }

  function renderFatalFailure(msg) {
    outputTerminal.textContent = `[Fatal Error]: ${msg}`;
    renderIr(null, '', false, [{ stage: 'System Error', message: msg }]);
    diagnosticsList.innerHTML = `
      <div class="diag-item">
        <div class="diag-meta-row">
          <span class="diag-stage-tag">System Error</span>
        </div>
        <div class="diag-msg">${escapeHtml(msg)}</div>
      </div>
    `;
    countDiagnostics.textContent = '1';
    countDiagnostics.classList.add('has-errors');
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ---------------------------------------------------------------------------
  // 12. Controls & Preset Loading
  // ---------------------------------------------------------------------------

  // Copy 3AC button handler
  if (btnCopyIr) {
    btnCopyIr.addEventListener('click', async () => {
      if (!activeIrCode) return;
      try {
        await navigator.clipboard.writeText(activeIrCode);
        const span = btnCopyIr.querySelector('span');
        const orig = span ? span.textContent : 'Copy 3AC';
        if (span) span.textContent = 'Copied!';
        setTimeout(() => {
          if (span) span.textContent = orig;
        }, 1500);
      } catch (e) {
        console.warn('Clipboard write failed:', e);
      }
    });
  }

  btnRun.addEventListener('click', runCompiler);

  btnResetCode.addEventListener('click', () => {
    const key = presetSelect.value;
    const code = PRESET_PROGRAMS[key] || PRESET_PROGRAMS['phase2_demo.vcl'] || PRESET_PROGRAMS['arithmetic.vcl'];
    if (editor) editor.setValue(code);
    runCompiler();
  });

  presetSelect.addEventListener('change', () => {
    const key = presetSelect.value;
    if (PRESET_PROGRAMS[key]) {
      if (editor) editor.setValue(PRESET_PROGRAMS[key]);
      runCompiler();
    }
  });

  // Initial Run
  setTimeout(() => {
    if (editor) {
      editor.refresh();
      updateCursorDisplay();
      updateDocLength();
    }
    runCompiler();
  }, 100);
});
