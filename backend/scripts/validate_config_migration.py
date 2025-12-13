"""
配置迁移验证脚本

对比YAML配置和Settings配置的值，确保配置值一致
"""

# 标准库
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

# 本地库
from app.config.config import settings
from app.utils.config_adapter import get_config_adapter
from app.utils.logger import logger


def compare_configs(yaml_config: dict, settings_config: dict, path: str = "", differences: list = None):
    """递归对比配置值
    
    Args:
        yaml_config: YAML配置字典
        settings_config: Settings配置字典
        path: 当前路径（用于显示）
        differences: 差异列表
    """
    if differences is None:
        differences = []
    
    for key, settings_value in settings_config.items():
        current_path = f"{path}.{key}" if path else key
        
        if key not in yaml_config:
            differences.append({
                "path": current_path,
                "type": "missing_in_yaml",
                "yaml_value": None,
                "settings_value": settings_value
            })
            continue
        
        yaml_value = yaml_config[key]
        
        if isinstance(settings_value, dict) and isinstance(yaml_value, dict):
            compare_configs(yaml_value, settings_value, current_path, differences)
        elif yaml_value != settings_value:
            differences.append({
                "path": current_path,
                "type": "value_mismatch",
                "yaml_value": yaml_value,
                "settings_value": settings_value
            })
    
    return differences


def validate_memory_config():
    """验证记忆配置"""
    print("\n=== 验证记忆配置 ===")
    adapter = get_config_adapter()
    yaml_config = adapter.config_loader.load_memory_config()
    
    settings_config = {
        "storage_mode": settings.memory_storage_mode,
        "async_write": settings.memory_async_write,
        "batch_size": settings.memory_batch_size,
        "dedup": {
            "enabled": settings.memory_dedup_enabled,
            "mode": settings.memory_dedup_mode,
            "content_threshold": settings.memory_dedup_content_threshold,
            "storage_threshold": settings.memory_dedup_storage_threshold,
            "check_interval_seconds": settings.memory_dedup_check_interval,
        }
    }
    
    differences = compare_configs(yaml_config, settings_config)
    
    if differences:
        print(f"发现 {len(differences)} 个差异：")
        for diff in differences:
            print(f"  - {diff['path']}: YAML={diff['yaml_value']}, Settings={diff['settings_value']}")
        return False
    else:
        print("✓ 记忆配置一致")
        return True


def validate_session_config():
    """验证会话配置"""
    print("\n=== 验证会话配置 ===")
    adapter = get_config_adapter()
    yaml_config = adapter.config_loader.load_session_config()
    
    settings_config = {
        "title": {
            "trigger_length": settings.session_title_trigger_length,
            "max_messages": settings.session_title_max_messages,
            "model": settings.session_title_model,
            "temperature": settings.session_title_temperature,
            "max_tokens": settings.session_title_max_tokens,
        }
    }
    
    differences = compare_configs(yaml_config, settings_config)
    
    if differences:
        print(f"发现 {len(differences)} 个差异：")
        for diff in differences:
            print(f"  - {diff['path']}: YAML={diff['yaml_value']}, Settings={diff['settings_value']}")
        return False
    else:
        print("✓ 会话配置一致")
        return True


def validate_context_config():
    """验证上下文配置"""
    print("\n=== 验证上下文配置 ===")
    adapter = get_config_adapter()
    yaml_config = adapter.config_loader.load_context_config()
    
    settings_config = {
        "intelligent_enabled": settings.context_intelligent_enabled,
        "recent": {
            "message_count": settings.context_recent_message_count,
        },
        "max_tokens": settings.context_max_tokens,
        "weights": {
            "summary": settings.context_summary_weight,
            "memory": settings.context_memory_weight,
        },
        "summary": {
            "trigger_count": settings.context_summary_trigger_count,
            "window_size": settings.context_summary_window_size,
            "model": settings.context_summary_model,
            "temperature": settings.context_summary_temperature,
        }
    }
    
    differences = compare_configs(yaml_config, settings_config)
    
    if differences:
        print(f"发现 {len(differences)} 个差异：")
        for diff in differences:
            print(f"  - {diff['path']}: YAML={diff['yaml_value']}, Settings={diff['settings_value']}")
        return False
    else:
        print("✓ 上下文配置一致")
        return True


def validate_performance_config():
    """验证性能配置"""
    print("\n=== 验证性能配置 ===")
    adapter = get_config_adapter()
    yaml_config = adapter.config_loader.load_performance_config()
    
    settings_config = {
        "slow_request": {
            "threshold": settings.performance_slow_request_threshold,
            "delete_threshold": settings.performance_slow_delete_threshold,
        }
    }
    
    differences = compare_configs(yaml_config, settings_config)
    
    if differences:
        print(f"发现 {len(differences)} 个差异：")
        for diff in differences:
            print(f"  - {diff['path']}: YAML={diff['yaml_value']}, Settings={diff['settings_value']}")
        return False
    else:
        print("✓ 性能配置一致")
        return True


def main():
    """主函数"""
    print("开始验证配置迁移...")
    
    results = []
    results.append(validate_memory_config())
    results.append(validate_session_config())
    results.append(validate_context_config())
    results.append(validate_performance_config())
    
    print("\n=== 验证结果 ===")
    if all(results):
        print("✓ 所有配置验证通过")
        return 0
    else:
        print("✗ 部分配置验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

