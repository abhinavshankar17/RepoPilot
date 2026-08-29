import React, { useState, useEffect } from 'react';
import { FileText, Code2, Layers, ChevronRight, AlertCircle, Loader2 } from 'lucide-react';
import { Citation, FileContentResponse } from '../types';
import { getFileContent } from '../services/api';

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

  // Load file content when a file or citation is selected
  const activePath = selectedCitation?.file_path || selectedFilePath;
  const highlightStart = selectedCitation?.start_line || 1;
  const highlightEnd = selectedCitation?.end_line || 1;

  useEffect(() => {
    if (!repositoryId || !activePath) {
      setFileContent(null);
      return;
    }

    const fetchContent = async () => {
      setLoadingFile(true);
      setFileError(null);
      try {
        const res = await getFileContent(repositoryId, activePath);
        setFileContent(res);
      } catch (err: any) {
        setFileError(err.message || 'Failed to load file source');
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
    <aside className="w-80 bg-slate-900 border-l border-slate-800 flex flex-col h-full select-none text-slate-200">
      {/* Panel Header & Tabs */}
      <div className="border-b border-slate-800 bg-slate-900">
        <div className="flex border-b border-slate-800">
          <button
            onClick={() => setActiveTab('citations')}
            className={`flex-1 py-2.5 px-3 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors border-b-2 ${
              activeTab === 'citations'
                ? 'border-indigo-500 text-indigo-400 bg-slate-800/50'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Citations ({citations.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('inspector')}
            className={`flex-1 py-2.5 px-3 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors border-b-2 ${
              activeTab === 'inspector'
                ? 'border-indigo-500 text-indigo-400 bg-slate-800/50'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Code Inspector</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Citations List */}
      {activeTab === 'citations' && (
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {citations.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs">
              <FileText className="w-8 h-8 mb-2 text-slate-700 stroke-[1.5]" />
              <p>No citation cards available.</p>
              <p className="text-[11px] text-slate-600 mt-1">Ask a RAG question to see retrieved source chunks.</p>
            </div>
          ) : (
            citations.map((c, i) => {
              const isSelected = selectedCitation?.chunk_id === c.chunk_id;
              return (
                <div
                  key={`${c.chunk_id}-${i}`}
                  onClick={() => handleCardClick(c)}
                  className={`bg-slate-950 border rounded-lg p-3 transition-all cursor-pointer hover:border-indigo-500/60 ${
                    isSelected ? 'border-indigo-500 bg-indigo-950/20 shadow-sm' : 'border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-medium mb-1">
                    <span className="text-slate-200 font-mono truncate max-w-[170px]">{c.file_path}</span>
                    <span className="text-[10px] bg-slate-800 text-indigo-300 border border-slate-700 px-1.5 py-0.5 rounded font-mono">
                      L{c.start_line}-{c.end_line}
                    </span>
                  </div>

                  {c.symbol && (
                    <div className="text-[10px] text-indigo-400 font-mono mb-2 flex items-center gap-1">
                      <span>Symbol:</span>
                      <span className="bg-indigo-500/10 px-1 rounded">{c.symbol}</span>
                    </div>
                  )}

                  <pre className="bg-slate-900 border border-slate-800/80 rounded p-2 text-[10px] font-mono text-slate-300 overflow-x-auto whitespace-pre">
                    {c.snippet}
                  </pre>

                  <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                    <span>Score: {(c.score * 100).toFixed(1)}%</span>
                    <span className="text-indigo-400 flex items-center gap-0.5 group-hover:underline">
                      Inspect Code <ChevronRight className="w-3 h-3" />
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
        <div className="flex-1 overflow-y-auto flex flex-col">
          {!activePath ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs">
              <Code2 className="w-8 h-8 mb-2 text-slate-700 stroke-[1.5]" />
              <p>No file selected for inspection.</p>
              <p className="text-[11px] text-slate-600 mt-1">Select a file from File Explorer or click a Citation card.</p>
            </div>
          ) : loadingFile ? (
            <div className="flex-1 flex items-center justify-center text-xs text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400 mr-2" />
              <span>Fetching source content...</span>
            </div>
          ) : fileError ? (
            <div className="p-4 text-xs text-rose-300 flex items-center space-x-2 bg-rose-500/10 m-3 rounded-lg border border-rose-500/30">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{fileError}</span>
            </div>
          ) : fileContent ? (
            <div className="flex-1 flex flex-col h-full">
              {/* File Sub-header */}
              <div className="p-2.5 bg-slate-950 border-b border-slate-800 text-[11px] flex items-center justify-between font-mono">
                <span className="text-slate-200 truncate">{fileContent.file_path}</span>
                <span className="text-slate-500">{fileContent.total_lines} lines</span>
              </div>

              {/* Code Content Line Viewer */}
              <div className="flex-1 overflow-auto bg-slate-950 p-2 font-mono text-[11px] leading-relaxed">
                {fileContent.content.split('\n').map((line, idx) => {
                  const lineNum = idx + 1;
                  const isHighlighted = lineNum >= highlightStart && lineNum <= highlightEnd;
                  return (
                    <div
                      key={lineNum}
                      className={`flex items-start px-1.5 py-0.5 rounded ${
                        isHighlighted ? 'bg-indigo-600/30 text-indigo-100 border-l-2 border-indigo-400' : 'text-slate-300'
                      }`}
                    >
                      <span className="w-8 text-right pr-3 select-none text-slate-600 shrink-0 text-[10px]">
                        {lineNum}
                      </span>
                      <pre className="whitespace-pre overflow-x-auto">{line || ' '}</pre>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </aside>
  );
};
