import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle, Loader2, FileCode2, ArrowRight } from 'lucide-react';
import { ChatMessage, Citation } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  onSendMessage: (query: string) => void;
  onSelectCitation: (citation: Citation) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  loading,
  error,
  onSendMessage,
  onSelectCitation,
}) => {
  const [inputQuery, setInputQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;
    onSendMessage(inputQuery.trim());
    setInputQuery('');
  };

  return (
    <main className="flex-1 bg-slate-950 flex flex-col h-full overflow-hidden text-slate-100">
      {/* Panel Header Bar */}
      <div className="p-4 border-b border-slate-800/90 bg-slate-900/60 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-2.5">
          <Bot className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-sm text-slate-200 tracking-wide">RAG Codebase Copilot</h2>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span className="bg-slate-800/80 border border-slate-700/60 px-2.5 py-1 rounded-lg">Hybrid Search</span>
          <span>+</span>
          <span className="bg-slate-800/80 border border-slate-700/60 px-2.5 py-1 rounded-lg">Reranking</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-xl mx-auto">
            <div className="bg-indigo-600/15 border border-indigo-500/30 p-4 rounded-2xl mb-4 text-indigo-400 shadow-xl shadow-indigo-500/10">
              <Sparkles className="w-8 h-8 stroke-[1.75]" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">Ask RepoPilot About Your Codebase</h3>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed">
              Ask natural-language questions about functions, architecture flows, modification impacts, or feature change plans grounded strictly in AST code parser context.
            </p>
            <div className="grid grid-cols-1 gap-2.5 w-full text-left">
              {[
                'Explain the request flow for POST /api/orders',
                'What could be affected if I modify auth.js?',
                'Where is the token generated?',
                'I want to add Google OAuth. Which files need modification?',
              ].map((sample, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(sample)}
                  className="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/60 p-3 rounded-xl text-xs text-slate-300 hover:text-indigo-200 transition-all flex items-center justify-between group cursor-pointer"
                >
                  <span>"{sample}"</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-transform group-hover:translate-x-1" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex space-x-3.5 max-w-3xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''
              }`}
            >
              {/* Role Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-tr from-cyan-600 to-blue-600 text-white'
                    : 'bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white'
                }`}
              >
                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Content Bubble */}
              <div className="flex-1 space-y-2">
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white font-medium shadow-md shadow-indigo-600/20'
                      : 'bg-slate-900/90 border border-slate-800/90 text-slate-200 shadow-md'
                  }`}
                >
                  {/* Rewritten Query Badge */}
                  {msg.rewrittenQuery && msg.rewrittenQuery !== msg.originalQuery && (
                    <div className="mb-3 p-2 bg-slate-950/80 border border-indigo-500/30 rounded-lg text-xs text-indigo-300 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Rewritten Search Query: <strong>"{msg.rewrittenQuery}"</strong></span>
                    </div>
                  )}

                  <div className="whitespace-pre-wrap font-sans text-sm">{msg.content}</div>

                  {/* Citation Pills */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80">
                      <p className="text-xs font-semibold text-slate-400 mb-2">Retrieved Sources:</p>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((c, idx) => (
                          <button
                            key={idx}
                            onClick={() => onSelectCitation(c)}
                            className="bg-slate-950 border border-slate-800 hover:border-indigo-500/70 text-indigo-300 text-xs px-2.5 py-1 rounded-lg flex items-center space-x-1.5 transition-all cursor-pointer font-mono"
                          >
                            <FileCode2 className="w-3.5 h-3.5 text-cyan-400" />
                            <span>{c.file_path}</span>
                            <span className="text-slate-500">L{c.start_line}-{c.end_line}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="text-[11px] text-slate-500 px-1">{msg.timestamp}</div>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-center space-x-3 text-slate-400 text-sm p-4 bg-slate-900/60 border border-slate-800 rounded-2xl max-w-md">
            <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
            <span>Analyzing repository chunks & generating answer...</span>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-2xl text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80">
        <form onSubmit={handleSubmit} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            placeholder="Ask a question about authentication, database, routes, or specific functions..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
            className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/40 rounded-2xl pl-5 pr-14 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="absolute right-2 bg-gradient-to-tr from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-40 text-white p-2.5 rounded-xl transition-all shadow-md active:scale-95 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </main>
  );
};
