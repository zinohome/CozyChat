import React from 'react';
import { Card, Descriptions, Avatar, Space, Typography } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/slices/authSlice';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '@/services/user';

const { Title } = Typography;

/**
 * 用户资料组件
 *
 * 显示用户基本信息。
 */
export const UserProfile: React.FC = () => {
  const { user } = useAuthStore();

  // 获取用户资料
  const { data: profile, isLoading } = useQuery({
    queryKey: ['user', 'profile', user?.id],
    queryFn: () => userApi.getUserProfile(user!.id),
    enabled: !!user?.id,
  });

  if (!user) {
    return null;
  }

  return (
    <Card loading={isLoading}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <Avatar size={64} icon={<UserOutlined />} src={profile?.avatar_url} />
          <div>
            <Title level={4} style={{ margin: 0 }}>
              {profile?.display_name || user.username}
            </Title>
            <div style={{ color: '#666' }}>{user.email}</div>
          </div>
        </Space>

        <Descriptions column={1} bordered>
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
          <Descriptions.Item label="角色">{user.role}</Descriptions.Item>
          {profile?.bio && (
            <Descriptions.Item label="简介">{profile.bio}</Descriptions.Item>
          )}
          {profile?.interests && profile.interests.length > 0 && (
            <Descriptions.Item label="兴趣">
              {profile.interests.join(', ')}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Space>
    </Card>
  );
};

