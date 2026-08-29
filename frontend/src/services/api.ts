import {
  HealthResponse,
  RepositoryCreate,
  RepositoryResponse,
  RepositoryListResponse,
  FileContentResponse,
  QueryRequest,
  QueryResponse
} from '../types';

const API_BASE = '/api/v1';

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function listRepositories(): Promise<RepositoryListResponse> {
  const response = await fetch(`${API_BASE}/repositories`);
  if (!response.ok) {
    throw new Error(`Failed to list repositories: ${response.statusText}`);
  }
  return response.json();
}

export async function getRepository(repoId: string): Promise<RepositoryResponse> {
  const response = await fetch(`${API_BASE}/repositories/${repoId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch repository: ${response.statusText}`);
  }
  return response.json();
}

export async function createRepository(data: RepositoryCreate): Promise<RepositoryResponse> {
  const response = await fetch(`${API_BASE}/repositories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to ingest repository' }));
    throw new Error(errorData.detail || 'Repository ingestion failed');
  }

  return response.json();
}

export async function getFileContent(
  repoId: string,
  filePath: string,
  startLine?: number,
  endLine?: number
): Promise<FileContentResponse> {
  let url = `${API_BASE}/repositories/${repoId}/files/${encodeURIComponent(filePath).replace(/%2F/g, '/')}`;
  const params = new URLSearchParams();
  if (startLine) params.append('start_line', startLine.toString());
  if (endLine) params.append('end_line', endLine.toString());
  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch file content' }));
    throw new Error(errorData.detail || 'File retrieval failed');
  }

  return response.json();
}

export async function queryRepository(repoId: string, data: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/repositories/${repoId}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to execute RAG query' }));
    throw new Error(errorData.detail || 'RAG query failed');
  }

  return response.json();
}
