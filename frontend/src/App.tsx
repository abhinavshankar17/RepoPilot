import React, { useState, useEffect } from 'react';
import { Compass } from 'lucide-react';
import { RepoInput } from './components/RepoInput';
import { QueryBox } from './components/QueryBox';
import { AnswerView } from './components/AnswerView';
import { checkHealth, createRepository, queryRepository } from './services/api';
import { RepositoryResponse, QueryResponse } from './types';
import './App.css';

export const App: React.FC = () => {
  const [health, setHealth] = useState<string>('checking');
  const [currentRepo, setCurrentRepo] = useState<RepositoryResponse | null>(null);
  const [ingestLoading, setIngestLoading] = useState<boolean>(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState<boolean>(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth()
      .then((res) => setHealth(res.status))
      .catch(() => setHealth('offline'));
  }, []);

  const handleIngest = async (repoUrl: string, branch?: string) => {
    setIngestLoading(true);
    setIngestError(null);
    setQueryResponse(null);
    try {
      const result = await createRepository({ url: repoUrl, branch });
      setCurrentRepo(result);
    } catch (err: any) {
      setIngestError(err.message || 'Failed to register repository');
    } finally {
      setIngestLoading(false);
    }
  };

  const handleQuery = async (query: string) => {
    if (!currentRepo) return;
    setQueryLoading(true);
    setQueryError(null);
    try {
      const result = await queryRepository(currentRepo.id, { query });
      setQueryResponse(result);
    } catch (err: any) {
      setQueryError(err.message || 'Failed to execute query');
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">
            <Compass size={22} />
          </div>
          <div>
            <div className="brand-title gradient-text">RepoPilot</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Developer Documentation & Codebase Copilot (Phase 1 Backend Foundation)
            </div>
          </div>
        </div>

        <div className="status-badge">
          <div className="status-dot" style={{ background: health === 'ok' ? 'var(--success)' : 'var(--warning)' }} />
          <span>Backend {health === 'ok' ? 'Online' : health}</span>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        <RepoInput
          onIngest={handleIngest}
          ingestData={currentRepo}
          loading={ingestLoading}
          error={ingestError}
        />

        <QueryBox
          onQuery={handleQuery}
          loading={queryLoading}
          disabled={!currentRepo}
        />

        <AnswerView
          queryResponse={queryResponse}
          loading={queryLoading}
          error={queryError}
        />
      </main>

      <footer style={{ marginTop: 'auto', paddingTop: '2rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        RepoPilot Phase 1 Backend Foundation • Pydantic v2 • Clean Architecture
      </footer>
    </div>
  );
};

export default App;
