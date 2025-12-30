import React from 'react';
import { Card, Descriptions, Tag, Space, Typography, Divider, Avatar } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import type { Personality } from '@/types/personality';

const { Title, Paragraph, Text } = Typography;

/**
 * 人格详情组件属性
 */
interface PersonalityDetailProps {
  /** 人格数据 */
  personality: Personality;
}

/**
 * 人格详情组件
 *
 * 显示人格的详细配置信息。
 */
export const PersonalityDetail: React.FC<PersonalityDetailProps> = ({
  personality,
}) => {
  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 基本信息 */}
          <div>
            <Space>
              <Avatar
                size={64}
                icon={<RobotOutlined />}
                src={personality.avatar_url}
              />
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  {personality.name}
                </Title>
                {personality.description && (
                  <Paragraph style={{ margin: '8px 0 0 0', color: '#666' }}>
                    {personality.description}
                  </Paragraph>
                )}
              </div>
            </Space>
          </div>

          <Divider />

          {/* 详细配置 */}
          <Descriptions title="配置信息" bordered column={1}>
            <Descriptions.Item label="人格ID">
              <Text code>{personality.id}</Text>
            </Descriptions.Item>
            
            {personality.ai_config && (
              <>
                <Descriptions.Item label="AI提供商">
                  <Tag color="blue">
                    {personality.ai_config.provider || 'openai'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="模型">
                  <Text>{personality.ai_config.model || 'gpt-3.5-turbo'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="温度">
                  <Text>{personality.ai_config.temperature || 0.7}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="最大Token">
                  <Text>{personality.ai_config.max_tokens || 2000}</Text>
                </Descriptions.Item>
              </>
            )}

            {personality.memory_config && (
              <>
                <Descriptions.Item label="记忆功能">
                  <Tag color={personality.memory_config.enabled ? 'green' : 'red'}>
                    {personality.memory_config.enabled ? '启用' : '禁用'}
                  </Tag>
                </Descriptions.Item>
                {personality.memory_config.save_mode && (
                  <Descriptions.Item label="保存模式">
                    <Tag>
                      {personality.memory_config.save_mode === 'both'
                        ? '用户+AI'
                        : personality.memory_config.save_mode === 'user'
                        ? '仅用户'
                        : '仅AI'}
                    </Tag>
                  </Descriptions.Item>
                )}
              </>
            )}

            {personality.tools_config && (
              <>
                <Descriptions.Item label="工具功能">
                  <Tag color={personality.tools_config.enabled ? 'green' : 'red'}>
                    {personality.tools_config.enabled ? '启用' : '禁用'}
                  </Tag>
                </Descriptions.Item>
                {personality.tools_config.allowed_tools &&
                  personality.tools_config.allowed_tools.length > 0 && (
                    <Descriptions.Item label="允许的工具">
                      <Space wrap>
                        {personality.tools_config.allowed_tools.map((tool) => (
                          <Tag key={tool}>{tool}</Tag>
                        ))}
                      </Space>
                    </Descriptions.Item>
                  )}
              </>
            )}

            {personality.system_prompt && (
              <Descriptions.Item label="系统提示词">
                <Paragraph
                  style={{
                    margin: 0,
                    maxHeight: '200px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {personality.system_prompt}
                </Paragraph>
              </Descriptions.Item>
            )}
          </Descriptions>
        </Space>
      </Card>
    </div>
  );
};

