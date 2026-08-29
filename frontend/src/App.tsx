import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { FileExplorer } from './components/FileExplorer';
import { ChatPanel } from './components/ChatPanel';
import { SourceInspectorPanel } from './components/SourceInspectorPanel';
import { IngestModal } from './components/IngestModal';
import { RepositoryResponse, ChatMessage, Citation } from './types';
import { listRepositories, queryRepository, checkHealth } from './services/api';

export const App: React.FC = () => {
  const [repositories, setRepositories] = useState<RepositoryResponse[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<RepositoryResponse | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);

  // Initial load: Fetch repositories list & health
  useEffect(() => {
    const init = async () => {
      try {
        await checkHealth();
        const res = await listRepositories();
        setRepositories(res.repositories);
        if (res.repositories.length > 0) {
          setSelectedRepo(res.repositories[0]);
        }
      } catch (err: any) {
        console.error('Initial repository fetch failed:', err);
      }
    };
    init();
  }, []);

  const handleRepoSuccess = (repo: RepositoryResponse) => {
    setRepositories((prev) => [repo, ...prev.filter((r) => r.id !== repo.id)]);
    setSelectedRepo(repo);
    setMessages([]);
    setCitations([]);
    setSelectedCitation(null);
    setSessionId(undefined);
  };

  const handleSendMessage = async (queryText: string) => {
    if (!selectedRepo) {
      setError('Please select or ingest a repository first.');
      return;
    }

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const response = await queryRepository(selectedRepo.id, {
        query: queryText,
        session_id: sessionId,
        top_k: 5,
      });

      setSessionId(response.session_id);
      setCitations(response.citations);

      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        originalQuery: response.original_query,
        rewrittenQuery: response.rewritten_query,
        content: response.answer,
        citations: response.citations,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'RAG query processing failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCitation = (citation: Citation) => {
    setSelectedCitation(citation);
    setSelectedFilePath(citation.file_path);
  };

  const handleSelectFile = (filePath: string) => {
    setSelectedFilePath(filePath);
    setSelectedCitation(null);
  };

  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-100 flex flex-col font-sans overflow-hidden">
      {/* Top Navigation Header */}
      <Header
        repositories={repositories}
        selectedRepo={selectedRepo}
        onSelectRepo={(repo) => {
          setSelectedRepo(repo);
          setMessages([]);
          setCitations([]);
          setSelectedCitation(null);
          setSelectedFilePath(null);
          setSessionId(undefined);
        }}
        onOpenIngestModal={() => setIsIngestModalOpen(true)}
      />

      {/* 3-Panel Developer Tool Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: File Explorer */}
        <FileExplorer
          repository={selectedRepo}
          selectedFilePath={selectedFilePath}
          onSelectFile={handleSelectFile}
        />

        {/* Center Panel: AI Chat */}
        <ChatPanel
          messages={messages}
          loading={loading}
          error={error}
          onSendMessage={handleSendMessage}
          onSelectCitation={handleSelectCitation}
        />

        {/* Right Panel: Source Citations & Code Inspector */}
        <SourceInspectorPanel
          repositoryId={selectedRepo?.id || null}
          citations={citations}
          selectedCitation={selectedCitation}
          onSelectCitation={handleSelectCitation}
          selectedFilePath={selectedFilePath}
        />
      </div>

      {/* Ingest Repository Modal */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onSuccess={handleRepoSuccess}
      />
    </div>
  );
};

export default App;
