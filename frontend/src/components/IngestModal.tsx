import React, { useState } from 'react';
import { X, GitBranch, Loader2, AlertCircle, Github } from 'lucide-react';
import { RepositoryCreate, RepositoryResponse } from '../types';
import { createRepository } from '../services/api';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (repo: RepositoryResponse) => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [url, setUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const payload: RepositoryCreate = {
        url: url.trim(),
        branch: branch.trim() || 'main',
      };
      const repo = await createRepository(payload);
      onSuccess(repo);
      setUrl('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to ingest repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-150">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-slate-100 font-semibold text-sm">
            <Github className="w-4 h-4 text-indigo-400" />
            <span>Ingest GitHub Repository</span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              GitHub Repository URL <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              placeholder="https://github.com/fastapi/fastapi"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              disabled={loading}
              className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-md px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Provides safe cloning, AST parsing, code chunking, and FAISS indexing.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center gap-1">
              <GitBranch className="w-3 h-3 text-slate-400" />
              <span>Branch</span>
            </label>
            <input
              type="text"
              placeholder="main"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              disabled={loading}
              className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-md px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
            />
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs px-3 py-2 rounded-md flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-4 py-2 rounded-md transition-all flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Cloning & Indexing...</span>
                </>
              ) : (
                <span>Start Ingestion</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
