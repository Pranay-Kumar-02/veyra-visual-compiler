import React from 'react';
import { PRESET_PROGRAMS } from '../constants';
import { WorkspaceMode, CompilationResult } from '../types';
import { Play, RotateCw } from 'lucide-react';

interface NavbarProps {
  onCompile: () => void;
  isCompiling: boolean;
  selectedPreset: string;
  onSelectPreset: (presetId: string) => void;
  mode: WorkspaceMode;
  onChangeMode: (mode: WorkspaceMode) => void;
  result: CompilationResult | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  onCompile,
  isCompiling,
  selectedPreset,
  onSelectPreset,
  mode,
  onChangeMode,
  result,
}) => {
  return (
    <header className="app-header">
      {/* Brand & Program Preset */}
      <div className="nav-left">
        <div className="brand-wrap">
          <div className="brand-glyph-box">
            <span style={{ fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>V</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span className="brand-title">Veyra</span>
            <span className="brand-version">v2.0</span>
          </div>
        </div>

        <div style={{ height: 16, width: 1, backgroundColor: 'var(--border-subtle)', margin: '0 4px' }} />

        <select
          className="preset-select"
          value={selectedPreset}
          onChange={(e) => onSelectPreset(e.target.value)}
          disabled={isCompiling}
          title="Select sample VCL program"
        >
          {Object.values(PRESET_PROGRAMS).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Mode Switcher Segmented Control */}
      <div className="nav-center">
        <div className="mode-segmented">
          <button
            className={`mode-btn ${mode === 'split-workbench' ? 'active' : ''}`}
            onClick={() => onChangeMode('split-workbench')}
            title="Standard compiler engineering workbench"
          >
            Workbench
          </button>
          <button
            className={`mode-btn ${mode === '3d-spatial' ? 'active' : ''}`}
            onClick={() => onChangeMode('3d-spatial')}
            title="Interactive compiler pipeline architecture"
          >
            Pipeline Studio
          </button>
          <button
            className={`mode-btn ${mode === 'focus-editor' ? 'active' : ''}`}
            onClick={() => onChangeMode('focus-editor')}
            title="Distraction-free code editor"
          >
            Focus
          </button>
        </div>
      </div>

      {/* Right Actions & Status */}
      <div className="nav-right">
        {/* Understated Status Pill */}
        {isCompiling ? (
          <span className="status-pill idle">Compiling...</span>
        ) : result ? (
          result.success ? (
            <span className="status-pill success">
              ● Ready ({result.metrics?.diagnostic_pipeline_duration_ms ?? 1}ms)
            </span>
          ) : (
            <span className="status-pill error">
              ● {result.diagnostics?.length ?? 1} Error
            </span>
          )
        ) : (
          <span className="status-pill idle">● Ready</span>
        )}

        {/* Primary Action Button */}
        <button
          className="btn btn-primary"
          onClick={onCompile}
          disabled={isCompiling}
          title="Compile and run (Ctrl+Enter)"
        >
          {isCompiling ? (
            <RotateCw size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Play size={12} fill="currentColor" />
          )}
          <span>Run</span>
          <kbd>Ctrl+↵</kbd>
        </button>
      </div>
    </header>
  );
};
