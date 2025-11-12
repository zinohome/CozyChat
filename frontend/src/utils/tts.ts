import { voiceApi } from '@/services/voice';
import { showError } from '@/utils/errorHandler';
import type { SpeechRequest } from '@/types/voice';

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
 * 播放TTS语音
 *
 * @param text 要播放的文本
 * @param personalityId 人格ID
 * @param onEnd 播放结束回调
 * @returns Audio对象，可用于控制播放
 */
export async function playTTS(
  text: string,
  personalityId?: string,
  onEnd?: () => void
): Promise<HTMLAudioElement | null> {
  const textToSpeak = extractPlainText(text);

  if (!textToSpeak) {
    return null;
  }

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
    await audio.play();
    return audio;
  } catch (error) {
    console.error('TTS播放失败:', error);
    showError(error, '语音合成失败');
    return null;
  }
}

