import React, { useState } from 'react';
import { GitBranch, FolderGit2, Loader2, CheckCircle2 } from 'lucide-react';
import { RepositoryResponse } from '../types';

interface RepoInputProps {
  onIngest: (repoUrl: string, branch?: string) => Promise<void>;
  ingestData: RepositoryResponse | null;
  loading: boolean;
  error: string | null;
}

export const RepoInput: React.FC<RepoInputProps> = ({ onIngest, ingestData, loading, error }) => {
  const [repoUrl, setRepoUrl] = useState('https://github.com/octocat/Hello-World');
  const [branch, setBranch] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim() || loading) return;
    onIngest(repoUrl.trim(), branch.trim() || undefined);
  };

  return (
    <div className="glass-panel section-card">
      <div className="section-title">
        <FolderGit2 className="w-5 h-5 text-indigo-400" size={20} />
        <span>Target Repository Registration</span>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 3, minWidth: '280px' }}>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. https://github.com/fastapi/fastapi"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={loading}
            />
          </div>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <input
              type="text"
              className="input-field"
              placeholder="Branch (optional)"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              disabled={loading}
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading || !repoUrl.trim()}>
            {loading ? (
              <>
                <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                Registering...
              </>
            ) : (
              <>
                <GitBranch size={18} />
                Register Repo
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div style={{ marginTop: '1rem', color: 'var(--error)', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {ingestData && (
        <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontWeight: 600 }}>
            <CheckCircle2 size={18} />
            Repository Registered (ID: {ingestData.id})
          </div>
          <div className="meta-grid">
            <div className="meta-box">
              <div className="meta-label">Repository Name</div>
              <div className="meta-value">{ingestData.name}</div>
            </div>
            <div className="meta-box">
              <div className="meta-label">File Count</div>
              <div className="meta-value">{ingestData.file_count}</div>
            </div>
            <div className="meta-box">
              <div className="meta-label">Chunk Count</div>
              <div className="meta-value">{ingestData.chunk_count}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
