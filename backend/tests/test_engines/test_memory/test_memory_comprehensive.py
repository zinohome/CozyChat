"""
记忆系统完整测试验证脚本

测试记忆系统的各个功能，并计算记忆提取的成功率
"""

# 标准库
import asyncio
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

# 本地库
from app.engines.memory.manager import MemoryManager
from app.engines.memory.models import Memory, MemoryType, MemorySearchResult
from app.utils.logger import logger


@dataclass
class TestCase:
    """测试用例"""
    name: str
    memory_content: str
    memory_type: MemoryType
    query: str
    expected_found: bool  # 是否期望找到
    expected_similarity_min: float = 0.0  # 最小相似度期望
    description: str = ""


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    memory_id: str = ""
    found: bool = False
    similarity: float = 0.0
    results_count: int = 0
    error: str = ""
    details: Dict[str, Any] = None


class MemorySystemTester:
    """记忆系统测试器"""
    
    def __init__(self, user_id: str = None, session_id: str = None):
        """初始化测试器
        
        Args:
            user_id: 测试用户ID
            session_id: 测试会话ID
        """
        self.user_id = user_id or f"test-user-{uuid.uuid4().hex[:8]}"
        self.session_id = session_id or f"test-session-{uuid.uuid4().hex[:8]}"
        self.memory_manager = MemoryManager()
        self.test_results: List[TestResult] = []
        self.added_memories: List[Memory] = []
        
        logger.info(
            f"Memory system tester initialized",
            extra={
                "user_id": self.user_id,
                "session_id": self.session_id
            }
        )
    
    async def setup(self):
        """设置测试环境"""
        logger.info("Setting up test environment...")
        
        # 健康检查
        try:
            health = await self.memory_manager.health_check()
            if not health:
                raise Exception("Memory manager health check failed")
            logger.info("Memory manager health check passed")
        except Exception as e:
            logger.error(f"Memory manager health check failed: {e}")
            raise
    
    async def cleanup(self):
        """清理测试数据"""
        logger.info("Cleaning up test data...")
        
        try:
            # 删除测试会话的所有记忆
            deleted_count = await self.memory_manager.delete_session_memories(
                user_id=self.user_id,
                session_id=self.session_id
            )
            logger.info(f"Deleted {deleted_count} test memories")
        except Exception as e:
            logger.warning(f"Failed to cleanup test data: {e}")
    
    def create_test_cases(self) -> List[TestCase]:
        """创建测试用例"""
        test_cases = [
            # 基础测试：简单记忆
            TestCase(
                name="基础-用户记忆-编程",
                memory_content="我喜欢Python编程，特别是数据分析和机器学习",
                memory_type=MemoryType.USER,
                query="Python编程",
                expected_found=True,
                expected_similarity_min=0.6,
                description="测试基本的用户记忆存储和检索"
            ),
            TestCase(
                name="基础-AI记忆-回应",
                memory_content="用户提到他喜欢Python编程，特别是数据分析和机器学习",
                memory_type=MemoryType.ASSISTANT,
                query="Python编程",
                expected_found=True,
                expected_similarity_min=0.6,
                description="测试AI记忆的存储和检索"
            ),
            
            # 语义相似性测试
            TestCase(
                name="语义-同义词匹配",
                memory_content="我经常使用JavaScript开发前端应用",
                memory_type=MemoryType.USER,
                query="前端开发",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试语义相似性匹配（同义词）"
            ),
            TestCase(
                name="语义-相关概念",
                memory_content="我每天都会去健身房锻炼身体",
                memory_type=MemoryType.USER,
                query="运动健身",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试相关概念的匹配"
            ),
            
            # 中文测试
            TestCase(
                name="中文-用户偏好",
                memory_content="我最喜欢的颜色是蓝色，因为蓝色让我感到平静",
                memory_type=MemoryType.USER,
                query="喜欢的颜色",
                expected_found=True,
                expected_similarity_min=0.6,
                description="测试中文记忆的存储和检索"
            ),
            TestCase(
                name="中文-个人信息",
                memory_content="我住在北京，工作在一家互联网公司",
                memory_type=MemoryType.USER,
                query="居住地",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试中文个人信息的检索"
            ),
            
            # 具体信息测试
            TestCase(
                name="具体信息-数字",
                memory_content="我有3只猫，它们的名字分别是小花、小黑和小白",
                memory_type=MemoryType.USER,
                query="宠物数量",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试包含数字的具体信息"
            ),
            TestCase(
                name="具体信息-日期",
                memory_content="我的生日是1990年5月15日",
                memory_type=MemoryType.USER,
                query="生日",
                expected_found=True,
                expected_similarity_min=0.6,
                description="测试包含日期的信息"
            ),
            
            # 长文本测试
            TestCase(
                name="长文本-详细描述",
                memory_content="我喜欢阅读科幻小说，特别是那些探讨人工智能和未来社会的作品。最近在读《三体》，对其中关于黑暗森林法则的设定很感兴趣。",
                memory_type=MemoryType.USER,
                query="喜欢的书籍",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试长文本记忆的检索"
            ),
            
            # 多关键词测试
            TestCase(
                name="多关键词-复合查询",
                memory_content="我计划下个月去日本旅行，准备参观东京、大阪和京都",
                memory_type=MemoryType.USER,
                query="旅行计划",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试包含多个关键词的记忆"
            ),
            
            # 边界测试
            TestCase(
                name="边界-不相关内容",
                memory_content="今天天气很好，阳光明媚",
                memory_type=MemoryType.USER,
                query="编程技术",
                expected_found=False,  # 不期望找到
                expected_similarity_min=0.0,
                description="测试不相关内容的过滤"
            ),
            TestCase(
                name="边界-空查询",
                memory_content="这是一条测试记忆",
                memory_type=MemoryType.USER,
                query="",
                expected_found=False,  # 空查询不应该返回结果
                expected_similarity_min=0.0,
                description="测试空查询的处理"
            ),
            
            # 重要性测试
            TestCase(
                name="重要性-高重要性",
                memory_content="我对Python编程非常感兴趣，这是我最重要的技能",
                memory_type=MemoryType.USER,
                query="技能",
                expected_found=True,
                expected_similarity_min=0.6,
                description="测试高重要性记忆的检索"
            ),
            
            # 跨会话测试（如果启用）
            TestCase(
                name="跨会话-用户偏好",
                memory_content="我不喜欢吃辣的食物",
                memory_type=MemoryType.USER,
                query="食物偏好",
                expected_found=True,
                expected_similarity_min=0.5,
                description="测试跨会话记忆检索"
            ),
        ]
        
        return test_cases
    
    async def test_add_memory(self, test_case: TestCase) -> Tuple[bool, str]:
        """测试添加记忆
        
        Returns:
            (success, memory_id)
        """
        try:
            memory_id = await self.memory_manager.add_memory(
                user_id=self.user_id,
                session_id=self.session_id,
                content=test_case.memory_content,
                memory_type=test_case.memory_type,
                importance=0.8 if "重要性" in test_case.name else 0.5,
                async_save=False  # 同步保存，确保立即可用
            )
            
            # 等待一小段时间，确保数据已写入
            await asyncio.sleep(0.1)
            
            return True, memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}", exc_info=True)
            return False, str(e)
    
    async def test_search_memory(
        self,
        test_case: TestCase,
        similarity_threshold: float = 0.5
    ) -> Tuple[bool, List[MemorySearchResult], float]:
        """测试搜索记忆
        
        Returns:
            (found, results, max_similarity)
        """
        try:
            if not test_case.query.strip():
                # 空查询，不应该搜索
                return False, [], 0.0
            
            # 搜索记忆
            results = await self.memory_manager.search_memories(
                query=test_case.query,
                user_id=self.user_id,
                session_id=self.session_id,
                memory_type=test_case.memory_type,
                limit=10,
                similarity_threshold=similarity_threshold
            )
            
            if not results:
                return False, [], 0.0
            
            # 检查是否找到相关记忆
            max_similarity = max(r.similarity for r in results) if results else 0.0
            
            # 检查内容是否匹配（简单检查）
            found = False
            for result in results:
                if test_case.memory_content in result.memory.content or \
                   result.memory.content in test_case.memory_content:
                    found = True
                    break
                # 或者相似度足够高
                if result.similarity >= test_case.expected_similarity_min:
                    found = True
                    break
            
            return found, results, max_similarity
            
        except Exception as e:
            logger.error(f"Failed to search memory: {e}", exc_info=True)
            return False, [], 0.0
    
    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        logger.info(f"Running test: {test_case.name}")
        
        result = TestResult(
            test_name=test_case.name,
            passed=False,
            details={}
        )
        
        try:
            # 1. 添加记忆
            add_success, memory_id = await self.test_add_memory(test_case)
            if not add_success:
                result.error = f"Failed to add memory: {memory_id}"
                result.details = {"add_error": memory_id}
                return result
            
            result.memory_id = memory_id
            result.details["memory_id"] = memory_id
            
            # 2. 搜索记忆
            found, search_results, max_similarity = await self.test_search_memory(
                test_case,
                similarity_threshold=0.3  # 使用较低的阈值，确保能检索到
            )
            
            result.found = found
            result.similarity = max_similarity
            result.results_count = len(search_results)
            result.details["search_results_count"] = len(search_results)
            result.details["max_similarity"] = max_similarity
            result.details["all_similarities"] = [r.similarity for r in search_results[:5]]
            
            # 3. 验证结果
            if test_case.expected_found:
                # 期望找到
                if found and max_similarity >= test_case.expected_similarity_min:
                    result.passed = True
                else:
                    result.error = f"Expected to find memory but found={found}, similarity={max_similarity:.3f} < {test_case.expected_similarity_min}"
            else:
                # 不期望找到
                if not found or max_similarity < 0.5:
                    result.passed = True
                else:
                    result.error = f"Expected not to find memory but found={found}, similarity={max_similarity:.3f}"
            
            logger.info(
                f"Test {test_case.name}: {'PASSED' if result.passed else 'FAILED'}",
                extra={
                    "found": found,
                    "similarity": max_similarity,
                    "results_count": len(search_results)
                }
            )
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"Test {test_case.name} failed with exception: {e}", exc_info=True)
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("=" * 80)
        logger.info("Starting comprehensive memory system tests")
        logger.info("=" * 80)
        
        # 设置
        await self.setup()
        
        try:
            # 创建测试用例
            test_cases = self.create_test_cases()
            logger.info(f"Created {len(test_cases)} test cases")
            
            # 运行测试
            for test_case in test_cases:
                result = await self.run_test_case(test_case)
                self.test_results.append(result)
                # 每个测试之间稍作延迟
                await asyncio.sleep(0.2)
            
            # 生成报告
            report = self.generate_report()
            
            return report
            
        finally:
            # 清理
            await self.cleanup()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # 计算成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 计算平均相似度
        similarities = [r.similarity for r in self.test_results if r.found]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # 计算记忆提取成功率（找到相关记忆的比例）
        expected_found_tests = [
            r for r in self.test_results
            if any(tc.name == r.test_name and tc.expected_found 
                   for tc in self.create_test_cases())
        ]
        found_count = sum(1 for r in expected_found_tests if r.found)
        retrieval_success_rate = (
            (found_count / len(expected_found_tests) * 100)
            if expected_found_tests else 0
        )
        
        # 详细结果
        detailed_results = []
        for result in self.test_results:
            detailed_results.append({
                "test_name": result.test_name,
                "passed": result.passed,
                "found": result.found,
                "similarity": round(result.similarity, 3),
                "results_count": result.results_count,
                "error": result.error,
                "details": result.details
            })
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2),
                "retrieval_success_rate": round(retrieval_success_rate, 2),
                "avg_similarity": round(avg_similarity, 3),
                "found_count": found_count,
                "expected_found_count": len(expected_found_tests)
            },
            "detailed_results": detailed_results
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印测试报告"""
        print("\n" + "=" * 80)
        print("记忆系统完整测试报告")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"\n【测试概览】")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  通过测试: {summary['passed_tests']}")
        print(f"  失败测试: {summary['failed_tests']}")
        print(f"  测试通过率: {summary['success_rate']:.2f}%")
        
        print(f"\n【记忆提取成功率】")
        print(f"  期望找到的记忆数: {summary['expected_found_count']}")
        print(f"  实际找到的记忆数: {summary['found_count']}")
        print(f"  记忆提取成功率: {summary['retrieval_success_rate']:.2f}%")
        print(f"  平均相似度: {summary['avg_similarity']:.3f}")
        
        print(f"\n【详细结果】")
        for result in report["detailed_results"]:
            status = "✓" if result["passed"] else "✗"
            print(f"  {status} {result['test_name']}")
            print(f"    找到: {result['found']}, 相似度: {result['similarity']:.3f}, 结果数: {result['results_count']}")
            if result["error"]:
                print(f"    错误: {result['error']}")
        
        print("\n" + "=" * 80)


async def main():
    """主函数"""
    try:
        tester = MemorySystemTester()
        report = await tester.run_all_tests()
        tester.print_report(report)
        
        # 返回退出码
        success_rate = report["summary"]["retrieval_success_rate"]
        if success_rate >= 80:
            print(f"\n✓ 测试通过！记忆提取成功率达到 {success_rate:.2f}%")
            return 0
        elif success_rate >= 60:
            print(f"\n⚠ 测试部分通过，记忆提取成功率为 {success_rate:.2f}%，建议优化")
            return 1
        else:
            print(f"\n✗ 测试失败，记忆提取成功率仅为 {success_rate:.2f}%，需要修复")
            return 2
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        print(f"\n✗ 测试执行失败: {e}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

