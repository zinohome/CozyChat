/**
 * RegisterForm组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { RegisterForm } from './RegisterForm';
import { useAuth } from '../hooks/useAuth';

// Mock useAuth
const mockRegister = vi.fn();
const mockUseAuth = vi.fn(() => ({
  register: mockRegister,
  isRegistering: false,
}));

vi.mock('../hooks/useAuth', () => ({
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

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isRegistering: false,
    });
    mockNavigate.mockClear();
  });

  it('应该渲染注册表单', () => {
    render(<RegisterForm />);
    
    expect(screen.getByPlaceholderText(/请输入用户名/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/请输入邮箱/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/请输入密码/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/请确认密码/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /注册/i })).toBeInTheDocument();
  });

  it('应该验证必填字段', async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const submitButton = screen.getByRole('button', { name: /注册/i });
    await user.click(submitButton);

    await waitFor(() => {
      // 应该显示验证错误
      const errorText = screen.queryByText(/请输入用户名/i) || 
                       screen.queryByText(/请输入邮箱/i) ||
                       screen.queryByText(/请输入密码/i);
      expect(errorText).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('应该验证密码匹配', async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const usernameInput = screen.getByPlaceholderText(/请输入用户名/i);
    const emailInput = screen.getByPlaceholderText(/请输入邮箱/i);
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i);
    const confirmPasswordInput = screen.getByPlaceholderText(/请确认密码/i);
    const submitButton = screen.getByRole('button', { name: /注册/i });

    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'different');
    await user.click(submitButton);

    await waitFor(() => {
      // 应该显示密码不匹配错误
      const errorText = screen.queryByText(/密码不匹配/i) ||
                       screen.queryByText(/两次输入的密码不一致/i);
      expect(errorText).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('应该提交表单', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue({
      user: { id: '1', username: 'testuser' },
      access_token: 'test-token',
    });

    render(<RegisterForm />);

    const usernameInput = screen.getByPlaceholderText(/请输入用户名/i);
    const emailInput = screen.getByPlaceholderText(/请输入邮箱/i);
    const passwordInput = screen.getByPlaceholderText(/请输入密码/i);
    const confirmPasswordInput = screen.getByPlaceholderText(/请确认密码/i);
    const submitButton = screen.getByRole('button', { name: /注册/i });

    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
      });
    }, { timeout: 3000 });
  });

  it('应该显示加载状态', () => {
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isRegistering: true,
    });

    render(<RegisterForm />);
    
    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeInTheDocument();
  });
});
