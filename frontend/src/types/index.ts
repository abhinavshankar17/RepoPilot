export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
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
  branch?: string;
  status: string;
  file_count: number;
  chunk_count: number;
  created_at: string;
  message?: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface QueryResponse {
  repository_id: string;
  query: string;
  answer: string;
  citations: Citation[];
}

export interface HealthResponse {
  status: string;
  environment: string;
  version: string;
}
