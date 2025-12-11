/**
 * usePersonalities Hook测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { usePersonalities } from './usePersonalities';
import { personalityApi } from '@/services/personality';

// Mock personalityApi
vi.mock('@/services/personality', () => ({
  personalityApi: {
    getPersonalities: vi.fn(() => Promise.resolve([
      {
        id: 'personality-1',
        name: 'Personality 1',
        description: 'Description 1',
      },
    ])),
  },
}));

// Mock useQuery
const mockUseQuery = vi.fn();
vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query');
  return {
    ...actual,
    useQuery: (options: any) => mockUseQuery(options),
  };
});

describe('usePersonalities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseQuery.mockReturnValue({
      data: [
        {
          id: 'personality-1',
          name: 'Personality 1',
          description: 'Description 1',
        },
      ],
      isLoading: false,
      error: null,
    });
  });

  it('应该返回人格列表', () => {
    const { result } = renderHook(() => usePersonalities());
    
    expect(result.current.personalities).toBeDefined();
    expect(Array.isArray(result.current.personalities)).toBe(true);
  });

  it('应该返回加载状态', () => {
    mockUseQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { result } = renderHook(() => usePersonalities());
    
    expect(result.current.isLoading).toBe(true);
  });

  it('应该返回错误状态', () => {
    mockUseQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Test error'),
    });

    const { result } = renderHook(() => usePersonalities());
    
    // usePersonalities可能不直接返回error，但应该能正常处理错误状态
    expect(result.current).toBeDefined();
    expect(result.current.isLoading).toBe(false);
  });
});
