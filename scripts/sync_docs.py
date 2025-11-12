#!/usr/bin/env python3
"""
文档同步脚本

从统一数据源（docs/PROJECT_STATUS.json）同步数据到各个文档文件。
确保所有文档中的完成度数据保持一致。

使用方法:
    python scripts/sync_docs.py [--dry-run] [--update-status]

选项:
    --dry-run: 只显示将要进行的更改，不实际修改文件
    --update-status: 更新PROJECT_STATUS.json（从实际代码统计）
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
STATUS_FILE = DOCS_DIR / "PROJECT_STATUS.json"

# 需要同步的文档文件
DOC_FILES = [
    "PROGRESS.md",
    "09-功能模块完成度报告.md",
    "10-未完成功能清单.md",
    "18-项目完整度评估报告.md",
]


def load_status() -> Dict[str, Any]:
    """加载统一数据源"""
    if not STATUS_FILE.exists():
        raise FileNotFoundError(f"状态文件不存在: {STATUS_FILE}")
    
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_status(data: Dict[str, Any]) -> None:
    """保存统一数据源"""
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_progress_md(status: Dict[str, Any], dry_run: bool = False) -> List[str]:
    """更新PROGRESS.md"""
    file_path = PROJECT_ROOT / "PROGRESS.md"
    if not file_path.exists():
        return [f"文件不存在: {file_path}"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = []
    
    # 更新前端进度
    backend_test = status['backend']['testing']['percentage']
    frontend_dev = status['frontend']['development']['percentage']
    frontend_test = status['frontend']['testing']['percentage']
    
    # 替换前端进度描述
    pattern = r'- \*\*前端进度\*\*:.*'
    replacement = f"- **前端进度**: {frontend_dev}% (基础框架和核心功能已完成)"
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        changes.append(f"更新前端进度: {frontend_dev}%")
    
    # 更新测试覆盖率
    pattern = r'\| 前端界面 \|.*\|.*\|'
    replacement = f"| 前端界面 | ✅ 部分完成 | {frontend_dev}% |"
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        changes.append(f"更新前端界面状态: {frontend_dev}%")
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes


def update_completion_report(status: Dict[str, Any], dry_run: bool = False) -> List[str]:
    """更新09-功能模块完成度报告.md"""
    file_path = DOCS_DIR / "09-功能模块完成度报告.md"
    if not file_path.exists():
        return [f"文件不存在: {file_path}"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = []
    
    # 更新总体完成度进度条
    overall = status['overall_progress']['percentage']
    backend_dev = status['backend']['development']['percentage']
    backend_test = status['backend']['testing']['percentage']
    frontend_dev = status['frontend']['development']['percentage']
    frontend_test = status['frontend']['testing']['percentage']
    
    # 更新进度条
    pattern = r'```\n总体进度:.*\n后端开发:.*\n后端测试:.*\n前端开发:.*\n前端测试:.*\n```'
    replacement = f"""```
总体进度: {'█' * (overall // 10)}{'░' * (10 - overall // 10)} {overall}%
后端开发: {'█' * 10} {backend_dev}%
后端测试: {'█' * (backend_test // 10)}{'░' * (10 - backend_test // 10)} {backend_test}%
前端开发: {'█' * (frontend_dev // 10)}{'░' * (10 - frontend_dev // 10)} {frontend_dev}%
前端测试: {'░' * 10} {frontend_test}%
```"""
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        changes.append(f"更新总体完成度进度条")
    
    # 更新统计数据
    pattern = r'- \*\*代码覆盖率\*\*:.*'
    replacement = f"- **代码覆盖率**: 约{backend_test}%（后端，目标：≥80%）"
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        changes.append(f"更新代码覆盖率: {backend_test}%")
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes


def update_pending_list(status: Dict[str, Any], dry_run: bool = False) -> List[str]:
    """更新10-未完成功能清单.md"""
    file_path = DOCS_DIR / "10-未完成功能清单.md"
    if not file_path.exists():
        return [f"文件不存在: {file_path}"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = []
    
    # 更新总体完成度
    overall = status['overall_progress']['percentage']
    backend_dev = status['backend']['development']['percentage']
    backend_test = status['backend']['testing']['percentage']
    frontend_dev = status['frontend']['development']['percentage']
    frontend_test = status['frontend']['testing']['percentage']
    
    # 更新进度条
    pattern = r'```\n总体进度:.*\n后端开发:.*\n后端测试:.*\n前端开发:.*\n```'
    replacement = f"""```
总体进度: {'█' * (overall // 10)}{'░' * (10 - overall // 10)} {overall}%
后端开发: {'█' * 10} {backend_dev}%
后端测试: {'█' * (backend_test // 10)}{'░' * (10 - backend_test // 10)} {backend_test}%
前端开发: {'█' * (frontend_dev // 10)}{'░' * (10 - frontend_dev // 10)} {frontend_dev}%
```"""
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        changes.append(f"更新总体完成度进度条")
    
    # 更新总体评价
    pattern = r'\*\*前端开发完成度\*\*:.*\n\*\*总体完成度\*\*:.*'
    replacement = f"""**后端开发完成度**: {backend_dev}%  
**后端测试完成度**: {backend_test}%  
**前端开发完成度**: {frontend_dev}%  
**前端测试完成度**: {frontend_test}%  
**总体完成度**: {overall}%"""
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        changes.append(f"更新总体评价")
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes


def sync_all_docs(dry_run: bool = False) -> Dict[str, List[str]]:
    """同步所有文档"""
    status = load_status()
    
    results = {}
    
    # 更新各个文档
    results['PROGRESS.md'] = update_progress_md(status, dry_run)
    results['09-功能模块完成度报告.md'] = update_completion_report(status, dry_run)
    results['10-未完成功能清单.md'] = update_pending_list(status, dry_run)
    
    return results


def main():
    """主函数"""
    dry_run = '--dry-run' in sys.argv
    update_status = '--update-status' in sys.argv
    
    if dry_run:
        print("🔍 干运行模式：只显示将要进行的更改，不实际修改文件\n")
    
    # 同步文档
    results = sync_all_docs(dry_run=dry_run)
    
    # 显示结果
    print("📝 文档同步结果：\n")
    for file, changes in results.items():
        if changes:
            print(f"✅ {file}:")
            for change in changes:
                print(f"   - {change}")
        else:
            print(f"⏭️  {file}: 无需更新")
    
    if not dry_run:
        print("\n✅ 文档同步完成！")
    else:
        print("\n💡 这是预览模式，使用不带 --dry-run 参数运行以实际更新文件")


if __name__ == '__main__':
    main()

