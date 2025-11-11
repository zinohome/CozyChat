import React from 'react';
import { Drawer, Tabs, Space } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { UserProfile } from './UserProfile';
import { HealthRecords } from './HealthRecords';

/**
 * 健康档案抽屉组件属性
 */
interface HealthRecordDrawerProps {
  /** 是否可见 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 健康档案抽屉组件
 *
 * 使用Ant Design的Drawer组件实现侧边栏。
 */
export const HealthRecordDrawer: React.FC<HealthRecordDrawerProps> = ({
  open,
  onClose,
}) => {
  const tabItems = [
    {
      key: 'basic',
      label: '基本信息',
      children: <UserProfile />,
    },
    {
      key: 'health',
      label: '健康记录',
      children: <HealthRecords />,
    },
  ];

  return (
    <Drawer
      title={
        <Space>
          <UserOutlined />
          健康档案
        </Space>
      }
      placement="right"
      width={700}
      open={open}
      onClose={onClose}
      maskClosable={false}
    >
      <Tabs items={tabItems} />
    </Drawer>
  );
};

