import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { Button, Space, Tooltip, message } from 'antd';
import { CopyOutlined, DeleteOutlined, CheckOutlined, UserOutlined, SoundOutlined, PauseOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { showSuccess, showError } from '@/utils/errorHandler';
import { voiceApi } from '@/services/voice';
import type { SpeechRequest } from '@/types/voice';

/**
 * 消息气泡组件属性
 */
interface MessageBubbleProps {
  /** 消息ID */
  id: string;
  /** 消息角色 */
  role: 'user' | 'assistant';
  /** 消息内容 */
  content: string;
  /** 时间戳 */
  timestamp: Date | string | number;
  /** 是否显示操作按钮 */
  showActions?: boolean;
  /** 删除回调 */
  onDelete?: (id: string) => void;
  /** 人格ID（用于TTS） */
  personalityId?: string;
}

/**
 * 消息气泡组件
 *
 * 支持Markdown渲染、代码高亮和消息操作。
 */
export const MessageBubble: React.FC<MessageBubbleProps> = ({
  id,
  role,
  content,
  timestamp,
  showActions = true,
  onDelete,
  personalityId,
}) => {
  const [copied, setCopied] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const isMobile = useIsMobile();
  const copyTimerRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 清理定时器和音频
  useEffect(() => {
    return () => {
      if (copyTimerRef.current) {
        clearTimeout(copyTimerRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  /**
   * 复制消息内容（支持降级方案）
   */
  const handleCopy = async () => {
    try {
      // 确保 content 是字符串
      const textToCopy = typeof content === 'string' ? content : String(content || '');
      
      if (!textToCopy.trim()) {
        message.warning('消息内容为空，无法复制');
        return;
      }
      
      // 优先使用现代 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(textToCopy);
        } catch (clipboardError) {
          // Clipboard API 失败，尝试降级方案
          throw new Error('Clipboard API failed, trying fallback');
        }
      } else {
        // 降级方案：使用传统的 execCommand 方法
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        textArea.setAttribute('readonly', '');
        document.body.appendChild(textArea);
        
        // 对于 iOS Safari，需要特殊处理
        if (navigator.userAgent.match(/ipad|iphone/i)) {
          const range = document.createRange();
          range.selectNodeContents(textArea);
          const selection = window.getSelection();
          if (selection) {
            selection.removeAllRanges();
            selection.addRange(range);
          }
          textArea.setSelectionRange(0, 999999);
        } else {
          textArea.select();
        }
        
        try {
          const successful = document.execCommand('copy');
          if (!successful) {
            throw new Error('execCommand copy failed');
          }
        } finally {
          document.body.removeChild(textArea);
        }
      }
      
      setCopied(true);
      showSuccess('已复制到剪贴板');
      if (copyTimerRef.current) {
        clearTimeout(copyTimerRef.current);
      }
      copyTimerRef.current = window.setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('复制失败:', error);
      // 提供更详细的错误信息
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      message.error(`复制失败: ${errorMessage}，请手动选择文本复制`);
    }
  };

  /**
   * 删除消息
   */
  const handleDelete = () => {
    if (onDelete) {
      onDelete(id);
    }
  };

  /**
   * 播放TTS语音
   */
  const handlePlayTTS = async () => {
    // 如果正在播放，则暂停
    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    // 如果已有音频对象，直接播放
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
      return;
    }

    // 提取纯文本内容（去除Markdown标记）
    const textToSpeak = content
      .replace(/```[\s\S]*?```/g, '') // 移除代码块
      .replace(/`[^`]+`/g, '') // 移除行内代码
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // 移除链接，保留文本
      .replace(/#{1,6}\s+/g, '') // 移除标题标记
      .replace(/\*\*([^*]+)\*\*/g, '$1') // 移除粗体标记
      .replace(/\*([^*]+)\*/g, '$1') // 移除斜体标记
      .replace(/^\s*[-*+]\s+/gm, '') // 移除列表标记
      .replace(/^\s*\d+\.\s+/gm, '') // 移除有序列表标记
      .trim();

    if (!textToSpeak) {
      message.warning('消息内容为空，无法播放');
      return;
    }

    try {
      setIsLoadingAudio(true);

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
      audioRef.current = audio;

      // 监听播放结束
      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
      });

      // 监听播放错误
      audio.addEventListener('error', (e) => {
        console.error('音频播放错误:', e);
        setIsPlaying(false);
        setIsLoadingAudio(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        showError(new Error('音频播放失败'), '播放失败');
      });

      // 开始播放
      await audio.play();
      setIsPlaying(true);
      setIsLoadingAudio(false);
    } catch (error) {
      console.error('TTS播放失败:', error);
      setIsLoadingAudio(false);
      showError(error, '语音合成失败');
    }
  };

  /**
   * 格式化时间
   */
  const formatTime = (ts: Date | string | number): string => {
    try {
      const date = typeof ts === 'string' 
        ? new Date(ts) 
        : typeof ts === 'number' 
          ? new Date(ts) 
          : ts;
      return format(date, 'HH:mm');
    } catch {
      return '';
    }
  };

  const isUser = role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        width: '100%',
        maxWidth: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* 角色标识 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '6px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          paddingLeft: isUser ? '0' : '4px',
          paddingRight: isUser ? '4px' : '0',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          width: isMobile ? '85%' : '75%',
        }}
      >
        {isUser ? (
          <>
            <UserOutlined style={{ fontSize: '14px' }} />
            <span>我</span>
          </>
        ) : (
          <>
            <img
              src="/assistant-icon.ico"
              alt="助手"
              style={{
                width: '24px',
                height: '24px',
                objectFit: 'contain',
                backgroundColor: 'transparent',
                background: 'transparent',
                mixBlendMode: 'multiply',
              }}
            />
            <span>助手</span>
          </>
        )}
      </div>

      <div
        style={{
          maxWidth: isMobile ? '85%' : '75%',
          width: 'fit-content',
          padding: isMobile ? '10px 12px' : '12px 16px',
          borderRadius: '12px',
          backgroundColor: isUser ? 'var(--message-user-bg)' : 'var(--message-assistant-bg)',
          color: isUser ? 'var(--message-user-text)' : 'var(--message-assistant-text)',
          position: 'relative',
          boxShadow: 'var(--shadow-sm)',
          transition: 'background-color 0.3s ease, color 0.3s ease',
          boxSizing: 'border-box',
          minWidth: 0, // 允许缩小
        }}
      >
        {/* Markdown内容 */}
        <div
            style={{
              fontSize: '14px',
              lineHeight: '1.6',
              wordBreak: 'break-word',
              overflowWrap: 'break-word',
              wordWrap: 'break-word',
              maxWidth: '100%',
              boxSizing: 'border-box',
            }}
          >
            <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                
                return !inline && language ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: '8px 0',
                      borderRadius: '6px',
                      fontSize: '13px',
                    }}
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code
                    className={className}
                    style={{
                      backgroundColor: isUser 
                        ? 'rgba(255,255,255,0.2)' 
                        : 'var(--bg-secondary)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      color: isUser ? 'inherit' : 'var(--text-primary)',
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
              // 优化链接样式
              a({ node, ...props }: any) {
                return (
                  <a
                    {...props}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: isUser ? 'var(--message-user-text)' : 'var(--primary-color)',
                      textDecoration: 'underline',
                    }}
                  />
                );
              },
              // 优化列表样式
              ul({ node, ...props }: any) {
                return (
                  <ul
                    {...props}
                    style={{
                      margin: '8px 0',
                      paddingLeft: '20px',
                    }}
                  />
                );
              },
              ol({ node, ...props }: any) {
                return (
                  <ol
                    {...props}
                    style={{
                      margin: '8px 0',
                      paddingLeft: '20px',
                    }}
                  />
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* 时间戳和操作按钮 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '8px',
            fontSize: '12px',
            opacity: 0.7,
          }}
        >
          <span>{formatTime(timestamp)}</span>
          {showActions && (
            <Space size="small" style={{ marginLeft: '8px' }}>
              {/* 只在助手消息显示播放按钮 */}
              {!isUser && personalityId && (
                <Tooltip title={isPlaying ? '暂停' : isLoadingAudio ? '加载中...' : '播放语音'}>
                  <Button
                    type="text"
                    size="small"
                    icon={isPlaying ? <PauseOutlined /> : <SoundOutlined />}
                    onClick={handlePlayTTS}
                    loading={isLoadingAudio}
                    disabled={isLoadingAudio}
                    style={{
                      color: 'var(--text-secondary)',
                      padding: '0 4px',
                      minWidth: 'auto',
                      height: 'auto',
                    }}
                  />
                </Tooltip>
              )}
              <Tooltip title={copied ? '已复制' : '复制'}>
                <Button
                  type="text"
                  size="small"
                  icon={copied ? <CheckOutlined /> : <CopyOutlined />}
                  onClick={handleCopy}
                  style={{
                    color: isUser ? 'rgba(255,255,255,0.8)' : 'var(--text-secondary)',
                    padding: '0 4px',
                    minWidth: 'auto',
                    height: 'auto',
                  }}
                />
              </Tooltip>
              {onDelete && (
                <Tooltip title="删除">
                  <Button
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={handleDelete}
                    danger
                    style={{
                      color: isUser ? 'rgba(255,255,255,0.8)' : 'var(--error-color)',
                      padding: '0 4px',
                      minWidth: 'auto',
                      height: 'auto',
                    }}
                  />
                </Tooltip>
              )}
            </Space>
          )}
        </div>
      </div>
    </div>
  );
};

