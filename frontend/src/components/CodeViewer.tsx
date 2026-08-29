import React, { useEffect, useRef } from 'react';
import { FileCode2, Code, ArrowUpRight, Hash, Layers } from 'lucide-react';
import { FileContentResponse } from '../types';

interface CodeViewerProps {
  fileData: FileContentResponse | null;
  language?: string;
  symbol?: string;
  startLine?: number;
  endLine?: number;
  loading: boolean;
  error: string | null;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  fileData,
  language,
  symbol,
  startLine,
  endLine,
  loading,
  error,
}) => {
  const highlightedLineRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Smooth jump-to-line and auto-scroll when startLine changes
  useEffect(() => {
    if (highlightedLineRef.current && startLine && startLine > 1) {
      highlightedLineRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    } else if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [fileData, startLine]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-slate-400 text-xs">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2" />
        <span>Loading source code content...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 m-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-lg text-xs">
        <p className="font-semibold text-rose-200">Failed to load file</p>
        <p className="text-[11px] mt-0.5">{error}</p>
      </div>
    );
  }

  if (!fileData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs select-none">
        <Code className="w-8 h-8 mb-2 text-slate-700 stroke-[1.5]" />
        <p>No file open in inspector.</p>
        <p className="text-[11px] text-slate-600 mt-1">Select a file from File Explorer or click a Citation card.</p>
      </div>
    );
  }

  const lines = fileData.content.split('\n');
  const targetStart = startLine || 1;
  const targetEnd = endLine || 1;
  const isRange = startLine && endLine && startLine <= endLine;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 font-mono text-xs overflow-hidden">
      {/* File Inspector Header Bar */}
      <div className="px-3 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-[11px] shrink-0">
        <div className="flex items-center space-x-2 truncate mr-2">
          <FileCode2 className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span className="text-slate-200 font-semibold truncate">{fileData.file_path}</span>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {symbol && (
            <span className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded text-[10px] flex items-center gap-1">
              <Layers className="w-3 h-3" />
              <span>{symbol}</span>
            </span>
          )}
          {language && (
            <span className="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px]">
              {language}
            </span>
          )}
          <span className="text-slate-500 text-[10px]">{fileData.total_lines} lines</span>
        </div>
      </div>

      {/* Cited Range Banner if highlighted */}
      {isRange && (
        <div className="px-3 py-1.5 bg-indigo-950/60 border-b border-indigo-500/30 text-[11px] text-indigo-300 flex items-center justify-between shrink-0">
          <span className="flex items-center gap-1 font-medium">
            <Hash className="w-3 h-3 text-indigo-400" />
            <span>Highlighting Cited Lines {targetStart}–{targetEnd}</span>
          </span>
          <button
            onClick={() => {
              highlightedLineRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
            className="text-[10px] underline hover:text-indigo-200 transition-colors flex items-center gap-0.5"
          >
            Jump to line {targetStart} <ArrowUpRight className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Code Content & Line Gutter */}
      <div ref={scrollContainerRef} className="flex-1 overflow-auto p-2 leading-relaxed">
        {lines.map((lineText, idx) => {
          const lineNum = idx + 1;
          const isTargetStart = lineNum === targetStart;
          const isHighlighted = isRange && lineNum >= targetStart && lineNum <= targetEnd;

          return (
            <div
              key={lineNum}
              ref={isTargetStart ? highlightedLineRef : null}
              className={`flex items-start px-2 py-0.5 rounded transition-colors ${
                isHighlighted
                  ? 'bg-indigo-600/30 text-indigo-100 border-l-2 border-indigo-400'
                  : 'text-slate-300 hover:bg-slate-900/50'
              }`}
            >
              {/* Line Number Gutter */}
              <span
                className={`w-9 text-right pr-3 select-none shrink-0 text-[10px] font-mono ${
                  isHighlighted ? 'text-indigo-400 font-bold' : 'text-slate-600'
                }`}
              >
                {lineNum}
              </span>

              {/* Code Line Text */}
              <pre className="whitespace-pre overflow-x-auto font-mono text-[11px]">{lineText || ' '}</pre>
            </div>
          );
        })}
      </div>
    </div>
  );
};
