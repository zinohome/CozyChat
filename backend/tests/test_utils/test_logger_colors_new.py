#!/usr/bin/env python3
"""
测试新的日志颜色（强制重新加载模块）
直接在 Cursor 终端中运行：python test_new_colors.py
"""
import sys
import os

# 强制删除已加载的 logger 模块，确保使用最新代码
if 'app.utils.logger' in sys.modules:
    del sys.modules['app.utils.logger']
if 'app.utils' in sys.modules:
    del sys.modules['app.utils']

print("=" * 70)
print("日志级别颜色测试（彩色背景 + 白色文字）")
print("=" * 70)
print()

# 测试直接的 ANSI 代码
print("测试 1: 直接 ANSI 代码（亮白色文字 vs 普通白色 vs 黑色）")
print("-" * 70)
print("\033[42m\033[97m\033[1m INFO \033[0m  ← 绿色背景 + 亮白色文字（新版本，最亮）")
print("\033[42m\033[37m\033[1m INFO \033[0m  ← 绿色背景 + 普通白色文字（中等亮度）")
print("\033[42m\033[30m\033[1m INFO \033[0m  ← 绿色背景 + 黑色文字（最暗）")
print()
print("\033[46m\033[97m\033[1m DEBUG \033[0m ← 青色背景 + 亮白色文字（新版本，最亮）")
print("\033[46m\033[37m\033[1m DEBUG \033[0m ← 青色背景 + 普通白色文字（中等亮度）")
print("\033[46m\033[30m\033[1m DEBUG \033[0m ← 青色背景 + 黑色文字（最暗）")
print()
print("\033[43m\033[97m\033[1m WARNING \033[0m ← 黄色背景 + 亮白色文字（新版本）")
print("\033[41m\033[97m\033[1m ERROR \033[0m ← 红色背景 + 亮白色文字（新版本）")
print("\033[45m\033[97m\033[1m CRITICAL \033[0m ← 紫色背景 + 亮白色文字（新版本）")
print()

# 测试实际日志系统
print("测试 2: 实际日志系统（应该是白色文字）")
print("-" * 70)
try:
    # 强制重新导入
    from app.utils.logger import logger
    
    logger.info("Info 日志 - 应该是【绿色背景 + 白色文字】")
    logger.debug("Debug 日志 - 应该是【青色背景 + 白色文字】")
    logger.warning("Warning 日志 - 应该是【黄色背景 + 白色文字】")
    logger.error("Error 日志 - 应该是【红色背景 + 白色文字】")
    
    print()
    print("✓ 日志系统测试完成")
except Exception as e:
    print(f"✗ 日志系统测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("检查结果：")
print()
print("如果上面的 INFO/DEBUG/WARNING/ERROR 标签中的文字是【白色】，")
print("说明配置正确。")
print()
print("如果文字是【黑色】，可能需要：")
print("1. 重启 Python 进程（关闭并重新启动后端服务）")
print("2. 或者在外部终端（iTerm2/Terminal.app）中查看")
print("=" * 70)

