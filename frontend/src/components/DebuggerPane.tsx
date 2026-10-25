import React, { useState, useEffect } from 'react';
import { DebugTraceData, DebugEventItem } from '../types';
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  StepBack,
  FastForward,
  Bug,
  Terminal,
  Activity,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

interface DebuggerPaneProps {
  trace?: DebugTraceData | null;
  onHighlightLine?: (line: number, col: number) => void;
}

export const DebuggerPane: React.FC<DebuggerPaneProps> = ({ trace, onHighlightLine }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Reset step to 0 when new trace arrives
  useEffect(() => {
    setCurrentStepIndex(0);
    setIsPlaying(false);
  }, [trace]);

  if (!trace || !trace.events || trace.events.length === 0) {
    return (
      <div className="state-empty-clean">
        <Bug size={26} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-dim)' }}>No Debugger Trace Available</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-muted)', maxWidth: 360, lineHeight: 1.5 }}>
          Compile source code to generate an interactive step-by-step AST execution trace with immutable variable snapshots.
        </div>
      </div>
    );
  }

  const events = trace.events;
  const currentEvent: DebugEventItem = events[Math.min(currentStepIndex, events.length - 1)];

  // Synchronize line highlight in the code editor
  useEffect(() => {
    if (currentEvent && currentEvent.line > 0 && onHighlightLine) {
      onHighlightLine(currentEvent.line, currentEvent.column);
    }
  }, [currentStepIndex, currentEvent, onHighlightLine]);

  // Automatic playback ticker
  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      if (currentStepIndex < events.length - 1) {
        timer = setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
        }, 750);
      } else {
        setIsPlaying(false);
      }
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isPlaying, currentStepIndex, events.length]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const handleStepBack = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.max(0, prev - 1));
  };

  const handleStepForward = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.min(events.length - 1, prev + 1));
  };

  const handleRunToEnd = () => {
    setIsPlaying(false);
    setCurrentStepIndex(events.length - 1);
  };

  const togglePlay = () => {
    if (currentStepIndex >= events.length - 1) {
      setCurrentStepIndex(0);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const visibleVars = Object.entries(currentEvent.variables || {});
  const progressPercent = Math.round(((currentStepIndex + 1) / events.length) * 100);

  return (
    <div className="view-content-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Execution Control Header Bar */}
      <div className="view-content-header" style={{ height: 42, padding: '0 14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title" style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12 }}>
            <Bug size={14} style={{ color: 'var(--accent)' }} />
            <span>Interactive Debugger</span>
          </span>
          <span
            style={{
              fontSize: 10.5,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-surface-elevated)',
              padding: '2px 7px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            Step {currentStepIndex + 1} of {events.length} ({progressPercent}%)
          </span>
        </div>

        {/* Debugger Controls Button Group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            onClick={handleReset}
            className="pane-action-btn"
            title="Reset trace to first step (Beginning)"
            disabled={currentStepIndex === 0 && !isPlaying}
          >
            <RotateCcw size={12} />
            <span>Reset</span>
          </button>

          <button
            onClick={handleStepBack}
            className="pane-action-btn"
            title="Step backward to previous execution snapshot"
            disabled={currentStepIndex === 0}
          >
            <StepBack size={12} />
            <span>Step Back</span>
          </button>

          <button
            onClick={togglePlay}
            className={`pane-action-btn ${isPlaying ? 'btn-pause' : 'btn-play'}`}
            title={isPlaying ? 'Pause automatic execution playback' : 'Play automatic step execution'}
          >
            {isPlaying ? <Pause size={12} /> : <Play size={12} />}
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <button
            onClick={handleStepForward}
            className="pane-action-btn"
            title="Step forward to next statement"
            disabled={currentStepIndex >= events.length - 1}
          >
            <StepForward size={12} />
            <span>Step Next</span>
          </button>

          <button
            onClick={handleRunToEnd}
            className="pane-action-btn"
            title="Run trace to completion"
            disabled={currentStepIndex >= events.length - 1}
          >
            <FastForward size={12} />
            <span>To End</span>
          </button>
        </div>
      </div>

      {/* Styled Timeline & Progress Bar */}
      <div
        style={{
          padding: '8px 16px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          <span>1 (Start)</span>
          <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Timeline Navigation</span>
          <span>{events.length} (Completion)</span>
        </div>
        <input
          type="range"
          min={0}
          max={events.length - 1}
          value={currentStepIndex}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentStepIndex(Number(e.target.value));
          }}
          className="debugger-slider"
          title={`Scrub to step ${currentStepIndex + 1}`}
        />
      </div>

      {/* Main Debugger Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side: Active Statement & Variable Watch Window */}
        <div style={{ flex: 1.3, padding: 14, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Active Statement Card */}
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-med)',
              borderRadius: 'var(--radius-sm)',
              padding: 12,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <Activity size={13} style={{ color: 'var(--accent)' }} />
                <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-main)' }}>
                  Current Execution Statement
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span
                  style={{
                    fontSize: 10,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-xs)',
                  }}
                >
                  Line {currentEvent.line}, Col {currentEvent.column}
                </span>

                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: 'var(--accent)',
                    background: 'var(--accent-subtle)',
                    border: '1px solid var(--accent-border)',
                    padding: '2px 7px',
                    borderRadius: 'var(--radius-xs)',
                  }}
                >
                  {currentEvent.node_type}
                </span>
              </div>
            </div>

            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                lineHeight: 1.5,
                color: 'var(--text-main)',
                background: 'var(--bg-input)',
                padding: '8px 10px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {currentEvent.description}
            </div>
          </div>

          {/* Branch Decision Callout (if active) */}
          {currentEvent.branch_info && (
            <div
              style={{
                background: 'rgba(52, 211, 153, 0.08)',
                border: '1px solid rgba(52, 211, 153, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '9px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <CheckCircle2 size={16} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
              <div style={{ fontSize: 11, color: 'var(--text-main)', lineHeight: 1.4 }}>
                <span style={{ fontWeight: 600 }}>Branch Condition Evaluated: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-success)' }}>
                  {String(currentEvent.branch_info.evaluated_result)}
                </span>
                {' '}— Executing <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{currentEvent.branch_info.branch_taken}</span> branch body
              </div>
            </div>
          )}

          {/* Runtime Error Alert (if error step) */}
          {currentEvent.error && (
            <div
              style={{
                background: 'var(--color-error-bg)',
                border: '1px solid var(--color-error-border)',
                borderRadius: 'var(--radius-sm)',
                padding: 12,
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-error)', fontWeight: 600, fontSize: 11.5 }}>
                <AlertCircle size={14} />
                <span>Runtime Exception Encountered</span>
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                {currentEvent.error.message}
              </div>
              {currentEvent.error.hint && (
                <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>
                  Hint: {currentEvent.error.hint}
                </div>
              )}
            </div>
          )}

          {/* Variables Watch Table */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-dim)' }}>
                Variables Watch Window ({visibleVars.length})
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Deterministic Snapshot
              </span>
            </div>

            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-med)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
              }}
            >
              {visibleVars.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-med)', textAlign: 'left' }}>
                      <th style={{ padding: '7px 12px', color: 'var(--text-muted)', fontWeight: 600, fontSize: 10 }}>VARIABLE</th>
                      <th style={{ padding: '7px 12px', color: 'var(--text-muted)', fontWeight: 600, fontSize: 10 }}>TYPE</th>
                      <th style={{ padding: '7px 12px', color: 'var(--text-muted)', fontWeight: 600, fontSize: 10 }}>VALUE</th>
                      <th style={{ padding: '7px 12px', color: 'var(--text-muted)', fontWeight: 600, fontSize: 10, textAlign: 'right' }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleVars.map(([vName, vData]) => {
                      const wasChanged = currentEvent.changed_variable === vName;
                      return (
                        <tr
                          key={vName}
                          style={{
                            borderBottom: '1px solid var(--border-subtle)',
                            background: wasChanged ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
                            transition: 'background 0.15s ease',
                          }}
                        >
                          <td style={{ padding: '7px 12px', fontWeight: 600, color: wasChanged ? 'var(--accent)' : 'var(--text-main)' }}>
                            {vName}
                          </td>
                          <td style={{ padding: '7px 12px', color: 'var(--color-purple)' }}>{vData.type}</td>
                          <td style={{ padding: '7px 12px', fontWeight: 700, color: 'var(--color-success)' }}>{String(vData.value)}</td>
                          <td style={{ padding: '7px 12px', textAlign: 'right' }}>
                            {wasChanged ? (
                              <span
                                style={{
                                  fontSize: 9,
                                  fontWeight: 700,
                                  color: 'var(--accent)',
                                  background: 'var(--accent-subtle)',
                                  border: '1px solid var(--accent-border)',
                                  padding: '2px 5px',
                                  borderRadius: 3,
                                  letterSpacing: '0.04em',
                                }}
                              >
                                UPDATED
                              </span>
                            ) : (
                              <span style={{ fontSize: 9.5, color: 'var(--text-faint)' }}>IN SCOPE</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: 20, color: 'var(--text-muted)', fontSize: 11, textAlign: 'center' }}>
                  No variables defined in current scope at this execution step.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Accumulated Output Terminal Snapshot */}
        <div
          style={{
            flex: 1,
            borderLeft: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-app)',
            minWidth: 260,
          }}
        >
          <div
            style={{
              height: 38,
              padding: '0 12px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
              <Terminal size={12} style={{ color: 'var(--color-success)' }} />
              <span>Program Standard Output</span>
            </div>

            <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {currentEvent.output_so_far.length} line(s) emitted
            </span>
          </div>

          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 12,
              fontFamily: 'var(--font-mono)',
              fontSize: 11.5,
              lineHeight: 1.6,
              color: 'var(--color-success)',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
              background: 'var(--bg-input)',
            }}
          >
            {currentEvent.output_so_far.length > 0 ? (
              currentEvent.output_so_far.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 8 }}>
                  <span style={{ color: 'var(--text-faint)', userSelect: 'none' }}>&gt;</span>
                  <span>{line}</span>
                </div>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: 11, lineHeight: 1.5 }}>
                No stdout output emitted at this execution step. Step forward to print() statements to view runtime output.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebuggerPane;
