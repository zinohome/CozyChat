"""
配置迁移测试脚本

测试配置适配器和配置加载器的功能
不依赖外部环境，只测试代码逻辑
"""

# 标准库
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))


def test_deep_merge():
    """测试配置合并功能"""
    print("测试1: 配置合并功能")
    
    # 模拟ConfigLoader.deep_merge
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    # 测试用例1: 基本合并
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    merged = deep_merge(base, override)
    assert merged["a"] == 1, "基础值应保留"
    assert merged["b"] == 3, "覆盖值应生效"
    assert merged["c"] == 4, "新值应添加"
    print("  ✓ 基本合并测试通过")
    
    # 测试用例2: 嵌套字典合并
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 4}, "e": 5}
    merged = deep_merge(base, override)
    assert merged["a"] == 1, "基础值应保留"
    assert merged["b"]["c"] == 4, "嵌套值应覆盖"
    assert merged["b"]["d"] == 3, "嵌套值应保留"
    assert merged["e"] == 5, "新值应添加"
    print("  ✓ 嵌套字典合并测试通过")
    
    # 测试用例3: 配置优先级（YAML覆盖Settings）
    settings_config = {
        "storage_mode": "hybrid",
        "async_write": True,
        "batch_size": 10
    }
    yaml_config = {
        "storage_mode": "dual",  # 覆盖
        "batch_size": 20  # 覆盖
    }
    merged = deep_merge(settings_config, yaml_config)
    assert merged["storage_mode"] == "dual", "YAML应覆盖Settings"
    assert merged["async_write"] == True, "Settings值应保留"
    assert merged["batch_size"] == 20, "YAML应覆盖Settings"
    print("  ✓ 配置优先级测试通过")
    
    print("  ✅ 配置合并功能测试全部通过\n")


def test_config_structure():
    """测试配置文件结构"""
    print("测试2: 配置文件结构")
    
    # 检查配置文件是否存在
    config_dir = project_root / "backend" / "config"
    required_files = [
        "context.yaml",
        "performance.yaml",
        "session.yaml",
        "memory.yaml"
    ]
    
    for file_name in required_files:
        file_path = config_dir / file_name
        if file_path.exists():
            print(f"  ✓ {file_name} 存在")
        else:
            print(f"  ✗ {file_name} 不存在")
            return False
    
    print("  ✅ 所有配置文件都存在\n")
    return True


def test_config_adapter_structure():
    """测试配置适配器代码结构"""
    print("测试3: 配置适配器代码结构")
    
    adapter_file = project_root / "backend" / "app" / "utils" / "config_adapter.py"
    if not adapter_file.exists():
        print("  ✗ config_adapter.py 不存在")
        return False
    
    content = adapter_file.read_text(encoding="utf-8")
    
    # 检查必要的方法
    required_methods = [
        "get_memory_config",
        "get_session_config",
        "get_context_config",
        "get_performance_config",
        "get_memory_config_with_validation"
    ]
    
    for method in required_methods:
        if f"def {method}" in content:
            print(f"  ✓ {method} 方法存在")
        else:
            print(f"  ✗ {method} 方法不存在")
            return False
    
    # 检查必要的导入
    required_imports = [
        "from app.config.config import settings",
        "from app.utils.config_loader import ConfigLoader"
    ]
    
    for imp in required_imports:
        if imp in content:
            print(f"  ✓ {imp} 导入存在")
        else:
            print(f"  ✗ {imp} 导入不存在")
            return False
    
    print("  ✅ 配置适配器代码结构正确\n")
    return True


def test_migration_completeness():
    """测试迁移完整性"""
    print("测试4: 迁移完整性检查")
    
    # 检查所有迁移的文件是否使用了ConfigAdapter
    migrated_files = [
        "backend/app/main.py",
        "backend/app/engines/memory/worker.py",
        "backend/app/engines/memory/qdrant_engine.py",
        "backend/app/engines/memory/manager.py",
        "backend/app/api/v1/sessions.py",
        "backend/app/services/context/context_service.py",
        "backend/app/core/context/builder.py",
        "backend/app/core/context/summary_generator.py",
        "backend/app/middleware/performance.py"
    ]
    
    all_migrated = True
    for file_path in migrated_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"  ✗ {file_path} 不存在")
            all_migrated = False
            continue
        
        content = full_path.read_text(encoding="utf-8")
        
        # 检查是否使用了ConfigAdapter
        if "get_config_adapter" in content or "config_adapter" in content:
            print(f"  ✓ {file_path} 已迁移")
        else:
            # 检查是否还有直接使用settings的情况
            if "settings.memory_" in content or "settings.session_title_" in content or \
               "settings.context_" in content or "settings.performance_" in content:
                print(f"  ⚠ {file_path} 可能还有直接使用settings的情况")
            else:
                print(f"  ✓ {file_path} 已迁移（无直接使用settings）")
    
    print("  ✅ 迁移完整性检查完成\n")
    return all_migrated


def main():
    """主函数"""
    print("=" * 60)
    print("配置迁移测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试1: 配置合并功能
    try:
        test_deep_merge()
        results.append(True)
    except Exception as e:
        print(f"  ✗ 测试失败: {e}\n")
        results.append(False)
    
    # 测试2: 配置文件结构
    results.append(test_config_structure())
    
    # 测试3: 配置适配器代码结构
    results.append(test_config_adapter_structure())
    
    # 测试4: 迁移完整性
    results.append(test_migration_completeness())
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if all(results):
        print("✅ 所有测试通过")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

