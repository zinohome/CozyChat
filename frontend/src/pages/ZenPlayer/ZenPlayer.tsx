import React, { useState, useRef, useEffect } from 'react';
import { Space } from 'antd';
import {
    ArrowLeftOutlined,
    PlayCircleFilled,
    PauseCircleFilled
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import styles from './ZenPlayer.module.css';

export const ZenPlayer: React.FC = () => {
    const navigate = useNavigate();
    const [isPlaying, setIsPlaying] = useState(false);
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
                // 使用一个免责声明或公开的白噪音资源。此处提供一个稳定的公开自然声音作为演示。
                // 如果资源失效，也不会阻塞UI动画
                audioRef.current.play().catch(e => console.log('Audio play failed, playing animation only', e));
            }
            setIsPlaying(!isPlaying);
        }
    };

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
                                <PauseCircleFilled className={styles.playIcon} style={{ opacity: 0.2 }} />
                            ) : (
                                <PlayCircleFilled className={styles.playIcon} />
                            )}
                        </div>

                        <div className={styles.controlText}>
                            {isPlaying ? '静心聆听' : '点击开始'}
                        </div>
                        <div className={styles.subText}>
                            晚风海浪 · 10 分钟
                        </div>

                        <div className={styles.instructions} style={{ opacity: isPlaying ? 1 : 0 }}>
                            {breathText}
                        </div>

                        {/* 音频标签，循环播放 */}
                        <audio
                            ref={audioRef}
                            src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3"
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
