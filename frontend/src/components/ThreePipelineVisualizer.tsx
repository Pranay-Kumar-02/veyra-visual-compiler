import React, { useState } from 'react';
import { COMPILER_STAGES } from '../constants';
import { CompilationResult } from '../types';
import { CheckCircle2, AlertCircle, Clock, ArrowRight, FileCode, Scan, GitBranch, Network, ShieldCheck, Table, Cpu, Terminal } from 'lucide-react';

interface ThreePipelineVisualizerProps {
  result: CompilationResult | null;
}

export const ThreePipelineVisualizer: React.FC<ThreePipelineVisualizerProps> = ({
  result,
}) => {
  const [selectedStageId, setSelectedStageId] = useState<string>('ir');

  const stagesExecuted = result?.stages_executed || [];
  const success = result?.success ?? true;

  // Determine stage execution state
  const getStageStatus = (stageId: string): 'passed' | 'failed' | 'idle' => {
    if (!result) return 'idle';

    const stageMap: Record<string, string> = {
      source: 'Source',
      lexer: 'Lexer',
      parser: 'Parser',
      ast: 'Parser',
      semantic: 'Semantic Analysis',
      symbols: 'Semantic Analysis',
      ir: 'IR Generation',
      execution: 'Interpreter',
    };

    const backendStage = stageMap[stageId] || '';
    const hasExecuted = stagesExecuted.includes(backendStage) || stageId === 'source';

    if (!success && result.diagnostics && result.diagnostics.length > 0) {
      const errStage = result.diagnostics[0].stage;
      if (stageId === 'lexer' && errStage === 'Lexical Error') return 'failed';
      if ((stageId === 'parser' || stageId === 'ast') && errStage === 'Syntax Error') return 'failed';
      if ((stageId === 'semantic' || stageId === 'symbols') && errStage === 'Semantic Error') return 'failed';
      if (stageId === 'execution' && errStage === 'Runtime Error') return 'failed';
    }

    if (hasExecuted) return 'passed';
    return 'idle';
  };

  const getStageMetric = (stageId: string): string => {
    if (!result) return 'Pending';
    switch (stageId) {
      case 'source':
        return 'VCL Source';
      case 'lexer':
        return `${result.tokens?.length || 0} tokens`;
      case 'parser':
        return result.ast ? 'Grammar Valid' : 'Syntax Trap';
      case 'ast':
        return result.ast ? `Root: ${result.ast.node_type}` : 'None';
      case 'semantic':
        return success ? 'Types Verified' : 'Scope Trap';
      case 'symbols':
        return `${result.symbol_table?.length || 0} symbols`;
      case 'ir':
        return `${result.ir?.instruction_count || 0} insts`;
      case 'execution':
        return success ? `Exit 0 (${result.output || 'OK'})` : 'Exit 1 (Trapped)';
      default:
        return 'Ready';
    }
  };

  const getStageIcon = (stageId: string) => {
    switch (stageId) {
      case 'source': return <FileCode size={14} />;
      case 'lexer': return <Scan size={14} />;
      case 'parser': return <GitBranch size={14} />;
      case 'ast': return <Network size={14} />;
      case 'semantic': return <ShieldCheck size={14} />;
      case 'symbols': return <Table size={14} />;
      case 'ir': return <Cpu size={14} />;
      case 'execution': return <Terminal size={14} />;
      default: return null;
    }
  };

  const selectedStage = COMPILER_STAGES.find((s) => s.id === selectedStageId) || COMPILER_STAGES[6];
  const selectedStatus = getStageStatus(selectedStage.id);

  return (
    <div className="spatial-studio-container">
      {/* Left/Center Area: Connected Pipeline Graph */}
      <div className="spatial-graph-area">
        {/* Header */}
        <div className="spatial-graph-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-main)' }}>
              Compiler Architecture Pipeline
            </span>
            <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              8 Connected Stages · Live State Synchronization
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10.5, fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--color-success)' }}>● Passed</span>
            <span style={{ color: 'var(--color-error)', marginLeft: 8 }}>● Failed</span>
            <span style={{ color: 'var(--text-faint)', marginLeft: 8 }}>● Idle</span>
          </div>
        </div>

        {/* Precision Connected Pipeline Canvas */}
        <div className="spatial-graph-canvas">
          <div className="pipeline-track">
            {COMPILER_STAGES.map((stage, idx) => {
              const status = getStageStatus(stage.id);
              const isActive = selectedStageId === stage.id;
              const metric = getStageMetric(stage.id);
              const isLast = idx === COMPILER_STAGES.length - 1;

              return (
                <React.Fragment key={stage.id}>
                  {/* Stage Station Card */}
                  <div
                    className={`stage-station-card ${status} ${isActive ? 'active' : ''}`}
                    onClick={() => setSelectedStageId(stage.id)}
                    title={`Click to inspect ${stage.title} artifacts`}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span className="stage-card-seq">{String(idx + 1).padStart(2, '0')}</span>
                      <span style={{ color: status === 'passed' ? 'var(--accent)' : 'var(--text-muted)' }}>
                        {getStageIcon(stage.id)}
                      </span>
                    </div>

                    <div className="stage-card-name">{stage.title}</div>

                    <div className="stage-card-metric">{metric}</div>

                    <div className={`stage-status-badge ${status}`}>
                      {status === 'passed' && <CheckCircle2 size={10} />}
                      {status === 'failed' && <AlertCircle size={10} />}
                      {status === 'idle' && <Clock size={10} />}
                      <span>{status.toUpperCase()}</span>
                    </div>
                  </div>

                  {/* Inter-stage Connector Pipe */}
                  {!isLast && (
                    <div className="stage-pipe-connector">
                      <div className={`stage-pipe-line ${status === 'passed' ? 'active' : ''}`} />
                      <ArrowRight
                        size={12}
                        style={{
                          position: 'absolute',
                          right: -3,
                          color: status === 'passed' ? 'var(--accent)' : 'var(--border-med)',
                        }}
                      />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Panel: Selected Stage Artifact Inspector */}
      <div className="spatial-inspector-panel">
        <div className="spatial-inspector-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-main)' }}>
              {selectedStage.title}
            </span>
            <span className="type-pill">{selectedStage.shortLabel}</span>
          </div>

          <div className={`stage-status-badge ${selectedStatus}`}>
            <span>● {selectedStatus.toUpperCase()}</span>
          </div>
        </div>

        <div className="spatial-inspector-content">
          {/* Theory & Description */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
              Compiler Stage Role
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.5 }}>
              {selectedStage.description}
            </div>
          </div>

          {/* Generated Artifacts Breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Stage Artifacts & State
            </div>

            {/* Stage: 3AC / IR */}
            {selectedStage.id === 'ir' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  <span>Linear Instructions: {result?.ir?.instruction_count || 0}</span>
                  <span>Temps: {result?.ir?.temp_count || 0}</span>
                  <span>Labels: {result?.ir?.label_count || 0}</span>
                </div>
                <div
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '10px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11.5,
                    lineHeight: 1.6,
                    maxHeight: 380,
                    overflowY: 'auto',
                    whiteSpace: 'pre',
                  }}
                >
                  {result?.ir?.instructions && result.ir.instructions.length > 0 ? (
                    result.ir.instructions.map((inst, i) => (
                      <div key={i} style={{ display: 'flex', gap: 12 }}>
                        <span style={{ color: 'var(--text-faint)', minWidth: 20, textAlign: 'right' }}>
                          {i + 1}
                        </span>
                        <span style={{ color: inst.kind === 'Label' ? '#e3b341' : inst.kind.startsWith('Jump') ? '#58a6ff' : 'var(--text-main)' }}>
                          {inst.formatted}
                        </span>
                      </div>
                    ))
                  ) : (
                    <span style={{ color: 'var(--text-faint)' }}>No 3AC generated</span>
                  )}
                </div>
              </div>
            )}

            {/* Stage: AST */}
            {selectedStage.id === 'ast' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Root Node: <span style={{ color: 'var(--accent)' }}>{result?.ast?.node_type || 'None'}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Direct Child Branches: <span style={{ color: 'var(--text-main)' }}>{result?.ast?.children?.length || 0}</span>
                </div>
                <pre
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    padding: 10,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    maxHeight: 320,
                    overflowY: 'auto',
                    color: 'var(--text-dim)',
                  }}
                >
                  {result?.ast ? JSON.stringify(result.ast, null, 2) : 'No AST generated'}
                </pre>
              </div>
            )}

            {/* Stage: Symbols */}
            {selectedStage.id === 'symbols' && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  Resolved Scope Bindings ({result?.symbol_table?.length || 0}):
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {result?.symbol_table && result.symbol_table.length > 0 ? (
                    result.symbol_table.map((s, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: 'var(--bg-input)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-xs)',
                          padding: '6px 10px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontFamily: 'var(--font-mono)',
                          fontSize: 11,
                        }}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{s.name}</span>
                        <span className="type-pill">{s.type}</span>
                        <span style={{ color: 'var(--text-dim)' }}>val: {String(s.value)}</span>
                        <span style={{ color: 'var(--text-faint)' }}>{s.scope}</span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: 'var(--text-faint)', fontSize: 11 }}>No symbols recorded</div>
                  )}
                </div>
              </div>
            )}

            {/* Stage: Lexer */}
            {selectedStage.id === 'lexer' && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  Token Stream ({result?.tokens?.length || 0} items):
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, maxHeight: 320, overflowY: 'auto' }}>
                  {result?.tokens && result.tokens.length > 0 ? (
                    result.tokens.map((t, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: 10.5,
                          fontFamily: 'var(--font-mono)',
                          padding: '2px 6px',
                          backgroundColor: 'var(--bg-input)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-xs)',
                          color: 'var(--text-main)',
                        }}
                      >
                        {t.lexeme}
                      </span>
                    ))
                  ) : (
                    <span style={{ color: 'var(--text-faint)', fontSize: 11 }}>No tokens emitted</span>
                  )}
                </div>
              </div>
            )}

            {/* Stage: Execution */}
            {selectedStage.id === 'execution' && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  Standard Output Capture:
                </div>
                <div
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '10px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    color: success ? 'var(--color-success)' : 'var(--color-error)',
                  }}
                >
                  &gt; {result?.output || '(No output produced)'}
                </div>
              </div>
            )}

            {/* Diagnostics failure card if trapped */}
            {selectedStatus === 'failed' && result?.diagnostics && result.diagnostics.length > 0 && (
              <div
                style={{
                  backgroundColor: 'var(--color-error-bg)',
                  border: '1px solid var(--color-error-border)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 10,
                  marginTop: 8,
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-error)', marginBottom: 4 }}>
                  {result.diagnostics[0].stage}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--text-main)', marginBottom: 4 }}>
                  {result.diagnostics[0].message}
                </div>
                {result.diagnostics[0].hint && (
                  <div style={{ fontSize: 10.5, color: 'var(--text-dim)', fontStyle: 'italic' }}>
                    Hint: {result.diagnostics[0].hint}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
