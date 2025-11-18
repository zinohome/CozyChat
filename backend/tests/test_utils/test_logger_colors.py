#!/usr/bin/env python3
"""
测试终端颜色输出脚本
直接在 Cursor 终端中运行：python test_color_output.py
"""
import sys
import os

print("=" * 60)
print("终端颜色支持测试")
print("=" * 60)
print()

# 检查环境
print("环境信息:")
print(f"  TERM: {os.environ.get('TERM', '未设置')}")
print(f"  COLORTERM: {os.environ.get('COLORTERM', '未设置')}")
print(f"  isatty: {sys.stdout.isatty()}")
print()

# 强制设置颜色环境变量
os.environ['FORCE_COLOR'] = '1'
os.environ['CLICOLOR_FORCE'] = '1'
print("已设置 FORCE_COLOR=1 和 CLICOLOR_FORCE=1")
print()

# 测试基本 ANSI 颜色
print("测试 1: 基本 ANSI 颜色代码")
print("-" * 60)
print("\033[31m这应该是红色\033[0m")
print("\033[32m这应该是绿色\033[0m")
print("\033[33m这应该是黄色\033[0m")
print("\033[34m这应该是蓝色\033[0m")
print("\033[35m这应该是紫色\033[0m")
print("\033[36m这应该是青色\033[0m")
print()

# 测试背景色 + 白色文字
print("测试 2: 背景色 + 白色文字（统一风格）")
print("-" * 60)
print("\033[41m\033[37m\033[1m 红色背景 + 白色文字 \033[0m")
print("\033[42m\033[37m\033[1m 绿色背景 + 白色文字 \033[0m")
print("\033[43m\033[37m\033[1m 黄色背景 + 白色文字 \033[0m")
print("\033[46m\033[37m\033[1m 青色背景 + 白色文字 \033[0m")
print("\033[45m\033[37m\033[1m 紫色背景 + 白色文字 \033[0m")
print()

# 测试日志格式（带背景色的标签，统一白色文字）
print("测试 3: 日志级别标签（彩色背景 + 白色文字）")
print("-" * 60)
timestamp = "\033[2m2025-11-18 15:45:30.123\033[0m"
info_level = "\033[42m\033[37m\033[1m INFO \033[0m"      # 绿色背景 + 白色文字
debug_level = "\033[46m\033[37m\033[1m DEBUG \033[0m"    # 青色背景 + 白色文字
warning_level = "\033[43m\033[37m\033[1m WARNING \033[0m"  # 黄色背景 + 白色文字
error_level = "\033[41m\033[37m\033[1m ERROR \033[0m"    # 红色背景 + 白色文字

print(f"{timestamp} {info_level} [app/test.py:10] Info message")
print(f"{timestamp} {debug_level} [app/test.py:11] Debug message")
print(f"{timestamp} {warning_level} [app/test.py:12] Warning message")
print(f"{timestamp} {error_level} [app/test.py:13] Error message")
print()

# 测试实际日志
print("测试 4: 实际日志系统")
print("-" * 60)
try:
    from app.utils.logger import logger
    logger.info("Info 日志测试 - 应该是粗体绿色")
    logger.debug("Debug 日志测试 - 应该是粗体青色")
    logger.warning("Warning 日志测试 - 应该是粗体黄色")
    logger.error("Error 日志测试 - 应该是粗体红色")
    print()
    print("✓ 日志系统测试完成")
except Exception as e:
    print(f"✗ 日志系统测试失败: {e}")

print()
print("=" * 60)
print("测试完成！")
print()
print("如果您看到上面的文字有颜色，说明终端支持 ANSI 颜色。")
print("如果看到的是纯文本（如 [31m红色[0m），说明 Cursor 终端不渲染颜色。")
print()
print("解决方案：")
print("1. 在外部终端（iTerm2/Terminal.app）运行后端服务")
print("2. 或者使用 Cursor 的 'Open in External Terminal' 功能")
print("=" * 60)

