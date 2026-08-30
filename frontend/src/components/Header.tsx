import React from 'react';
import { Compass, Plus, Database, Sparkles } from 'lucide-react';
import { RepositoryResponse } from '../types';

interface HeaderProps {
  repositories: RepositoryResponse[];
  selectedRepo: RepositoryResponse | null;
  onSelectRepo: (repo: RepositoryResponse) => void;
  onOpenIngestModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  repositories,
  selectedRepo,
  onSelectRepo,
  onOpenIngestModal,
}) => {
  return (
    <header className="bg-slate-900/90 border-b border-slate-800 text-slate-100 px-6 py-3.5 flex items-center justify-between shadow-md select-none backdrop-blur-md z-20">
      {/* Brand Logo & Title */}
      <div className="flex items-center space-x-3.5">
        <div className="bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-500 p-2.5 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
          <Compass className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
              RepoPilot
            </h1>
            <span className="text-xs font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              v1.0 RAG Copilot
            </span>
          </div>
          <p className="text-xs text-slate-400 font-normal">Codebase Intelligence & AST Citations Engine</p>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* Repository Selector Dropdown */}
        <div className="relative flex items-center">
          <div className="flex items-center space-x-2.5 bg-slate-800/90 border border-slate-700/80 hover:border-slate-600 text-slate-200 text-sm px-3.5 py-2 rounded-xl transition-all shadow-inner">
            <Database className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400 font-medium">Repository:</span>
            <select
              value={selectedRepo?.id || ''}
              onChange={(e) => {
                const found = repositories.find((r) => r.id === e.target.value);
                if (found) onSelectRepo(found);
              }}
              className="bg-transparent text-indigo-300 font-semibold focus:outline-none cursor-pointer text-sm pr-2"
            >
              {repositories.length === 0 ? (
                <option value="" className="bg-slate-900 text-slate-400">No Repositories Ingested</option>
              ) : (
                repositories.map((repo) => (
                  <option key={repo.id} value={repo.id} className="bg-slate-900 text-slate-200 py-1">
                    {repo.name} ({repo.file_count} files)
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {/* Ingest Repository Button */}
        <button
          onClick={onOpenIngestModal}
          className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm px-4 py-2 rounded-xl transition-all shadow-md shadow-indigo-600/30 active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Ingest Repo</span>
        </button>
      </div>
    </header>
  );
};
