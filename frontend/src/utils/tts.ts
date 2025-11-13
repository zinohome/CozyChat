import { voiceApi } from '@/services/voice';
import { showError } from '@/utils/errorHandler';
import type { SpeechRequest } from '@/types/voice';
import { TTS_CONFIG } from '@/config/tts';

/**
 * TTS播放工具
 *
 * 提供文本转语音播放功能。
 */

/**
 * 提取纯文本内容（去除Markdown标记）
 */
export function extractPlainText(content: string): string {
  return content
    .replace(/```[\s\S]*?```/g, '') // 移除代码块
    .replace(/`[^`]+`/g, '') // 移除行内代码
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // 移除链接，保留文本
    .replace(/#{1,6}\s+/g, '') // 移除标题标记
    .replace(/\*\*([^*]+)\*\*/g, '$1') // 移除粗体标记
    .replace(/\*([^*]+)\*/g, '$1') // 移除斜体标记
    .replace(/^\s*[-*+]\s+/gm, '') // 移除列表标记
    .replace(/^\s*\d+\.\s+/gm, '') // 移除有序列表标记
    .trim();
}

/**
 * 将文本分段（按句子和段落分割）
 *
 * @param text 要分段的文本
 * @param maxLength 每段最大长度
 * @returns 文本段落数组
 */
function splitTextIntoSegments(text: string, maxLength: number): string[] {
  const segments: string[] = [];
  const sentences = text.split(/([。！？\n]+)/);
  
  let currentSegment = '';
  
  for (let i = 0; i < sentences.length; i++) {
    const sentence = sentences[i];
    const nextSentence = sentences[i + 1] || '';
    const combined = currentSegment + sentence + nextSentence;
    
    if (combined.length <= maxLength) {
      currentSegment = combined;
      i++; // 跳过下一个句子（已经合并）
    } else {
      if (currentSegment.trim()) {
        segments.push(currentSegment.trim());
      }
      currentSegment = sentence + nextSentence;
      i++; // 跳过下一个句子（已经合并）
    }
  }
  
  if (currentSegment.trim()) {
    segments.push(currentSegment.trim());
  }
  
  // 如果分段后仍有超长段落，强制按长度分割
  const finalSegments: string[] = [];
  for (const segment of segments) {
    if (segment.length <= maxLength) {
      finalSegments.push(segment);
    } else {
      // 强制分割
      for (let i = 0; i < segment.length; i += maxLength) {
        finalSegments.push(segment.slice(i, i + maxLength));
      }
    }
  }
  
  return finalSegments.filter(s => s.trim().length > 0);
}

/**
 * 播放单个音频段落
 *
 * @param audioBlob 音频Blob
 * @returns Promise<HTMLAudioElement>
 */
function playAudioSegment(audioBlob: Blob): Promise<HTMLAudioElement> {
  return new Promise((resolve, reject) => {
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
    });
    
    audio.addEventListener('error', (e) => {
      URL.revokeObjectURL(audioUrl);
      reject(e);
    });
    
    audio.play()
      .then(() => resolve(audio))
      .catch(reject);
  });
}

/**
 * 使用分段TTS播放语音（边转边播放）
 *
 * @param text 要播放的文本
 * @param personalityId 人格ID
 * @param onEnd 播放结束回调
 * @param onProgress 进度回调（可选）
 * @returns Audio对象，可用于控制播放（返回最后一个音频对象）
 */
async function playTTSSegmented(
  text: string,
  personalityId?: string,
  onEnd?: () => void,
  onProgress?: (progress: number) => void
): Promise<HTMLAudioElement | null> {
  try {
    // 将文本分段
    const segments = splitTextIntoSegments(text, TTS_CONFIG.SEGMENT_LENGTH);
    console.log(`文本分段: ${segments.length}段，总长度: ${text.length}字符`);
    
    if (segments.length === 0) {
      return null;
    }
    
    // 并行转换所有段落（提前准备）
    const convertSegment = async (segment: string, index: number): Promise<{ index: number; blob: Blob }> => {
      const request: SpeechRequest = {
        input: segment,
        model: 'tts-1',
        voice: 'alloy',
        speed: 1.0,
        personality_id: personalityId,
      };
      
      const audioBlob = await voiceApi.synthesize(request);
      console.log(`第${index + 1}段转换完成（${segment.length}字符）`);
      
      // 更新进度
      if (onProgress) {
        const progress = Math.floor(((index + 1) / segments.length) * 90); // 90%用于转换，10%用于播放
        onProgress(progress);
      }
      
      return { index, blob: audioBlob };
    };
    
    // 启动所有段落的转换（并行）
    const conversionPromises = segments.map((segment, index) => convertSegment(segment, index));
    
    // 等待第一段转换完成，立即播放
    const firstResult = await conversionPromises[0];
    let lastAudio: HTMLAudioElement | null = null;
    
    try {
      lastAudio = await playAudioSegment(firstResult.blob);
      console.log(`第1段开始播放（${segments[0].length}字符）`);
    } catch (playError: any) {
      if (playError.name === 'NotAllowedError') {
        console.warn('音频自动播放被浏览器阻止');
        return null;
      }
      throw playError;
    }
    
    // 在第一段播放的同时，等待后续段落转换完成
    // 然后按顺序播放
    for (let i = 1; i < segments.length; i++) {
      // 等待当前段转换完成（如果还没完成）
      const result = await conversionPromises[i];
      
      // 等待上一段播放完成
      if (lastAudio) {
        await new Promise<void>((resolve) => {
          const onEnded = () => {
            lastAudio!.removeEventListener('ended', onEnded);
            resolve();
          };
          lastAudio!.addEventListener('ended', onEnded);
        });
      }
      
      // 播放当前段（此时已经转换完成）
      try {
        lastAudio = await playAudioSegment(result.blob);
        console.log(`第${i + 1}段开始播放（${segments[i].length}字符）`);
      } catch (playError: any) {
        if (playError.name === 'NotAllowedError') {
          console.warn('音频自动播放被浏览器阻止');
          return lastAudio;
        }
        throw playError;
      }
    }
    
    // 监听最后一段播放结束
    if (lastAudio && onEnd) {
      lastAudio.addEventListener('ended', () => {
        onEnd();
      });
    }
    
    if (onProgress) {
      onProgress(100);
    }
    
    return lastAudio;
  } catch (error: any) {
    console.error('分段TTS播放失败:', error);
    if (error.name !== 'NotAllowedError') {
      showError(error, '语音合成失败');
    }
    return null;
  }
}

/**
 * 使用流式TTS播放语音（适用于长文本，但等待全部完成）
 *
 * @param text 要播放的文本
 * @param personalityId 人格ID
 * @param onEnd 播放结束回调
 * @param onProgress 进度回调（可选）
 * @returns Audio对象，可用于控制播放
 */
async function playTTSStream(
  text: string,
  personalityId?: string,
  onEnd?: () => void,
  onProgress?: (progress: number) => void
): Promise<HTMLAudioElement | null> {
  try {
    // 构建TTS请求
    const request: SpeechRequest = {
      input: text,
      model: 'tts-1',
      voice: 'alloy',
      speed: 1.0,
      personality_id: personalityId,
    };

    // 收集所有音频块
    const audioChunks: Blob[] = [];
    let totalSize = 0;

    // 流式接收音频数据
    for await (const chunk of voiceApi.synthesizeStream(request)) {
      audioChunks.push(chunk);
      totalSize += chunk.size;
      
      // 更新进度（估算：假设每1000字节约1秒音频）
      if (onProgress) {
        const estimatedProgress = Math.min(95, (totalSize / 1000) * 10); // 最多95%，留5%给合并和播放
        onProgress(estimatedProgress);
      }
    }

    // 合并所有音频块
    const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
    
    if (onProgress) {
      onProgress(100);
    }

    // 创建音频对象
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);

    // 监听播放结束
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
      if (onEnd) {
        onEnd();
      }
    });

    // 监听播放错误
    audio.addEventListener('error', (e) => {
      console.error('音频播放错误:', e);
      URL.revokeObjectURL(audioUrl);
      showError(new Error('音频播放失败'), '播放失败');
    });

    // 开始播放
    try {
      await audio.play();
      return audio;
    } catch (playError: any) {
      if (playError.name === 'NotAllowedError') {
        console.warn('音频自动播放被浏览器阻止，需要用户交互后才能播放');
        URL.revokeObjectURL(audioUrl);
        return null;
      }
      throw playError;
    }
  } catch (error: any) {
    console.error('流式TTS播放失败:', error);
    if (error.name !== 'NotAllowedError') {
      showError(error, '语音合成失败');
    }
    return null;
  }
}

/**
 * 播放TTS语音（自动选择普通或流式）
 *
 * @param text 要播放的文本
 * @param personalityId 人格ID
 * @param onEnd 播放结束回调
 * @param onProgress 进度回调（可选，仅流式TTS时调用）
 * @returns Audio对象，可用于控制播放
 */
export async function playTTS(
  text: string,
  personalityId?: string,
  onEnd?: () => void,
  onProgress?: (progress: number) => void
): Promise<HTMLAudioElement | null> {
  const textToSpeak = extractPlainText(text);

  if (!textToSpeak) {
    return null;
  }

  // 根据文本长度选择TTS方式
  const useStream = textToSpeak.length > TTS_CONFIG.STREAM_THRESHOLD;

  if (useStream) {
    // 长文本：使用分段TTS（边转边播放）
    console.log(`使用分段TTS（文本长度: ${textToSpeak.length}字符）`);
    return playTTSSegmented(textToSpeak, personalityId, onEnd, onProgress);
  } else {
    // 短文本：使用普通TTS
    try {
      // 构建TTS请求
      const request: SpeechRequest = {
        input: textToSpeak,
        model: 'tts-1',
        voice: 'alloy',
        speed: 1.0,
        personality_id: personalityId,
      };

      // 调用TTS API
      const audioBlob = await voiceApi.synthesize(request);

      // 创建音频对象
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      // 监听播放结束
      audio.addEventListener('ended', () => {
        URL.revokeObjectURL(audioUrl);
        if (onEnd) {
          onEnd();
        }
      });

      // 监听播放错误
      audio.addEventListener('error', (e) => {
        console.error('音频播放错误:', e);
        URL.revokeObjectURL(audioUrl);
        showError(new Error('音频播放失败'), '播放失败');
      });

      // 开始播放
      try {
        await audio.play();
        return audio;
      } catch (playError: any) {
        if (playError.name === 'NotAllowedError') {
          console.warn('音频自动播放被浏览器阻止，需要用户交互后才能播放');
          URL.revokeObjectURL(audioUrl);
          return null;
        }
        throw playError;
      }
    } catch (error: any) {
      console.error('TTS播放失败:', error);
      if (error.name !== 'NotAllowedError') {
        showError(error, '语音合成失败');
      }
      return null;
    }
  }
}

