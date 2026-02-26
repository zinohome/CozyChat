import React, { useState } from 'react';
import { Card, Tabs, Row, Col, Button, Space, Divider, Tag, Timeline, Empty } from 'antd';
import {
  UserOutlined,
  HeartOutlined,
  FileTextOutlined,
  CalendarOutlined,
  AppleOutlined,
  ThunderboltOutlined,
  MedicineBoxOutlined,
  FolderOpenOutlined,
  EditOutlined,
  PlusOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileWordOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import styles from './HealthRecord.module.css';

/**
 * 健康档案页面
 * 
 * 参考 yyAsistant 设计，提供健康自测、健康史、健康报告等功能
 */
export const HealthRecord: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('health_history');

  // 获取用户资料（包含 display_name）
  const { data: profile } = useQuery({
    queryKey: ['user', 'profile', user?.id],
    queryFn: () => userApi.getCurrentUserProfile(),
    enabled: !!user?.id,
  });

  const handleBack = () => {
    navigate('/chat');
  };

  // 顶部用户信息区域
  const renderUserHeader = () => (
    <Card className={styles.userCard}>
      <Row gutter={24} align="middle" wrap={false}>
        <Col flex="none">
          <div className={styles.avatarContainer}>
            <img
              src="/images/health/man.png"
              alt="用户头像"
              className={styles.avatar}
            />
          </div>
        </Col>
        <Col flex="auto">
          <Space direction="vertical" size={8} className={styles.userInfo}>
            <Space size={12} wrap>
              <span className={styles.userName}>
                {profile?.display_name || user?.username || '用户'}
              </span>
              <span className={styles.userDetail}>男</span>
            </Space>
            <span className={styles.userAge}>65岁</span>
            <div className={styles.userIdCard}>
              <span className={styles.idLabel}>身份证：</span>
              <span className={styles.userDetail}>320***********1234</span>
            </div>
            <Button type="link" size="small" icon={<EditOutlined />} style={{ padding: 0 }}>
              编辑资料
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  // 健康自测Tab
  const renderHealthCheckTab = () => (
    <div className={styles.tabContent}>
      <div className={styles.recordList}>
        {[
          { title: '血压自测', value: '125/80 mmHg', status: '正常', color: 'green', time: '2024-03-20 08:30' },
          { title: '血糖自测', value: '5.8 mmol/L', status: '正常', color: 'green', time: '2024-03-20 07:00' },
          { title: '体重测量', value: '72.5 kg', status: '正常', color: 'blue', time: '2024-03-19 19:00' },
          { title: '体温测量', value: '36.5°C', status: '正常', color: 'green', time: '2024-03-19 18:00' },
          { title: '心率测量', value: '78 bpm', status: '正常', color: 'green', time: '2024-03-19 18:00' },
        ].map((item, index) => (
          <Card key={index} size="small" className={styles.recordCard}>
            <Row align="middle">
              <Col flex="auto">
                <Space direction="horizontal" style={{ width: '100%', alignItems: 'center' }} wrap>
                  <span className={styles.recordTitle}>{item.title}</span>
                  <Divider type="vertical" />
                  <span className={styles.recordValue}>{item.value}</span>
                  <Tag color={item.color}>{item.status}</Tag>
                  <span className={styles.recordTime}>{item.time}</span>
                </Space>
              </Col>
              <Col flex="none">
                <Button type="link" size="small">查看详情</Button>
              </Col>
            </Row>
          </Card>
        ))}
      </div>
      <Button
        type="primary"
        block
        size="large"
        icon={<PlusOutlined />}
        className={styles.addButton}
      >
        添加自测记录
      </Button>
    </div>
  );

  // 健康史Tab
  const renderHealthHistoryTab = () => (
    <div className={styles.tabContent}>
      {/* 家族史 */}
      <Card size="small" className={styles.sectionCard}>
        <Row align="middle">
          <Col flex="auto">
            <span className={styles.sectionTitle}>家族史</span>
          </Col>
          <Col flex="none">
            <Button type="link" size="small">编辑</Button>
          </Col>
        </Row>
        <Divider style={{ margin: '12px 0' }} />
        <Space style={{ marginBottom: '8px' }} wrap>
          <Tag color="red">高血压</Tag>
          <Tag color="orange">糖尿病</Tag>
          <Tag color="purple">心脏病</Tag>
        </Space>
        <div className={styles.description}>父亲患有高血压和糖尿病，母亲有心脏病病史</div>
      </Card>

      {/* 个人史 */}
      <Card size="small" className={styles.sectionCard}>
        <Row align="middle">
          <Col flex="auto">
            <span className={styles.sectionTitle}>个人史</span>
          </Col>
          <Col flex="none">
            <Button type="link" size="small">编辑</Button>
          </Col>
        </Row>
        <Divider style={{ margin: '12px 0' }} />
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <FileTextOutlined style={{ color: 'var(--primary-color)' }} />
            <span className={styles.infoLabel}>饮酒情况：</span>
            <span>偶尔饮酒，每周1-2次</span>
          </Space>
          <Space>
            <FileTextOutlined style={{ color: 'var(--primary-color)' }} />
            <span className={styles.infoLabel}>吸烟情况：</span>
            <span>已戒烟3年</span>
          </Space>
          <Space>
            <FileTextOutlined style={{ color: 'var(--primary-color)' }} />
            <span className={styles.infoLabel}>过敏史：</span>
            <span>青霉素过敏</span>
          </Space>
        </Space>
      </Card>

      {/* 既往病史 */}
      <Card size="small" className={styles.sectionCard}>
        <Row align="middle">
          <Col flex="auto">
            <span className={styles.sectionTitle}>既往病史</span>
          </Col>
          <Col flex="none">
            <Button type="link" size="small">编辑</Button>
          </Col>
        </Row>
        <Divider style={{ margin: '12px 0' }} />
        <div className={styles.timelineContainer}>
          <Timeline
            className={styles.customTimeline}
            items={[
              {
                children: (
                  <div className={styles.timelineItem}>
                    <span className={styles.timelineContent}>急性胃炎，已治愈</span>
                    <span className={styles.timelineLabel}>2023年6月</span>
                  </div>
                ),
              },
              {
                children: (
                  <div className={styles.timelineItem}>
                    <span className={styles.timelineContent}>阑尾炎手术</span>
                    <span className={styles.timelineLabel}>2022年3月</span>
                  </div>
                ),
              },
              {
                children: (
                  <div className={styles.timelineItem}>
                    <span className={styles.timelineContent}>感冒发烧</span>
                    <span className={styles.timelineLabel}>2021年1月</span>
                  </div>
                ),
              },
            ]}
          />
        </div>
      </Card>
    </div>
  );

  // 健康报告Tab
  const renderHealthReportTab = () => (
    <div className={styles.tabContent}>
      <Empty
        description="暂无健康报告"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" icon={<FileTextOutlined />}>
          生成健康报告
        </Button>
      </Empty>
    </div>
  );

  // 健康计划Tab
  const renderHealthPlanTab = () => (
    <div className={styles.tabContent}>
      <Empty
        description="暂无健康计划"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" icon={<CalendarOutlined />}>
          生成专属健康计划
        </Button>
      </Empty>
    </div>
  );

  // 饮食健康Tab
  const renderDietHealthTab = () => (
    <div className={styles.tabContent}>
      {/* 今日饮食统计 */}
      <Card size="small" className={styles.sectionCard}>
        <div className={styles.sectionTitle} style={{ marginBottom: '12px' }}>今日饮食</div>
        <Divider style={{ margin: '8px 0' }} />
        <div className={styles.statsContainer}>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>摄入卡路里</div>
            <div className={styles.statValue} style={{ color: 'var(--primary-color)' }}>1,856</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>目标卡路里</div>
            <div className={styles.statValue} style={{ color: '#52c41a' }}>2,000</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>剩余</div>
            <div className={styles.statValue} style={{ color: '#faad14' }}>144</div>
          </div>
        </div>
      </Card>

      <Button
        type="primary"
        block
        size="large"
        icon={<PlusOutlined />}
        className={styles.addButton}
      >
        添加饮食记录
      </Button>
    </div>
  );

  // 运动健康Tab
  const renderExerciseHealthTab = () => (
    <div className={styles.tabContent}>
      {/* 今日运动数据 */}
      <Card size="small" className={styles.sectionCard}>
        <div className={styles.sectionTitle} style={{ marginBottom: '12px' }}>今日运动</div>
        <Divider style={{ margin: '8px 0' }} />
        <div className={styles.statsContainer}>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>步数</div>
            <div className={styles.statValue} style={{ color: 'var(--primary-color)' }}>8,234</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>距离</div>
            <div className={styles.statValue} style={{ color: '#52c41a' }}>5.8 km</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>卡路里</div>
            <div className={styles.statValue} style={{ color: '#faad14' }}>456</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>运动时长</div>
            <div className={styles.statValue} style={{ color: '#722ed1' }}>45分钟</div>
          </div>
        </div>
      </Card>

      <Button
        type="primary"
        block
        size="large"
        icon={<PlusOutlined />}
        className={styles.addButton}
      >
        添加运动记录
      </Button>
    </div>
  );

  // 药物记录Tab
  const renderMedicationRecordTab = () => (
    <div className={styles.tabContent}>
      {/* 当前用药 */}
      <Card size="small" className={styles.sectionCard}>
        <div className={styles.sectionTitle} style={{ marginBottom: '12px' }}>当前用药</div>
        <Divider style={{ margin: '8px 0' }} />
        <div className={styles.medicationList}>
          {[
            { name: '阿司匹林肠溶片', dose: '100mg', freq: '每日1次，饭后服用', duration: '长期服用' },
            { name: '氨氯地平片', dose: '5mg', freq: '每日1次，早饭后服用', duration: '长期服用' },
          ].map((item, index) => (
            <div key={index} className={styles.medicationItem}>
              <Space direction="horizontal" style={{ width: '100%' }} wrap>
                <span className={styles.medicationName}>{item.name}</span>
                <Tag color="blue">进行中</Tag>
                <span className={styles.medicationDetail}>剂量：{item.dose}</span>
                <Divider type="vertical" />
                <span className={styles.medicationDetail}>{item.freq}</span>
                <Divider type="vertical" />
                <span className={styles.medicationDetail}>{item.duration}</span>
                <Space style={{ marginLeft: 'auto' }}>
                  <Button type="link" size="small">详情</Button>
                  <Button type="link" size="small" danger>暂停</Button>
                </Space>
              </Space>
            </div>
          ))}
        </div>
      </Card>

      <Button
        type="primary"
        block
        size="large"
        icon={<PlusOutlined />}
        className={styles.addButton}
      >
        添加用药记录
      </Button>
    </div>
  );

  // 就医资料夹Tab
  const renderMedicalFolderTab = () => (
    <div className={styles.tabContent}>
      <Space style={{ marginBottom: '16px', justifyContent: 'flex-end', width: '100%' }}>
        <Button type="primary" icon={<PlusOutlined />}>上传资料</Button>
        <Button icon={<FolderOpenOutlined />}>新建文件夹</Button>
      </Space>

      <div className={styles.fileList}>
        {[
          { name: '2024年体检报告.pdf', type: 'pdf', icon: <FilePdfOutlined />, tag: '体检报告', date: '2024-03-15', size: '2.3MB' },
          { name: 'X光片-胸部检查.jpg', type: 'image', icon: <FileImageOutlined />, tag: '影像资料', date: '2024-02-20', size: '5.6MB' },
          { name: '血常规检查报告.pdf', type: 'pdf', icon: <FilePdfOutlined />, tag: '检查报告', date: '2024-01-10', size: '856KB' },
          { name: '病历记录.docx', type: 'word', icon: <FileWordOutlined />, tag: '病历', date: '2023-12-05', size: '1.2MB' },
        ].map((item, index) => (
          <div key={index} className={styles.fileItem}>
            <Row align="middle">
              <Col flex="none">
                <div className={styles.fileIcon}>{item.icon}</div>
              </Col>
              <Col flex="auto">
                <Space direction="horizontal" style={{ width: '100%' }} wrap>
                  <span className={styles.fileName}>{item.name}</span>
                  <Tag color="blue">{item.tag}</Tag>
                  <span className={styles.fileDetail}>检查日期：{item.date} | 大小：{item.size}</span>
                  <Space style={{ marginLeft: 'auto' }}>
                    <Button type="link" size="small">查看</Button>
                    <Button type="link" size="small">下载</Button>
                    <Button type="link" size="small" danger>删除</Button>
                  </Space>
                </Space>
              </Col>
            </Row>
          </div>
        ))}
      </div>
    </div>
  );

  const tabItems = [
    {
      key: 'health_history',
      label: (
        <span>
          <FileTextOutlined />
          健康史
        </span>
      ),
      children: renderHealthHistoryTab(),
    },
    {
      key: 'health_check',
      label: (
        <span>
          <HeartOutlined />
          健康自测
        </span>
      ),
      children: renderHealthCheckTab(),
    },
    {
      key: 'health_report',
      label: (
        <span>
          <FileTextOutlined />
          健康报告
        </span>
      ),
      children: renderHealthReportTab(),
    },
    {
      key: 'health_plan',
      label: (
        <span>
          <CalendarOutlined />
          健康计划
        </span>
      ),
      children: renderHealthPlanTab(),
    },
    {
      key: 'diet_health',
      label: (
        <span>
          <AppleOutlined />
          饮食健康
        </span>
      ),
      children: renderDietHealthTab(),
    },
    {
      key: 'exercise_health',
      label: (
        <span>
          <ThunderboltOutlined />
          运动健康
        </span>
      ),
      children: renderExerciseHealthTab(),
    },
    {
      key: 'medication_record',
      label: (
        <span>
          <MedicineBoxOutlined />
          药物记录
        </span>
      ),
      children: renderMedicationRecordTab(),
    },
    {
      key: 'medical_folder',
      label: (
        <span>
          <FolderOpenOutlined />
          就医资料夹
        </span>
      ),
      children: renderMedicalFolderTab(),
    },
  ];

  try {
    return (
      <MainLayout>
        <div className={styles.container}>
          <div className={styles.header}>
            <Space>
              <ArrowLeftOutlined
                onClick={handleBack}
                className={styles.backButton}
              />
              <span className={styles.title}>健康档案</span>
            </Space>
          </div>

          <div className={styles.content}>
            {renderUserHeader()}
            <Card className={styles.tabsCard}>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={tabItems}
                tabPosition="top"
              />
            </Card>
          </div>
        </div>
      </MainLayout>
    );
  } catch (error) {
    console.error('HealthRecord render error:', error);
    return (
      <MainLayout>
        <div style={{ padding: '24px' }}>
          <div>页面加载出错，请刷新重试</div>
          <div style={{ marginTop: '16px', color: '#999' }}>
            {error instanceof Error ? error.message : String(error)}
          </div>
        </div>
      </MainLayout>
    );
  }
};

export default HealthRecord;

