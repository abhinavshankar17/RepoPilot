import React, { useState } from 'react';
import { FileCode2, Folder, Search, FileText, Database, Layers } from 'lucide-react';
import { RepositoryResponse } from '../types';

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

  if (!repository) {
    return (
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full select-none">
        <div className="p-3 border-b border-slate-800 text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <Folder className="w-3.5 h-3.5 text-indigo-400" />
          <span>File Explorer</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-center text-slate-500 text-xs">
          <Database className="w-8 h-8 mb-2 text-slate-700 stroke-[1.5]" />
          <p>No repository selected.</p>
          <p className="text-[11px] text-slate-600 mt-1">Ingest or select a repository to view file structure.</p>
        </div>
      </aside>
    );
  }

  // Generate file list from metadata or placeholder files
  const sampleFiles = [
    'src/middleware/auth.js',
    'src/middleware/jwt.js',
    'src/controllers/user.js',
    'src/db/connection.py',
    'src/services/order.py',
    'README.md',
    'package.json',
  ];

  const filteredFiles = sampleFiles.filter((f) => f.toLowerCase().includes(filter.toLowerCase()));

  const getFileIcon = (path: string) => {
    if (path.endsWith('.py')) return <FileCode2 className="w-3.5 h-3.5 text-amber-400" />;
    if (path.endsWith('.js') || path.endsWith('.ts') || path.endsWith('.tsx') || path.endsWith('.jsx'))
      return <FileCode2 className="w-3.5 h-3.5 text-cyan-400" />;
    if (path.endsWith('.md')) return <FileText className="w-3.5 h-3.5 text-emerald-400" />;
    return <FileCode2 className="w-3.5 h-3.5 text-slate-400" />;
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full select-none text-slate-200">
      {/* Panel Header */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
          <Folder className="w-3.5 h-3.5 text-indigo-400" />
          <span>File Explorer</span>
        </div>
        <span className="text-[10px] font-medium bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded border border-slate-700">
          {repository.file_count} files
        </span>
      </div>

      {/* Repository Info Summary */}
      <div className="px-3 py-2 bg-slate-950/50 border-b border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
        <span className="font-semibold text-slate-300 truncate max-w-[130px]">{repository.name}</span>
        <span className="text-[10px] text-slate-500 font-mono">{repository.branch || 'main'}</span>
      </div>

      {/* Filter Input */}
      <div className="p-2 border-b border-slate-800">
        <div className="relative">
          <Search className="w-3 h-3 text-slate-500 absolute left-2 top-2" />
          <input
            type="text"
            placeholder="Filter files..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded pl-7 pr-2 py-1 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none"
          />
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto py-1">
        {filteredFiles.length === 0 ? (
          <div className="p-3 text-center text-slate-500 text-xs">No files match filter.</div>
        ) : (
          filteredFiles.map((file) => {
            const isSelected = selectedFilePath === file;
            return (
              <button
                key={file}
                onClick={() => onSelectFile(file)}
                className={`w-full text-left px-3 py-1.5 flex items-center space-x-2 text-xs transition-colors hover:bg-slate-800/70 ${
                  isSelected ? 'bg-indigo-600/20 text-indigo-200 border-l-2 border-indigo-500 font-medium' : 'text-slate-300'
                }`}
              >
                {getFileIcon(file)}
                <span className="truncate text-[11px] font-mono">{file}</span>
              </button>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-2 border-t border-slate-800 bg-slate-950/40 text-[10px] text-slate-500 flex items-center justify-between">
        <span className="flex items-center gap-1">
          <Layers className="w-3 h-3 text-indigo-400" />
          <span>FAISS Indexed</span>
        </span>
        <span className="text-emerald-400 font-medium">Ready</span>
      </div>
    </aside>
  );
};
