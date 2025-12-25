const API_BASE = '/api/v1'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  headers?: Record<string, string>
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      credentials: 'include',
    }

    if (body) {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || 'Request failed')
    }

    return response.json()
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint)
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body })
  }

  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body })
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const api = new ApiClient(API_BASE)
