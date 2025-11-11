import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios before importing api
const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
};

vi.mock('axios', async () => {
  const actual = await vi.importActual('axios');
  return {
    ...actual,
    default: {
      ...(actual as any).default,
      create: vi.fn(() => mockAxiosInstance),
    },
  };
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'test-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该处理GET请求', async () => {
    const { apiClient } = await import('./api');
    const mockData = { id: '1', name: 'Test' };
    mockAxiosInstance.get.mockResolvedValue({ data: mockData });

    const result = await apiClient.get('/test');

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined);
    expect(result).toEqual(mockData);
  });

  it('应该处理POST请求', async () => {
    const { apiClient } = await import('./api');
    const mockData = { success: true };
    const requestData = { name: 'Test' };
    mockAxiosInstance.post.mockResolvedValue({ data: mockData });

    const result = await apiClient.post('/test', requestData);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', requestData, undefined);
    expect(result).toEqual(mockData);
  });

  it('应该处理PUT请求', async () => {
    const { apiClient } = await import('./api');
    const mockData = { id: '1', name: 'Updated' };
    const requestData = { name: 'Updated' };
    mockAxiosInstance.put.mockResolvedValue({ data: mockData });

    const result = await apiClient.put('/test', requestData);

    expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test', requestData, undefined);
    expect(result).toEqual(mockData);
  });

  it('应该处理DELETE请求', async () => {
    const { apiClient } = await import('./api');
    mockAxiosInstance.delete.mockResolvedValue({ data: {} });

    await apiClient.delete('/test');

    expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test', undefined);
  });
});

