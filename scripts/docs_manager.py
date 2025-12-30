#!/usr/bin/env python3
"""
文档管理工具

功能:
1. 扫描所有文档，提取元数据
2. 检查文档是否过期（超过30天未更新）
3. 生成文档索引文件
4. 验证文档与代码的关联性
5. 生成文档更新报告

使用:
    python scripts/docs_manager.py scan        # 扫描文档
    python scripts/docs_manager.py index       # 生成索引
    python scripts/docs_manager.py check       # 检查过期文档
    python scripts/docs_manager.py report      # 生成报告
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class DocumentMetadata:
    """文档元数据"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.title = ""
        self.version = ""
        self.created = None
        self.last_updated = None
        self.status = "unknown"
        self.author = ""
        self.reviewers = []
        self.related_code = []
        self.tags = []
        
        self._extract_metadata()
    
    def _extract_metadata(self):
        """从文档中提取元数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取YAML front matter
            yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                try:
                    metadata = yaml.safe_load(yaml_match.group(1))
                    self.title = metadata.get('title', '')
                    self.version = metadata.get('version', '')
                    self.created = self._parse_date(metadata.get('created'))
                    self.last_updated = self._parse_date(metadata.get('last_updated'))
                    self.status = metadata.get('status', 'unknown')
                    self.author = metadata.get('author', '')
                    self.reviewers = metadata.get('reviewers', [])
                    self.related_code = metadata.get('related_code', [])
                    self.tags = metadata.get('tags', [])
                except yaml.YAMLError:
                    pass
            
            # 如果没有元数据，尝试从Git获取
            if not self.last_updated:
                self.last_updated = self._get_git_last_modified()
            
            # 如果没有标题，从文件名提取
            if not self.title:
                self.title = self.file_path.stem.replace('-', ' ').replace('_', ' ')
        
        except Exception as e:
            print(f"⚠️  读取文档失败: {self.file_path} - {e}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d')
        except ValueError:
            return None
    
    def _get_git_last_modified(self) -> Optional[datetime]:
        """从Git获取最后修改时间"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cd', '--date=iso', str(self.file_path)],
                capture_output=True,
                text=True,
                cwd=self.file_path.parent
            )
            if result.returncode == 0 and result.stdout.strip():
                date_str = result.stdout.strip()
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
        except Exception:
            pass
        return None
    
    def is_outdated(self, days: int = 30) -> bool:
        """检查文档是否过期"""
        if not self.last_updated:
            return True
        return (datetime.now() - self.last_updated).days > days
    
    def get_status_emoji(self) -> str:
        """获取状态表情"""
        emoji_map = {
            'active': '✅',
            'outdated': '⚠️',
            'deprecated': '❌',
            'draft': '🚧',
            'archived': '📦',
            'unknown': '❓'
        }
        return emoji_map.get(self.status, '❓')
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'file_path': str(self.file_path),
            'title': self.title,
            'version': self.version,
            'created': self.created.isoformat() if self.created else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': self.status,
            'author': self.author,
            'reviewers': self.reviewers,
            'related_code': self.related_code,
            'tags': self.tags,
            'is_outdated': self.is_outdated()
        }


