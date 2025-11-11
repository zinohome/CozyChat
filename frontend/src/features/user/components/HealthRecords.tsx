import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, DatePicker, InputNumber, Space, Empty, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { userApi } from '@/services/user';
import { showError, showSuccess } from '@/utils/errorHandler';
import { format, parseISO } from 'date-fns';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';

const { TextArea } = Input;

/**
 * 健康记录项
 */
interface HealthRecord {
  id: string;
  date: Dayjs;
  weight?: number;
  blood_pressure?: string;
  heart_rate?: number;
  notes?: string;
}

/**
 * 健康记录组件
 */
export const HealthRecords: React.FC = () => {
  const [form] = Form.useForm();
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  /**
   * 加载健康记录
   */
  const loadHealthRecords = async () => {
    setLoading(true);
    try {
      const profile = await userApi.getCurrentUserProfile();
      // 从用户画像的habits字段中获取健康记录
      const healthData = (profile as any).profile?.habits?.health_records || [];
      setRecords(
        healthData.map((record: any) => ({
          ...record,
          date: dayjs(record.date || new Date()),
        }))
      );
    } catch (error) {
      showError(error, '加载健康记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealthRecords();
  }, []);

  /**
   * 保存健康记录
   */
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      // 构建健康记录数据
      const newRecord: HealthRecord = {
        id: `record-${Date.now()}`,
        date: values.date,
        weight: values.weight,
        blood_pressure: values.blood_pressure,
        heart_rate: values.heart_rate,
        notes: values.notes,
      };

      // 获取当前用户画像
      const profile = await userApi.getCurrentUserProfile();
      const currentHabits = (profile as any).profile?.habits || {};
      const currentRecords = currentHabits.health_records || [];

      // 更新健康记录
      const updatedRecords = [...currentRecords, {
        ...newRecord,
        date: newRecord.date.format('YYYY-MM-DD'),
      }];

      // 更新用户偏好（将健康记录存储在habits中）
      // 注意：这里需要后端支持更新habits字段
      // 目前先显示成功，实际保存需要后端API支持
      showSuccess('健康记录已保存（需要后端API支持）');
      form.resetFields();
      
      // 更新本地状态
      setRecords([...records, newRecord]);
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      showError(error, '保存健康记录失败');
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * 删除健康记录
   */
  const handleDelete = (id: string) => {
    const updatedRecords = records.filter((record) => record.id !== id);
    setRecords(updatedRecords);
    showSuccess('健康记录已删除');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Card title="添加健康记录" style={{ marginBottom: '16px' }}>
        <Form form={form} layout="vertical">
          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Space style={{ width: '100%' }} size="middle">
            <Form.Item
              name="weight"
              label="体重 (kg)"
              style={{ flex: 1 }}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="请输入体重"
                min={0}
                max={300}
                precision={1}
              />
            </Form.Item>

            <Form.Item
              name="blood_pressure"
              label="血压 (mmHg)"
              style={{ flex: 1 }}
            >
              <Input placeholder="如：120/80" />
            </Form.Item>

            <Form.Item
              name="heart_rate"
              label="心率 (bpm)"
              style={{ flex: 1 }}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="请输入心率"
                min={0}
                max={300}
              />
            </Form.Item>
          </Space>

          <Form.Item name="notes" label="备注">
            <TextArea
              rows={3}
              placeholder="请输入备注信息"
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleSave}
              loading={submitting}
              block
            >
              添加记录
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="历史记录">
        {records.length === 0 ? (
          <Empty description="暂无健康记录" />
        ) : (
          <div>
            {records
              .sort((a, b) => b.date.valueOf() - a.date.valueOf())
              .map((record) => (
                <Card
                  key={record.id}
                  size="small"
                  style={{ marginBottom: '12px' }}
                  actions={[
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDelete(record.id)}
                    >
                      删除
                    </Button>,
                  ]}
                >
                  <div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>日期：</strong>
                      {format(record.date.toDate(), 'yyyy-MM-dd')}
                    </div>
                    <Space size="large">
                      {record.weight && (
                        <div>
                          <strong>体重：</strong>
                          {record.weight} kg
                        </div>
                      )}
                      {record.blood_pressure && (
                        <div>
                          <strong>血压：</strong>
                          {record.blood_pressure} mmHg
                        </div>
                      )}
                      {record.heart_rate && (
                        <div>
                          <strong>心率：</strong>
                          {record.heart_rate} bpm
                        </div>
                      )}
                    </Space>
                    {record.notes && (
                      <div style={{ marginTop: '8px', color: '#666' }}>
                        <strong>备注：</strong>
                        {record.notes}
                      </div>
                    )}
                  </div>
                </Card>
              ))}
          </div>
        )}
      </Card>
    </div>
  );
};

