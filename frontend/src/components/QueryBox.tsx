import React, { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';

interface QueryBoxProps {
  onQuery: (query: string) => Promise<void>;
  loading: boolean;
  disabled: boolean;
}

const EXAMPLE_QUESTIONS = [
  "Where is authentication implemented?",
  "How does JWT authentication work?",
  "Where is the database connection initialized?",
  "Which files handle user registration?",
  "What dependencies does this module have?"
];

export const QueryBox: React.FC<QueryBoxProps> = ({ onQuery, loading, disabled }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading || disabled) return;
    onQuery(query.trim());
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    if (!disabled && !loading) {
      onQuery(example);
    }
  };

  return (
    <div className="glass-panel section-card">
      <div className="section-title">
        <Sparkles className="w-5 h-5 text-purple-400" size={20} />
        <span>Ask Natural Language Questions</span>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem' }}>
        <input
          type="text"
          className="input-field"
          placeholder={disabled ? "Please ingest a repository first..." : "Ask anything about the codebase..."}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled || loading}
        />
        <button type="submit" className="btn-primary" disabled={disabled || loading || !query.trim()}>
          {loading ? (
            <>
              <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
              Searching...
            </>
          ) : (
            <>
              <Search size={18} />
              Query
            </>
          )}
        </button>
      </form>

      <div style={{ marginTop: '1rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>
          Suggested questions:
        </span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {EXAMPLE_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleExampleClick(q)}
              disabled={disabled || loading}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                fontSize: '0.8rem',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-full)',
                cursor: disabled || loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
