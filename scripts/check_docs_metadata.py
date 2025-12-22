#!/usr/bin/env python3
"""
文档元数据检查脚本（用于pre-commit hook）

功能:
1. 检查提交的.md文件是否包含必要的元数据
2. 验证last_updated字段是否更新
3. 确保文档状态合理

使用:
    python scripts/check_docs_metadata.py [file1.md file2.md ...]
"""

import re
import sys
import yaml
from pathlib import Path
from datetime import datetime


def check_document_metadata(file_path: Path) -> tuple[bool, list[str]]:
    """
    检查文档元数据
    
    Returns:
        (is_valid, errors): 是否有效，错误列表
    """
    errors = []
    
    # 跳过非docs目录的文件
    if 'docs' not in file_path.parts:
        return True, []
    
    # 跳过特殊文件
    skip_files = {'INDEX.md', 'README.md', 'DOCS_REPORT.json', '.template.md'}
    if file_path.name in skip_files:
        return True, []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"无法读取文件: {e}")
        return False, errors
    
    # 检查是否有YAML front matter
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        errors.append("缺少YAML元数据区块（---开头和结尾）")
        return False, errors
    
    # 解析YAML
    try:
        metadata = yaml.safe_load(yaml_match.group(1))
    except yaml.YAMLError as e:
        errors.append(f"YAML格式错误: {e}")
        return False, errors
    
    # 检查必需字段
    required_fields = ['title', 'version', 'last_updated', 'status']
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            errors.append(f"缺少必需字段: {field}")
    
    # 检查last_updated格式
    if 'last_updated' in metadata:
        last_updated = str(metadata['last_updated'])
        try:
            datetime.strptime(last_updated, '%Y-%m-%d')
        except ValueError:
            errors.append(f"last_updated格式错误: {last_updated}，应为YYYY-MM-DD")
    
    # 检查status值
    valid_statuses = ['active', 'outdated', 'deprecated', 'draft', 'archived']
    if 'status' in metadata:
        if metadata['status'] not in valid_statuses:
            errors.append(
                f"status值无效: {metadata['status']}，"
                f"应为: {', '.join(valid_statuses)}"
            )
    
    # 检查version格式（建议使用semantic versioning）
    if 'version' in metadata:
        version = str(metadata['version'])
        if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
            errors.append(
                f"version格式建议使用语义化版本: {version}，"
                "如 1.0.0 或 1.0"
            )
    
    return len(errors) == 0, errors


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_docs_metadata.py [file1.md file2.md ...]")
        sys.exit(0)
    
    files = [Path(f) for f in sys.argv[1:] if f.endswith('.md')]
    
    if not files:
        print("✅ 没有需要检查的Markdown文件")
        sys.exit(0)
    
    print(f"🔍 检查 {len(files)} 个文档的元数据...")
    print()
    
    has_errors = False
    
    for file_path in files:
        is_valid, errors = check_document_metadata(file_path)
        
        if not is_valid:
            has_errors = True
            print(f"❌ {file_path}")
            for error in errors:
                print(f"   - {error}")
            print()
        else:
            print(f"✅ {file_path}")
    
    if has_errors:
        print("\n⚠️  发现文档元数据问题！")
        print("\n💡 修复建议:")
        print("   1. 参考 docs/.template.md 添加元数据")
        print("   2. 确保包含所有必需字段: title, version, last_updated, status")
        print("   3. last_updated 格式为 YYYY-MM-DD")
        print("   4. status 为: active, outdated, deprecated, draft, archived")
        print()
        sys.exit(1)
    else:
        print("\n✅ 所有文档元数据检查通过！")
        sys.exit(0)


if __name__ == '__main__':
    main()

