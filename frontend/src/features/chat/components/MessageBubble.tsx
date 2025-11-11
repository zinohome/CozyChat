import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { Button, Space, Tooltip, message, Input } from 'antd';
import { CopyOutlined, DeleteOutlined, CheckOutlined, EditOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { showSuccess } from '@/utils/errorHandler';

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
  /** 编辑回调 */
  onEdit?: (id: string, newContent: string) => void;
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
  onEdit,
}) => {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content);
  const isMobile = useIsMobile();
  const copyTimerRef = useRef<number | null>(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (copyTimerRef.current) {
        clearTimeout(copyTimerRef.current);
      }
    };
  }, []);

  /**
   * 复制消息内容
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      showSuccess('已复制到剪贴板');
      if (copyTimerRef.current) {
        clearTimeout(copyTimerRef.current);
      }
      copyTimerRef.current = window.setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      message.error('复制失败');
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
   * 开始编辑
   */
  const handleStartEdit = () => {
    setIsEditing(true);
    setEditContent(content);
  };

  /**
   * 保存编辑
   */
  const handleSaveEdit = () => {
    if (onEdit && editContent.trim() && editContent !== content) {
      onEdit(id, editContent.trim());
    }
    setIsEditing(false);
  };

  /**
   * 取消编辑
   */
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(content);
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
      }}
    >
      <div
        style={{
          maxWidth: isMobile ? '85%' : '75%',
          padding: isMobile ? '10px 12px' : '12px 16px',
          borderRadius: '12px',
          backgroundColor: isUser ? '#1890ff' : '#f0f0f0',
          color: isUser ? '#fff' : '#000',
          position: 'relative',
        }}
      >
        {/* 编辑模式 */}
        {isEditing ? (
          <div>
            <Input.TextArea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              autoSize={{ minRows: 2, maxRows: 10 }}
              style={{
                marginBottom: '8px',
                backgroundColor: isUser ? 'rgba(255,255,255,0.2)' : '#fff',
                color: isUser ? '#fff' : '#000',
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  handleSaveEdit();
                } else if (e.key === 'Escape') {
                  handleCancelEdit();
                }
              }}
            />
            <Space>
              <Button size="small" type="primary" onClick={handleSaveEdit}>
                保存
              </Button>
              <Button size="small" onClick={handleCancelEdit}>
                取消
              </Button>
            </Space>
          </div>
        ) : (
          /* Markdown内容 */
          <div
            style={{
              fontSize: '14px',
              lineHeight: '1.6',
              wordBreak: 'break-word',
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
                      backgroundColor: isUser ? 'rgba(255,255,255,0.2)' : '#e6f7ff',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '13px',
                      fontFamily: 'monospace',
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
                      color: isUser ? '#fff' : '#1890ff',
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
        )}

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
              <Tooltip title={copied ? '已复制' : '复制'}>
                <Button
                  type="text"
                  size="small"
                  icon={copied ? <CheckOutlined /> : <CopyOutlined />}
                  onClick={handleCopy}
                  style={{
                    color: isUser ? 'rgba(255,255,255,0.8)' : '#666',
                    padding: '0 4px',
                    minWidth: 'auto',
                    height: 'auto',
                  }}
                />
              </Tooltip>
              {onEdit && role === 'user' && (
                <Tooltip title="编辑">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={handleStartEdit}
                    style={{
                      color: isUser ? 'rgba(255,255,255,0.8)' : '#666',
                      padding: '0 4px',
                      minWidth: 'auto',
                      height: 'auto',
                    }}
                  />
                </Tooltip>
              )}
              {onDelete && (
                <Tooltip title="删除">
                  <Button
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={handleDelete}
                    danger
                    style={{
                      color: isUser ? 'rgba(255,255,255,0.8)' : '#ff4d4f',
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

