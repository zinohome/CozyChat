/**
 * 传输层工厂
 * 
 * 根据配置创建相应的传输层实例
 */

import type { ITransport, TransportType } from './TransportInterface';
import { WebRTCTransport } from './WebRTCTransport';
// import { WebSocketTransport } from './WebSocketTransport'; // 阶段3实现

/**
 * 传输层工厂类
 */
export class TransportFactory {
  /**
   * 创建传输层实例
   * 
   * @param type - 传输层类型
   * @param config - 传输层配置
   * @returns 传输层实例
   */
  static create(type: TransportType, config: Record<string, any>): ITransport {
    switch (type) {
      case 'webrtc':
        return new WebRTCTransport(config);
      case 'websocket':
        // 阶段3实现
        // return new WebSocketTransport(config);
        throw new Error('WebSocket transport is not implemented yet');
      default:
        throw new Error(`Unsupported transport type: ${type}`);
    }
  }
}

