import React, { useState, useRef, useEffect } from 'react';
import { Space } from 'antd';
import {
    ArrowLeftOutlined,
    PlayCircleFilled,
    PauseCircleFilled,
    StepBackwardOutlined,
    StepForwardOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import styles from './ZenPlayer.module.css';

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

export const ZenPlayer: React.FC = () => {
    const navigate = useNavigate();
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [breathText, setBreathText] = useState('准备呼吸');

    // 简单的呼吸文本循环逻辑
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isPlaying) {
            setBreathText('深吸气...');
            let cycle = 0;
            interval = setInterval(() => {
                cycle = (cycle + 1) % 2;
                if (cycle === 0) setBreathText('深吸气...');
                else setBreathText('慢呼气...');
            }, 4000); // 基于 8 秒循环
        } else {
            setBreathText('准备呼吸');
        }
        return () => clearInterval(interval);
    }, [isPlaying]);

    const handleBack = () => {
        navigate('/chat');
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

    try {
        return (
            <MainLayout>
                <div className={styles.container}>
                    <div className={styles.header}>
                        <ArrowLeftOutlined
                            onClick={handleBack}
                            className={styles.backButton}
                        />
                        <span className={styles.title}>禅定模式</span>
                        <div style={{ width: 40 }}></div> {/* 占位以居中标题 */}
                    </div>

                    <div className={styles.content}>
                        <div
                            className={`${styles.circleContainer} ${isPlaying ? styles.playing : ''}`}
                            onClick={togglePlay}
                        >
                            <div className={styles.breathingCircle}></div>
                            {isPlaying ? (
                                <PauseCircleFilled className={styles.playIcon} />
                            ) : (
                                <PlayCircleFilled className={styles.playIcon} />
                            )}
                        </div>

                        <Space size="large" style={{ marginTop: '20px', marginBottom: '20px' }}>
                            <StepBackwardOutlined
                                style={{ fontSize: 24, color: 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                                onClick={handlePrev}
                            />
                            <div className={styles.controlText} style={{ margin: 0, width: '120px' }}>
                                {isPlaying ? '静心聆听' : '点击开始'}
                            </div>
                            <StepForwardOutlined
                                style={{ fontSize: 24, color: 'rgba(255,255,255,0.7)', cursor: 'pointer' }}
                                onClick={handleNext}
                            />
                        </Space>

                        <div className={styles.subText}>
                            {TRACKS[currentTrackIndex].title}
                        </div>

                        <div className={styles.instructions} style={{ opacity: isPlaying ? 1 : 0 }}>
                            {breathText}
                        </div>

                        {/* 音频标签，循环播放，使用Apple高质量音频 */}
                        <audio
                            ref={audioRef}
                            src={TRACKS[currentTrackIndex].url}
                            loop
                        />
                    </div>
                </div>
            </MainLayout>
        );
    } catch (error) {
        console.error('ZenPlayer render error:', error);
        return (
            <MainLayout>
                <div style={{ padding: '24px' }}>
                    <div>页面加载出错，请刷新重试</div>
                </div>
            </MainLayout>
        );
    }
};

export default ZenPlayer;
