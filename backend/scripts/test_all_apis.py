#!/usr/bin/env python3
"""
全面API测试脚本

测试所有API端点，确保功能正常
"""

import sys
import json
import requests
from typing import Dict, Optional, Any
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/v1"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# 测试结果
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}

def print_test(name: str, status: str, message: str = ""):
    """打印测试结果"""
    if status == "PASS":
        print(f"{Colors.GREEN}✓{Colors.RESET} {name}")
        test_results["passed"] += 1
    elif status == "FAIL":
        print(f"{Colors.RED}✗{Colors.RESET} {name}: {message}")
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")
    elif status == "SKIP":
        print(f"{Colors.YELLOW}⊘{Colors.RESET} {name}: {message}")
        test_results["skipped"] += 1
    else:
        print(f"{Colors.BLUE}?{Colors.RESET} {name}: {message}")

def test_endpoint(
    method: str,
    url: str,
    name: str,
    headers: Optional[Dict] = None,
    data: Optional[Any] = None,
    expected_status: Any = 200,  # 可以是int或list
    require_auth: bool = False
) -> Optional[Dict]:
    """测试API端点"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            print_test(name, "FAIL", f"Unsupported method: {method}")
            return None
        
        # 支持多个期望状态码
        expected_statuses = expected_status if isinstance(expected_status, list) else [expected_status]
        if response.status_code in expected_statuses:
            print_test(name, "PASS")
            try:
                return response.json()
            except:
                return {"status": "ok"}
        elif response.status_code == 401 and require_auth:
            print_test(name, "SKIP", "Requires authentication")
            return None
        else:
            print_test(name, "FAIL", f"Expected {expected_status}, got {response.status_code}: {response.text[:100]}")
            return None
    except requests.exceptions.RequestException as e:
        print_test(name, "FAIL", f"Request error: {str(e)}")
        return None

def main():
    """主测试函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}CozyChat API 全面测试{Colors.RESET}")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 测试用户凭据
    test_user = {
        "username": f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
        "password": "Test123456!"
    }
    
    auth_token = None
    
    # ==================== 1. 健康检查 ====================
    print(f"\n{Colors.BOLD}1. 健康检查{Colors.RESET}")
    print("-" * 80)
    
    test_endpoint("GET", f"{BASE_URL}/", "Root endpoint")
    test_endpoint("GET", f"{API_BASE}/health", "Health check")
    
    # ==================== 2. 认证API ====================
    print(f"\n{Colors.BOLD}2. 认证API{Colors.RESET}")
    print("-" * 80)
    
    # 注册用户
    register_data = test_endpoint(
        "POST",
        f"{API_BASE}/users/register",
        "Register user",
        data=test_user,
        expected_status=201
    )
    
    if register_data:
        print(f"   User ID: {register_data.get('user_id', 'N/A')}")
    
    # 登录
    login_data = test_endpoint(
        "POST",
        f"{API_BASE}/users/login",
        "Login user",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        },
        expected_status=200
    )
    
    if login_data:
        auth_token = login_data.get("access_token")
        refresh_token = login_data.get("refresh_token")
        print(f"   Access Token: {auth_token[:20]}..." if auth_token else "   No token")
    
    # 刷新token
    if refresh_token:
        test_endpoint(
            "POST",
            f"{API_BASE}/auth/refresh",
            "Refresh token",
            data={"refresh_token": refresh_token},
            expected_status=200
        )
    
    # ==================== 3. 用户管理API ====================
    print(f"\n{Colors.BOLD}3. 用户管理API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping user management tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_endpoint("GET", f"{API_BASE}/users/me", "Get current user", headers=headers)
        test_endpoint("GET", f"{API_BASE}/users/me/profile", "Get user profile", headers=headers)
        test_endpoint("GET", f"{API_BASE}/users/me/preferences", "Get user preferences", headers=headers)
        test_endpoint("GET", f"{API_BASE}/users/me/stats", "Get user statistics", headers=headers)
        
        # 更新用户偏好
        test_endpoint(
            "PUT",
            f"{API_BASE}/users/me/preferences",
            "Update user preferences",
            headers=headers,
            data={"default_personality": "health_assistant", "language": "zh-CN"},
            expected_status=200
        )
        
        # 更新用户信息
        test_endpoint(
            "PUT",
            f"{API_BASE}/users/me",
            "Update current user",
            headers=headers,
            data={"display_name": "Test User"},
            expected_status=200
        )
    
    # ==================== 4. 模型API ====================
    print(f"\n{Colors.BOLD}4. 模型API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping model tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 列出所有模型
        models_data = test_endpoint("GET", f"{API_BASE}/models", "List models", headers=headers)
        
        if models_data:
            models = models_data.get("data", [])
            print(f"   Found {len(models)} models:")
            for model in models[:5]:  # 只显示前5个
                print(f"     - {model.get('id', 'N/A')} ({model.get('provider', 'N/A')})")
            
            # 获取特定模型详情
            if models:
                first_model_id = models[0].get("id")
                if first_model_id:
                    test_endpoint(
                        "GET",
                        f"{API_BASE}/models/{first_model_id}",
                        f"Get model details: {first_model_id}",
                        headers=headers
                    )
    
    # ==================== 5. 聊天API ====================
    print(f"\n{Colors.BOLD}5. 聊天API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping chat tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 列出引擎
        engines_data = test_endpoint("GET", f"{API_BASE}/chat/engines", "List engines", headers=headers)
        
        # 创建聊天补全（非流式）
        chat_data = test_endpoint(
            "POST",
            f"{API_BASE}/chat/completions",
            "Create chat completion (non-stream)",
            headers=headers,
            data={
                "messages": [
                    {"role": "user", "content": "Hello, say hi in one word"}
                ],
                "engine_type": "openai",
                "model": "gpt-4.1",
                "stream": False
            },
            expected_status=200
        )
        
        if chat_data:
            choices = chat_data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                print(f"   Response: {content[:50]}...")
    
    # ==================== 6. 人格API ====================
    print(f"\n{Colors.BOLD}6. 人格API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping personality tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 列出人格
        personalities_data = test_endpoint("GET", f"{API_BASE}/personalities", "List personalities", headers=headers)
        
        if personalities_data:
            personalities = personalities_data.get("personalities", [])
            print(f"   Found {len(personalities)} personalities")
            
            # 获取特定人格
            if personalities:
                first_personality_id = personalities[0].get("id")
                if first_personality_id:
                    # 尝试获取第一个可用的人格
                    personality_data = test_endpoint(
                        "GET",
                        f"{API_BASE}/personalities/{first_personality_id}",
                        f"Get personality: {first_personality_id}",
                        headers=headers
                    )
                    # 如果第一个失败，尝试其他
                    if not personality_data and len(personalities) > 1:
                        second_personality_id = personalities[1].get("id")
                        if second_personality_id:
                            test_endpoint(
                                "GET",
                                f"{API_BASE}/personalities/{second_personality_id}",
                                f"Get personality: {second_personality_id}",
                                headers=headers
                            )
    
    # ==================== 7. 会话API ====================
    print(f"\n{Colors.BOLD}7. 会话API{Colors.RESET}")
    print("-" * 80)
    
    session_id = None
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping session tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 创建会话（需要personality_id）
        personality_id = "health_assistant"  # 使用默认人格
        session_data = test_endpoint(
            "POST",
            f"{API_BASE}/sessions",
            "Create session",
            headers=headers,
            data={
                "personality_id": personality_id,
                "title": "Test Session"
            },
            expected_status=201
        )
        
        if session_data:
            session_id = session_data.get("session_id")
            print(f"   Session ID: {session_id}")
        
        # 列出会话
        test_endpoint("GET", f"{API_BASE}/sessions", "List sessions", headers=headers)
        
        # 获取会话详情
        if session_id:
            test_endpoint(
                "GET",
                f"{API_BASE}/sessions/{session_id}",
                "Get session details",
                headers=headers
            )
            
            # 更新会话
            test_endpoint(
                "PUT",
                f"{API_BASE}/sessions/{session_id}",
                "Update session",
                headers=headers,
                data={"title": "Updated Test Session"},
                expected_status=200
            )
    
    # ==================== 8. 记忆API ====================
    print(f"\n{Colors.BOLD}8. 记忆API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping memory tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 记忆健康检查
        test_endpoint("GET", f"{API_BASE}/memory/health", "Memory health check", headers=headers)
        
        # 创建记忆（需要user_id和session_id）
        user_id = register_data.get("user_id") if register_data else None
        if user_id and session_id:
            memory_data = test_endpoint(
                "POST",
                f"{API_BASE}/memory/",
                "Create memory",
                headers=headers,
                data={
                    "user_id": user_id,
                    "session_id": session_id,
                    "content": "This is a test memory",
                    "memory_type": "user",
                    "metadata": {"test": True}
                },
                expected_status=[200, 201]  # 接受200或201
            )
        else:
            print_test("Create memory", "SKIP", "No user_id or session_id available")
            memory_data = None
        
        memory_id = None
        if memory_data:
            memory_id = memory_data.get("memory_id")
            print(f"   Memory ID: {memory_id}")
        
        # 搜索记忆（需要user_id）
        if user_id:
            test_endpoint(
                "POST",
                f"{API_BASE}/memory/search",
                "Search memories",
                headers=headers,
                data={
                    "user_id": user_id,
                    "query": "test",
                    "limit": 10
                },
                expected_status=200
            )
        else:
            print_test("Search memories", "SKIP", "No user_id available")
        
        # 获取记忆统计
        if register_data:
            user_id = register_data.get("user_id")
            if user_id:
                test_endpoint(
                    "GET",
                    f"{API_BASE}/memory/stats/{user_id}",
                    "Get memory statistics",
                    headers=headers
                )
        
        # 删除记忆（需要user_id作为查询参数）
        if memory_id and user_id:
            test_endpoint(
                "DELETE",
                f"{API_BASE}/memory/{memory_id}?user_id={user_id}",
                "Delete memory",
                headers=headers,
                expected_status=200
            )
        else:
            print_test("Delete memory", "SKIP", "No memory_id or user_id available")
    
    # ==================== 9. 工具API ====================
    print(f"\n{Colors.BOLD}9. 工具API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping tool tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 列出工具
        tools_data = test_endpoint("GET", f"{API_BASE}/tools", "List tools", headers=headers)
        
        if tools_data:
            tools = tools_data.get("tools", [])
            print(f"   Found {len(tools)} tools")
            
            # 执行工具（如果有可用工具）
            if tools:
                first_tool = tools[0]
                tool_name = first_tool.get("name")
                if tool_name:
                    test_endpoint(
                        "POST",
                        f"{API_BASE}/tools/execute",
                        f"Execute tool: {tool_name}",
                        headers=headers,
                        data={
                            "tool_name": tool_name,
                            "arguments": {}
                        },
                        expected_status=200
                    )
    
    # ==================== 10. 音频API ====================
    print(f"\n{Colors.BOLD}10. 音频API{Colors.RESET}")
    print("-" * 80)
    
    if not auth_token:
        print(f"{Colors.YELLOW}⚠ Skipping audio tests (no auth token){Colors.RESET}\n")
    else:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 注意：音频API需要实际的文件，这里只测试端点是否存在
        print_test("Audio transcription endpoint", "SKIP", "Requires audio file")
        print_test("Audio speech endpoint", "SKIP", "Requires text input")
    
    # ==================== 清理 ====================
    print(f"\n{Colors.BOLD}11. 清理{Colors.RESET}")
    print("-" * 80)
    
    if auth_token and session_id:
        headers = {"Authorization": f"Bearer {auth_token}"}
        test_endpoint(
            "DELETE",
            f"{API_BASE}/sessions/{session_id}",
            "Delete test session",
            headers=headers,
            expected_status=200
        )
    
    # ==================== 测试总结 ====================
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}测试总结{Colors.RESET}")
    print(f"{'='*80}")
    print(f"{Colors.GREEN}通过: {test_results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}失败: {test_results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}跳过: {test_results['skipped']}{Colors.RESET}")
    print(f"总计: {test_results['passed'] + test_results['failed'] + test_results['skipped']}")
    
    if test_results['errors']:
        print(f"\n{Colors.RED}错误详情:{Colors.RESET}")
        for error in test_results['errors']:
            print(f"  - {error}")
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    # 返回退出码
    return 0 if test_results['failed'] == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试脚本错误: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

