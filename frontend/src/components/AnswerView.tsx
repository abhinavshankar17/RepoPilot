import React from 'react';
import { Bot, MessageSquare, Loader2 } from 'lucide-react';
import { QueryResponse } from '../types';
import { CitationList } from './CitationList';

interface AnswerViewProps {
  queryResponse: QueryResponse | null;
  loading: boolean;
  error: string | null;
}

export const AnswerView: React.FC<AnswerViewProps> = ({ queryResponse, loading, error }) => {
  if (loading) {
    return (
      <div className="glass-panel section-card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-indigo)' }}>
        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
        <span>Retrieving code chunks and synthesizing answer...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel section-card" style={{ borderColor: 'var(--error)' }}>
        <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⚠️ Query execution error: {error}
        </div>
      </div>
    );
  }

  if (!queryResponse) return null;

  return (
    <div className="glass-panel section-card">
      <div className="section-title">
        <Bot className="w-5 h-5 text-cyan-400" size={20} />
        <span>Grounded Copilot Answer</span>
      </div>

      <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', borderLeft: '3px solid var(--accent-indigo)' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <MessageSquare size={14} />
          Question asked:
        </div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
          {queryResponse.query}
        </div>
      </div>

      <div style={{ fontSize: '1rem', color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
        {queryResponse.answer}
      </div>

      <CitationList citations={queryResponse.citations} />
    </div>
  );
};
