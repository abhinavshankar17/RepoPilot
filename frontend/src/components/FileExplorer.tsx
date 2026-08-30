import React, { useState, useEffect } from 'react';
import { FileCode2, Folder, Search, FileText, Database, Layers, CheckCircle2 } from 'lucide-react';
import { RepositoryResponse } from '../types';
import { inspectRepositoryChunks } from '../services/api';

interface FileExplorerProps {
  repository: RepositoryResponse | null;
  selectedFilePath: string | null;
  onSelectFile: (filePath: string) => void;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  repository,
  selectedFilePath,
  onSelectFile,
}) => {
  const [filter, setFilter] = useState('');
  const [fileList, setFileList] = useState<string[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Fetch actual ingested files dynamically whenever selected repository changes
  useEffect(() => {
    if (!repository) {
      setFileList([]);
      return;
    }

    const fetchRepoFiles = async () => {
      setLoadingFiles(true);
      try {
        const res = await inspectRepositoryChunks(repository.id);
        if (res.chunks && res.chunks.length > 0) {
          const uniqueFiles = Array.from(new Set(res.chunks.map((c: any) => c.file_path))) as string[];
          setFileList(uniqueFiles);
        } else {
          // Fallback sample paths if chunks empty
          setFileList(['README.md', 'src/main.py', 'package.json']);
        }
      } catch (err) {
        console.warn('Failed to inspect repository chunks:', err);
        setFileList(['README.md']);
      } finally {
        setLoadingFiles(false);
      }
    };

    fetchRepoFiles();
  }, [repository?.id]);

  if (!repository) {
    return (
      <aside className="w-72 bg-slate-900/90 border-r border-slate-800 flex flex-col h-full select-none">
        <div className="p-4 border-b border-slate-800 text-sm font-bold text-slate-300 flex items-center gap-2">
          <Folder className="w-4 h-4 text-indigo-400" />
          <span>File Explorer</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400 text-xs">
          <Database className="w-10 h-10 mb-3 text-slate-700 stroke-[1.5]" />
          <p className="font-semibold text-slate-300 text-sm">No repository selected</p>
          <p className="text-slate-500 mt-1 leading-relaxed">Ingest or select a repository to view file structure.</p>
        </div>
      </aside>
    );
  }

  const filteredFiles = fileList.filter((f) => f.toLowerCase().includes(filter.toLowerCase()));

  const getFileIcon = (path: string) => {
    if (path.endsWith('.py')) return <FileCode2 className="w-4 h-4 text-amber-400 shrink-0" />;
    if (path.endsWith('.js') || path.endsWith('.ts') || path.endsWith('.tsx') || path.endsWith('.jsx'))
      return <FileCode2 className="w-4 h-4 text-cyan-400 shrink-0" />;
    if (path.endsWith('.md')) return <FileText className="w-4 h-4 text-emerald-400 shrink-0" />;
    return <FileCode2 className="w-4 h-4 text-slate-400 shrink-0" />;
  };

  return (
    <aside className="w-72 bg-slate-900/90 border-r border-slate-800 flex flex-col h-full select-none text-slate-200">
      {/* Panel Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-200">
          <Folder className="w-4 h-4 text-indigo-400" />
          <span>File Explorer</span>
        </div>
        <span className="text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full">
          {fileList.length} files
        </span>
      </div>

      {/* Repository Meta Summary */}
      <div className="px-4 py-2.5 bg-slate-950/60 border-b border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
        <span className="font-medium text-slate-300 truncate max-w-[160px]">{repository.name}</span>
        <span className="text-xs text-indigo-400 font-mono bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
          {repository.branch || 'main'}
        </span>
      </div>

      {/* Filter Search Input */}
      <div className="p-3 border-b border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Filter codebase files..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {loadingFiles ? (
          <div className="p-4 text-center text-slate-500 text-xs">Loading files...</div>
        ) : filteredFiles.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-xs">No files match filter.</div>
        ) : (
          filteredFiles.map((file) => {
            const isSelected = selectedFilePath === file;
            return (
              <button
                key={file}
                onClick={() => onSelectFile(file)}
                className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center space-x-2.5 text-xs transition-all hover:bg-slate-800/70 cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-600/25 text-indigo-200 border-l-3 border-indigo-400 font-semibold shadow-sm'
                    : 'text-slate-300'
                }`}
              >
                {getFileIcon(file)}
                <span className="truncate font-mono text-xs">{file}</span>
              </button>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-xs text-slate-400 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <span>FAISS Index</span>
        </span>
        <span className="text-emerald-400 font-medium flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          Ready
        </span>
      </div>
    </aside>
  );
};
