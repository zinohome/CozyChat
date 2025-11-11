import { http, HttpResponse } from 'msw';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Mock API handlers for MSW
 */
export const handlers = [
  // 认证相关
  http.post(`${API_BASE_URL}/v1/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      expires_in: 3600,
      user: {
        id: 'user-1',
        username: 'testuser',
        email: 'test@example.com',
      },
    });
  }),

  http.post(`${API_BASE_URL}/v1/auth/register`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      expires_in: 3600,
      user: {
        id: 'user-1',
        username: 'testuser',
        email: 'test@example.com',
      },
    });
  }),

  http.get(`${API_BASE_URL}/v1/auth/me`, () => {
    return HttpResponse.json({
      id: 'user-1',
      username: 'testuser',
      email: 'test@example.com',
    });
  }),

  // 会话相关
  http.get(`${API_BASE_URL}/v1/sessions`, () => {
    return HttpResponse.json({
      items: [
        {
          id: 'session-1',
          title: '测试会话',
          created_at: new Date().toISOString(),
          last_message_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }),

  http.post(`${API_BASE_URL}/v1/sessions`, () => {
    return HttpResponse.json({
      id: 'session-2',
      title: '新会话',
      created_at: new Date().toISOString(),
    });
  }),

  // 消息相关
  http.get(`${API_BASE_URL}/v1/chat/sessions/:sessionId/messages`, () => {
    return HttpResponse.json([
      {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date().toISOString(),
        session_id: 'session-1',
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date().toISOString(),
        session_id: 'session-1',
      },
    ]);
  }),

  // 人格相关
  http.get(`${API_BASE_URL}/v1/personalities`, () => {
    return HttpResponse.json([
      {
        id: 'default',
        name: '默认助手',
        description: '默认AI助手',
      },
    ]);
  }),
];

