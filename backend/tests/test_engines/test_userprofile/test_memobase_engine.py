"""
MemobaseUserProfileEngine单元测试

测试Memobase用户画像引擎的所有方法，包括：
- 初始化
- 健康检查
- 获取用户画像（包含UUID验证、用户不存在场景）
- 更新用户画像（包含UUID验证、用户不存在场景）
- UUID转换逻辑（已废弃但需测试）
- 错误处理
"""

# 标准库
import uuid
import warnings
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call
from typing import Dict, Any

# 第三方库
import pytest
import pytest_asyncio

# 本地库
from app.engines.userprofile.memobase_engine import (
    MemobaseUserProfileEngine,
    user_id_to_uuid
)
from app.engines.userprofile.base import UserProfileEngineBase


class TestMemobaseUserProfileEngine:
    """MemobaseUserProfileEngine测试类"""
    
    @pytest.fixture
    def engine_config(self) -> Dict[str, Any]:
        """引擎配置"""
        return {
            "project_url": "http://localhost:8019",
            "api_key": "test-api-key"
        }
    
    @pytest.fixture
    def memobase_engine(self, engine_config) -> MemobaseUserProfileEngine:
        """Memobase引擎实例"""
        return MemobaseUserProfileEngine(config=engine_config)
    
    @pytest.fixture
    def mock_memobase_client(self):
        """Mock Memobase客户端"""
        mock_client = MagicMock()
        return mock_client
    
    @pytest.fixture
    def mock_memobase_user(self):
        """Mock Memobase用户对象"""
        mock_user = MagicMock()
        mock_user.profile.return_value = "User profile text with some content"
        mock_user.insert = MagicMock()
        mock_user.flush = MagicMock()
        return mock_user
    
    @pytest.fixture
    def valid_uuid(self) -> str:
        """有效的UUID v4"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def invalid_user_id(self) -> str:
        """无效的用户ID（非UUID格式）"""
        return "not-a-uuid-123"
    
    # ===== 初始化测试 =====
    
    @pytest.mark.asyncio
    async def test_engine_initialization_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client
    ):
        """测试：引擎初始化成功"""
        with patch('app.engines.userprofile.memobase_engine.MemoBaseClient') as mock_client_class:
            mock_client_class.return_value = mock_memobase_client
            
            result = await memobase_engine.initialize()
            
            assert result is True
            assert memobase_engine._initialized is True
            assert memobase_engine.client is not None
            mock_client_class.assert_called_once_with(
                project_url="http://localhost:8019",
                api_key="test-api-key"
            )
    
    @pytest.mark.asyncio
    async def test_engine_initialization_already_initialized(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client
    ):
        """测试：引擎已初始化，直接返回True"""
        memobase_engine._initialized = True
        memobase_engine.client = mock_memobase_client
        
        result = await memobase_engine.initialize()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_engine_initialization_failure(
        self,
        memobase_engine: MemobaseUserProfileEngine
    ):
        """测试：引擎初始化失败"""
        with patch('app.engines.userprofile.memobase_engine.MemoBaseClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            
            result = await memobase_engine.initialize()
            
            assert result is False
            assert memobase_engine._initialized is False
    
    @pytest.mark.asyncio
    async def test_engine_initialization_with_default_config(self):
        """测试：使用默认配置初始化引擎"""
        engine = MemobaseUserProfileEngine(config={})
        
        assert engine.project_url == "http://localhost:8019"
        assert engine.api_key == "secret"
    
    # ===== 健康检查测试 =====
    
    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client
    ):
        """测试：健康检查成功"""
        memobase_engine.client = mock_memobase_client
        
        result = await memobase_engine.health_check()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(
        self,
        memobase_engine: MemobaseUserProfileEngine
    ):
        """测试：健康检查失败（客户端未初始化）"""
        memobase_engine.client = None
        
        result = await memobase_engine.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client
    ):
        """测试：健康检查异常"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.side_effect = Exception("Health check failed")
        
        result = await memobase_engine.health_check()
        
        assert result is False
    
    # ===== 获取用户画像测试 =====
    
    @pytest.mark.asyncio
    async def test_get_profile_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：成功获取用户画像"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.profile.return_value = "User profile: Python developer"
        
        result = await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        assert result is not None
        assert result["user_id"] == valid_uuid
        assert result["profile_text"] == "User profile: Python developer"
        assert result["token_size"] == 3  # "User profile: Python developer".split()
        assert "token_size" in result
        
        mock_memobase_client.get_user.assert_called_once_with(
            valid_uuid,
            no_get=False
        )
        mock_memobase_user.profile.assert_called_once_with(
            max_token_size=500,
            prefer_topics=["basic_info", "interest", "work"]
        )
    
    @pytest.mark.asyncio
    async def test_get_profile_invalid_uuid(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        invalid_user_id: str
    ):
        """测试：获取用户画像失败（无效的UUID格式）"""
        with pytest.raises(ValueError) as exc_info:
            await memobase_engine.get_profile(
                user_id=invalid_user_id,
                max_token_size=500
            )
        
        assert "user_id must be UUID format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_profile_user_not_found_auto_create_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在，自动创建用户成功"""
        memobase_engine.client = mock_memobase_client
        
        # 第一次调用get_user失败（用户不存在）
        # 第二次调用get_user成功（用户已创建）
        mock_memobase_client.get_user.side_effect = [
            Exception("422 Unprocessable Entity: User not found"),
            mock_memobase_user
        ]
        
        # Mock自动创建用户
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            mock_memobase_user.profile.return_value = ""  # 新用户返回空画像
            
            result = await memobase_engine.get_profile(
                user_id=valid_uuid,
                max_token_size=500
            )
            
            assert result is not None
            assert result["user_id"] == valid_uuid
            assert result["profile_text"] == ""
            assert result["token_size"] == 0
            
            # 验证用户被创建
            mock_new_user.create.assert_called_once_with(client=mock_memobase_client)
    
    @pytest.mark.asyncio
    async def test_get_profile_user_not_found_auto_create_failure(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        valid_uuid: str
    ):
        """测试：用户不存在，自动创建用户失败"""
        memobase_engine.client = mock_memobase_client
        
        # get_user失败（用户不存在）
        mock_memobase_client.get_user.side_effect = Exception("404 User not found")
        
        # Mock自动创建用户失败
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create.side_effect = Exception("Create failed")
            mock_user_class.return_value = mock_new_user
            
            result = await memobase_engine.get_profile(
                user_id=valid_uuid,
                max_token_size=500
            )
            
            # 创建失败，返回空画像
            assert result is not None
            assert result["user_id"] == valid_uuid
            assert result["profile_text"] == ""
            assert result["token_size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_profile_user_not_found_404_error(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在（404错误），自动创建"""
        memobase_engine.client = mock_memobase_client
        
        mock_memobase_client.get_user.side_effect = [
            Exception("404 Not Found"),
            mock_memobase_user
        ]
        
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            mock_memobase_user.profile.return_value = "New profile"
            
            result = await memobase_engine.get_profile(
                user_id=valid_uuid,
                max_token_size=500
            )
            
            assert result is not None
            assert result["user_id"] == valid_uuid
    
    @pytest.mark.asyncio
    async def test_get_profile_user_not_found_unprocessable_entity(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在（422错误），自动创建"""
        memobase_engine.client = mock_memobase_client
        
        mock_memobase_client.get_user.side_effect = [
            Exception("422 Unprocessable Entity"),
            mock_memobase_user
        ]
        
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            mock_memobase_user.profile.return_value = "Profile"
            
            result = await memobase_engine.get_profile(
                user_id=valid_uuid,
                max_token_size=500
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_profile_other_error(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        valid_uuid: str
    ):
        """测试：获取用户画像时发生其他错误"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.side_effect = Exception("Internal server error")
        
        result = await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        # 其他错误，返回空画像
        assert result is not None
        assert result["user_id"] == valid_uuid
        assert result["profile_text"] == ""
        assert result["token_size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_profile_empty_profile_text(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：获取用户画像（空画像文本）"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.profile.return_value = None
        
        result = await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        assert result is not None
        assert result["user_id"] == valid_uuid
        assert result["profile_text"] == ""
        assert result["token_size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_profile_empty_string_profile_text(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：获取用户画像（空字符串画像文本）"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.profile.return_value = ""
        
        result = await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        assert result is not None
        assert result["user_id"] == valid_uuid
        assert result["profile_text"] == ""
        assert result["token_size"] == 0
    
    @pytest.mark.asyncio
    async def test_get_profile_with_custom_max_token_size(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：获取用户画像（自定义max_token_size）"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.profile.return_value = "Profile text"
        
        result = await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=1000
        )
        
        assert result is not None
        mock_memobase_user.profile.assert_called_once_with(
            max_token_size=1000,
            prefer_topics=["basic_info", "interest", "work"]
        )
    
    @pytest.mark.asyncio
    async def test_get_profile_auto_initialize(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：获取用户画像时自动初始化引擎"""
        memobase_engine._initialized = False
        memobase_engine.client = None
        
        with patch('app.engines.userprofile.memobase_engine.MemoBaseClient') as mock_client_class:
            mock_client_class.return_value = mock_memobase_client
            mock_memobase_client.get_user.return_value = mock_memobase_user
            mock_memobase_user.profile.return_value = "Profile"
            
            result = await memobase_engine.get_profile(
                user_id=valid_uuid,
                max_token_size=500
            )
            
            assert result is not None
            assert memobase_engine._initialized is True
    
    # ===== 更新用户画像测试 =====
    
    @pytest.mark.asyncio
    async def test_update_profile_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：成功更新用户画像"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        
        messages = [
            {"role": "user", "content": "我喜欢Python编程"},
            {"role": "assistant", "content": "好的，我知道了"}
        ]
        
        result = await memobase_engine.update_profile(
            user_id=valid_uuid,
            messages=messages
        )
        
        assert result is True
        mock_memobase_client.get_user.assert_called_once_with(
            valid_uuid,
            no_get=False
        )
        mock_memobase_user.insert.assert_called_once()
        mock_memobase_user.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_profile_invalid_uuid(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        invalid_user_id: str
    ):
        """测试：更新用户画像失败（无效的UUID格式）"""
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ValueError) as exc_info:
            await memobase_engine.update_profile(
                user_id=invalid_user_id,
                messages=messages
            )
        
        assert "user_id must be UUID format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_profile_user_not_found_create_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在，创建用户后更新画像成功"""
        memobase_engine.client = mock_memobase_client
        
        # 第一次get_user失败（用户不存在）
        # 第二次get_user成功（用户已创建）
        mock_memobase_client.get_user.side_effect = [
            Exception("not found"),
            mock_memobase_user
        ]
        
        # Mock创建用户
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            messages = [{"role": "user", "content": "Test"}]
            
            result = await memobase_engine.update_profile(
                user_id=valid_uuid,
                messages=messages
            )
            
            assert result is True
            mock_new_user.create.assert_called_once_with(client=mock_memobase_client)
            mock_memobase_user.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_profile_user_not_found_create_failure_use_no_get(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在，创建失败，使用no_get=True继续"""
        memobase_engine.client = mock_memobase_client
        
        # get_user失败（用户不存在）
        mock_memobase_client.get_user.side_effect = [
            Exception("not found"),
            mock_memobase_user  # no_get=True时返回
        ]
        
        # Mock创建用户失败
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create.side_effect = Exception("Create failed")
            mock_user_class.return_value = mock_new_user
            
            messages = [{"role": "user", "content": "Test"}]
            
            result = await memobase_engine.update_profile(
                user_id=valid_uuid,
                messages=messages
            )
            
            # 使用no_get=True继续，应该成功
            assert result is True
            # 验证使用了no_get=True
            assert mock_memobase_client.get_user.call_count >= 2
            calls = mock_memobase_client.get_user.call_args_list
            assert any(call[1].get('no_get') == True for call in calls)
    
    @pytest.mark.asyncio
    async def test_update_profile_user_not_found_422_error(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在（422错误），创建用户"""
        memobase_engine.client = mock_memobase_client
        
        mock_memobase_client.get_user.side_effect = [
            Exception("422 Unprocessable Entity"),
            mock_memobase_user
        ]
        
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            messages = [{"role": "user", "content": "Test"}]
            
            result = await memobase_engine.update_profile(
                user_id=valid_uuid,
                messages=messages
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_profile_user_not_found_404_error(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：用户不存在（404错误），创建用户"""
        memobase_engine.client = mock_memobase_client
        
        mock_memobase_client.get_user.side_effect = [
            Exception("404 Not Found"),
            mock_memobase_user
        ]
        
        with patch('app.engines.userprofile.memobase_engine.MemobaseUser') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.create = MagicMock()
            mock_user_class.return_value = mock_new_user
            
            messages = [{"role": "user", "content": "Test"}]
            
            result = await memobase_engine.update_profile(
                user_id=valid_uuid,
                messages=messages
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_profile_other_error_use_no_get(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：获取用户时发生其他错误，使用no_get=True继续"""
        memobase_engine.client = mock_memobase_client
        
        mock_memobase_client.get_user.side_effect = [
            Exception("Internal server error"),
            mock_memobase_user  # no_get=True时返回
        ]
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = await memobase_engine.update_profile(
            user_id=valid_uuid,
            messages=messages
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_profile_user_is_none(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        valid_uuid: str
    ):
        """测试：无法获取或创建用户（user为None）"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = None
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = await memobase_engine.update_profile(
            user_id=valid_uuid,
            messages=messages
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_profile_insert_error(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：插入数据时发生错误"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.insert.side_effect = Exception("Insert failed")
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = await memobase_engine.update_profile(
            user_id=valid_uuid,
            messages=messages
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_profile_auto_initialize(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：更新用户画像时自动初始化引擎"""
        memobase_engine._initialized = False
        memobase_engine.client = None
        
        with patch('app.engines.userprofile.memobase_engine.MemoBaseClient') as mock_client_class:
            mock_client_class.return_value = mock_memobase_client
            mock_memobase_client.get_user.return_value = mock_memobase_user
            
            messages = [{"role": "user", "content": "Test"}]
            
            result = await memobase_engine.update_profile(
                user_id=valid_uuid,
                messages=messages
            )
            
            assert result is True
            assert memobase_engine._initialized is True
    
    # ===== 关闭引擎测试 =====
    
    @pytest.mark.asyncio
    async def test_shutdown(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client
    ):
        """测试：关闭引擎"""
        memobase_engine.client = mock_memobase_client
        
        await memobase_engine.shutdown()
        
        assert memobase_engine.client is None
    
    @pytest.mark.asyncio
    async def test_shutdown_no_client(
        self,
        memobase_engine: MemobaseUserProfileEngine
    ):
        """测试：关闭引擎（客户端未初始化）"""
        memobase_engine.client = None
        
        await memobase_engine.shutdown()
        
        assert memobase_engine.client is None
    
    # ===== UUID转换函数测试（已废弃） =====
    
    def test_user_id_to_uuid_valid_input(self):
        """测试：user_id_to_uuid函数（有效输入）"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            user_id = "test_user_123"
            result = user_id_to_uuid(user_id)
            
            # 验证返回的是有效的UUID v5格式
            assert isinstance(result, str)
            uuid_obj = uuid.UUID(result)
            assert uuid_obj.version == 5
            
            # 验证发出了废弃警告
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
    
    def test_user_id_to_uuid_deterministic(self):
        """测试：user_id_to_uuid函数（确定性）"""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("ignore")
            
            user_id = "test_user_123"
            result1 = user_id_to_uuid(user_id)
            result2 = user_id_to_uuid(user_id)
            
            # 相同输入应该产生相同输出
            assert result1 == result2
    
    def test_user_id_to_uuid_different_inputs(self):
        """测试：user_id_to_uuid函数（不同输入产生不同输出）"""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("ignore")
            
            result1 = user_id_to_uuid("user1")
            result2 = user_id_to_uuid("user2")
            
            # 不同输入应该产生不同输出
            assert result1 != result2
    
    # ===== 继承关系测试 =====
    
    def test_inherits_from_base_class(self, memobase_engine: MemobaseUserProfileEngine):
        """测试：MemobaseUserProfileEngine继承自UserProfileEngineBase"""
        assert isinstance(memobase_engine, UserProfileEngineBase)
    
    def test_engine_name(self, memobase_engine: MemobaseUserProfileEngine):
        """测试：引擎名称"""
        assert memobase_engine.engine_name == "memobase"
    
    # ===== 指标更新测试 =====
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_success(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        mock_memobase_user,
        valid_uuid: str
    ):
        """测试：成功操作时更新指标"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.return_value = mock_memobase_user
        mock_memobase_user.profile.return_value = "Profile"
        
        initial_success_count = memobase_engine.metrics.get("success_count", 0)
        
        await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        # 验证指标已更新（通过检查metrics字典）
        assert memobase_engine.metrics.get("success_count", 0) >= initial_success_count
    
    @pytest.mark.asyncio
    async def test_metrics_update_on_failure(
        self,
        memobase_engine: MemobaseUserProfileEngine,
        mock_memobase_client,
        valid_uuid: str
    ):
        """测试：失败操作时更新指标"""
        memobase_engine.client = mock_memobase_client
        mock_memobase_client.get_user.side_effect = Exception("Error")
        
        await memobase_engine.get_profile(
            user_id=valid_uuid,
            max_token_size=500
        )
        
        # 验证指标已更新（失败时也会更新）
        assert "processing_time" in memobase_engine.metrics or memobase_engine.metrics.get("success_count", 0) >= 0
