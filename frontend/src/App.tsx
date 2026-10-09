import React, { useState, useEffect, useRef } from 'react';
import { PRESET_PROGRAMS } from './constants';
import {
  CompilationResult,
  ViewTab,
  WorkspaceMode
} from './types';
import { Navbar } from './components/Navbar';
import { ThreePipelineVisualizer } from './components/ThreePipelineVisualizer';
import { EditorPane } from './components/EditorPane';
import { AstVisualizer } from './components/AstVisualizer';
import { ThreeAddressCodePane } from './components/ThreeAddressCodePane';
import { SymbolTablePane } from './components/SymbolTablePane';
import { TokenStreamPane } from './components/TokenStreamPane';
import { DiagnosticsPane } from './components/DiagnosticsPane';
import { OutputTerminal } from './components/OutputTerminal';
import { TelemetryBar } from './components/TelemetryBar';

export const App: React.FC = () => {
  const [selectedPreset, setSelectedPreset] = useState<string>('phase2_demo');
  const [code, setCode] = useState<string>(PRESET_PROGRAMS['phase2_demo'].code);
  const [mode, setMode] = useState<WorkspaceMode>('split-workbench'); // Default to Workbench
  const [activeTab, setActiveTab] = useState<ViewTab>('ast');
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [result, setResult] = useState<CompilationResult | null>(null);
  const [errorLine, setErrorLine] = useState<number | null>(null);
  const [cursorPos, setCursorChange] = useState<{ line: number; col: number }>({ line: 1, col: 1 });

  // Resizable pane state
  const [editorWidth, setEditorWidth] = useState<number>(460);
  const isDraggingRef = useRef<boolean>(false);

  // Trigger compilation against the Flask backend
  const handleCompile = async (sourceOverride?: string) => {
    const sourceCode = sourceOverride !== undefined ? sourceOverride : code;
    setIsCompiling(true);

    try {
      const response = await fetch('/api/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source: sourceCode, code: sourceCode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: CompilationResult = await response.json();
      setResult(data);

      if (data.success) {
        setErrorLine(null);
      } else {
        if (data.diagnostics && data.diagnostics.length > 0) {
          setErrorLine(data.diagnostics[0].line);
          setActiveTab('diagnostics');
        }
      }
    } catch (err: any) {
      console.error('Compilation failed:', err);
      setResult({
        success: false,
        tokens: [],
        ast: null,
        symbol_table: [],
        ir: null,
        ir_code: '',
        diagnostics: [
          {
            stage: 'System Error',
            message: `Backend connection error: ${err.message}`,
            line: 1,
            column: 1,
            severity: 'error',
            hint: 'Ensure python app.py is running on http://127.0.0.1:5000',
            formatted: err.message,
          },
        ],
        output: '',
        output_lines: [],
        stages_executed: [],
        metrics: {
          token_count: 0,
          symbol_count: 0,
          ir_instruction_count: 0,
          diagnostic_count: 1,
          output_line_count: 0,
          diagnostic_pipeline_duration_ms: 0,
        },
      });
      setErrorLine(1);
    } finally {
      setIsCompiling(false);
    }
  };

  // Compile initial preset on mount
  useEffect(() => {
    handleCompile();
  }, []);

  // Handle Preset changes
  const handleSelectPreset = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = PRESET_PROGRAMS[presetId];
    if (preset) {
      setCode(preset.code);
      handleCompile(preset.code);
    }
  };

  // Global keyboard shortcuts
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleCompile();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [code]);

  // Pane resizing handlers
  const handleMouseDown = () => {
    isDraggingRef.current = true;
    document.body.style.cursor = 'col-resize';
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const minWidth = 280;
      const maxWidth = window.innerWidth - 320;
      const newWidth = Math.max(minWidth, Math.min(maxWidth, e.clientX));
      setEditorWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        document.body.style.cursor = 'default';
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleSelectLocation = (line: number, col: number) => {
    setErrorLine(line);
    setCursorChange({ line: line as any, col: col as any });
  };

  const diagCount = result?.diagnostics?.length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Top Application Header */}
      <Navbar
        onCompile={() => handleCompile()}
        isCompiling={isCompiling}
        selectedPreset={selectedPreset}
        onSelectPreset={handleSelectPreset}
        mode={mode}
        onChangeMode={setMode}
        result={result}
      />

      {/* Main Workspace Body */}
      <div className="app-body">
        {mode === '3d-spatial' ? (
          /* Dedicated 3D Spatial Pipeline Studio Mode */
          <ThreePipelineVisualizer
            result={result}
          />
        ) : (
          /* Workbench & Focus Modes */
          <div className="workbench-split">
            {/* Source Editor Pane */}
            <div style={{ width: mode === 'focus-editor' ? '100%' : editorWidth, display: 'flex' }}>
              <EditorPane
                code={code}
                onChangeCode={setCode}
                onCompile={() => handleCompile()}
                errorLine={errorLine}
                cursorPos={cursorPos}
                onCursorChange={setCursorChange}
              />
            </div>

            {/* Split Resizer Divider */}
            {mode !== 'focus-editor' && (
              <div className="resizer-bar" onMouseDown={handleMouseDown} />
            )}

            {/* Right: Compiler Artifact Inspector Pane */}
            {mode !== 'focus-editor' && (
              <div className="pane-inspector">
                {/* Tab Navigation */}
                <div className="pane-tabbar">
                  <div className="tab-group">
                    <button
                      className={`tab-btn ${activeTab === 'ast' ? 'active' : ''}`}
                      onClick={() => setActiveTab('ast')}
                    >
                      <span>AST</span>
                    </button>

                    <button
                      className={`tab-btn ${activeTab === 'ir' ? 'active' : ''}`}
                      onClick={() => setActiveTab('ir')}
                    >
                      <span>3AC / IR</span>
                      {result?.ir && (
                        <span className="tab-count">({result.ir.instruction_count})</span>
                      )}
                    </button>

                    <button
                      className={`tab-btn ${activeTab === 'symbols' ? 'active' : ''}`}
                      onClick={() => setActiveTab('symbols')}
                    >
                      <span>Symbols</span>
                      {result?.symbol_table && (
                        <span className="tab-count">({result.symbol_table.length})</span>
                      )}
                    </button>

                    <button
                      className={`tab-btn ${activeTab === 'tokens' ? 'active' : ''}`}
                      onClick={() => setActiveTab('tokens')}
                    >
                      <span>Tokens</span>
                      {result?.tokens && (
                        <span className="tab-count">({result.tokens.length})</span>
                      )}
                    </button>

                    <button
                      className={`tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
                      onClick={() => setActiveTab('diagnostics')}
                    >
                      <span>Diagnostics</span>
                      {diagCount > 0 && (
                        <span className="tab-count has-error">({diagCount})</span>
                      )}
                    </button>

                    <button
                      className={`tab-btn ${activeTab === 'output' ? 'active' : ''}`}
                      onClick={() => setActiveTab('output')}
                    >
                      <span>Output</span>
                    </button>
                  </div>
                </div>

                {/* Tab Content Display */}
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                  {activeTab === 'ast' && (
                    <AstVisualizer
                      ast={result?.ast || null}
                      onSelectNodeLocation={handleSelectLocation}
                    />
                  )}

                  {activeTab === 'ir' && (
                    <ThreeAddressCodePane
                      ir={result?.ir || null}
                      irCode={result?.ir_code || ''}
                    />
                  )}

                  {activeTab === 'symbols' && (
                    <SymbolTablePane
                      symbols={result?.symbol_table || []}
                    />
                  )}

                  {activeTab === 'tokens' && (
                    <TokenStreamPane
                      tokens={result?.tokens || []}
                    />
                  )}

                  {activeTab === 'diagnostics' && (
                    <DiagnosticsPane
                      diagnostics={result?.diagnostics || []}
                      onSelectLocation={handleSelectLocation}
                    />
                  )}

                  {activeTab === 'output' && (
                    <OutputTerminal
                      output={result?.output || ''}
                      outputLines={result?.output_lines || []}
                      success={result?.success ?? true}
                      durationMs={result?.metrics?.diagnostic_pipeline_duration_ms}
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Telemetry Status Bar */}
      <TelemetryBar result={result} isCompiling={isCompiling} />
    </div>
  );
};

export default App;
