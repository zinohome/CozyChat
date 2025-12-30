import React, { useState } from 'react';
import { Card, Avatar, Typography, Space, Button } from 'antd';
import { RobotOutlined, EyeOutlined } from '@ant-design/icons';
import { PersonalityPreview } from './PersonalityPreview';
import type { Personality } from '@/types/personality';

const { Text, Paragraph } = Typography;

/**
 * 人格卡片组件属性
 */
interface PersonalityCardProps {
  /** 人格数据 */
  personality: Personality;
  /** 是否选中 */
  isSelected?: boolean;
  /** 选择回调 */
  onSelect?: () => void;
  /** 显示预览按钮 */
  showPreview?: boolean;
}

/**
 * 人格卡片组件
 *
 * 显示单个人格信息，支持预览功能。
 */
export const PersonalityCard: React.FC<PersonalityCardProps> = ({
  personality,
  isSelected = false,
  onSelect,
  showPreview = true,
}) => {
  const [previewOpen, setPreviewOpen] = useState(false);

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreviewOpen(true);
  };

  return (
    <>
      <Card
        hoverable
        onClick={onSelect}
        style={{
          cursor: 'pointer',
          border: isSelected ? '2px solid #1890ff' : '1px solid #e8e8e8',
          backgroundColor: isSelected ? '#f0f8ff' : '#fff',
        }}
        actions={
          showPreview
            ? [
                <Button
                  key="preview"
                  type="text"
                  icon={<EyeOutlined />}
                  onClick={handlePreview}
                  size="small"
                >
                  预览
                </Button>,
              ]
            : undefined
        }
      >
        <Space>
          <Avatar
            size={48}
            icon={<RobotOutlined />}
            src={personality.avatar_url}
          />
          <div style={{ flex: 1 }}>
            <Text strong style={{ fontSize: '16px', display: 'block' }}>
              {personality.name}
            </Text>
            {personality.description && (
              <Paragraph
                ellipsis={{ rows: 2 }}
                style={{ margin: 0, color: '#666' }}
              >
                {personality.description}
              </Paragraph>
            )}
          </div>
        </Space>
      </Card>

      <PersonalityPreview
        personality={personality}
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        onSelect={onSelect ? () => onSelect() : undefined}
      />
    </>
  );
};

