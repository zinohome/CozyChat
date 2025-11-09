import React from 'react';
import { Select, Card, Space, Typography } from 'antd';
import { usePersonalities } from '../hooks/usePersonalities';
import { PersonalityCard } from './PersonalityCard';
import type { Personality } from '@/types/personality';

const { Title } = Typography;
const { Option } = Select;

/**
 * 人格选择器组件属性
 */
interface PersonalitySelectorProps {
  /** 当前选中的人格ID */
  value?: string;
  /** 选择回调 */
  onChange?: (personalityId: string) => void;
  /** 显示模式 */
  mode?: 'select' | 'card';
}

/**
 * 人格选择器组件
 *
 * 支持下拉选择和卡片选择两种模式。
 */
export const PersonalitySelector: React.FC<PersonalitySelectorProps> = ({
  value,
  onChange,
  mode = 'select',
}) => {
  const { personalities, isLoading } = usePersonalities();

  if (mode === 'select') {
    return (
      <Select
        value={value}
        onChange={onChange}
        loading={isLoading}
        placeholder="选择人格"
        style={{ width: '100%' }}
      >
        {personalities.map((personality) => (
          <Option key={personality.id} value={personality.id}>
            {personality.name}
          </Option>
        ))}
      </Select>
    );
  }

  return (
    <div>
      <Title level={5}>选择人格</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        {personalities.map((personality) => (
          <PersonalityCard
            key={personality.id}
            personality={personality}
            isSelected={personality.id === value}
            onSelect={() => onChange?.(personality.id)}
          />
        ))}
      </Space>
    </div>
  );
};

