import React, { useState } from 'react';
import { X, GitBranch, Github, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { createRepository } from '../services/api';
import { RepositoryResponse } from '../types';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (repo: RepositoryResponse) => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setIngesting(true);
    setError(null);

    try {
      const repo = await createRepository({
        url: repoUrl.trim(),
        branch: branch.trim() || undefined,
      });
      onSuccess(repo);
      onClose();
      setRepoUrl('');
      setBranch('');
    } catch (err: any) {
      setError(err.message || 'Failed to ingest repository');
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center space-x-2.5">
            <div className="bg-gradient-to-tr from-indigo-600 to-cyan-500 p-2 rounded-xl text-white shadow-md">
              <Github className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100">Ingest GitHub Repository</h3>
              <p className="text-xs text-slate-400">Scan AST code structure & index into FAISS</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs flex items-center space-x-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
              GitHub Repository URL <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <Github className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="url"
                required
                placeholder="https://github.com/username/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={ingesting}
                className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/40 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all shadow-inner"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
              Branch Name <span className="text-slate-500 font-normal">(Optional)</span>
            </label>
            <div className="relative">
              <GitBranch className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                placeholder="main (default)"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                disabled={ingesting}
                className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/40 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all shadow-inner"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={ingesting}
              className="px-4 py-2.5 rounded-xl border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-semibold transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={ingesting || !repoUrl.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center space-x-2 cursor-pointer active:scale-95"
            >
              {ingesting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Parsing AST & Indexing FAISS...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-cyan-300" />
                  <span>Start Ingestion</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
