import React, { useState } from 'react';
import { SymbolItem } from '../types';
import { Search, Table } from 'lucide-react';

interface SymbolTablePaneProps {
  symbols: SymbolItem[];
}

export const SymbolTablePane: React.FC<SymbolTablePaneProps> = ({ symbols }) => {
  const [filterText, setFilterText] = useState('');
  const [scopeFilter, setScopeFilter] = useState<string>('all');

  if (!symbols || symbols.length === 0) {
    return (
      <div className="state-empty-clean">
        <Table size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Symbol Table Empty</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Variable definitions and scope bindings will appear here after semantic analysis.
        </div>
      </div>
    );
  }

  const scopes = Array.from(new Set(symbols.map((s) => s.scope)));

  const filteredSymbols = symbols.filter((s) => {
    const matchesText =
      s.name.toLowerCase().includes(filterText.toLowerCase()) ||
      s.type.toLowerCase().includes(filterText.toLowerCase());

    const matchesScope = scopeFilter === 'all' || s.scope === scopeFilter;

    return matchesText && matchesScope;
  });

  return (
    <div className="view-content-pane">
      {/* Header */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title">Symbol Table</span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {symbols.length} identifiers resolved
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {scopes.length > 1 && (
            <select
              value={scopeFilter}
              onChange={(e) => setScopeFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-xs)',
                padding: '2px 6px',
                color: 'var(--text-dim)',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                outline: 'none',
              }}
            >
              <option value="all">All Scopes</option>
              {scopes.map((sc) => (
                <option key={sc} value={sc}>
                  {sc}
                </option>
              ))}
            </select>
          )}

          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={10} style={{ position: 'absolute', left: 6, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search symbol..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-xs)',
                padding: '2px 6px 2px 20px',
                color: 'var(--text-main)',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                outline: 'none',
                width: 120,
              }}
            />
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="grid-container">
        <table className="tech-grid">
          <thead>
            <tr>
              <th>Identifier</th>
              <th>Type</th>
              <th>Value</th>
              <th>Scope</th>
              <th>Level</th>
              <th>Pos</th>
            </tr>
          </thead>
          <tbody>
            {filteredSymbols.map((sym, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{sym.name}</td>
                <td>
                  <span className="type-pill">{sym.type}</span>
                </td>
                <td style={{ color: 'var(--text-dim)' }}>
                  {sym.value !== undefined ? String(sym.value) : '—'}
                </td>
                <td style={{ color: 'var(--text-muted)' }}>{sym.scope}</td>
                <td style={{ color: 'var(--text-faint)' }}>{sym.scope_level}</td>
                <td style={{ color: 'var(--text-faint)' }}>
                  {sym.line}:{sym.column}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
