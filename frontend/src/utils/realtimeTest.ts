/**
 * 验证 Realtime API 端点是否可用
 */

/**
 * 测试 WebRTC 端点是否可用
 * 
 * @param baseUrl - 基础 URL（例如：https://oneapi.naivehero.top）
 * @param apiKey - API 密钥
 * @returns 测试结果
 */
export async function testWebRTCEndpoint(
  baseUrl: string,
  apiKey: string
): Promise<{
  success: boolean;
  endpoint: string;
  error?: string;
  status?: number;
  response?: any;
}> {
  // WebRTC 端点：/v1/realtime/calls
  const endpoint = `${baseUrl}/v1/realtime/calls`;
  
  try {
    // 创建一个简单的 WebRTC offer 用于测试
    const pc = new RTCPeerConnection();
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    if (!offer.sdp) {
      return {
        success: false,
        endpoint,
        error: 'Failed to create WebRTC offer',
      };
    }
    
    // 发送 POST 请求到端点
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/sdp',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: offer.sdp,
    });
    
    // 清理
    pc.close();
    
    return {
      success: response.ok,
      endpoint,
      status: response.status,
      response: response.ok ? await response.text() : await response.text(),
    };
  } catch (error: any) {
    return {
      success: false,
      endpoint,
      error: error.message || 'Unknown error',
    };
  }
}

/**
 * 测试 WebSocket 端点是否可用
 * 
 * @param baseUrl - 基础 URL（例如：https://oneapi.naivehero.top）
 * @param apiKey - API 密钥
 * @returns 测试结果
 */
export async function testWebSocketEndpoint(
  baseUrl: string,
  apiKey: string
): Promise<{
  success: boolean;
  endpoint: string;
  error?: string;
}> {
  // WebSocket 端点：wss://oneapi.naivehero.top/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01
  const wsBaseUrl = baseUrl.replace(/^https?:\/\//, 'wss://');
  const endpoint = `${wsBaseUrl}/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01`;
  
  return new Promise((resolve) => {
    const protocols = [
      'realtime',
      `openai-insecure-api-key.${apiKey}`,
      'openai-beta.realtime-v1',
    ];
    
    const ws = new WebSocket(endpoint, protocols);
    
    const timeout = setTimeout(() => {
      ws.close();
      resolve({
        success: false,
        endpoint,
        error: 'Connection timeout',
      });
    }, 5000);
    
    ws.onopen = () => {
      clearTimeout(timeout);
      ws.close();
      resolve({
        success: true,
        endpoint,
      });
    };
    
    ws.onerror = (error) => {
      clearTimeout(timeout);
      ws.close();
      resolve({
        success: false,
        endpoint,
        error: 'WebSocket connection failed',
      });
    };
  });
}

/**
 * 验证所有 Realtime API 端点
 * 
 * @param baseUrl - 基础 URL
 * @param apiKey - API 密钥
 * @returns 验证结果
 */
export async function verifyRealtimeEndpoints(
  baseUrl: string,
  apiKey: string
): Promise<{
  webrtc: Awaited<ReturnType<typeof testWebRTCEndpoint>>;
  websocket: Awaited<ReturnType<typeof testWebSocketEndpoint>>;
}> {
  console.log('开始验证 Realtime API 端点...');
  console.log('Base URL:', baseUrl);
  
  const [webrtc, websocket] = await Promise.all([
    testWebRTCEndpoint(baseUrl, apiKey),
    testWebSocketEndpoint(baseUrl, apiKey),
  ]);
  
  console.log('WebRTC 端点测试结果:', webrtc);
  console.log('WebSocket 端点测试结果:', websocket);
  
  return { webrtc, websocket };
}

