import React, { useState } from 'react';
import { Card, Tabs, Row, Col, Space, Divider, Tag, Timeline } from 'antd';
import {
    HeartOutlined,
    FileTextOutlined,
    SmileOutlined,
    MehOutlined,
    FrownOutlined,
    ArrowLeftOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import styles from './StressProfile.module.css';

/**
 * 压力档案页面 (Stress Profile)
 */
export const StressProfile: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState('stress_stats');

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
                            <span className={styles.userDetail}>的疗愈空间</span>
                        </Space>
                        <div className={styles.userIdCard}>
                            <span className={styles.idLabel}>情绪标签：</span>
                            <Tag color="orange" style={{ marginLeft: 8 }}>重度疲劳</Tag>
                            <Tag color="purple">连轴转</Tag>
                        </div>
                    </Space>
                </Col>
            </Row>
        </Card>
    );

    // 压力评估Tab
    const renderStressStatsTab = () => (
        <div className={styles.tabContent}>
            {/* 今日压力状态 */}
            <Card size="small" className={styles.sectionCard}>
                <div className={styles.sectionTitle} style={{ marginBottom: '12px' }}>今日状态速览</div>
                <Divider style={{ margin: '8px 0' }} />
                <div className={styles.statsContainer}>
                    <div className={styles.statItem}>
                        <div className={styles.statLabel}>当前压力指数</div>
                        <div className={styles.statValue} style={{ color: '#ff4d4f' }}>85/100</div>
                    </div>
                    <div className={styles.statItem}>
                        <div className={styles.statLabel}>连续失眠天数</div>
                        <div className={styles.statValue} style={{ color: '#faad14' }}>3 天</div>
                    </div>
                    <div className={styles.statItem}>
                        <div className={styles.statLabel}>静心时长</div>
                        <div className={styles.statValue} style={{ color: '#52c41a' }}>0 分钟</div>
                    </div>
                </div>
            </Card>

            <Card size="small" className={styles.sectionCard} style={{ background: 'linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%)' }}>
                <Row align="middle">
                    <Col flex="auto">
                        <span className={styles.sectionTitle} style={{ color: '#1890ff' }}>🤖 AI 减压建议</span>
                    </Col>
                </Row>
                <Divider style={{ margin: '12px 0', borderColor: '#bae7ff' }} />
                <div className={styles.description} style={{ color: '#0050b3', fontWeight: 500 }}>
                    你已经连续高强度工作了 14 小时，身体和大脑都处在透支边缘。<br /><br />
                    请允许自己停下来休息一下。今天建议点击下方『开启禅定』，听 5 分钟的《晚风海浪》，让思绪飘散。不用回消息，不用想工作，这 5 分钟只属于你自己。
                </div>
            </Card>
        </div>
    );

    // 情绪日记Tab
    const renderMoodDiaryTab = () => (
        <div className={styles.tabContent}>
            <Card size="small" className={styles.sectionCard}>
                <Row align="middle">
                    <Col flex="auto">
                        <span className={styles.sectionTitle}>最近的情绪轨迹</span>
                    </Col>
                </Row>
                <Divider style={{ margin: '12px 0' }} />
                <div className={styles.timelineContainer}>
                    <Timeline
                        className={styles.customTimeline}
                        items={[
                            {
                                color: 'red',
                                children: (
                                    <div className={styles.timelineItem}>
                                        <span className={styles.timelineLabel}>今天 19:30</span>
                                        <span className={styles.timelineContent}>感觉天都要塌了，所有的DDL都堆在了一起。<FrownOutlined style={{ color: 'red', marginLeft: 4 }} /></span>
                                    </div>
                                ),
                            },
                            {
                                color: 'orange',
                                children: (
                                    <div className={styles.timelineItem}>
                                        <span className={styles.timelineLabel}>昨天 03:00</span>
                                        <span className={styles.timelineContent}>又失眠了，心跳得很快，脑子里一直在复盘白天开会的细节。<MehOutlined style={{ color: 'orange', marginLeft: 4 }} /></span>
                                    </div>
                                ),
                            },
                            {
                                color: 'green',
                                children: (
                                    <div className={styles.timelineItem}>
                                        <span className={styles.timelineLabel}>前天 14:00</span>
                                        <span className={styles.timelineContent}>难得喝到一杯好喝的燕麦拿铁，阳光很好，稍微喘了口气。<SmileOutlined style={{ color: 'green', marginLeft: 4 }} /></span>
                                    </div>
                                ),
                            },
                        ]}
                    />
                </div>
            </Card>
        </div>
    );

    const tabItems = [
        {
            key: 'stress_stats',
            label: (
                <span>
                    <HeartOutlined />
                    状态评估
                </span>
            ),
            children: renderStressStatsTab(),
        },
        {
            key: 'mood_diary',
            label: (
                <span>
                    <FileTextOutlined />
                    情绪日记
                </span>
            ),
            children: renderMoodDiaryTab(),
        }
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
                            <span className={styles.title}>压力档案</span>
                        </Space>
                    </div>

                    <div className={styles.content}>
                        {renderUserHeader()}
                        <Card className={styles.tabsCard} bodyStyle={{ padding: '0 12px 12px 12px' }}>
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
        console.error('StressProfile render error:', error);
        return (
            <MainLayout>
                <div style={{ padding: '24px' }}>
                    <div>页面加载出错，请刷新重试</div>
                </div>
            </MainLayout>
        );
    }
};

export default StressProfile;
