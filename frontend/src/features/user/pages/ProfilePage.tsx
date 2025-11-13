import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, Form, Input, Button, Avatar, Space, Upload, message } from 'antd';
import { ArrowLeftOutlined, UserOutlined, UploadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/slices/authSlice';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/user';
import { showError, showSuccess } from '@/utils/errorHandler';
import type { UserProfile } from '@/types/user';
import type { UploadFile, UploadProps } from 'antd';
import './ProfilePage.css';

/**
 * 个人资料页面
 *
 * 用户个人资料编辑页面。
 */
export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<Partial<UserProfile>>();
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>();

  // 获取用户资料
  const { data: profile, isLoading } = useQuery({
    queryKey: ['user', 'profile', user?.id],
    queryFn: () => userApi.getCurrentUserProfile(),
    enabled: !!user?.id,
  });

  // 更新用户资料Mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => {
      if (!user?.id) {
        throw new Error('用户未登录');
      }
      return userApi.updateUserProfile(user.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'profile', user?.id] });
      queryClient.invalidateQueries({ queryKey: ['user', 'profile'] });
      showSuccess('个人资料已保存');
    },
    onError: (error) => {
      showError(error, '保存个人资料失败');
    },
  });

  // 初始化表单数据
  useEffect(() => {
    if (profile) {
      form.setFieldsValue({
        display_name: profile.display_name || '',
        bio: profile.bio || '',
        interests: profile.interests?.join(', ') || '',
      });
      setAvatarUrl(profile.avatar_url);
    }
  }, [profile, form]);

  /**
   * 即时保存个人资料
   */
  const saveProfile = async (field: string, value: any) => {
    if (!user?.id) return;

    try {
      const updateData: Partial<UserProfile> = {};
      
      if (field === 'interests') {
        // 处理兴趣字段（字符串转数组）
        const interests = value
          ? value
              .split(',')
              .map((item: string) => item.trim())
              .filter((item: string) => item.length > 0)
          : [];
        updateData.interests = interests;
      } else if (field === 'avatar_url') {
        updateData.avatar_url = value;
      } else {
        updateData[field as keyof UserProfile] = value;
      }

      await updateMutation.mutateAsync(updateData);
    } catch (error) {
      // 错误已在 mutation 中处理
    }
  };

  /**
   * 处理显示名称变化（失焦时保存）
   */
  const handleDisplayNameBlur = async (e: React.FocusEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value !== profile?.display_name) {
      await saveProfile('display_name', value);
    }
  };

  /**
   * 处理个人简介变化（失焦时保存）
   */
  const handleBioBlur = async (e: React.FocusEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value !== profile?.bio) {
      await saveProfile('bio', value);
    }
  };

  /**
   * 处理兴趣变化（失焦时保存）
   */
  const handleInterestsBlur = async (e: React.FocusEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const currentInterests = profile?.interests?.join(', ') || '';
    if (value !== currentInterests) {
      await saveProfile('interests', value);
    }
  };

  /**
   * 处理头像上传
   */
  const handleAvatarChange: UploadProps['onChange'] = async (info) => {
    if (info.file.status === 'done') {
      // 如果上传成功，从响应中获取头像URL
      if (info.file.response?.avatar_url) {
        const newAvatarUrl = info.file.response.avatar_url;
        setAvatarUrl(newAvatarUrl);
        // 即时保存头像
        await saveProfile('avatar_url', newAvatarUrl);
        message.success('头像上传成功');
      } else {
        // 如果没有响应，使用本地预览
        const reader = new FileReader();
        reader.onloadend = async () => {
          const newAvatarUrl = reader.result as string;
          setAvatarUrl(newAvatarUrl);
          // 即时保存头像
          await saveProfile('avatar_url', newAvatarUrl);
        };
        if (info.file.originFileObj) {
          reader.readAsDataURL(info.file.originFileObj);
        }
      }
    } else if (info.file.status === 'error') {
      message.error('头像上传失败');
    }
  };

  /**
   * 自定义上传请求（暂时使用本地预览，实际应该上传到服务器）
   */
  const customRequest: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    
    // TODO: 实现实际上传逻辑
    // 目前使用本地预览
    const reader = new FileReader();
    reader.onloadend = () => {
      setAvatarUrl(reader.result as string);
      onSuccess?.({ avatar_url: reader.result as string });
    };
    reader.onerror = () => {
      onError?.(new Error('读取文件失败'));
    };
    reader.readAsDataURL(file as File);
  };

  const handleClose = () => {
    navigate('/chat');
  };

  return (
    <MainLayout>
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
        <Card
          className="profile-card"
          title={
            <Space>
              <ArrowLeftOutlined
                onClick={handleClose}
                className="profile-back-button"
                style={{ cursor: 'pointer', fontSize: '16px' }}
              />
              <span>个人资料</span>
            </Space>
          }
          styles={{
            header: {
              backgroundColor: 'var(--primary-color)',
              borderBottomColor: 'var(--primary-color)',
            },
          }}
          style={{
            borderColor: 'var(--primary-color)',
          }}
        >
          <Form
            form={form}
            layout="vertical"
          >
            {/* 头像上传 */}
            <Form.Item label="头像">
              <Space direction="vertical" align="center" style={{ width: '100%' }}>
                <Avatar
                  size={120}
                  icon={<UserOutlined />}
                  src={avatarUrl}
                  style={{
                    border: '2px solid var(--border-color)',
                  }}
                />
                <Upload
                  name="avatar"
                  showUploadList={false}
                  onChange={handleAvatarChange}
                  customRequest={customRequest}
                  accept="image/*"
                >
                  <Button icon={<UploadOutlined />}>上传头像</Button>
                </Upload>
              </Space>
            </Form.Item>

            {/* 用户名（只读） */}
            <Form.Item label="用户名">
              <Input value={user?.username} disabled />
            </Form.Item>

            {/* 邮箱（只读） */}
            <Form.Item label="邮箱">
              <Input value={user?.email} disabled />
            </Form.Item>

            {/* 显示名称 */}
            <Form.Item
              name="display_name"
              label="显示名称"
              rules={[
                { max: 50, message: '显示名称不能超过50个字符' },
              ]}
            >
              <Input 
                placeholder="请输入显示名称"
                onBlur={handleDisplayNameBlur}
              />
            </Form.Item>

            {/* 个人简介 */}
            <Form.Item
              name="bio"
              label="个人简介"
              rules={[
                { max: 200, message: '个人简介不能超过200个字符' },
              ]}
            >
              <Input.TextArea
                rows={4}
                placeholder="请输入个人简介"
                maxLength={200}
                showCount
                onBlur={handleBioBlur}
              />
            </Form.Item>

            {/* 兴趣 */}
            <Form.Item
              name="interests"
              label="兴趣"
              tooltip="多个兴趣请用逗号分隔"
            >
              <Input 
                placeholder="例如：编程, 阅读, 旅行"
                onBlur={handleInterestsBlur}
              />
            </Form.Item>
          </Form>
        </Card>
      </div>
    </MainLayout>
  );
};

export default ProfilePage;

