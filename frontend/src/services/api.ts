import { HealthResponse, RepositoryCreate, RepositoryResponse, QueryRequest, QueryResponse } from '../types';

const API_BASE = '/api/v1';

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
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
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create repository' }));
    throw new Error(errorData.detail || 'Repository registration failed');
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
    const errorData = await response.json().catch(() => ({ detail: 'Failed to execute query' }));
    throw new Error(errorData.detail || 'Query execution failed');
  }

  return response.json();
}
