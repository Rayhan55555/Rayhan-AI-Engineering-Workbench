import { apiClient, ApiResponse } from './client';

export interface BackendAgent {
  id: string;
  slug: string;
  name: string;
  purpose: string;
  status: 'Planned' | 'Configured' | 'Available' | 'Running' | 'Failed' | 'Maintenance';
  allowed_tools: string[];
  phase: number;
  limitations: string[];
  created_at: string;
  updated_at: string;
}

export async function getAgents(
  status?: string,
  search?: string
): Promise<ApiResponse<BackendAgent[]>> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (search) params.append('search', search);

  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiClient<BackendAgent[]>(`/api/v1/agents${qs}`);
}

export async function getAgentBySlug(slug: string): Promise<ApiResponse<BackendAgent>> {
  return apiClient<BackendAgent>(`/api/v1/agents/${slug}`);
}

export async function seedAgents(): Promise<ApiResponse<BackendAgent[]>> {
  return apiClient<BackendAgent[]>('/api/v1/agents/seed', {
    method: 'POST',
  });
}
