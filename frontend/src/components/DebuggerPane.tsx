import React, { useState, useEffect } from 'react';
import { DebugTraceData, DebugEventItem } from '../types';
import {
  Play,
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
        <Bug size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No Debugger Trace Available</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Compile source code to generate an interactive step-by-step AST execution trace.
        </div>
      </div>
    );
  }

  const events = trace.events;
  const currentEvent: DebugEventItem = events[Math.min(currentStepIndex, events.length - 1)];

  // Update line highlight when stepping
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
        }, 800);
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

  return (
    <div className="view-content-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header Bar */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Bug size={14} style={{ color: '#ec4899' }} />
            Step-by-Step Runtime Debugger
          </span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Step {currentStepIndex + 1} of {events.length}
          </span>
        </div>

        {/* Debugger Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            onClick={handleReset}
            className="pane-action-btn"
            title="Reset to Start"
            disabled={currentStepIndex === 0 && !isPlaying}
          >
            <RotateCcw size={12} />
            <span>Reset</span>
          </button>

          <button
            onClick={handleStepBack}
            className="pane-action-btn"
            title="Step Backward (Previous Snapshot)"
            disabled={currentStepIndex === 0}
          >
            <StepBack size={12} />
            <span>Step Back</span>
          </button>

          <button
            onClick={togglePlay}
            className="pane-action-btn"
            style={{
              background: isPlaying ? 'rgba(236, 72, 153, 0.2)' : undefined,
              borderColor: isPlaying ? '#ec4899' : undefined,
              color: isPlaying ? '#ec4899' : undefined,
            }}
            title={isPlaying ? 'Pause Playback' : 'Auto Play Steps'}
          >
            <Play size={12} />
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <button
            onClick={handleStepForward}
            className="pane-action-btn"
            title="Step Forward (Next Event)"
            disabled={currentStepIndex >= events.length - 1}
          >
            <StepForward size={12} />
            <span>Step Next</span>
          </button>

          <button
            onClick={handleRunToEnd}
            className="pane-action-btn"
            title="Run to Completion"
            disabled={currentStepIndex >= events.length - 1}
          >
            <FastForward size={12} />
            <span>To End</span>
          </button>
        </div>
      </div>

      {/* Progress Timeline Slider */}
      <div style={{ padding: '8px 16px', background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)' }}>
        <input
          type="range"
          min={0}
          max={events.length - 1}
          value={currentStepIndex}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentStepIndex(Number(e.target.value));
          }}
          style={{
            width: '100%',
            accentColor: 'var(--accent-primary)',
            cursor: 'pointer',
          }}
        />
      </div>

      {/* Main Debugger Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side: Current Step Callout & Watch Variables */}
        <div style={{ flex: 1.2, padding: 16, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Active Statement Banner */}
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 12,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Activity size={13} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
                  Current Execution State
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span
                  style={{
                    fontSize: 10,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    background: 'var(--bg-app)',
                    padding: '2px 6px',
                    borderRadius: 4,
                  }}
                >
                  Line {currentEvent.line}, Col {currentEvent.column}
                </span>

                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: 'var(--accent-primary)',
                    background: 'rgba(99, 102, 241, 0.1)',
                    padding: '2px 6px',
                    borderRadius: 4,
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
                color: 'var(--text-main)',
                background: 'var(--bg-app)',
                padding: '8px 10px',
                borderRadius: 5,
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
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: 8,
                padding: 10,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <CheckCircle2 size={16} style={{ color: '#10b981' }} />
              <div style={{ fontSize: 11, color: 'var(--text-main)' }}>
                <span style={{ fontWeight: 600 }}>Branch Decision: </span>
                Evaluated to <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#10b981' }}>{String(currentEvent.branch_info.evaluated_result)}</span>
                {' '}— Taking <span style={{ fontWeight: 700 }}>{currentEvent.branch_info.branch_taken}</span> branch
              </div>
            </div>
          )}

          {/* Runtime Error Alert (if error step) */}
          {currentEvent.error && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: 8,
                padding: 12,
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#ef4444', fontWeight: 600, fontSize: 12 }}>
                <AlertCircle size={15} />
                Runtime Error Encountered
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
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)' }}>
                Variables Watch Window ({visibleVars.length})
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                Deterministic memory snapshot
              </span>
            </div>

            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6,
                overflow: 'hidden',
              }}
            >
              {visibleVars.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                      <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontWeight: 600 }}>Variable</th>
                      <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontWeight: 600 }}>Type</th>
                      <th style={{ padding: '6px 10px', color: 'var(--text-muted)', fontWeight: 600 }}>Value</th>
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
                            background: wasChanged ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                            transition: 'background 0.2s ease',
                          }}
                        >
                          <td style={{ padding: '6px 10px', fontWeight: 600, color: wasChanged ? 'var(--accent-primary)' : 'var(--text-main)' }}>
                            {vName}
                            {wasChanged && (
                              <span style={{ marginLeft: 6, fontSize: 9, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
                                (updated)
                              </span>
                            )}
                          </td>
                          <td style={{ padding: '6px 10px', color: '#a855f7' }}>{vData.type}</td>
                          <td style={{ padding: '6px 10px', fontWeight: 700, color: '#10b981' }}>{String(vData.value)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 11, textAlign: 'center' }}>
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
          }}
        >
          <div
            style={{
              padding: '8px 12px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
              <Terminal size={12} style={{ color: '#10b981' }} />
              Console Output at Step {currentStepIndex + 1}
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
              color: '#10b981',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
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
              <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No output emitted yet. Step forward to statements with print().
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebuggerPane;
