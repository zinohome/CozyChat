"""
Tavily 搜索工具

提供互联网搜索功能，可以获取关于特定问题的答案和相关搜索结果
"""

# 标准库
from typing import Any, Dict, Optional

# 第三方库
from tavily import TavilyClient

# 本地库
from app.config.config import settings
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class TavilySearchTool(Tool):
    """Tavily 搜索工具
    
    提供互联网搜索功能，可以获取关于特定问题的答案和相关搜索结果
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化 Tavily 搜索工具
        
        Args:
            api_key: Tavily API密钥（可选，如果不提供则从配置读取）
        """
        super().__init__(tool_type=ToolType.BUILTIN)
        self.api_key = api_key or getattr(settings, "tavily_api_key", None)
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "tavily_search"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "用于在互联网上搜索信息的工具，可以获取关于特定问题的答案和相关搜索结果。"
            "适用于需要获取最新信息、事实查询、新闻搜索等场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "query": {
                "type": "string",
                "description": "要搜索的查询语句，例如'谁是梅西？'或'2024年奥运会在哪里举行？'",
                "required": True
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "description": "搜索深度，basic为基本搜索，advanced为高级搜索，默认为basic",
                "required": False
            }
        }
    
    async def execute(
        self,
        query: str,
        search_depth: Optional[str] = None
    ) -> str:
        """执行搜索
        
        Args:
            query: 搜索查询语句
            search_depth: 搜索深度（basic/advanced），默认为basic
            
        Returns:
            str: 搜索结果或错误信息
        """
        if not self.api_key:
            error_msg = "错误：未配置Tavily API密钥。请在环境变量中设置TAVILY_API_KEY"
            logger.warning(error_msg)
            return error_msg
        
        if not query or not query.strip():
            error_msg = "错误：搜索查询不能为空"
            logger.warning(error_msg)
            return error_msg
        
        try:
            # 获取搜索深度参数，如果没有提供则使用默认值
            search_depth = search_depth or "basic"
            
            # 创建Tavily客户端并执行搜索
            tavily_client = TavilyClient(api_key=self.api_key)
            response = tavily_client.search(
                query=query.strip(),
                search_depth=search_depth,
                topic="general",  # 默认添加topic参数
                country="china"   # 默认添加country参数
            )
            
            # 格式化返回结果
            result = self._format_search_results(response, query)
            
            logger.info(
                f"Tavily search executed: {query}",
                extra={"query": query, "search_depth": search_depth}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"错误：Tavily搜索执行失败 - {str(e)}"
            logger.error(f"Tavily search error: {error_msg}", exc_info=True)
            return error_msg
    
    def _format_search_results(self, response: Dict[str, Any], query: str) -> str:
        """格式化搜索结果
        
        Args:
            response: Tavily API返回的响应
            query: 原始查询
            
        Returns:
            str: 格式化后的搜索结果
        """
        result_parts = []
        
        # 添加查询信息
        result_parts.append(f"🔍 搜索查询: {query}")
        result_parts.append("")
        
        # 添加答案（如果有）
        answer = response.get("answer")
        if answer:
            result_parts.append("📝 答案:")
            result_parts.append(answer)
            result_parts.append("")
        
        # 添加搜索结果
        results = response.get("results", [])
        if results:
            result_parts.append(f"📚 相关结果 ({len(results)} 条):")
            result_parts.append("")
            
            for i, item in enumerate(results[:5], 1):  # 最多显示5条结果
                title = item.get("title", "无标题")
                url = item.get("url", "")
                content = item.get("content", "")
                score = item.get("score")
                
                result_parts.append(f"{i}. {title}")
                if url:
                    result_parts.append(f"   🔗 {url}")
                if content:
                    # 限制内容长度，避免过长
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                    result_parts.append(f"   📄 {content_preview}")
                if score is not None:
                    result_parts.append(f"   ⭐ 相关度: {score:.2f}")
                result_parts.append("")
        
        # 添加响应时间（如果有）
        response_time = response.get("response_time")
        if response_time:
            result_parts.append(f"⏱️ 响应时间: {response_time:.2f}秒")
        
        return "\n".join(result_parts)

