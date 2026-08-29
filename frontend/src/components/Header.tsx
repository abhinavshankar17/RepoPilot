import React from 'react';
import { Compass, Plus, Database } from 'lucide-react';
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
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 px-4 py-2.5 flex items-center justify-between shadow-sm select-none">
      {/* Brand Logo */}
      <div className="flex items-center space-x-3">
        <div className="bg-indigo-600 p-1.5 rounded-lg flex items-center justify-center text-white shadow-md">
          <Compass className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-wide text-slate-100 flex items-center gap-2">
            RepoPilot
            <span className="text-[10px] font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded">
              v1.0 RAG
            </span>
          </h1>
        </div>
      </div>

      {/* Center / Right controls */}
      <div className="flex items-center space-x-3">
        {/* Repository Selector Dropdown */}
        <div className="relative flex items-center">
          <div className="flex items-center space-x-2 bg-slate-800 border border-slate-700 hover:border-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded-md transition-colors">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400 font-normal">Repository:</span>
            <select
              value={selectedRepo?.id || ''}
              onChange={(e) => {
                const found = repositories.find((r) => r.id === e.target.value);
                if (found) onSelectRepo(found);
              }}
              className="bg-transparent text-indigo-300 font-semibold focus:outline-none cursor-pointer pr-1"
            >
              {repositories.length === 0 ? (
                <option value="">No Repositories</option>
              ) : (
                repositories.map((repo) => (
                  <option key={repo.id} value={repo.id} className="bg-slate-900 text-slate-200">
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
          className="flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-3 py-1.5 rounded-md transition-all shadow-sm active:scale-95"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ingest Repo</span>
        </button>
      </div>
    </header>
  );
};
