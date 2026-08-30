import React, { useState, useEffect } from 'react';
import { FileText, Code2, Layers, ChevronRight, X, AlertTriangle } from 'lucide-react';
import { Citation, FileContentResponse } from '../types';
import { getFileContent } from '../services/api';
import { CodeViewer } from './CodeViewer';

interface SourceInspectorPanelProps {
  repositoryId: string | null;
  citations: Citation[];
  selectedCitation: Citation | null;
  onSelectCitation: (citation: Citation) => void;
  selectedFilePath: string | null;
}

export const SourceInspectorPanel: React.FC<SourceInspectorPanelProps> = ({
  repositoryId,
  citations,
  selectedCitation,
  onSelectCitation,
  selectedFilePath,
}) => {
  const [activeTab, setActiveTab] = useState<'citations' | 'inspector'>('citations');
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  const activePath = selectedCitation?.file_path || selectedFilePath;

  useEffect(() => {
    if (!repositoryId || !activePath) {
      setFileContent(null);
      setFileError(null);
      return;
    }

    const fetchContent = async () => {
      setLoadingFile(true);
      setFileError(null);
      try {
        const res = await getFileContent(repositoryId, activePath);
        setFileContent(res);
      } catch (err: any) {
        setFileError(err.message || 'File not found in current repository index');
        setFileContent(null);
      } finally {
        setLoadingFile(false);
      }
    };

    fetchContent();
  }, [repositoryId, activePath]);

  const handleCardClick = (citation: Citation) => {
    onSelectCitation(citation);
    setActiveTab('inspector');
  };

  return (
    <aside className="w-[420px] bg-slate-900/95 border-l border-slate-800 flex flex-col h-full select-none text-slate-200">
      {/* Tab Header Bar */}
      <div className="border-b border-slate-800 bg-slate-950/80">
        <div className="flex">
          <button
            onClick={() => setActiveTab('citations')}
            className={`flex-1 py-3 px-4 text-xs font-bold flex items-center justify-center space-x-2 transition-all border-b-2 cursor-pointer ${
              activeTab === 'citations'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Citations ({citations.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('inspector')}
            className={`flex-1 py-3 px-4 text-xs font-bold flex items-center justify-center space-x-2 transition-all border-b-2 cursor-pointer ${
              activeTab === 'inspector'
                ? 'border-indigo-500 text-indigo-300 bg-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>Code Inspector</span>
          </button>
        </div>
      </div>

      {/* Dismissible Inline Error Message */}
      {fileError && activeTab === 'inspector' && (
        <div className="p-3 bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{fileError}</span>
          </div>
          <button onClick={() => setFileError(null)} className="text-amber-400 hover:text-amber-200">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Tab 1: Citations List */}
      {activeTab === 'citations' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
          {citations.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 text-xs">
              <FileText className="w-10 h-10 mb-3 text-slate-700 stroke-[1.5]" />
              <p className="font-semibold text-slate-300 text-sm">No citation cards available</p>
              <p className="text-slate-500 mt-1 leading-relaxed">Ask a RAG question to view grounded source code cards.</p>
            </div>
          ) : (
            citations.map((c, i) => {
              const isSelected = selectedCitation?.chunk_id === c.chunk_id;
              return (
                <div
                  key={`${c.chunk_id}-${i}`}
                  onClick={() => handleCardClick(c)}
                  className={`bg-slate-950/80 border rounded-xl p-4 transition-all cursor-pointer hover:border-indigo-500/70 shadow-sm ${
                    isSelected ? 'border-indigo-500 bg-indigo-950/30 shadow-indigo-500/10' : 'border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold mb-2">
                    <span className="text-slate-200 font-mono truncate max-w-[220px]">{c.file_path}</span>
                    <span className="text-xs font-mono bg-slate-900 text-indigo-300 border border-slate-700/80 px-2 py-0.5 rounded-md">
                      L{c.start_line}–{c.end_line}
                    </span>
                  </div>

                  {c.symbol && (
                    <div className="text-xs text-indigo-400 font-mono mb-2 flex items-center gap-1.5">
                      <span className="text-slate-500">Symbol:</span>
                      <span className="bg-indigo-500/15 border border-indigo-500/30 px-1.5 py-0.5 rounded">{c.symbol}</span>
                    </div>
                  )}

                  <pre className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre leading-relaxed">
                    {c.snippet}
                  </pre>

                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                    <span>Relevance: {(c.score * 100).toFixed(1)}%</span>
                    <span className="text-indigo-400 font-medium flex items-center gap-1 hover:underline">
                      Inspect Code <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Tab 2: Code Inspector */}
      {activeTab === 'inspector' && (
        <CodeViewer
          fileData={fileContent}
          symbol={selectedCitation?.symbol}
          startLine={selectedCitation?.start_line}
          endLine={selectedCitation?.end_line}
          loading={loadingFile}
          error={fileError}
        />
      )}
    </aside>
  );
};
