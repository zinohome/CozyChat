import { useState, useCallback, useRef } from 'react';

/**
 * 文件上传Hook返回值
 */
export interface UseFileUploadReturn {
  /** 是否正在上传 */
  isUploading: boolean;
  /** 上传进度（0-100） */
  progress: number;
  /** 上传的文件 */
  files: File[];
  /** 错误信息 */
  error: string | null;
  /** 选择文件 */
  selectFiles: (accept?: string, multiple?: boolean) => Promise<File[]>;
  /** 拖拽上传 */
  handleDrop: (event: React.DragEvent) => void;
  /** 拖拽悬停 */
  handleDragOver: (event: React.DragEvent) => void;
  /** 清除文件 */
  clearFiles: () => void;
  /** 上传文件 */
  upload: (url: string, onProgress?: (progress: number) => void) => Promise<any>;
}

/**
 * 文件上传Hook
 *
 * 提供文件选择和上传功能，支持拖拽上传、进度显示等。
 */
export const useFileUpload = (): UseFileUploadReturn => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement | null>(null);

  /**
   * 选择文件
   */
  const selectFiles = useCallback(
    (accept?: string, multiple = false): Promise<File[]> => {
      return new Promise((resolve, reject) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = accept || '*/*';
        input.multiple = multiple;

        input.onchange = (event) => {
          const selectedFiles = Array.from((event.target as HTMLInputElement).files || []);
          if (selectedFiles.length > 0) {
            setFiles(selectedFiles);
            resolve(selectedFiles);
          } else {
            reject(new Error('未选择文件'));
          }
        };

        input.oncancel = () => {
          reject(new Error('取消选择文件'));
        };

        input.click();
      });
    },
    []
  );

  /**
   * 处理拖拽放置
   */
  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();

    const droppedFiles = Array.from(event.dataTransfer.files);
    if (droppedFiles.length > 0) {
      setFiles(droppedFiles);
      setError(null);
    }
  }, []);

  /**
   * 处理拖拽悬停
   */
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  /**
   * 清除文件
   */
  const clearFiles = useCallback(() => {
    setFiles([]);
    setError(null);
    setProgress(0);
  }, []);

  /**
   * 上传文件
   */
  const upload = useCallback(
    async (url: string, onProgress?: (progress: number) => void): Promise<any> => {
      if (files.length === 0) {
        throw new Error('没有文件可上传');
      }

      setIsUploading(true);
      setProgress(0);
      setError(null);

      try {
        const formData = new FormData();
        files.forEach((file) => {
          formData.append('files', file);
        });

        const token = localStorage.getItem('access_token');
        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              const percentComplete = (event.loaded / event.total) * 100;
              setProgress(percentComplete);
              onProgress?.(percentComplete);
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const response = JSON.parse(xhr.responseText);
                setIsUploading(false);
                setProgress(100);
                resolve(response);
              } catch {
                setIsUploading(false);
                setProgress(100);
                resolve(xhr.responseText);
              }
            } else {
              const error = JSON.parse(xhr.responseText).detail || '上传失败';
              setError(error);
              setIsUploading(false);
              reject(new Error(error));
            }
          });

          xhr.addEventListener('error', () => {
            setError('上传失败');
            setIsUploading(false);
            reject(new Error('上传失败'));
          });

          xhr.addEventListener('abort', () => {
            setError('上传已取消');
            setIsUploading(false);
            reject(new Error('上传已取消'));
          });

          xhr.open('POST', url);
          if (token) {
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          }
          xhr.send(formData);
        });
      } catch (err: any) {
        setError(err.message || '上传失败');
        setIsUploading(false);
        throw err;
      }
    },
    [files]
  );

  return {
    isUploading,
    progress,
    files,
    error,
    selectFiles,
    handleDrop,
    handleDragOver,
    clearFiles,
    upload,
  };
};

