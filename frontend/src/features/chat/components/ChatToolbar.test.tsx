/**
 * ChatToolbar组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ChatToolbar } from './ChatToolbar';
import { useIsMobile } from '@/hooks/useMediaQuery';

// Mock dependencies
const mockNavigate = vi.fn();

vi.mock('@/hooks/useMediaQuery', () => ({
  useIsMobile: vi.fn(() => false),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ChatToolbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useIsMobile as any).mockReturnValue(false);
  });

  it('应该渲染工具栏', () => {
    render(<ChatToolbar />);
    
    // 应该显示健康档案按钮
    expect(screen.getByRole('button', { name: /健康档案/i })).toBeInTheDocument();
    // 应该显示个人资料按钮
    expect(screen.getByRole('button', { name: /个人资料/i })).toBeInTheDocument();
    // 应该显示偏好设置按钮
    expect(screen.getByRole('button', { name: /偏好设置/i })).toBeInTheDocument();
  });

  it('应该处理健康档案点击', async () => {
    const user = userEvent.setup();
    render(<ChatToolbar />);

    const healthButton = screen.getByRole('button', { name: /健康档案/i });
    await user.click(healthButton);

    expect(mockNavigate).toHaveBeenCalledWith('/health-record');
  });

  it('应该处理个人资料点击', async () => {
    const user = userEvent.setup();
    render(<ChatToolbar />);

    const profileButton = screen.getByRole('button', { name: /个人资料/i });
    await user.click(profileButton);

    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });

  it('应该处理偏好设置点击', async () => {
    const user = userEvent.setup();
    render(<ChatToolbar />);

    const settingsButton = screen.getByRole('button', { name: /偏好设置/i });
    await user.click(settingsButton);

    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });

  it('应该在移动端显示', () => {
    (useIsMobile as any).mockReturnValue(true);
    render(<ChatToolbar />);
    
    // 组件应该正常渲染
    expect(screen.getByRole('button', { name: /健康档案/i })).toBeInTheDocument();
  });

  it('应该接受isMobile prop', () => {
    render(<ChatToolbar isMobile={true} />);
    
    // 组件应该正常渲染
    expect(screen.getByRole('button', { name: /健康档案/i })).toBeInTheDocument();
  });
});
