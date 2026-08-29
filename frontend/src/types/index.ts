export interface Citation {
  chunk_id: string;
  file_path: string;
  symbol?: string;
  start_line: number;
  end_line: number;
  language: string;
  score: number;
  snippet: string;
}

export interface RepositoryCreate {
  url: string;
  branch?: string;
}

export interface RepositoryResponse {
  id: string;
  name: string;
  url: string;
  branch: string;
  status: string;
  storage_path: string;
  file_count: number;
  chunk_count: number;
  detected_languages: string[];
  created_at: string;
  updated_at: string;
  message?: string;
}

export interface RepositoryListResponse {
  total: number;
  repositories: RepositoryResponse[];
}

export interface FileContentResponse {
  repository_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  total_lines: number;
  content: string;
}

export interface QueryRequest {
  query: string;
  session_id?: string;
  top_k?: number;
}

export interface QueryResponse {
  repository_id: string;
  session_id?: string;
  original_query: string;
  rewritten_query: string;
  answer: string;
  citations: Citation[];
}

export interface HealthResponse {
  status: string;
  environment: string;
  version: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  originalQuery?: string;
  rewrittenQuery?: string;
  content: string;
  citations?: Citation[];
  timestamp: string;
}
