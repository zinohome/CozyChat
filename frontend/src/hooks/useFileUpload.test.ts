import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFileUpload } from './useFileUpload';

// Mock XMLHttpRequest
class MockXMLHttpRequest {
  open = vi.fn();
  send = vi.fn();
  setRequestHeader = vi.fn();
  upload = {
    addEventListener: vi.fn(),
  };
  addEventListener = vi.fn();
  status = 200;
  responseText = JSON.stringify({ success: true });
}

global.XMLHttpRequest = MockXMLHttpRequest as any;

// Mock document.createElement
const mockClick = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  global.document.createElement = vi.fn(() => ({
    click: mockClick,
    type: 'file',
    accept: '',
    multiple: false,
    files: null,
    onchange: null,
    oncancel: null,
  })) as any;
  global.document.body.appendChild = mockAppendChild;
  global.document.body.removeChild = mockRemoveChild;
});

describe('useFileUpload', () => {
  it('应该初始化为空状态', () => {
    const { result } = renderHook(() => useFileUpload());
    expect(result.current.isUploading).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(Array.isArray(result.current.files)).toBe(true);
    expect(result.current.files.length).toBe(0);
    expect(result.current.error).toBe(null);
  });

  it('应该选择文件', async () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
    } as FileList;

    // Mock文件选择
    const mockInput = {
      type: 'file',
      accept: '',
      multiple: false,
      files: fileList,
      click: vi.fn(),
      onchange: null as any,
      oncancel: null as any,
    };

    global.document.createElement = vi.fn(() => mockInput as any);

    await act(async () => {
      const promise = result.current.selectFiles();
      // 模拟用户选择文件
      if (mockInput.onchange) {
        mockInput.onchange({ target: mockInput } as any);
      }
      const files = await promise;
      expect(files).toHaveLength(1);
    });
  });

  it('应该处理拖拽上传', () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dataTransfer = {
      files: [file],
    } as DataTransfer;

    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer,
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(event);
    });

    expect(result.current.files).toHaveLength(1);
    expect(result.current.files[0].name).toBe('test.txt');
  });

  it('应该处理拖拽悬停', () => {
    const { result } = renderHook(() => useFileUpload());

    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDragOver(event);
    });

    expect(event.preventDefault).toHaveBeenCalled();
  });

  it('应该清除文件', () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dataTransfer = {
      files: [file],
    } as DataTransfer;

    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer,
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(event);
      result.current.clearFiles();
    });

    expect(result.current.files).toHaveLength(0);
  });

  it('应该上传文件', async () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dataTransfer = {
      files: [file],
    } as DataTransfer;

    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer,
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(event);
    });

    // Mock XMLHttpRequest
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: {
        addEventListener: vi.fn(),
      },
      addEventListener: vi.fn(),
      status: 200,
      responseText: JSON.stringify({ success: true }),
    };

    global.XMLHttpRequest = vi.fn(() => mockXHR as any) as any;

    await act(async () => {
      const uploadPromise = result.current.upload('/api/upload');

      // 模拟上传进度
      const progressHandler = mockXHR.upload.addEventListener.mock.calls.find(
        (call: any[]) => call[0] === 'progress'
      )?.[1];
      if (progressHandler) {
        progressHandler({
          lengthComputable: true,
          loaded: 50,
          total: 100,
        } as ProgressEvent);
      }

      // 模拟上传完成
      const loadHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any[]) => call[0] === 'load'
      )?.[1];
      if (loadHandler) {
        loadHandler();
      }

      await uploadPromise;
    });

    expect(result.current.isUploading).toBe(false);
  });

  it('应该处理上传错误', async () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dataTransfer = {
      files: [file],
    } as DataTransfer;

    const event = {
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
      dataTransfer,
    } as unknown as React.DragEvent;

    act(() => {
      result.current.handleDrop(event);
    });

    // Mock XMLHttpRequest with error
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: {
        addEventListener: vi.fn(),
      },
      addEventListener: vi.fn(),
      status: 500,
      responseText: JSON.stringify({ detail: 'Upload failed' }),
    };

    global.XMLHttpRequest = vi.fn(() => mockXHR as any) as any;

    await act(async () => {
      const uploadPromise = result.current.upload('/api/upload');

      // 模拟错误
      const errorHandler = mockXHR.addEventListener.mock.calls.find(
        (call: any[]) => call[0] === 'load'
      )?.[1];
      if (errorHandler) {
        errorHandler();
      }

      try {
        await uploadPromise;
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
      }
    });

    expect(result.current.error).toBeTruthy();
  });
});

