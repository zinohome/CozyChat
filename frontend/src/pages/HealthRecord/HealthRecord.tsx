import React, { useState } from 'react';
import { Card, Row, Col, Button, Space, Progress, Tag } from 'antd';
import {
  HeartOutlined,
  FileTextOutlined,
  CalendarOutlined,
  AppleOutlined,
  ThunderboltOutlined,
  MedicineBoxOutlined,
  FolderOpenOutlined,
  EditOutlined,
  PlusOutlined,
  ArrowLeftOutlined,
  ClockCircleOutlined,
  PlayCircleFilled,
  VideoCameraOutlined,
  SoundOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import styles from './HealthRecord.module.css';

/**
 * 健康档案页面 (Health Record)
 * 
 * 修改说明：
 * 1. 响应用户需求，将原有的 8 个标签简化集成至 3 个核心页面
 * 2. 视觉风格参考「我在」App 焕新设计，采用轻量化、卡片式布局
 * 3. 强化手机端体验，集成图表化概览
 */
export const HealthRecord: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // 获取用户资料
  const { data: profile } = useQuery({
    queryKey: ['user', 'profile', user?.id],
    queryFn: () => userApi.getCurrentUserProfile(),
    enabled: !!user?.id,
  });

  const handleBack = () => {
    navigate('/chat');
  };

  // 渲染更专业的折线图 (带网格线、数据点、发光效果和坐标系)
  const renderProfessionalChart = () => (
    <div className={styles.chartContainer} style={{ height: '150px', marginTop: '20px', marginLeft: '0px' }}>
      <svg className={styles.mockChartLine} viewBox="-10 0 115 55" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="proGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#4caf50', stopOpacity: 0.4 }} />
            <stop offset="100%" style={{ stopColor: '#4caf50', stopOpacity: 0.0 }} />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="0.8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* 背景网格虚线 */}
        <line x1="0" y1="10" x2="100" y2="10" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />
        <line x1="0" y1="25" x2="100" y2="25" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />
        <line x1="0" y1="40" x2="100" y2="40" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />

        {/* 坐标轴文字 (Y轴) */}
        <text x="-3" y="11" fontSize="4.5" fill="#999" textAnchor="end">100</text>
        <text x="-3" y="26" fontSize="4.5" fill="#999" textAnchor="end">80</text>
        <text x="-3" y="41" fontSize="4.5" fill="#999" textAnchor="end">60</text>

        {/* 渐变填充区域 */}
        <path
          d="M0,35 C15,35 15,18 30,18 C45,18 45,28 60,28 C75,28 75,12 90,12 C95,12 100,16 100,16 L100,50 L0,50 Z"
          fill="url(#proGrad)"
        />

        {/* 核心折线 */}
        <path
          d="M0,35 C15,35 15,18 30,18 C45,18 45,28 60,28 C75,28 75,12 90,12 C95,12 100,16 100,16"
          fill="none"
          stroke="#4caf50"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#glow)"
        />

        {/* 数据散点 */}
        <circle cx="0" cy="35" r="1.5" fill="#fff" stroke="#4caf50" strokeWidth="1" />
        <circle cx="30" cy="18" r="1.5" fill="#fff" stroke="#4caf50" strokeWidth="1" />
        <circle cx="60" cy="28" r="1.5" fill="#fff" stroke="#4caf50" strokeWidth="1" />
        <circle cx="90" cy="12" r="1.5" fill="#fff" stroke="#4caf50" strokeWidth="1" />
        <circle cx="100" cy="16" r="1.5" fill="#fff" stroke="#4caf50" strokeWidth="1" />

        {/* X轴文字 */}
        <text x="0" y="52" fontSize="4.5" fill="#999" textAnchor="middle">周一</text>
        <text x="30" y="52" fontSize="4.5" fill="#999" textAnchor="middle">周三</text>
        <text x="60" y="52" fontSize="4.5" fill="#999" textAnchor="middle">周五</text>
        <text x="90" y="52" fontSize="4.5" fill="#999" textAnchor="middle">周日</text>
      </svg>
    </div>
  );

  // ================= 页面主体 =================
  return (
    <MainLayout>
      <div className={styles.container}>
        <div className={styles.header}>
          <Space>
            <ArrowLeftOutlined onClick={handleBack} className={styles.backButton} />
            <span className={styles.title}>身体节律</span>
          </Space>
        </div>

        <div className={styles.greetingHeader}>
          <div className={styles.greetingText}>
            您好，{profile?.display_name || user?.username || '杜亦南'}!
          </div>
          <div className={styles.subGreetingText}>倾听身体，回归自然稳态。</div>
        </div>

        <div className={styles.content}>
          {/* 1. 当前状态 (趋势图) */}
          <div className={styles.healthMetricCard} style={{ padding: '20px', paddingBottom: '10px' }}>
            <div className={styles.metricHeader}>
              <div className={styles.metricTitle}>
                <HeartOutlined style={{ color: '#4caf50' }} />
                当前状态
              </div>
              <span className={styles.metricStatus}>分数 85 (良好)</span>
            </div>
            <div className={styles.metricSubValue}>基于近期睡眠、运动与静息心率评估</div>
            {renderProfessionalChart()}
          </div>

          {/* 2. 今日建议 (营养与运动) */}
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTitle}>今日建议</div>
          </div>
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={12}>
              <div className={styles.adviceCard}>
                <div className={styles.adviceIcon} style={{ background: '#fff3e0', color: '#ff9800' }}>
                  <AppleOutlined />
                </div>
                <div className={styles.adviceTitle}>营养建议</div>
                <div className={styles.adviceContent}>今日代谢平稳，建议多摄入高纤维抗氧化蔬菜。</div>
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.adviceCard}>
                <div className={styles.adviceIcon} style={{ background: '#e3f2fd', color: '#2196f3' }}>
                  <ThunderboltOutlined />
                </div>
                <div className={styles.adviceTitle}>运动建议</div>
                <div className={styles.adviceContent}>昨晚睡眠充足，适合进行心率 130 左右的有氧训练。</div>
              </div>
            </Col>
          </Row>

          {/* 3. 健身教练 (数据与教程) */}
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTitle}>健康教练</div>
          </div>

          {/* 跑步数据卡片 */}
          <div className={styles.subCard} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '13px', color: '#666' }}>今日步数</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#333' }}>8,240 <span style={{ fontSize: '12px', fontWeight: 400, color: '#999' }}>/ 10,000步</span></div>
            </div>
            <Progress type="circle" percent={82} size={50} strokeColor="#4caf50" strokeWidth={10} />
          </div>

          {/* 瑜伽/普拉提 视频卡片 */}
          <div className={styles.mediaCard} style={{ backgroundImage: 'linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.6) 100%), url(/images/yoga-cover.jpg)' }}>
            <div className={styles.mediaInfo}>
              <Tag color="magenta" style={{ border: 'none', marginBottom: '8px' }}>瑜伽跟练</Tag>
              <div className={styles.mediaTitle}>肩颈舒缓流瑜伽 (15分钟)</div>
            </div>
            <div className={styles.mediaAction}>
              <PlayCircleFilled style={{ fontSize: '40px', color: '#fff', opacity: 0.9 }} />
            </div>
          </div>

          {/* 太极/五禽戏 视频卡片 */}
          <div className={styles.mediaCard} style={{ backgroundImage: `linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.6) 100%), url('/images/taichi-cover.jpg')` }}>
            <div className={styles.mediaInfo}>
              <Tag color="cyan" style={{ border: 'none', marginBottom: '8px' }}>太极养生</Tag>
              <div className={styles.mediaTitle}>八式太极拳</div>
            </div>
            <div className={styles.mediaAction}>
              <PlayCircleFilled style={{ fontSize: '40px', color: '#fff', opacity: 0.9 }} />
            </div>
          </div>

        </div>
      </div>
    </MainLayout>
  );
};

export default HealthRecord;

