#!/usr/bin/env python3
"""
文档同步检查脚本

检查项目文档与代码实现的一致性，生成同步报告。

使用方法：
    python scripts/sync_docs.py
    python scripts/sync_docs.py --fix  # 自动修复可修复的问题
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DocumentSyncChecker:
    """文档同步检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "backend"
        self.frontend_root = project_root / "frontend"
        self.docs_root = project_root / "docs"
        
        self.issues = defaultdict(list)
        self.stats = {
            "total_docs": 0,
            "checked_docs": 0,
            "issues_found": 0,
            "outdated_docs": 0,
            "missing_docs": 0,
        }
    
    def check_all(self) -> Dict:
        """执行所有检查"""
        print("🔍 开始文档同步检查...\n")
        
        # 1. 统计文档数量
        self._count_documents()
        
        # 2. 检查核心架构文档
        print("📋 检查核心架构文档...")
        self._check_architecture_docs()
        
        # 3. 检查API文档
        print("📋 检查API文档...")
        self._check_api_docs()
        
        # 4. 检查数据库文档
        print("📋 检查数据库文档...")
        self._check_database_docs()
        
        # 5. 检查开发规范文档
        print("📋 检查开发规范文档...")
        self._check_dev_guidelines()
        
        # 6. 检查测试文档
        print("📋 检查测试文档...")
        self._check_test_docs()
        
        # 7. 检查过时文档
        print("📋 检查过时文档...")
        self._check_outdated_docs()
        
        # 8. 检查缺失文档
        print("📋 检查缺失文档...")
        self._check_missing_docs()
        
        # 9. 生成报告
        return self._generate_report()
    
    def _count_documents(self):
        """统计文档数量"""
        if self.docs_root.exists():
            md_files = list(self.docs_root.rglob("*.md"))
            self.stats["total_docs"] = len(md_files)
            print(f"📊 发现 {len(md_files)} 个文档文件\n")
    
    def _check_architecture_docs(self):
        """检查架构文档"""
        # 检查后端架构文档
        backend_arch_doc = self.docs_root / "02-后端架构设计.md"
        if backend_arch_doc.exists():
            self.stats["checked_docs"] += 1
            content = backend_arch_doc.read_text(encoding="utf-8")
            
            # 检查关键模块是否在文档中提及
            modules_to_check = [
                ("services", "服务层"),
                ("engines", "引擎层"),
                ("core", "核心业务"),
                ("api", "API接口"),
            ]
            
            for module, desc in modules_to_check:
                module_path = self.backend_root / "app" / module
                if module_path.exists() and module not in content.lower():
                    self.issues["architecture"].append({
                        "type": "missing_content",
                        "doc": str(backend_arch_doc.name),
                        "message": f"后端架构文档缺少{desc}({module})的描述"
                    })
        else:
            self.issues["architecture"].append({
                "type": "missing_doc",
                "message": "缺少后端架构设计文档"
            })
        
        # 检查前端架构文档
        frontend_arch_doc = self.docs_root / "03-前端架构设计.md"
        if frontend_arch_doc.exists():
            self.stats["checked_docs"] += 1
        else:
            self.issues["architecture"].append({
                "type": "missing_doc",
                "message": "缺少前端架构设计文档"
            })
    
    def _check_api_docs(self):
        """检查API文档"""
        api_doc = self.docs_root / "04-API接口设计.md"
        
        if not api_doc.exists():
            self.issues["api"].append({
                "type": "missing_doc",
                "message": "缺少API接口设计文档"
            })
            return
        
        self.stats["checked_docs"] += 1
        content = api_doc.read_text(encoding="utf-8")
        
        # 检查API路由文件
        api_dir = self.backend_root / "app" / "api" / "v1"
        if api_dir.exists():
            api_files = [f for f in api_dir.glob("*.py") if f.stem not in ["__init__", "deps"]]
            
            for api_file in api_files:
                module_name = api_file.stem
                # 检查API文档中是否提及该模块
                if module_name not in content.lower():
                    self.issues["api"].append({
                        "type": "missing_content",
                        "doc": api_doc.name,
                        "message": f"API文档未包含 {module_name} 模块的接口说明"
                    })
    
    def _check_database_docs(self):
        """检查数据库文档"""
        db_doc = self.docs_root / "05-数据库设计.md"
        
        if not db_doc.exists():
            self.issues["database"].append({
                "type": "missing_doc",
                "message": "缺少数据库设计文档"
            })
            return
        
        self.stats["checked_docs"] += 1
        content = db_doc.read_text(encoding="utf-8")
        
        # 检查数据库模型文件
        models_dir = self.backend_root / "app" / "models"
        if models_dir.exists():
            model_files = [f for f in models_dir.glob("*.py") if f.stem not in ["__init__", "base"]]
            
            for model_file in model_files:
                model_name = model_file.stem
                # 检查数据库文档中是否提及该模型
                if model_name not in content.lower():
                    self.issues["database"].append({
                        "type": "missing_content",
                        "doc": db_doc.name,
                        "message": f"数据库文档未包含 {model_name} 模型的设计说明"
                    })
    
    def _check_dev_guidelines(self):
        """检查开发规范文档"""
        dev_doc = self.docs_root / "06-开发规范.md"
        
        if dev_doc.exists():
            self.stats["checked_docs"] += 1
            content = dev_doc.read_text(encoding="utf-8")
            
            # 检查关键规范是否包含
            required_sections = [
                ("Python开发规范", "backend"),
                ("React开发规范", "frontend"),
                ("代码风格", "style"),
                ("测试规范", "test"),
            ]
            
            for section, keyword in required_sections:
                if keyword not in content.lower():
                    self.issues["guidelines"].append({
                        "type": "missing_section",
                        "doc": dev_doc.name,
                        "message": f"开发规范文档缺少 {section} 章节"
                    })
        else:
            self.issues["guidelines"].append({
                "type": "missing_doc",
                "message": "缺少开发规范文档"
            })
    
    def _check_test_docs(self):
        """检查测试文档"""
        test_doc = self.docs_root / "07-测试规范.md"
        
        if test_doc.exists():
            self.stats["checked_docs"] += 1
        else:
            self.issues["testing"].append({
                "type": "missing_doc",
                "message": "缺少测试规范文档"
            })
    
    def _check_outdated_docs(self):
        """检查过时文档"""
        # 检查临时/过渡性文档
        outdated_patterns = [
            r"\d+-项目.*评估",
            r"\d+-.*分析报告",
            r".*修复.*总结",
            r".*实施总结",
            r".*完成报告",
        ]
        
        if not self.docs_root.exists():
            return
        
        for doc_file in self.docs_root.glob("*.md"):
            filename = doc_file.name
            
            # 跳过核心文档
            if filename.startswith(("00-", "01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-")):
                continue
            
            # 检查是否匹配过时文档模式
            for pattern in outdated_patterns:
                if re.match(pattern, filename):
                    self.issues["outdated"].append({
                        "type": "outdated_doc",
                        "doc": filename,
                        "message": f"可能是过时的临时文档，建议归档或删除"
                    })
                    self.stats["outdated_docs"] += 1
                    break
    
    def _check_missing_docs(self):
        """检查缺失文档"""
        required_docs = [
            ("README.md", "项目主README"),
            ("docs/00-实施路线图.md", "实施路线图"),
            ("docs/01-项目概述.md", "项目概述"),
            ("docs/02-后端架构设计.md", "后端架构设计"),
            ("docs/03-前端架构设计.md", "前端架构设计"),
            ("docs/04-API接口设计.md", "API接口设计"),
            ("docs/05-数据库设计.md", "数据库设计"),
            ("docs/06-开发规范.md", "开发规范"),
            ("docs/07-测试规范.md", "测试规范"),
            ("backend/README.md", "后端README"),
            ("frontend/README.md", "前端README"),
        ]
        
        for doc_path, doc_name in required_docs:
            full_path = self.project_root / doc_path
            if not full_path.exists():
                self.issues["missing"].append({
                    "type": "missing_doc",
                    "doc": doc_path,
                    "message": f"缺少{doc_name}"
                })
                self.stats["missing_docs"] += 1
    
    def _generate_report(self) -> Dict:
        """生成检查报告"""
        # 统计问题总数
        total_issues = sum(len(issues) for issues in self.issues.values())
        self.stats["issues_found"] = total_issues
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "issues": dict(self.issues),
            "summary": self._generate_summary()
        }
        
        return report
    
    def _generate_summary(self) -> str:
        """生成摘要"""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("📊 文档同步检查报告")
        lines.append("="*70)
        lines.append(f"\n统计信息:")
        lines.append(f"  总文档数: {self.stats['total_docs']}")
        lines.append(f"  已检查: {self.stats['checked_docs']}")
        lines.append(f"  发现问题: {self.stats['issues_found']}")
        lines.append(f"  过时文档: {self.stats['outdated_docs']}")
        lines.append(f"  缺失文档: {self.stats['missing_docs']}")
        
        if self.stats['issues_found'] == 0:
            lines.append("\n✅ 文档与代码完全同步！")
        else:
            lines.append(f"\n⚠️  发现 {self.stats['issues_found']} 个问题需要处理")
            
            # 按类别列出问题
            for category, issues in self.issues.items():
                if issues:
                    lines.append(f"\n{category.upper()} ({len(issues)} 个问题):")
                    for issue in issues:
                        lines.append(f"  - {issue['message']}")
        
        lines.append("\n" + "="*70)
        return "\n".join(lines)


def save_report(report: Dict, output_file: Path):
    """保存报告到文件"""
    # 保存JSON格式
    json_file = output_file.with_suffix(".json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 保存Markdown格式
    md_file = output_file.with_suffix(".md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(report["summary"])
    
    print(f"\n📄 报告已保存:")
    print(f"  JSON: {json_file}")
    print(f"  Markdown: {md_file}")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    # 创建检查器
    checker = DocumentSyncChecker(project_root)
    
    # 执行检查
    report = checker.check_all()
    
    # 打印摘要
    print(report["summary"])
    
    # 保存报告
    output_file = project_root / "docs" / "文档同步检查报告"
    save_report(report, output_file)
    
    # 返回退出码
    return 0 if report["stats"]["issues_found"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
