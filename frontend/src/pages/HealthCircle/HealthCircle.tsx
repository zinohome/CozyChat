import React, { useState } from 'react';
import { Card, Tabs, Row, Col, Button, Space, Tag, Empty, message } from 'antd';
import {
  TeamOutlined,
  PlusOutlined,
  RightOutlined,
  ArrowLeftOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import styles from './HealthCircle.module.css';

/**
 * 健康圈数据接口
 */
interface HealthCircle {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  isJoined?: boolean;
}

/**
 * 健康圈页面
 * 
 * 提供我的健康圈和发现更多健康圈功能
 */
export const HealthCircle: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('my_circles');

  // 模拟数据：我的健康圈
  const myCircles: HealthCircle[] = [
    {
      id: '1',
      name: '血压健康圈',
      description: '专注于血压健康管理，分享血压监测技巧、饮食建议和生活方式调整经验',
      memberCount: 1250,
      isJoined: true,
    },
    {
      id: '2',
      name: '血糖健康圈',
      description: '血糖健康管理交流平台，分享血糖监测方法、饮食控制和运动建议',
      memberCount: 3200,
      isJoined: true,
    },
    {
      id: '3',
      name: '血脂健康圈',
      description: '关注血脂健康，分享降脂饮食、运动方案和药物治疗经验',
      memberCount: 2100,
      isJoined: true,
    },
    {
      id: '4',
      name: '睡眠健康圈',
      description: '改善睡眠质量，分享助眠技巧、睡眠健康知识和作息调整经验',
      memberCount: 1800,
      isJoined: true,
    },
    {
      id: '5',
      name: '骨质疏松健康圈',
      description: '关注骨骼健康，分享补钙方法、运动建议和预防骨质疏松的经验',
      memberCount: 1500,
      isJoined: true,
    },
  ];

  // 模拟数据：发现更多健康圈
  const discoverCircles: HealthCircle[] = [
    {
      id: '4',
      name: '心脏健康圈',
      description: '关注心脏健康，分享心血管疾病预防和康复经验',
      memberCount: 2100,
      isJoined: false,
    },
    {
      id: '5',
      name: '营养健康圈',
      description: '科学营养搭配，健康饮食指导，分享营养知识和食谱',
      memberCount: 4500,
      isJoined: false,
    },
    {
      id: '6',
      name: '睡眠健康圈',
      description: '改善睡眠质量，分享助眠技巧和睡眠健康知识',
      memberCount: 1800,
      isJoined: false,
    },
    {
      id: '7',
      name: '心理健康圈',
      description: '关注心理健康，提供情绪管理和心理支持',
      memberCount: 3200,
      isJoined: false,
    },
    {
      id: '8',
      name: '老年健康圈',
      description: '专为老年人打造的健康交流平台，分享养生经验和健康知识',
      memberCount: 5600,
      isJoined: false,
    },
  ];

  const handleBack = () => {
    navigate('/chat');
  };

  const handleEnterCircle = (circleId: string) => {
    // TODO: 实现进入健康圈功能
    message.info(`进入健康圈: ${circleId}`);
  };

  const handleJoinCircle = (circleId: string) => {
    // TODO: 实现加入健康圈功能
    message.success('加入成功！');
    // 这里应该更新状态，将健康圈从发现列表移到我的健康圈列表
  };

  // 我的健康圈Tab
  const renderMyCirclesTab = () => (
    <div className={styles.tabContent}>
      {myCircles.length === 0 ? (
        <Empty
          description="您还没有加入任何健康圈"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button
            type="primary"
            onClick={() => setActiveTab('discover')}
          >
            去发现更多
          </Button>
        </Empty>
      ) : (
        <div className={styles.circleList}>
          {myCircles.map((circle) => (
            <Card
              key={circle.id}
              className={styles.circleCard}
              hoverable
            >
              <Row align="middle" gutter={16}>
                <Col flex="auto">
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space>
                      <TeamOutlined
                        style={{ color: 'var(--primary-color)', fontSize: '20px' }}
                      />
                      <span className={styles.circleName}>{circle.name}</span>
                      <Tag color="blue">{circle.memberCount}人</Tag>
                    </Space>
                    <div className={styles.circleDescription}>
                      {circle.description}
                    </div>
                  </Space>
                </Col>
                <Col flex="none">
                  <Button
                    type="text"
                    icon={<RightOutlined />}
                    onClick={() => handleEnterCircle(circle.id)}
                    className={styles.enterButton}
                  >
                    进入
                  </Button>
                </Col>
              </Row>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  // 发现更多Tab
  const renderDiscoverTab = () => (
    <div className={styles.tabContent}>
      {discoverCircles.length === 0 ? (
        <Empty
          description="暂无更多健康圈"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <div className={styles.circleList}>
          {discoverCircles.map((circle) => (
            <Card
              key={circle.id}
              className={styles.circleCard}
              hoverable
            >
              <Row align="middle" gutter={16}>
                <Col flex="auto">
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space>
                      <TeamOutlined
                        style={{ color: 'var(--primary-color)', fontSize: '20px' }}
                      />
                      <span className={styles.circleName}>{circle.name}</span>
                      <Tag color="blue">{circle.memberCount}人</Tag>
                    </Space>
                    <div className={styles.circleDescription}>
                      {circle.description}
                    </div>
                  </Space>
                </Col>
                <Col flex="none">
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => handleJoinCircle(circle.id)}
                    className={styles.joinButton}
                  >
                    加入
                  </Button>
                </Col>
              </Row>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const tabItems = [
    {
      key: 'my_circles',
      label: (
        <span>
          <UserOutlined />
          我的健康圈
        </span>
      ),
      children: renderMyCirclesTab(),
    },
    {
      key: 'discover',
      label: (
        <span>
          <TeamOutlined />
          发现更多
        </span>
      ),
      children: renderDiscoverTab(),
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
              <span className={styles.title}>健康圈</span>
            </Space>
          </div>

          <div className={styles.content}>
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
    console.error('HealthCircle render error:', error);
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

export default HealthCircle;

