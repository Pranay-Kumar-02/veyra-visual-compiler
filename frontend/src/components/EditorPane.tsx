import React, { useRef, useState } from 'react';
import { Copy, RotateCcw, Check } from 'lucide-react';

interface EditorPaneProps {
  code: string;
  onChangeCode: (code: string) => void;
  onCompile: () => void;
  errorLine: number | null;
  cursorPos: { line: number; col: number };
  onCursorChange: (pos: { line: number; col: number }) => void;
}

export const EditorPane: React.FC<EditorPaneProps> = ({
  code,
  onChangeCode,
  onCompile,
  errorLine,
  cursorPos,
  onCursorChange,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [copied, setCopied] = useState(false);

  const lines = code.split('\n');
  const lineCount = lines.length;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onCompile();
      return;
    }

    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;

      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      onChangeCode(newCode);

      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      }, 0);
    }
  };

  const updateCursorPosition = () => {
    if (!textareaRef.current) return;
    const text = textareaRef.current.value;
    const selStart = textareaRef.current.selectionStart;

    const linesBefore = text.substring(0, selStart).split('\n');
    const curLine = linesBefore.length;
    const curCol = linesBefore[linesBefore.length - 1].length + 1;

    onCursorChange({ line: curLine, col: curCol });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="pane-editor">
      {/* Tab bar */}
      <div className="pane-tabbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-main)', padding: '4px 6px' }}>
            main.vcl
          </span>
          {errorLine && (
            <span style={{ fontSize: 10, color: 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
              line {errorLine}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <button
            className="btn-icon"
            onClick={handleCopy}
            title={copied ? 'Copied' : 'Copy code'}
          >
            {copied ? <Check size={12} style={{ color: 'var(--color-success)' }} /> : <Copy size={12} />}
          </button>
          <button
            className="btn-icon"
            onClick={() => onChangeCode('')}
            title="Clear editor"
          >
            <RotateCcw size={12} />
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="editor-container">
        {/* Line Numbers Column */}
        <div className="editor-line-numbers">
          {Array.from({ length: lineCount }).map((_, i) => {
            const lineNum = i + 1;
            const isError = errorLine === lineNum;
            const isCurrent = cursorPos.line === lineNum;

            return (
              <div
                key={lineNum}
                className={`editor-line-number ${isError ? 'has-error' : ''}`}
                style={{
                  color: isError
                    ? 'var(--color-error)'
                    : isCurrent
                    ? 'var(--text-main)'
                    : 'var(--text-faint)',
                  fontSize: 11,
                  lineHeight: '1.6',
                }}
              >
                {lineNum}
              </div>
            );
          })}
        </div>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          className="editor-textarea"
          value={code}
          onChange={(e) => onChangeCode(e.target.value)}
          onKeyDown={handleKeyDown}
          onKeyUp={updateCursorPosition}
          onClick={updateCursorPosition}
          placeholder="// Enter VCL source code..."
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
        />
      </div>

      {/* Bottom Status Bar */}
      <div className="editor-status-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>VCL</span>
          <span>UTF-8</span>
          <span>Spaces: 4</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>Ln {cursorPos.line}, Col {cursorPos.col}</span>
          <span>{lineCount} lines</span>
        </div>
      </div>
    </div>
  );
};
