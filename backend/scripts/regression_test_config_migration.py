"""
配置迁移回归测试脚本

测试配置迁移后，现有功能是否正常工作
不依赖pytest，可以直接运行
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))


def test_config_loader_new_methods():
    """测试：ConfigLoader新增方法"""
    print("测试1: ConfigLoader新增方法")
    
    try:
        from app.utils.config_loader import ConfigLoader, get_config_loader
        
        loader = get_config_loader()
        
        # 测试load_context_config
        try:
            context_config = loader.load_context_config()
            print(f"  ✓ load_context_config() 成功: {type(context_config)}")
        except Exception as e:
            print(f"  ⚠ load_context_config() 失败（可能文件不存在）: {e}")
        
        # 测试load_performance_config
        try:
            performance_config = loader.load_performance_config()
            print(f"  ✓ load_performance_config() 成功: {type(performance_config)}")
        except Exception as e:
            print(f"  ⚠ load_performance_config() 失败（可能文件不存在）: {e}")
        
        # 测试resolve_env_placeholders
        test_config = {"url": "${QDRANT_URL}", "key": "test_value"}
        resolved = loader.resolve_env_placeholders(test_config)
        print(f"  ✓ resolve_env_placeholders() 成功")
        print(f"    输入: {test_config}")
        print(f"    输出: {resolved}")
        
        # 测试deep_merge
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"c": 3}, "d": 4}
        merged = ConfigLoader.deep_merge(base, override)
        assert merged["a"] == 1
        assert merged["b"]["c"] == 3
        assert merged["d"] == 4
        print(f"  ✓ deep_merge() 成功")
        print(f"    base: {base}")
        print(f"    override: {override}")
        print(f"    merged: {merged}")
        
        print("  ✅ ConfigLoader新增方法测试通过\n")
        return True
        
    except Exception as e:
        print(f"  ✗ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config_adapter_basic():
    """测试：ConfigAdapter基本功能"""
    print("测试2: ConfigAdapter基本功能")
    
    try:
        from app.utils.config_adapter import ConfigAdapter, get_config_adapter
        
        adapter = get_config_adapter()
        
        # 测试get_memory_config
        memory_config = adapter.get_memory_config()
        assert isinstance(memory_config, dict)
        assert "storage_mode" in memory_config or "async_write" in memory_config
        print(f"  ✓ get_memory_config() 成功")
        print(f"    配置项: {list(memory_config.keys())[:5]}...")
        
        # 测试get_session_config
        session_config = adapter.get_session_config()
        assert isinstance(session_config, dict)
        print(f"  ✓ get_session_config() 成功")
        
        # 测试get_context_config
        context_config = adapter.get_context_config()
        assert isinstance(context_config, dict)
        print(f"  ✓ get_context_config() 成功")
        
        # 测试get_performance_config
        performance_config = adapter.get_performance_config()
        assert isinstance(performance_config, dict)
        print(f"  ✓ get_performance_config() 成功")
        
        # 测试缓存
        memory_config1 = adapter.get_memory_config()
        memory_config2 = adapter.get_memory_config()
        assert memory_config1 == memory_config2
        print(f"  ✓ 配置缓存功能正常")
        
        print("  ✅ ConfigAdapter基本功能测试通过\n")
        return True
        
    except Exception as e:
        print(f"  ✗ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """测试：向后兼容性"""
    print("测试3: 向后兼容性")
    
    try:
        from app.config.config import settings
        from app.utils.config_adapter import get_config_adapter
        
        # 验证Settings中的配置项仍然存在
        assert hasattr(settings, 'memory_storage_mode')
        assert hasattr(settings, 'memory_async_write')
        assert hasattr(settings, 'session_title_trigger_length')
        assert hasattr(settings, 'context_max_tokens')
        assert hasattr(settings, 'performance_slow_request_threshold')
        print("  ✓ Settings中的配置项仍然存在（向后兼容）")
        
        # 验证ConfigAdapter可以使用Settings作为后备
        adapter = get_config_adapter()
        memory_config = adapter.get_memory_config()
        
        # 即使YAML不存在，也应该有值（从Settings读取）
        assert "storage_mode" in memory_config or "async_write" in memory_config
        print("  ✓ ConfigAdapter可以使用Settings作为后备")
        
        print("  ✅ 向后兼容性测试通过\n")
        return True
        
    except Exception as e:
        print(f"  ✗ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config_priority():
    """测试：配置优先级"""
    print("测试4: 配置优先级（YAML > Settings）")
    
    try:
        from app.utils.config_loader import ConfigLoader
        from app.config.config import settings
        
        # 测试deep_merge的优先级
        settings_config = {
            "storage_mode": "hybrid",
            "async_write": True,
            "batch_size": 10
        }
        
        yaml_config = {
            "storage_mode": "dual",  # 应该覆盖
            "batch_size": 20  # 应该覆盖
        }
        
        merged = ConfigLoader.deep_merge(settings_config, yaml_config)
        
        assert merged["storage_mode"] == "dual", "YAML应覆盖Settings"
        assert merged["async_write"] == True, "Settings值应保留"
        assert merged["batch_size"] == 20, "YAML应覆盖Settings"
        
        print("  ✓ 配置优先级正确：YAML > Settings")
        print(f"    Settings: storage_mode=hybrid, batch_size=10")
        print(f"    YAML: storage_mode=dual, batch_size=20")
        print(f"    结果: storage_mode={merged['storage_mode']}, batch_size={merged['batch_size']}")
        
        print("  ✅ 配置优先级测试通过\n")
        return True
        
    except Exception as e:
        print(f"  ✗ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_migrated_files_import():
    """测试：迁移的文件能否正常导入"""
    print("测试5: 迁移的文件能否正常导入")
    
    migrated_files = [
        "app.main",
        "app.engines.memory.worker",
        "app.engines.memory.qdrant_engine",
        "app.engines.memory.manager",
        "app.api.v1.sessions",
        "app.services.context.context_service",
        "app.core.context.builder",
        "app.core.context.summary_generator",
        "app.middleware.performance"
    ]
    
    all_imported = True
    for module_name in migrated_files:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name} 导入成功")
        except Exception as e:
            print(f"  ✗ {module_name} 导入失败: {e}")
            all_imported = False
    
    if all_imported:
        print("  ✅ 所有迁移的文件都能正常导入\n")
    else:
        print("  ⚠ 部分文件导入失败\n")
    
    return all_imported


def test_config_files_exist():
    """测试：配置文件是否存在"""
    print("测试6: 配置文件是否存在")
    
    config_dir = project_root / "backend" / "config"
    required_files = [
        "context.yaml",
        "performance.yaml",
        "session.yaml",
        "memory.yaml"
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = config_dir / file_name
        if file_path.exists():
            print(f"  ✓ {file_name} 存在")
        else:
            print(f"  ✗ {file_name} 不存在")
            all_exist = False
    
    if all_exist:
        print("  ✅ 所有配置文件都存在\n")
    else:
        print("  ⚠ 部分配置文件不存在\n")
    
    return all_exist


def main():
    """主函数"""
    print("=" * 70)
    print("配置迁移回归测试")
    print("=" * 70)
    print()
    
    results = []
    
    # 运行所有测试
    results.append(test_config_files_exist())
    results.append(test_config_loader_new_methods())
    results.append(test_config_adapter_basic())
    results.append(test_backward_compatibility())
    results.append(test_config_priority())
    results.append(test_migrated_files_import())
    
    # 总结
    print("=" * 70)
    print("回归测试总结")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if all(results):
        print("✅ 所有回归测试通过")
        print("\n配置迁移成功，现有功能未受影响！")
        return 0
    else:
        print("❌ 部分回归测试失败")
        print("\n请检查失败的测试项")
        return 1


if __name__ == "__main__":
    sys.exit(main())

