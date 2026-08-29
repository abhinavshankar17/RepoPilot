import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Loader2, Sparkles, AlertTriangle, ArrowRight } from 'lucide-react';
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
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const sampleQuestions = [
    'Where is authentication implemented?',
    'How does JWT verification work?',
    'Where is the database connection initialized?',
    'Which files handle user registration?',
  ];

  return (
    <main className="flex-1 bg-slate-950 flex flex-col h-full overflow-hidden text-slate-100">
      {/* Panel Header */}
      <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 text-indigo-400" />
          <h2 className="text-xs font-semibold text-slate-200">RAG Codebase Copilot</h2>
        </div>
        <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded font-mono">
          Hybrid Search + Reranking
        </span>
      </div>

      {/* Messages Scroll Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-lg mx-auto">
            <div className="bg-indigo-600/10 p-3 rounded-xl text-indigo-400 border border-indigo-500/20 mb-3 shadow-inner">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">Ask RepoPilot About Your Codebase</h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Ask natural-language questions about architecture, authentication flows, database setup, or specific function definitions.
            </p>

            <div className="w-full space-y-2 text-left">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Suggested Developer Questions:
              </span>
              {sampleQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => onSendMessage(q)}
                  className="w-full text-left bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/80 text-xs text-slate-300 p-2.5 rounded-lg transition-all flex items-center justify-between group"
                >
                  <span>{q}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col space-y-1 ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              {/* Message Header */}
              <div className="flex items-center space-x-1.5 px-1 text-[10px] text-slate-400">
                {msg.role === 'user' ? (
                  <>
                    <span>Developer</span>
                    <User className="w-3 h-3 text-indigo-400" />
                  </>
                ) : (
                  <>
                    <Bot className="w-3 h-3 text-emerald-400" />
                    <span>RepoPilot Copilot</span>
                  </>
                )}
              </div>

              {/* Message Body */}
              <div
                className={`max-w-3xl rounded-xl p-3.5 text-xs leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-none'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none'
                }`}
              >
                {/* Rewritten Query Badge */}
                {msg.role === 'assistant' && msg.rewrittenQuery && msg.originalQuery && msg.rewrittenQuery !== msg.originalQuery && (
                  <div className="mb-2 p-2 bg-indigo-950/40 border border-indigo-500/20 rounded text-[11px] text-indigo-300">
                    <span className="font-semibold text-indigo-400">Context Resolved Query: </span>
                    <span>"{msg.rewrittenQuery}"</span>
                  </div>
                )}

                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-invert prose-xs max-w-none space-y-2">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}

                {/* Inline Citations Badges */}
                {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[10px] font-semibold text-slate-400 mr-1">Retrieved Sources:</span>
                    {msg.citations.map((c, i) => (
                      <button
                        key={`${c.chunk_id}-${i}`}
                        onClick={() => onSelectCitation(c)}
                        className="bg-slate-800 hover:bg-indigo-600/30 text-indigo-300 border border-slate-700 hover:border-indigo-500/50 text-[10px] px-2 py-0.5 rounded font-mono transition-colors flex items-center gap-1"
                      >
                        <span>{c.file_path}</span>
                        <span className="text-slate-400">L{c.start_line}-{c.end_line}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="flex items-start space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 p-3 rounded-xl max-w-md animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-slate-300">Executing Hybrid Search & LLM RAG...</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Searching vector store + BM25 keyword index and reranking code chunks.</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs p-3 rounded-xl flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200">Query Failed</p>
              <p className="text-[11px] mt-0.5">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Form */}
      <div className="p-3 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Ask a question about authentication, database, routes, or specific functions..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-sm"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
      </div>
    </main>
  );
};
