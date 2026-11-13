import { apiClient, ApiResponse } from './client';
import { ExecutionItem, ExecutionStatusType } from '../../types';

export interface ExecutionCreateResponse {
  execution_id: string;
  task_id: string;
  agent_slug: string;
  status: ExecutionStatusType;
  simulated: boolean;
  message: string;
}

export interface PaginatedExecutions {
  items: ExecutionItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export async function submitExecution(
  agent_slug: string,
  instruction: string,
  scope: 'read_only' | 'suggest' | 'implement' = 'read_only',
  project_id?: string,
  context?: Record<string, any>
): Promise<ApiResponse<ExecutionCreateResponse>> {
  return apiClient<ExecutionCreateResponse>('/api/v1/executions', {
    method: 'POST',
    body: JSON.stringify({
      agent_slug,
      instruction,
      scope,
      project_id,
      context,
    }),
  });
}

export async function getExecutionById(executionId: string): Promise<ApiResponse<ExecutionItem>> {
  return apiClient<ExecutionItem>(`/api/v1/executions/${executionId}`);
}

export async function listExecutions(
  agent_slug?: string,
  status?: ExecutionStatusType,
  page = 1,
  limit = 10
): Promise<ApiResponse<PaginatedExecutions>> {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (agent_slug) params.append('agent_slug', agent_slug);
  if (status) params.append('status', status);

  return apiClient<PaginatedExecutions>(`/api/v1/executions?${params.toString()}`);
}

export async function cancelExecution(executionId: string): Promise<ApiResponse<ExecutionItem>> {
  return apiClient<ExecutionItem>(`/api/v1/executions/${executionId}`, {
    method: 'DELETE',
  });
}

export async function approveExecution(
  executionId: string,
  note?: string
): Promise<ApiResponse<ExecutionItem>> {
  return apiClient<ExecutionItem>(`/api/v1/executions/${executionId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved: true, note }),
  });
}

export async function rejectExecution(
  executionId: string,
  reason: string
): Promise<ApiResponse<ExecutionItem>> {
  return apiClient<ExecutionItem>(`/api/v1/executions/${executionId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

