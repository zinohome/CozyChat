#!/usr/bin/env python3
"""
更新测试覆盖率脚本

从测试结果中提取覆盖率数据，更新PROJECT_STATUS.json。

使用方法:
    python scripts/update_test_coverage.py [--backend] [--frontend]

选项:
    --backend: 更新后端测试覆盖率
    --frontend: 更新前端测试覆盖率
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATUS_FILE = PROJECT_ROOT / "docs" / "PROJECT_STATUS.json"


def load_status() -> Dict[str, Any]:
    """加载状态文件"""
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_status(data: Dict[str, Any]) -> None:
    """保存状态文件"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_backend_coverage() -> Dict[str, Any]:
    """获取后端测试覆盖率"""
    try:
        result = subprocess.run(
            ['pytest', '--cov=app', '--cov-report=json', '--quiet'],
            cwd=PROJECT_ROOT / 'backend',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 读取coverage.json
        coverage_file = PROJECT_ROOT / 'backend' / 'coverage.json'
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                return {
                    'percentage': round(total_coverage, 2),
                    'test_count': coverage_data.get('totals', {}).get('num_statements', 0),
                }
    except Exception as e:
        print(f"获取后端覆盖率失败: {e}")
    
    return {'percentage': 0, 'test_count': 0}


def get_frontend_coverage() -> Dict[str, Any]:
    """获取前端测试覆盖率"""
    try:
        result = subprocess.run(
            ['pnpm', 'test:coverage', '--run'],
            cwd=PROJECT_ROOT / 'frontend',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 从输出中提取覆盖率
        output = result.stdout + result.stderr
        match = re.search(r'Statements\s+:\s+(\d+\.\d+)%', output)
        if match:
            return {
                'percentage': round(float(match.group(1)), 2),
                'test_count': 0,  # 需要从其他方式获取
            }
    except Exception as e:
        print(f"获取前端覆盖率失败: {e}")
    
    return {'percentage': 0, 'test_count': 0}


def update_backend_coverage(status: Dict[str, Any]) -> None:
    """更新后端测试覆盖率"""
    coverage = get_backend_coverage()
    status['backend']['testing']['percentage'] = coverage['percentage']
    print(f"✅ 后端测试覆盖率: {coverage['percentage']}%")


def update_frontend_coverage(status: Dict[str, Any]) -> None:
    """更新前端测试覆盖率"""
    coverage = get_frontend_coverage()
    status['frontend']['testing']['percentage'] = coverage['percentage']
    print(f"✅ 前端测试覆盖率: {coverage['percentage']}%")


def main():
    """主函数"""
    update_backend = '--backend' in sys.argv
    update_frontend = '--frontend' in sys.argv
    
    if not update_backend and not update_frontend:
        update_backend = True
        update_frontend = True
    
    status = load_status()
    
    if update_backend:
        print("📊 获取后端测试覆盖率...")
        update_backend_coverage(status)
    
    if update_frontend:
        print("📊 获取前端测试覆盖率...")
        update_frontend_coverage(status)
    
    save_status(status)
    print("✅ 测试覆盖率已更新到 PROJECT_STATUS.json")


if __name__ == '__main__':
    main()

