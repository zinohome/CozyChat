/**
 * 音频可视化器
 * 
 * 负责：
 * - 初始化用户音频可视化
 * - 初始化助手音频可视化
 * - 提取频率数据
 * - 清理资源
 */

/**
 * 音频可视化器类
 */
export class AudioVisualizer {
  // 用户音频
  private userAnalyser: AnalyserNode | null = null;
  private userAudioContext: AudioContext | null = null;
  private userAnimationFrame: number | null = null;
  private isUpdatingUser: boolean = false;

  // 助手音频
  private assistantAnalyser: AnalyserNode | null = null;
  private assistantSource: MediaElementAudioSourceNode | MediaStreamAudioSourceNode | null = null;
  private assistantAudioContext: AudioContext | null = null;
  private assistantAnimationFrame: number | null = null;
  private isUpdatingAssistant: boolean = false;

  // 回调函数
  private onUserFrequencyData: ((data: Uint8Array) => void) | null = null;
  private onAssistantFrequencyData: ((data: Uint8Array) => void) | null = null;

  // 标志位：用于控制循环
  private isCalling: boolean = false;

  /**
   * 设置通话状态
   */
  setCallingState(isCalling: boolean): void {
    this.isCalling = isCalling;
  }

  /**
   * 初始化用户音频可视化
   * 
   * @param mediaStream - 用户的 MediaStream
   * @param callback - 频率数据回调
   */
  async initUserVisualization(
    mediaStream: MediaStream,
    callback: (data: Uint8Array) => void
  ): Promise<void> {
    try {
      // 如果已经在更新，先停止
      if (this.isUpdatingUser) {
        if (this.userAnimationFrame) {
          cancelAnimationFrame(this.userAnimationFrame);
          this.userAnimationFrame = null;
        }
        this.isUpdatingUser = false;
      }

      // 创建 AudioContext
      let audioContext: AudioContext;
      try {
        audioContext = new AudioContext({ sampleRate: 24000 });
        this.userAudioContext = audioContext;
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
      } catch (e) {
        console.error('[AudioVisualizer] 创建用户 AudioContext 失败:', e);
        return;
      }

      // 创建音频源和分析器
      const source = audioContext.createMediaStreamSource(mediaStream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      this.userAnalyser = analyser;

      source.connect(analyser);

      // 保存回调
      this.onUserFrequencyData = callback;

      console.log('[AudioVisualizer] 用户音频可视化已初始化');
    } catch (err) {
      console.error('[AudioVisualizer] 初始化用户音频可视化失败:', err);
      this.isUpdatingUser = false;
    }
  }

  /**
   * 初始化助手音频可视化
   * 
   * @param audioElement - 助手的 HTMLAudioElement
   * @param callback - 频率数据回调
   */
  initAssistantVisualization(
    audioElement: HTMLAudioElement,
    callback: (data: Uint8Array) => void
  ): void {
    try {
      // 如果已经在更新，先停止
      if (this.isUpdatingAssistant) {
        if (this.assistantAnimationFrame) {
          cancelAnimationFrame(this.assistantAnimationFrame);
          this.assistantAnimationFrame = null;
        }
        this.isUpdatingAssistant = false;
      }

      // 清理之前的连接（如果存在）
      if (this.assistantSource) {
        try {
          this.assistantSource.disconnect();
        } catch (e) {
          // 忽略断开连接错误
        }
        this.assistantSource = null;
      }

      if (this.assistantAudioContext) {
        try {
          this.assistantAudioContext.close();
        } catch (e) {
          // 忽略关闭错误
        }
        this.assistantAudioContext = null;
      }

      // 创建 AudioContext
      let audioContext: AudioContext;
      try {
        audioContext = new AudioContext({ sampleRate: 24000 });
        this.assistantAudioContext = audioContext;
        if (audioContext.state === 'suspended') {
          audioContext.resume();
        }
      } catch (e) {
        console.error('[AudioVisualizer] 创建助手 AudioContext 失败:', e);
        return;
      }

      // 优先使用 srcObject 的 MediaStream（更可靠）
      let source: MediaElementAudioSourceNode | MediaStreamAudioSourceNode;

      if (audioElement.srcObject instanceof MediaStream) {
        // 如果 audioElement 有 srcObject（MediaStream），直接使用它
        try {
          const streamSource = audioContext.createMediaStreamSource(audioElement.srcObject);
          this.assistantSource = streamSource;
          source = streamSource;
        } catch (e: any) {
          console.error('[AudioVisualizer] 从 MediaStream 创建音频源失败:', e);
          throw e;
        }
      } else {
        // 如果没有 srcObject，尝试从 audioElement 创建 MediaElementSource
        try {
          source = audioContext.createMediaElementSource(audioElement);
          this.assistantSource = source;
        } catch (e: any) {
          if (e.name === 'InvalidStateError' && e.message.includes('already connected')) {
            // 音频元素已被连接，跳过可视化（避免重复播放）
            console.warn('[AudioVisualizer] 音频元素已被连接，跳过可视化');
            return;
          } else {
            throw e;
          }
        }
      }

      // 创建分析器
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.1;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      this.assistantAnalyser = analyser;

      source.connect(analyser);
      analyser.connect(audioContext.destination);

      // 保存回调
      this.onAssistantFrequencyData = callback;

      console.log('[AudioVisualizer] 助手音频可视化已初始化');
    } catch (err) {
      console.error('[AudioVisualizer] 初始化助手音频可视化失败:', err);
      this.isUpdatingAssistant = false;
    }
  }

  /**
   * 启动用户频率提取
   */
  startUserFrequencyExtraction(): void {
    if (!this.userAnalyser || !this.onUserFrequencyData) {
      console.warn('[AudioVisualizer] 无法启动用户频率提取：未初始化');
      return;
    }

    if (this.isUpdatingUser) {
      console.warn('[AudioVisualizer] 用户频率提取已在运行');
      return;
    }

    this.isUpdatingUser = true;

    const updateUserAudioVisualization = () => {
      // 检查是否应该继续更新
      if (!this.userAnalyser || !this.isCalling || !this.isUpdatingUser) {
        this.isUpdatingUser = false;
        this.userAnimationFrame = null;
        return;
      }

      try {
        const bufferLength = this.userAnalyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.userAnalyser.getByteFrequencyData(dataArray);

        // 调用回调
        if (this.onUserFrequencyData) {
          this.onUserFrequencyData(dataArray);
        }

        // 继续下一帧
        this.userAnimationFrame = requestAnimationFrame(updateUserAudioVisualization);
      } catch (err) {
        console.error('[AudioVisualizer] 更新用户音频可视化失败:', err);
        this.isUpdatingUser = false;
        this.userAnimationFrame = null;
      }
    };

    // 延迟启动，确保 isCalling 已设置
    setTimeout(() => {
      if (this.isCalling && this.userAnalyser && this.isUpdatingUser) {
        updateUserAudioVisualization();
      }
    }, 200);

    console.log('[AudioVisualizer] 用户频率提取已启动');
  }

  /**
   * 获取当前用户频率数据
   */
  getCurrentUserFrequencyData(): Uint8Array | null {
    if (!this.userAnalyser) {
      return null;
    }
    const bufferLength = this.userAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.userAnalyser.getByteFrequencyData(dataArray);
    return dataArray;
  }

  /**
   * 获取当前助手频率数据
   */
  getCurrentAssistantFrequencyData(): Uint8Array | null {
    if (!this.assistantAnalyser) {
      return null;
    }
    const bufferLength = this.assistantAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.assistantAnalyser.getByteFrequencyData(dataArray);
    return dataArray;
  }

  /**
   * 启动助手频率提取
   */
  startAssistantFrequencyExtraction(): void {
    if (!this.assistantAnalyser || !this.onAssistantFrequencyData) {
      console.warn('[AudioVisualizer] 无法启动助手频率提取：未初始化');
      return;
    }

    this.isUpdatingAssistant = true;

    const updateAssistantAudioVisualization = () => {
      // 检查是否应该继续更新
      if (!this.assistantAnalyser || !this.isCalling || !this.isUpdatingAssistant) {
        this.isUpdatingAssistant = false;
        this.assistantAnimationFrame = null;
        return;
      }

      try {
        const bufferLength = this.assistantAnalyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.assistantAnalyser.getByteFrequencyData(dataArray);

        // 调用回调
        if (this.onAssistantFrequencyData) {
          this.onAssistantFrequencyData(dataArray);
        }

        // 继续下一帧
        this.assistantAnimationFrame = requestAnimationFrame(updateAssistantAudioVisualization);
      } catch (err) {
        console.error('[AudioVisualizer] 更新助手音频可视化失败:', err);
        this.isUpdatingAssistant = false;
        this.assistantAnimationFrame = null;
      }
    };

    // 立即启动或延迟启动
    if (this.isCalling && this.assistantAnalyser) {
      updateAssistantAudioVisualization();
    } else {
      setTimeout(() => {
        if (this.isCalling && this.assistantAnalyser && this.isUpdatingAssistant) {
          updateAssistantAudioVisualization();
        }
      }, 200);
    }

    console.log('[AudioVisualizer] 助手频率提取已启动');
  }

  /**
   * 停止频率提取
   */
  stopFrequencyExtraction(): void {
    if (this.userAnimationFrame) {
      cancelAnimationFrame(this.userAnimationFrame);
      this.userAnimationFrame = null;
    }
    if (this.assistantAnimationFrame) {
      cancelAnimationFrame(this.assistantAnimationFrame);
      this.assistantAnimationFrame = null;
    }
    this.isUpdatingUser = false;
    this.isUpdatingAssistant = false;
    console.log('[AudioVisualizer] 频率提取已停止');
  }

  /**
   * 清理资源
   */
  cleanup(): void {
    this.stopFrequencyExtraction();

    // 断开和关闭助手音频上下文
    if (this.assistantSource) {
      try {
        this.assistantSource.disconnect();
      } catch (e) {
        // 忽略错误
      }
      this.assistantSource = null;
    }
    if (this.assistantAudioContext) {
      try {
        this.assistantAudioContext.close();
      } catch (e) {
        // 忽略错误
      }
      this.assistantAudioContext = null;
    }

    // 关闭用户音频上下文
    if (this.userAudioContext) {
      try {
        this.userAudioContext.close();
      } catch (e) {
        // 忽略错误
      }
      this.userAudioContext = null;
    }

    this.userAnalyser = null;
    this.assistantAnalyser = null;
    this.onUserFrequencyData = null;
    this.onAssistantFrequencyData = null;

    console.log('[AudioVisualizer] 资源已清理');
  }
}

