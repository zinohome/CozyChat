import React, { useState, useRef, useEffect } from 'react';
import { Row, Col, Space, Button, Progress, Tag } from 'antd';
import {
    ArrowLeftOutlined,
    PlusOutlined,
    PlayCircleFilled,
    PauseCircleFilled,
    StepForwardOutlined,
    StepBackwardOutlined,
    SoundOutlined,
    MutedOutlined,
    BellOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import styles from './StressProfile.module.css';

/**
 * 疗愈空间 (Healing Space) -> 情绪节律
 * 
 * 修改说明：
 * 1. 参考「我在」Mental Health V5 设计稿重构
 * 2. 采用单页仪表盘布局，集成压力趋势、心情日志和冥想推荐
 * 3. 强化情感化交互与视觉美感
 */

const TRACKS = [
    { title: "自然: 溪流晨语", url: "/audio/zen/1.mp3" },
    { title: "自然: 鸟鸣幽谷", url: "/audio/zen/2.mp3" },
    { title: "自然: 晚风海浪", url: "/audio/zen/3.mp3" },
    { title: "轻音乐: 颂钵冥想", url: "/audio/zen/4.mp3" },
    { title: "轻音乐: 星空畅想", url: "/audio/zen/5.mp3" },
    { title: "白噪音: 深度助眠", url: "/audio/zen/6.mp3" },
    { title: "轻音乐: 云端漫步", url: "/audio/zen/7.mp3" },
    { title: "自然: 悠然时光", url: "/audio/zen/8.mp3" },
    { title: "白噪音: 极光闪烁", url: "/audio/zen/9.mp3" },
    { title: "白噪音: 远山回音", url: "/audio/zen/10.mp3" },
];
export const StressProfile: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuthStore();

    // 获取用户资料
    const { data: profile } = useQuery({
        queryKey: ['user', 'profile', user?.id],
        queryFn: () => userApi.getCurrentUserProfile(),
        enabled: !!user?.id,
    });

    // 冥想播放器状态
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isMuted, setIsMuted] = useState(false);

    // 格式化时间 M:SS
    const formatTime = (time: number) => {
        if (isNaN(time)) return '0:00';
        const m = Math.floor(time / 60);
        const s = Math.floor(time % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    const handleTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
        }
    };

    const handleLoadedMetadata = () => {
        if (audioRef.current) {
            setDuration(audioRef.current.duration);
        }
    };

    const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!audioRef.current || !duration) return;
        const bar = e.currentTarget;
        const rect = bar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percent = clickX / rect.width;
        const newTime = percent * duration;
        audioRef.current.currentTime = newTime;
        setCurrentTime(newTime);
    };

    const toggleMute = () => {
        if (audioRef.current) {
            audioRef.current.muted = !audioRef.current.muted;
            setIsMuted(!isMuted);
        }
    };

    const togglePlay = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play().catch(e => console.log('Audio play failed', e));
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handlePrev = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentTrackIndex((prev) => (prev === 0 ? TRACKS.length - 1 : prev - 1));
    };

    const handleNext = (e: React.MouseEvent) => {
        e.stopPropagation();
        setCurrentTrackIndex((prev) => (prev === TRACKS.length - 1 ? 0 : prev + 1));
    };

    // 切换曲目时自动播放
    useEffect(() => {
        if (isPlaying && audioRef.current) {
            audioRef.current.play().catch(e => console.log('Audio play failed', e));
        }
    }, [currentTrackIndex]);

    const handleBack = () => {
        navigate('/chat');
    };

    // 趋势图渲染 (SVG)
    const renderTrendChart = () => (
        <div className={styles.chartContainer}>
            <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
                <defs>
                    <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style={{ stopColor: '#4caf50', stopOpacity: 0.2 }} />
                        <stop offset="100%" style={{ stopColor: '#4caf50', stopOpacity: 0 }} />
                    </linearGradient>
                </defs>
                <path
                    d="M0,25 Q15,15 30,22 Q45,30 60,18 Q75,10 90,20 L100,15 L100,40 L0,40 Z"
                    fill="url(#trendGradient)"
                />
                <path
                    d="M0,25 Q15,15 30,22 Q45,30 60,18 Q75,10 90,20 L100,15"
                    fill="none"
                    stroke="#4caf50"
                    strokeWidth="2"
                    strokeLinecap="round"
                />
                {/* 数据点 */}
                <circle cx="15" cy="15" r="1.5" fill="#4caf50" />
                <circle cx="30" cy="22" r="1.5" fill="#4caf50" />
                <circle cx="45" cy="30" r="1.5" fill="#4caf50" />
                <circle cx="60" cy="18" r="1.5" fill="#4caf50" />
                <circle cx="75" cy="10" r="1.5" fill="#4caf50" />
                <circle cx="90" cy="20" r="1.5" fill="#4caf50" />
            </svg>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#999', marginTop: '4px' }}>
                <span>8月</span><span>8日</span><span>周三</span><span>周六</span><span>周二</span><span>周三</span><span>周四</span>
            </div>
        </div>
    );

    return (
        <MainLayout>
            <div className={styles.container}>
                {/* Header */}
                <div className={styles.header}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        <Space>
                            <ArrowLeftOutlined onClick={handleBack} className={styles.backButton} />
                            <span className={styles.title}>情绪节律</span>
                        </Space>
                        <BellOutlined style={{ fontSize: '18px', color: '#666' }} />
                    </Space>
                </div>

                {/* Personalized Greeting */}
                <div className={styles.greetingHeader}>
                    <div className={styles.greetingText}>
                        您好，{profile?.display_name || user?.username || '杜亦南'}!
                    </div>
                    <div className={styles.subGreetingText}>让情绪如水般自然流动。</div>
                </div>

                <div className={styles.content}>
                    {/* 今日提示 (无大标题, 块状横向卡片) */}
                    <div className={styles.tipsContainer}>
                        <div className={styles.tipCard}>
                            <div className={styles.tipHeader}>
                                <span style={{ fontSize: '18px' }}>💼</span> 职场关系
                            </div>
                            <div className={styles.tipContent}>
                                今日能量较低，建议在工作中保持适当边界感，避免卷入不必要的冲突。
                            </div>
                        </div>
                        <div className={styles.tipCard}>
                            <div className={styles.tipHeader}>
                                <span style={{ fontSize: '18px' }}>❤️</span> 亲密关系
                            </div>
                            <div className={styles.tipContent}>
                                晚间是交流的好时机，尝试用“我感觉到...”来表达，而不是指责。
                            </div>
                        </div>
                        <div className={styles.tipCard}>
                            <div className={styles.tipHeader}>
                                <span style={{ fontSize: '18px' }}>👶</span> 亲子关系
                            </div>
                            <div className={styles.tipContent}>
                                面对孩子的情绪，先深呼吸三次，在稳住自己后再给予回应。
                            </div>
                        </div>
                    </div>

                    {/* 当前节律 (趋势图) */}
                    <div className={styles.metricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricLabel}>当前节律</div>
                            <div className={styles.trendInfo}>
                                <div className={styles.trendValue}>2.4</div>
                                <div className={styles.trendStatus}>稳步回升</div>
                            </div>
                        </div>
                        {renderTrendChart()}
                    </div>

                    {/* 正念冥想 */}
                    <div className={styles.meditationCard}>
                        <div
                            className={styles.meditationCover}
                            style={{ backgroundImage: 'linear-gradient(45deg, #2c3e50, #4ca1af), url(/images/meditation-cover.jpg)' }}
                        >
                            <div className={styles.meditationInfo}>
                                <div style={{ fontSize: '12px', opacity: 0.8 }}>正念冥想 · 每日推荐</div>
                                <div className={styles.meditationTitle}>{TRACKS[currentTrackIndex].title}</div>
                            </div>
                        </div>
                        <div className={styles.meditationControls}>
                            <div className={styles.progressBar} onClick={handleProgressBarClick} style={{ cursor: 'pointer' }}>
                                <div className={styles.progressFill} style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}></div>
                            </div>
                            <div className={styles.timeInfo}>
                                <span>{formatTime(currentTime)}</span>
                                <span>{formatTime(duration)}</span>
                            </div>
                            <div className={styles.playerIcons}>
                                <StepBackwardOutlined onClick={handlePrev} style={{ fontSize: '20px', color: '#666', cursor: 'pointer' }} />
                                {isPlaying ? (
                                    <PauseCircleFilled onClick={togglePlay} style={{ fontSize: '40px', color: 'var(--primary-color)', cursor: 'pointer' }} />
                                ) : (
                                    <PlayCircleFilled onClick={togglePlay} style={{ fontSize: '40px', color: 'var(--primary-color)', cursor: 'pointer' }} />
                                )}
                                <StepForwardOutlined onClick={handleNext} style={{ fontSize: '20px', color: '#666', cursor: 'pointer' }} />
                                {isMuted ? (
                                    <MutedOutlined onClick={toggleMute} style={{ fontSize: '18px', color: '#666', cursor: 'pointer' }} />
                                ) : (
                                    <SoundOutlined onClick={toggleMute} style={{ fontSize: '18px', color: '#666', cursor: 'pointer' }} />
                                )}
                            </div>
                        </div>
                        {/* 真正的音频播放器实体 */}
                        <audio
                            ref={audioRef}
                            src={TRACKS[currentTrackIndex].url}
                            onTimeUpdate={handleTimeUpdate}
                            onLoadedMetadata={handleLoadedMetadata}
                            loop
                        />
                    </div>

                    {/* 我的心情日志 */}
                    <div className={styles.moodLogCard}>
                        <div className={styles.sectionHeader}>
                            <div className={styles.metricLabel}>我的心情日志</div>
                            <Button type="text" size="small" icon={<PlusOutlined />} style={{ background: '#f0fdf4', color: '#16a34a', borderRadius: '12px' }}>添加</Button>
                        </div>
                        <div className={styles.moodList}>
                            {[
                                { date: '8月22日 星期四', emoji: '☀️', mood: '平静', tags: '阅读、散步、喝茶' },
                                { date: '8月21日 星期三', emoji: '😊', mood: '快乐', tags: '完成项目、收到礼物' },
                                { date: '8月20日 星期二', emoji: '😌', mood: '舒缓', tags: '冥想、练习瑜伽' },
                            ].map((item, i) => (
                                <div key={i} className={styles.moodItem}>
                                    <span className={styles.moodDate}>{item.date}</span>
                                    <span>-</span>
                                    <span className={styles.moodEmoji}>{item.emoji}</span>
                                    <span className={styles.moodContent}>{item.mood}</span>
                                    <span>-</span>
                                    <span className={styles.moodTags}>"{item.tags}"</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default StressProfile;