class DocumentManager:
    """文档管理器"""
    
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.documents: List[DocumentMetadata] = []
    
    def scan_documents(self):
        """扫描所有文档"""
        print("🔍 扫描文档目录...")
        
        # 排除的目录
        exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', 'htmlcov'}
        
        for md_file in self.docs_root.rglob('*.md'):
            # 跳过排除目录
            if any(excluded in md_file.parts for excluded in exclude_dirs):
                continue
            
            doc = DocumentMetadata(md_file)
            self.documents.append(doc)
        
        print(f"✅ 找到 {len(self.documents)} 个文档")
    
    def generate_index(self, output_path: Path):
        """生成文档索引"""
        print("📝 生成文档索引...")
        
        # 按分类组织文档
        categories = {}
        for doc in self.documents:
            # 获取相对路径的第一级目录作为分类
            rel_path = doc.file_path.relative_to(self.docs_root)
            if len(rel_path.parts) > 1:
                category = rel_path.parts[0]
            else:
                category = "根目录"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(doc)
        
        # 生成Markdown索引
        lines = [
            "# CozyChat 文档索引",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**文档总数**: {len(self.documents)} 篇",
            "",
            "## 📊 文档状态概览",
            ""
        ]
        
        # 统计状态
        status_counts = {}
        outdated_count = 0
        for doc in self.documents:
            status_counts[doc.status] = status_counts.get(doc.status, 0) + 1
            if doc.is_outdated():
                outdated_count += 1
        
        lines.extend([
            f"- ✅ 活跃文档: {status_counts.get('active', 0)} 篇",
            f"- ⚠️ 待更新文档: {outdated_count} 篇",
            f"- ❌ 已废弃文档: {status_counts.get('deprecated', 0)} 篇",
            f"- 🚧 草稿文档: {status_counts.get('draft', 0)} 篇",
            "",
        ])
        
        # 生成分类文档列表
        for category, docs in sorted(categories.items()):
            lines.extend([
                f"## 📁 {category}",
                "",
                "| 文档 | 版本 | 状态 | 最后更新 | 说明 |",
                "|------|------|------|----------|------|"
            ])
            
            # 按更新时间排序
            sorted_docs = sorted(
                docs,
                key=lambda d: d.last_updated or datetime.min,
                reverse=True
            )
            
            for doc in sorted_docs:
                rel_path = doc.file_path.relative_to(self.docs_root)
                last_updated = doc.last_updated.strftime('%Y-%m-%d') if doc.last_updated else '未知'
                
                # 标记过期文档
                outdated_mark = " ⏰" if doc.is_outdated() else ""
                
                lines.append(
                    f"| [{doc.title}]({rel_path}) | "
                    f"{doc.version or '-'} | "
                    f"{doc.get_status_emoji()} | "
                    f"{last_updated}{outdated_mark} | "
                    f"{', '.join(doc.tags[:2]) if doc.tags else '-'} |"
                )
            
            lines.append("")
        
        # 添加过期文档警告
        outdated_docs = [d for d in self.documents if d.is_outdated()]
        if outdated_docs:
            lines.extend([
                "## ⚠️ 需要更新的文档（超过30天未更新）",
                ""
            ])
            
            for i, doc in enumerate(outdated_docs[:10], 1):
                days = (datetime.now() - doc.last_updated).days if doc.last_updated else 999
                rel_path = doc.file_path.relative_to(self.docs_root)
                lines.append(f"{i}. **{doc.title}** ({days}天未更新)")
                lines.append(f"   - 路径: `{rel_path}`")
                if doc.related_code:
                    lines.append(f"   - 关联代码: `{doc.related_code[0]}`")
                lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ 索引已生成: {output_path}")
    
    def check_outdated(self):
        """检查过期文档"""
        print("🔍 检查过期文档...")
        
        outdated_docs = [d for d in self.documents if d.is_outdated()]
        
        if not outdated_docs:
            print("✅ 所有文档都是最新的！")
            return
        
        print(f"\n⚠️  发现 {len(outdated_docs)} 个过期文档（超过30天未更新）:\n")
        
        for doc in sorted(outdated_docs, key=lambda d: d.last_updated or datetime.min):
            days = (datetime.now() - doc.last_updated).days if doc.last_updated else 999
            rel_path = doc.file_path.relative_to(self.docs_root)
            print(f"  - {doc.title}")
            print(f"    路径: {rel_path}")
            print(f"    最后更新: {days}天前")
            if doc.related_code:
                print(f"    关联代码: {doc.related_code[0]}")
            print()
    
    def generate_report(self, output_path: Path):
        """生成详细报告"""
        print("📊 生成文档报告...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(self.documents),
            'documents': [doc.to_dict() for doc in self.documents],
            'statistics': {
                'by_status': {},
                'by_category': {},
                'outdated_count': 0
            }
        }
        
        # 统计
        for doc in self.documents:
            # 按状态统计
            status = doc.status
            report['statistics']['by_status'][status] = \
                report['statistics']['by_status'].get(status, 0) + 1
            
            # 按分类统计
            rel_path = doc.file_path.relative_to(self.docs_root)
            category = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
            report['statistics']['by_category'][category] = \
                report['statistics']['by_category'].get(category, 0) + 1
            
            # 过期统计
            if doc.is_outdated():
                report['statistics']['outdated_count'] += 1
        
        # 写入JSON报告
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 报告已生成: {output_path}")
        
        # 打印摘要
        print("\n📊 统计摘要:")
        print(f"  总文档数: {report['total_documents']}")
        print(f"  过期文档: {report['statistics']['outdated_count']}")
        print("\n  按状态分布:")
        for status, count in report['statistics']['by_status'].items():
            emoji = DocumentMetadata(Path('.')).get_status_emoji()
            print(f"    {status}: {count}")


def main():
    import sys
    
    # 获取命令
    command = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_root = project_root / 'docs'
    
    # 创建管理器
    manager = DocumentManager(docs_root)
    
    # 执行命令
    if command == 'scan':
        manager.scan_documents()
        print(f"\n✅ 扫描完成! 共找到 {len(manager.documents)} 个文档")
    
    elif command == 'index':
        manager.scan_documents()
        output_path = docs_root / 'INDEX.md'
        manager.generate_index(output_path)
    
    elif command == 'check':
        manager.scan_documents()
        manager.check_outdated()
    
    elif command == 'report':
        manager.scan_documents()
        output_path = docs_root / 'DOCS_REPORT.json'
        manager.generate_report(output_path)
    
    else:
        print(f"❌ 未知命令: {command}")
        print("\n使用方法:")
        print("  python scripts/docs_manager.py scan        # 扫描文档")
        print("  python scripts/docs_manager.py index       # 生成索引")
        print("  python scripts/docs_manager.py check       # 检查过期文档")
        print("  python scripts/docs_manager.py report      # 生成报告")


if __name__ == '__main__':
    main()

