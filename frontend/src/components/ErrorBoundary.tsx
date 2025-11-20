/**
 * 错误边界组件
 * 
 * 捕获React组件树中的错误并显示友好的错误界面
 * 集成Sentry进行错误追踪
 */

import React, { Component, ReactNode } from 'react';
import { Button, Result } from 'antd';
import * as Sentry from '@sentry/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  eventId: string | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      eventId: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      eventId: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // 上报到Sentry
    Sentry.withScope((scope) => {
      scope.setContext('react_error_info', {
        componentStack: errorInfo.componentStack,
      });
      
      const eventId = Sentry.captureException(error);
      this.setState({ eventId });
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      eventId: null,
    });
    window.location.reload();
  };

  handleFeedback = () => {
    if (this.state.eventId) {
      Sentry.showReportDialog({
        eventId: this.state.eventId,
        lang: 'zh-CN',
        title: '遇到了问题？',
        subtitle: '我们的团队已收到通知，感谢您的反馈！',
        subtitle2: '如果您愿意，可以告诉我们发生了什么。',
        labelName: '名称',
        labelEmail: '邮箱',
        labelComments: '详细描述',
        labelClose: '关闭',
        labelSubmit: '提交',
        errorGeneric: '提交反馈时出现错误，请稍后重试。',
        errorFormEntry: '某些字段无效，请更正后重试。',
        successMessage: '感谢您的反馈！',
      });
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="抱歉，出现了一些问题"
          subTitle={this.state.error?.message || '未知错误'}
          extra={[
            <Button type="primary" onClick={this.handleReset} key="reload">
              刷新页面
            </Button>,
            this.state.eventId && (
              <Button onClick={this.handleFeedback} key="feedback">
                反馈问题
              </Button>
            ),
          ]}
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

