"""
多用户 Agent 实现示例
实现会话记忆和专业记忆的分离与共享
"""

import asyncio
from typing import List, Optional
from uuid import UUID
import cognee
from cognee.modules.users.models import User
from cognee.modules.users.methods import create_user, get_user
from cognee.modules.users.permissions.methods import (
    give_permission_on_dataset,
    check_permission_on_dataset
)
from cognee.modules.search.types import SearchType
from cognee.shared.logging_utils import get_logger

logger = get_logger()


class MultiUserAgent:
    """
    多用户 Agent 类
    管理会话记忆和专业记忆
    """
    
    def __init__(self):
        # 专业记忆数据集列表
        self.professional_datasets = [
            "medical_knowledge",
            "psychology_knowledge"
        ]
        # 用户会话数据集映射 {user_id: dataset_name}
        self.user_datasets = {}
    
    async def initialize(self):
        """初始化 Agent，创建专业记忆数据集"""
        logger.info("初始化专业记忆数据集...")
        
        # 确保 Cognee 已设置
        await cognee.setup()
        
        # 创建专业记忆数据集（如果不存在）
        for dataset_name in self.professional_datasets:
            try:
                # 尝试添加空数据来创建数据集
                await cognee.add(
                    data=[],
                    dataset_name=dataset_name
                )
                logger.info(f"专业记忆数据集 '{dataset_name}' 已创建或已存在")
            except Exception as e:
                logger.warning(f"创建数据集 '{dataset_name}' 时出错: {e}")
    
    async def add_professional_knowledge(
        self,
        data: str,
        domain: str,
        node_sets: Optional[List[str]] = None
    ):
        """
        添加专业知识到共享记忆
        
        Args:
            data: 专业文档内容
            domain: 专业领域 ("medical" 或 "psychology")
            node_sets: 节点集列表，用于组织知识
        """
        dataset_name = f"{domain}_knowledge"
        
        if dataset_name not in self.professional_datasets:
            raise ValueError(f"不支持的专业领域: {domain}")
        
        # 默认节点集
        if node_sets is None:
            if domain == "medical":
                node_sets = ["medical_concepts", "medical_procedures"]
            elif domain == "psychology":
                node_sets = ["psychology_theories", "psychology_methods"]
        
        # 添加数据
        await cognee.add(
            data=data,
            dataset_name=dataset_name,
            node_set=node_sets
        )
        
        # 认知化处理
        await cognee.cognify(
            dataset_name=dataset_name
        )
        
        logger.info(f"已添加 {domain} 专业知识到 '{dataset_name}'")
    
    async def register_user(
        self,
        user_id: str,
        email: str,
        password: str
    ) -> User:
        """
        注册新用户，创建专属会话数据集
        
        Args:
            user_id: 用户ID
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            User: 创建的用户对象
        """
        # 创建用户
        try:
            user = await create_user(
                email=email,
                password=password
            )
            logger.info(f"用户 {email} 已创建")
        except Exception as e:
            # 如果用户已存在，获取现有用户
            user = await get_user(email=email)
            logger.info(f"用户 {email} 已存在，使用现有用户")
        
        # 创建用户专属会话数据集
        dataset_name = f"conversation_{user_id}"
        
        try:
            await cognee.add(
                data=[],
                dataset_name=dataset_name,
                user=user
            )
            
            # 授予用户完整权限
            await give_permission_on_dataset(
                principal=user,
                dataset_name=dataset_name,
                permission="write"
            )
            
            self.user_datasets[user_id] = dataset_name
            logger.info(f"用户 {user_id} 的会话数据集 '{dataset_name}' 已创建")
            
        except Exception as e:
            logger.warning(f"创建会话数据集时出错: {e}")
            # 数据集可能已存在
        
        return user
    
    async def save_conversation(
        self,
        user_id: str,
        message: str,
        response: str,
        user: User
    ):
        """
        保存对话到用户会话记忆
        
        Args:
            user_id: 用户ID
            message: 用户消息
            response: Agent 响应
            user: 用户对象
        """
        dataset_name = self.user_datasets.get(user_id)
        if not dataset_name:
            raise ValueError(f"用户 {user_id} 未注册")
        
        # 组合对话内容
        conversation_text = f"用户: {message}\n助手: {response}"
        
        # 添加到会话数据集
        await cognee.add(
            data=conversation_text,
            dataset_name=dataset_name,
            user=user,
            node_set=[f"user_{user_id}_conversations"]
        )
        
        # 认知化处理（提取用户偏好、上下文等）
        await cognee.cognify(
            dataset_name=dataset_name,
            user=user
        )
        
        logger.info(f"对话已保存到用户 {user_id} 的会话记忆")
    
    async def search_professional_knowledge(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        top_k: int = 5
    ):
        """
        搜索专业知识
        
        Args:
            query: 查询文本
            domains: 要搜索的专业领域列表，None 表示搜索所有领域
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if domains is None:
            datasets = self.professional_datasets
        else:
            datasets = [f"{domain}_knowledge" for domain in domains]
        
        results = await cognee.search(
            query_text=query,
            datasets=datasets,
            query_type=SearchType.GRAPH_COMPLETION,
            top_k=top_k
        )
        
        return results
    
    async def search_user_conversation(
        self,
        user_id: str,
        query: str,
        user: User,
        top_k: int = 3
    ):
        """
        搜索用户会话记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            user: 用户对象
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        dataset_name = self.user_datasets.get(user_id)
        if not dataset_name:
            raise ValueError(f"用户 {user_id} 未注册")
        
        results = await cognee.search(
            query_text=query,
            datasets=[dataset_name],
            user=user,
            query_type=SearchType.GRAPH_COMPLETION,
            top_k=top_k
        )
        
        return results
    
    async def hybrid_search(
        self,
        user_id: str,
        query: str,
        user: User,
        top_k: int = 10
    ):
        """
        混合搜索：同时搜索专业记忆和用户会话记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            user: 用户对象
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        # 构建数据集列表
        datasets = self.professional_datasets.copy()
        user_dataset = self.user_datasets.get(user_id)
        if user_dataset:
            datasets.append(user_dataset)
        
        # 构建节点集列表
        node_names = [
            "medical_concepts",
            "medical_procedures",
            "psychology_theories",
            "psychology_methods"
        ]
        if user_dataset:
            node_names.append(f"user_{user_id}_conversations")
        
        # 执行混合搜索
        results = await cognee.search(
            query_text=query,
            datasets=datasets,
            user=user,
            query_type=SearchType.GRAPH_COMPLETION,
            node_name=node_names,
            use_combined_context=True,
            top_k=top_k
        )
        
        return results
    
    async def chat(
        self,
        user_id: str,
        message: str,
        user: User
    ) -> str:
        """
        处理用户对话（完整流程）
        
        Args:
            user_id: 用户ID
            message: 用户消息
            user: 用户对象
            
        Returns:
            Agent 响应
        """
        # 1. 混合搜索：获取专业知识和用户上下文
        search_results = await self.hybrid_search(
            user_id=user_id,
            query=message,
            user=user,
            top_k=10
        )
        
        # 2. 生成响应（这里简化处理，实际应该使用 LLM）
        # 提取搜索结果中的文本
        context_text = ""
        if isinstance(search_results, list):
            for result in search_results:
                if hasattr(result, 'content'):
                    context_text += result.content + "\n"
                elif isinstance(result, str):
                    context_text += result + "\n"
        
        # 简化的响应生成（实际应该使用 LLM）
        response = f"基于以下上下文回答您的问题：\n{context_text[:500]}..."
        
        # 3. 保存对话到会话记忆
        await self.save_conversation(
            user_id=user_id,
            message=message,
            response=response,
            user=user
        )
        
        return response


# 使用示例
async def main():
    """主函数示例"""
    
    # 创建 Agent 实例
    agent = MultiUserAgent()
    
    # 初始化专业记忆
    await agent.initialize()
    
    # 添加专业知识（示例）
    medical_knowledge = """
    高血压是一种常见的心血管疾病，定义为收缩压≥140mmHg或舒张压≥90mmHg。
    治疗方法包括生活方式改变和药物治疗。
    """
    
    psychology_knowledge = """
    认知行为疗法（CBT）是一种心理治疗方法，通过改变不良认知模式来改善情绪和行为。
    它广泛应用于治疗抑郁症、焦虑症等心理障碍。
    """
    
    # 添加医学知识
    await agent.add_professional_knowledge(
        data=medical_knowledge,
        domain="medical",
        node_sets=["medical_concepts", "medical_conditions"]
    )
    
    # 添加心理学知识
    await agent.add_professional_knowledge(
        data=psychology_knowledge,
        domain="psychology",
        node_sets=["psychology_theories", "psychology_methods"]
    )
    
    # 注册用户
    user1 = await agent.register_user(
        user_id="user_001",
        email="user1@example.com",
        password="password123"
    )
    
    user2 = await agent.register_user(
        user_id="user_002",
        email="user2@example.com",
        password="password123"
    )
    
    # 用户1 进行对话
    response1 = await agent.chat(
        user_id="user_001",
        message="什么是高血压？",
        user=user1
    )
    print(f"用户1 的响应: {response1}")
    
    # 用户2 进行对话
    response2 = await agent.chat(
        user_id="user_002",
        message="什么是认知行为疗法？",
        user=user2
    )
    print(f"用户2 的响应: {response2}")
    
    # 搜索专业知识
    medical_results = await agent.search_professional_knowledge(
        query="高血压的治疗方法",
        domains=["medical"],
        top_k=3
    )
    print(f"医学知识搜索结果: {medical_results}")
    
    # 搜索用户会话记忆
    conversation_results = await agent.search_user_conversation(
        user_id="user_001",
        query="高血压",
        user=user1,
        top_k=2
    )
    print(f"用户1 的会话记忆搜索结果: {conversation_results}")


if __name__ == "__main__":
    asyncio.run(main())

