import React from 'react';
import { FileCode, Hash } from 'lucide-react';
import { Citation } from '../types';

interface CitationListProps {
  citations: Citation[];
}

export const CitationList: React.FC<CitationListProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <FileCode size={16} />
        <span>Source File Citations ({citations.length})</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {citations.map((c, idx) => (
          <div key={idx} className="citation-card">
            <div className="citation-header">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
                <FileCode size={14} />
                {c.file_path}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: 'var(--text-muted)' }}>
                <Hash size={13} />
                Lines {c.start_line} - {c.end_line}
              </span>
            </div>
            <pre><code>{c.snippet}</code></pre>
          </div>
        ))}
      </div>
    </div>
  );
};
