#!/usr/bin/env python3
"""
下载 embedding 模型脚本

用于预先下载 sentence-transformers 模型，避免首次使用时等待下载
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
from app.utils.logger import logger


def download_model(model_name: str):
    """下载指定的 embedding 模型
    
    Args:
        model_name: 模型名称，如 'BGE-base-zh-v1.5'
    """
    try:
        logger.info(f"开始下载模型: {model_name}")
        print(f"📥 正在下载模型: {model_name}")
        print("   这可能需要几分钟，请耐心等待...")
        
        # 加载模型（会自动下载）
        model = SentenceTransformer(model_name, device='cpu')
        
        # 测试编码以确保模型正常工作
        test_text = "测试文本"
        embedding = model.encode(test_text)
        
        logger.info(
            f"模型下载成功",
            extra={
                "model": model_name,
                "dimension": len(embedding),
                "test_embedding_shape": embedding.shape
            }
        )
        
        print(f"✅ 模型下载成功！")
        print(f"   模型名称: {model_name}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   模型位置: {model._model_card_vars.get('model_name', '默认位置')}")
        
        return True
        
    except Exception as e:
        logger.error(f"下载模型失败: {e}", exc_info=True)
        print(f"❌ 下载模型失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="下载 embedding 模型")
    parser.add_argument(
        "--model",
        type=str,
        default="BAAI/bge-base-zh-v1.5",
        help="要下载的模型名称（默认: BAAI/bge-base-zh-v1.5）"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Embedding 模型下载工具")
    print("=" * 60)
    print()
    
    success = download_model(args.model)
    
    if success:
        print()
        print("=" * 60)
        print("✅ 下载完成！现在可以在配置中使用该模型了。")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ 下载失败，请检查网络连接和模型名称。")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

