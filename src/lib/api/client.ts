/**
 * Base API Client for Rayhan AI Engineering Workbench
 * Connects frontend to the FastAPI REST backend.
 */

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && (import.meta.env.VITE_API_URL || import.meta.env.NEXT_PUBLIC_API_URL)) ||
  'http://localhost:8000';

// In-memory token storage (Security rule: Never store JWT in localStorage)
let inMemoryAccessToken: string | null = null;
let onUnauthorizedCallback: (() => void) | null = null;

export const setAccessToken = (token: string | null) => {
  inMemoryAccessToken = token;
};

export const getAccessToken = (): string | null => {
  return inMemoryAccessToken;
};

export const registerUnauthorizedHandler = (cb: () => void) => {
  onUnauthorizedCallback = cb;
};

export interface ApiResponse<T> {
  data: T | null;
  error: {
    code: string;
    message: string;
    statusCode: number;
  } | null;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (inMemoryAccessToken) {
    headers['Authorization'] = `Bearer ${inMemoryAccessToken}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback();
      }
      const errBody = await response.json().catch(() => ({}));
      return {
        data: null,
        error: {
          code: errBody.error || 'unauthorized',
          message: errBody.message || 'Session expired or unauthorized',
          statusCode: 401,
        },
      };
    }

    if (response.status === 204) {
      return { data: null, error: null };
    }

    const json = await response.json();

    if (!response.ok) {
      return {
        data: null,
        error: {
          code: json.error || 'api_error',
          message: json.message || 'API request failed',
          statusCode: response.status,
        },
      };
    }

    return { data: json as T, error: null };
  } catch (err) {
    return {
      data: null,
      error: {
        code: 'network_error',
        message: err instanceof Error ? err.message : 'Network request failed',
        statusCode: 0,
      },
    };
  }
}
