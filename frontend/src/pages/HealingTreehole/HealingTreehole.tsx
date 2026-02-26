import React, { useState } from 'react';
import { Card, Tabs, Row, Col, Button, Space, Tag, Empty, message, Avatar } from 'antd';
import {
    HeartOutlined,
    HeartFilled,
    ArrowLeftOutlined,
    MessageOutlined,
    UserOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import styles from './HealingTreehole.module.css';

interface TreeholePost {
    id: string;
    author: string;
    content: string;
    hugCount: number;
    time: string;
    isHugged?: boolean;
}

export const HealingTreehole: React.FC = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('my_hugs');

    // 模拟数据：温暖的帖子
    const [posts, setPosts] = useState<TreeholePost[]>([
        {
            id: '1',
            author: '匿名的小熊',
            content: '今天被主管当着全组人的面批评了，感觉自己好没用。一直躲在工位哭，连饭都不想吃...',
            hugCount: 128,
            time: '10分钟前',
            isHugged: false,
        },
        {
            id: '2',
            author: '午夜飞行',
            content: '谢谢这个减压助手陪我熬过了凌晨3点的失眠，听着海浪声，感觉心跳慢慢平复下来了。大家晚安。',
            hugCount: 356,
            time: '2小时前',
            isHugged: true,
        },
        {
            id: '3',
            author: '路过的风',
            content: '连续加了半个月的班，终于赶完项目了。虽然赚到了钱，但感觉身体已经被掏空。明天我要去公园躺一整天。',
            hugCount: 89,
            time: '5小时前',
            isHugged: false,
        },
        {
            id: '4',
            author: '不想长大',
            content: '为什么成年人的世界这么难？我只是想好好做个简单的人而已。',
            hugCount: 210,
            time: '昨天 23:40',
            isHugged: false,
        }
    ]);

    const handleBack = () => {
        navigate('/chat');
    };

    const handleHug = (postId: string) => {
        setPosts(posts.map(post => {
            if (post.id === postId) {
                if (!post.isHugged) {
                    message.success('送出一个温暖的抱抱 🌸');
                    return { ...post, hugCount: post.hugCount + 1, isHugged: true };
                } else {
                    return { ...post, hugCount: post.hugCount - 1, isHugged: false };
                }
            }
            return post;
        }));
    };

    const renderTreeholeList = () => (
        <div className={styles.tabContent}>
            {posts.length === 0 ? (
                <Empty
                    description="树洞里静悄悄的"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ) : (
                <div className={styles.circleList}>
                    {posts.map((post) => (
                        <Card
                            key={post.id}
                            className={styles.circleCard}
                            hoverable
                        >
                            <Row>
                                <Col flex="auto">
                                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                                        <Space align="center">
                                            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#bae7ff', color: '#1890ff' }} />
                                            <span className={styles.circleName}>{post.author}</span>
                                            <span style={{ color: '#bfbfbf', fontSize: 12 }}>{post.time}</span>
                                        </Space>
                                        <div className={styles.circleDescription} style={{ fontSize: 15, color: '#333' }}>
                                            {post.content}
                                        </div>
                                        <Space style={{ marginTop: 8 }}>
                                            <Button
                                                type="text"
                                                size="small"
                                                icon={post.isHugged ? <HeartFilled style={{ color: '#ff4d4f' }} /> : <HeartOutlined />}
                                                onClick={() => handleHug(post.id)}
                                                style={{ color: post.isHugged ? '#ff4d4f' : '#8c8c8c' }}
                                            >
                                                {post.isHugged ? '已抱抱' : '抱抱'} ({post.hugCount})
                                            </Button>
                                            <Button type="text" size="small" icon={<MessageOutlined />} style={{ color: '#8c8c8c' }}>
                                                回应
                                            </Button>
                                        </Space>
                                    </Space>
                                </Col>
                            </Row>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );

    const renderMyMoments = () => (
        <div className={styles.tabContent}>
            <Card
                className={styles.circleCard}
                style={{ textAlign: 'center', padding: '40px 0', borderStyle: 'dashed' }}
                onClick={() => message.info('功能开发中')}
            >
                <span style={{ color: '#bfbfbf' }}>写下你想倒在树洞里的情绪...</span>
            </Card>
        </div>
    );

    const tabItems = [
        {
            key: 'world',
            label: (
                <span>
                    <HeartOutlined />
                    大家的心声
                </span>
            ),
            children: renderTreeholeList(),
        },
        {
            key: 'my_moments',
            label: (
                <span>
                    <UserOutlined />
                    我的倾诉
                </span>
            ),
            children: renderMyMoments(),
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
                            <span className={styles.title}>疗愈树洞</span>
                        </Space>
                    </div>

                    <div className={styles.content}>
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
        console.error('HealingTreehole render error:', error);
        return (
            <MainLayout>
                <div style={{ padding: '24px' }}>
                    <div>页面加载出错，请刷新重试</div>
                </div>
            </MainLayout>
        );
    }
};

export default HealingTreehole;
