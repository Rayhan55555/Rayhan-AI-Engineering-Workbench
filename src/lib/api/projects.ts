import { apiClient, ApiResponse } from './client';

export interface BackendProject {
  id: string;
  name: string;
  description: string | null;
  status: 'Active' | 'Paused' | 'Archived';
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedProjects {
  items: BackendProject[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export async function getProjects(
  page = 1,
  limit = 10,
  status?: string
): Promise<ApiResponse<PaginatedProjects>> {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (status) params.append('status', status);

  return apiClient<PaginatedProjects>(`/api/v1/projects?${params.toString()}`);
}

export async function createProject(
  name: string,
  description?: string,
  status = 'Active'
): Promise<ApiResponse<BackendProject>> {
  return apiClient<BackendProject>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify({ name, description, status }),
  });
}

export async function getProjectById(id: string): Promise<ApiResponse<BackendProject>> {
  return apiClient<BackendProject>(`/api/v1/projects/${id}`);
}

export async function updateProject(
  id: string,
  data: { name?: string; description?: string; status?: string }
): Promise<ApiResponse<BackendProject>> {
  return apiClient<BackendProject>(`/api/v1/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<ApiResponse<null>> {
  return apiClient<null>(`/api/v1/projects/${id}`, {
    method: 'DELETE',
  });
}
