import React, { useEffect, useRef } from 'react';
import { FileCode2, Code2, AlertTriangle } from 'lucide-react';
import { FileContentResponse } from '../types';

interface CodeViewerProps {
  fileData: FileContentResponse | null;
  symbol?: string;
  startLine?: number;
  endLine?: number;
  loading: boolean;
  error: string | null;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  fileData,
  symbol,
  startLine,
  endLine,
  loading,
  error,
}) => {
  const targetLineRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to cited line range when selection changes
  useEffect(() => {
    if (targetLineRef.current) {
      targetLineRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [fileData?.file_path, startLine]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400 text-xs">
        <Code2 className="w-8 h-8 mb-2 text-indigo-400 animate-pulse" />
        <p className="font-semibold text-slate-300 text-sm">Loading source file...</p>
      </div>
    );
  }

  if (error || !fileData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400 text-xs">
        <AlertTriangle className="w-8 h-8 mb-2 text-amber-400 stroke-[1.5]" />
        <p className="font-semibold text-slate-300 text-sm">No source file open</p>
        <p className="text-slate-500 mt-1 max-w-xs leading-relaxed">
          {error || 'Select a file from the File Explorer or click a citation card to inspect code.'}
        </p>
      </div>
    );
  }

  const lines = fileData.content.split('\n');

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden font-mono select-text">
      {/* Sticky File Header */}
      <div className="p-3 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-2 truncate">
          <FileCode2 className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="font-bold text-xs text-slate-200 truncate">{fileData.file_path}</span>
        </div>
        <div className="flex items-center space-x-2 text-xs shrink-0">
          {symbol && (
            <span className="bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded font-mono">
              {symbol}
            </span>
          )}
          <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
            {fileData.total_lines} lines
          </span>
        </div>
      </div>

      {/* Code Scrolling Area */}
      <div className="flex-1 overflow-auto p-2">
        <div className="min-w-max">
          {lines.map((lineContent, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = startLine && endLine ? lineNum >= startLine && lineNum <= endLine : false;
            const isFirstTargetLine = lineNum === startLine;

            return (
              <div
                key={lineNum}
                ref={isFirstTargetLine ? targetLineRef : null}
                className={`flex items-stretch text-xs leading-6 transition-colors ${
                  isHighlighted
                    ? 'bg-indigo-600/25 border-l-4 border-indigo-400 font-semibold'
                    : 'hover:bg-slate-900/60'
                }`}
              >
                {/* Line Number Gutter */}
                <div
                  className={`w-12 text-right pr-4 select-none font-mono text-xs border-r border-slate-800/80 ${
                    isHighlighted ? 'text-indigo-300 font-bold bg-indigo-950/40' : 'text-slate-600'
                  }`}
                >
                  {lineNum}
                </div>

                {/* Line Code Content */}
                <div className="pl-4 pr-6 font-mono text-xs whitespace-pre text-slate-200">
                  {lineContent || ' '}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
