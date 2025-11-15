/**
 * 传输层策略工厂
 * 
 * 根据配置创建相应的传输层策略实例
 */

import type { ITransportStrategy } from './ITransportStrategy';
import { WebRTCStrategy } from './WebRTCStrategy';
import { WebSocketStrategy } from './WebSocketStrategy';

/**
 * 传输层策略工厂类
 */
export class TransportStrategyFactory {
  /**
   * 创建传输层策略实例
   * 
   * @param type - 传输层类型
   * @returns 传输层策略实例
   */
  static create(type: 'webrtc' | 'websocket'): ITransportStrategy {
    switch (type) {
      case 'webrtc':
        return new WebRTCStrategy();
      case 'websocket':
        return new WebSocketStrategy();
      default:
        throw new Error(`Unsupported transport type: ${type}`);
    }
  }
}

