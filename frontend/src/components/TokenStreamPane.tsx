import React, { useState } from 'react';
import { TokenItem } from '../types';
import { Search, Scan } from 'lucide-react';

interface TokenStreamPaneProps {
  tokens: TokenItem[];
}

export const TokenStreamPane: React.FC<TokenStreamPaneProps> = ({ tokens }) => {
  const [filterText, setFilterText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (!tokens || tokens.length === 0) {
    return (
      <div className="state-empty-clean">
        <Scan size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No Tokens Emitted</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Lexer token stream will appear once source code is processed.
        </div>
      </div>
    );
  }

  const categories = Array.from(new Set(tokens.map((t) => t.category || 'OTHER')));

  const filteredTokens = tokens.filter((tok) => {
    const matchesText =
      tok.lexeme.toLowerCase().includes(filterText.toLowerCase()) ||
      tok.type.toLowerCase().includes(filterText.toLowerCase());

    const matchesCategory =
      selectedCategory === 'all' || (tok.category || 'OTHER') === selectedCategory;

    return matchesText && matchesCategory;
  });

  return (
    <div className="view-content-pane">
      {/* Header */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title">Token Stream</span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {tokens.length} tokens
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {categories.length > 1 && (
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
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
              <option value="all">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          )}

          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={10} style={{ position: 'absolute', left: 6, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search token..."
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
              <th>#</th>
              <th>Lexeme</th>
              <th>Type</th>
              <th>Category</th>
              <th>Literal</th>
              <th>Pos</th>
            </tr>
          </thead>
          <tbody>
            {filteredTokens.map((tok, i) => (
              <tr key={i}>
                <td style={{ color: 'var(--text-faint)' }}>{i + 1}</td>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  <code>{tok.lexeme}</code>
                </td>
                <td style={{ color: 'var(--text-dim)' }}>{tok.type}</td>
                <td>
                  <span className="type-pill">{tok.category || 'OTHER'}</span>
                </td>
                <td style={{ color: 'var(--text-muted)' }}>
                  {tok.literal !== null && tok.literal !== undefined ? String(tok.literal) : '—'}
                </td>
                <td style={{ color: 'var(--text-faint)' }}>
                  {tok.line}:{tok.column}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
