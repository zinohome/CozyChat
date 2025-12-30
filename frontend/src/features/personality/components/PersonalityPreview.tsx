import React from 'react';
import { Modal, Button } from 'antd';
import { PersonalityDetail } from './PersonalityDetail';
import type { Personality } from '@/types/personality';

/**
 * 人格预览组件属性
 */
interface PersonalityPreviewProps {
  /** 人格数据 */
  personality: Personality | null;
  /** 是否可见 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 选择回调 */
  onSelect?: (personalityId: string) => void;
}

/**
 * 人格预览组件
 *
 * 显示人格的详细信息和预览。
 */
export const PersonalityPreview: React.FC<PersonalityPreviewProps> = ({
  personality,
  open,
  onClose,
  onSelect,
}) => {
  if (!personality) return null;

  const handleSelect = () => {
    onSelect?.(personality.id);
    onClose();
  };

  return (
    <Modal
      title={`人格预览: ${personality.name}`}
      open={open}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={onClose}>
          关闭
        </Button>,
        onSelect && (
          <Button key="select" type="primary" onClick={handleSelect}>
            选择此人格
          </Button>
        ),
      ].filter(Boolean)}
    >
      <PersonalityDetail personality={personality} />
    </Modal>
  );
};

