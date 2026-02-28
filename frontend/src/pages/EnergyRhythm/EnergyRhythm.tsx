import React, { useState, useEffect } from 'react';
import { Space } from 'antd';
import {
    ArrowLeftOutlined,
    BellOutlined,
    ThunderboltOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/store/slices/authSlice';
import { userApi } from '@/services/user';
import styles from './EnergyRhythm.module.css';

// 昼夜节律各个阶段的配置
interface PhaseConfig {
    name: string;
    x: number;
    y: number;
    desc: string;
    title: string;
    items: string[];
}

function getCurrentPhaseConfig(h: number): PhaseConfig {
    if (h >= 6 && h < 10) return { name: '晨间唤醒', x: 12.5, y: 15, desc: '能量爬坡阶段，适合安排重要的规划任务', title: '晨间充电 (06:00 - 10:00)', items: ['吃一顿高蛋白的营养早餐。', '进行15分钟的晨间唤醒拉伸。', '列出今天最重要的三件事。'] };
    if (h >= 10 && h < 13) return { name: '认知高峰', x: 25, y: 10, desc: '精力最充沛的黄金时段，适合深度脑力工作', title: '认知顶峰 (10:00 - 13:00)', items: ['专注解决复杂难题，不查看邮件。', '进行深度思考和创意产出。', '控制咖啡因的摄入量。'] };
    if (h >= 13 && h < 15) return { name: '午后回落', x: 37.5, y: 25, desc: '生理节律自然回落，能量逐渐缓冲', title: '午后调整 (13:00 - 15:00)', items: ['进行20分钟的闭目养神或午休。', '起身散步，让血液重新循环。', '处理简单回复类的机械性任务。'] };
    if (h >= 15 && h < 18) return { name: '第二活力期', x: 50, y: 18, desc: '能量小幅回升，适合沟通与协作', title: '高价值沟通 (15:00 - 18:00)', items: ['安排团队会议或外部沟通。', '清理收件箱和待办事项。', '为明天的重点任务做铺垫。'] };
    // 高压人群晚间能量细化管理
    if (h >= 18 && h < 19) return { name: '晚间过渡', x: 56, y: 25, desc: '交感神经仍活跃，需要人为降载', title: '工作向恢复过渡 (18:00 - 19:00)', items: ['当前进入节律过渡阶段。', '建议减少高压沟通。', '可以安排 10 分钟轻度步行。', '不再开启新的复杂任务。', '为今晚的恢复预留空间。'] };
    if (h >= 19 && h < 20) return { name: '疲劳显现', x: 62, y: 28, desc: '前额叶疲劳，决策质量下降', title: '认知控制力下降 (19:00 - 20:00)', items: ['当前不适合重大决策。', '建议停止战略性思考。', '可以整理已完成事项。', '将未完成事项留给明日上午。', '降低信息输入强度。'] };
    if (h >= 20 && h < 21) return { name: '恢复启动', x: 68, y: 32, desc: '褪黑素开始分泌，蓝光会延迟入睡', title: '恢复窗口启动 (20:00 - 21:00)', items: ['当前进入恢复窗口。', '建议减少屏幕暴露。', '可以进行 3 分钟缓慢呼吸。', '不再处理冲突性沟通。', '允许今天停止推进。'] };
    if (h >= 21 && h < 22) return { name: '神经下行', x: 74, y: 35, desc: '神经系统建立明确结束信号', title: '神经系统下行 (21:00 - 22:00)', items: ['当前属于夜间恢复区间。', '建议关闭主要工作通道。', '不再进行复杂讨论。', '可以写下明日三件最重要事项。', '让节律自然下行。'] };
    return { name: '深度休眠', x: 80, y: 38, desc: '机体深度自我修复和排毒时间', title: '绝对休息 (22:00 - 06:00)', items: ['保持卧室完全黑暗，调节适宜温度。', '睡前听一段平静的白噪音。', '顺应自然规律，切忌熬夜。'] };
}

export const EnergyRhythm: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuthStore();

    // 动态获取当前时间 (支持实时更新)
    const [currentDate, setCurrentDate] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentDate(new Date()), 60000); // 每分钟更新一次
        return () => clearInterval(timer);
    }, []);

    const currentHour = currentDate.getHours();
    const currentMinutes = currentDate.getMinutes();
    const phase = getCurrentPhaseConfig(currentHour);

    // 精确计算动态锚点的位置，使其在曲线上随分钟数平滑过渡
    // 简化的插值计算，仅仅为了视觉连续性，也可以直接用 base 坐标
    const calculateExactX = (h: number, m: number) => {
        let shiftedHour = h >= 6 ? h - 6 : h + 18; // 以早上 6 点为起点 0
        const totalHours = shiftedHour + (m / 60);
        return (totalHours / 24) * 100;
    };

    const exactX = calculateExactX(currentHour, currentMinutes);

    // 为了省去贝塞尔曲线上的精确 Y 值计算，我们这里就直接取 phase.y 并在小范围内近似或者干脆直接用对应的段值。
    // 因为这只是 Demo 效果，跟随 phase.x 的预设更稳定。我们将发光圆点固定在当前阶段的代表位置。

    const { data: profile } = useQuery({
        queryKey: ['user', 'profile', user?.id],
        queryFn: () => userApi.getCurrentUserProfile(),
        enabled: !!user?.id,
    });

    const handleBack = () => {
        navigate('/chat');
    };

    // 绘制专业级昼夜节律波形图
    const renderProfessionalCircadianChart = () => (
        <div className={styles.chartContainer}>
            <svg viewBox="-5 0 110 50" preserveAspectRatio="none" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
                <defs>
                    <linearGradient id="energyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style={{ stopColor: '#6366f1', stopOpacity: 0.4 }} />
                        <stop offset="100%" style={{ stopColor: '#6366f1', stopOpacity: 0.0 }} />
                    </linearGradient>
                    <filter id="glowIndigo" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="0.8" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {/* 背景网格虚线 */}
                <line x1="0" y1="10" x2="100" y2="10" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />
                <line x1="0" y1="25" x2="100" y2="25" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />
                <line x1="0" y1="40" x2="100" y2="40" stroke="#f0f0f0" strokeWidth="0.5" strokeDasharray="2,2" />

                {/* X轴时间标签 */}
                <text x="0" y="48" fontSize="4.5" fill="#999" textAnchor="middle">6:00</text>
                <text x="25" y="48" fontSize="4.5" fill="#999" textAnchor="middle">12:00</text>
                <text x="50" y="48" fontSize="4.5" fill="#999" textAnchor="middle">18:00</text>
                <text x="75" y="48" fontSize="4.5" fill="#999" textAnchor="middle">0:00</text>
                <text x="100" y="48" fontSize="4.5" fill="#999" textAnchor="middle">6:00</text>

                {/* 渐变填充区域 */}
                <path
                    d="M0,35 C8,35 15,10 25,10 C30,10 32,25 37.5,25 C42,25 45,18 50,18 C60,18 70,35 75,38 C85,40 95,35 100,35 L100,50 L0,50 Z"
                    fill="url(#energyGrad)"
                />

                {/* 核心平滑折线 */}
                <path
                    d="M0,35 C8,35 15,10 25,10 C30,10 32,25 37.5,25 C42,25 45,18 50,18 C60,18 70,35 75,38 C85,40 95,35 100,35"
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    filter="url(#glowIndigo)"
                />

                {/* 动态时间点锚点 */}
                <g transform={`translate(${phase.x}, ${phase.y})`}>
                    <circle cx="0" cy="0" r="3" fill="#818cf8" opacity="0.6">
                        <animate attributeName="r" values="3;6;3" dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.6;0.2;0.6" dur="2s" repeatCount="indefinite" />
                    </circle>
                    <circle cx="0" cy="0" r="1.5" fill="#fff" stroke="#6366f1" strokeWidth="1" />
                    {/* Tooltip气泡效果 */}
                    <rect x="-6" y="-7.5" width="12" height="4.5" rx="1.5" fill="#6366f1" />
                    <text x="0" y="-4.5" fontSize="3" fill="#fff" textAnchor="middle" fontWeight="bold">当前</text>
                </g>
            </svg>
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
                            <span className={styles.title}>能量节律</span>
                        </Space>
                        <BellOutlined style={{ fontSize: '18px', color: '#666' }} />
                    </Space>
                </div>

                {/* 规范化的两行问候语 */}
                <div className={styles.greetingHeader}>
                    <div className={styles.greetingText}>
                        您好，{profile?.display_name || user?.username || '杜亦南'}!
                    </div>
                    <div className={styles.subGreetingText}>顺应昼夜，找到属于你的平衡点。</div>
                </div>

                <div className={styles.content}>
                    {/* 卡片化：精力曲线 */}
                    <div className={styles.energyMetricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricTitle}>
                                <ThunderboltOutlined style={{ color: '#6366f1' }} />
                                精力曲线
                            </div>
                            <span className={styles.metricStatus}>{phase.name}</span>
                        </div>
                        <div className={styles.metricValue}>{phase.name}</div>
                        <div className={styles.metricSubValue}>{phase.desc}</div>

                        {renderProfessionalCircadianChart()}
                    </div>

                    {/* 卡片化：动态能量管理建议 */}
                    <div className={styles.sectionHeader}>
                        <div className={styles.sectionTitle}>当前行动建议</div>
                    </div>

                    <div className={styles.adviceList}>
                        <div className={styles.adviceCard}>
                            <div className={styles.adviceTitle}>
                                <ThunderboltOutlined style={{ color: '#6366f1' }} />
                                {phase.title}
                            </div>
                            {phase.items.map((item, index) => (
                                <div key={index} className={styles.adviceItem}>
                                    <CheckCircleFilled className={styles.adviceIcon} />
                                    <span>{item}</span>
                                </div>
                            ))}
                        </div>

                        {/* 动态核心原则 */}
                        {currentHour >= 18 && currentHour < 22 ? (
                            <div className={styles.adviceCard} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', boxShadow: 'none' }}>
                                <div className={styles.adviceTitle} style={{ color: '#64748b', fontSize: '14px', marginBottom: '12px' }}>
                                    高压职场人晚间管理核心原则 (18:00-22:00)
                                </div>
                                <div className={styles.adviceItem} style={{ color: '#64748b' }}>
                                    <span style={{ marginRight: '8px' }}>1️⃣</span>
                                    <span style={{ fontWeight: 500 }}>不做重大决策</span>
                                </div>
                                <div className={styles.adviceItem} style={{ color: '#64748b' }}>
                                    <span style={{ marginRight: '8px' }}>2️⃣</span>
                                    <span style={{ fontWeight: 500 }}>不开启新任务</span>
                                </div>
                                <div className={styles.adviceItem} style={{ color: '#64748b' }}>
                                    <span style={{ marginRight: '8px' }}>3️⃣</span>
                                    <span style={{ fontWeight: 500 }}>保护睡眠窗口</span>
                                </div>
                            </div>
                        ) : (
                            <div className={styles.adviceCard} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', boxShadow: 'none' }}>
                                <div className={styles.adviceTitle} style={{ color: '#64748b', fontSize: '14px', marginBottom: '12px' }}>
                                    全天候核心原则
                                </div>
                                <div className={styles.adviceItem} style={{ color: '#64748b' }}>
                                    <span style={{ marginRight: '6px' }}>•</span>
                                    <span>避免在深陷低谷时强迫自己进行高强度脑力工作。</span>
                                </div>
                                <div className={styles.adviceItem} style={{ color: '#64748b' }}>
                                    <span style={{ marginRight: '6px' }}>•</span>
                                    <span>适当的放空和散步，是脑力劳动者最好的休息。</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default EnergyRhythm;
