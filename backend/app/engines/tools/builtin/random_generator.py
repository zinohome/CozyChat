"""
随机数生成器工具

提供各种随机数生成功能
"""

# 标准库
import random
import string
import uuid
from typing import Any, Dict, Optional

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class RandomGeneratorTool(Tool):
    """随机数生成器工具
    
    提供随机数、随机字符串、UUID等生成功能
    """
    
    def __init__(self):
        """初始化随机数生成器工具"""
        super().__init__(tool_type=ToolType.BUILTIN)
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "random_generator"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "生成各种类型的随机数据。支持："
            "随机整数（指定范围）、随机浮点数（指定范围）、"
            "随机字符串（指定长度和字符集）、"
            "随机选择（从列表中随机选择元素）、"
            "UUID生成（标准UUID格式）。"
            "适用于需要生成随机数据、随机选择、唯一标识符等场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "type": {
                "type": "string",
                "description": "生成类型。可选值：'integer'（随机整数）、'float'（随机浮点数）、'string'（随机字符串）、'choice'（随机选择）、'uuid'（UUID）。",
                "required": True
            },
            "min": {
                "type": "number",
                "description": "最小值（仅用于integer和float类型）。对于integer，默认为0；对于float，默认为0.0",
                "required": False
            },
            "max": {
                "type": "number",
                "description": "最大值（仅用于integer和float类型）。对于integer，默认为100；对于float，默认为1.0",
                "required": False
            },
            "length": {
                "type": "integer",
                "description": "字符串长度（仅用于string类型），默认10",
                "required": False
            },
            "charset": {
                "type": "string",
                "description": "字符集类型（仅用于string类型）。可选值：'alphanumeric'（字母数字，默认）、'letters'（仅字母）、'digits'（仅数字）、'hex'（十六进制）、'custom'（自定义，需配合custom_chars参数）",
                "required": False
            },
            "custom_chars": {
                "type": "string",
                "description": "自定义字符集（仅用于string类型，当charset='custom'时使用）",
                "required": False
            },
            "choices": {
                "type": "array",
                "description": "选择列表（仅用于choice类型），例如：['选项1', '选项2', '选项3']",
                "items": {
                    "type": "string"
                },
                "required": False
            },
            "count": {
                "type": "integer",
                "description": "生成数量（可选），默认为1。可以生成多个随机值",
                "required": False
            }
        }
    
    async def execute(
        self,
        type: str,
        min: Optional[float] = None,
        max: Optional[float] = None,
        length: Optional[int] = None,
        charset: Optional[str] = None,
        custom_chars: Optional[str] = None,
        choices: Optional[list] = None,
        count: Optional[int] = None
    ) -> str:
        """执行随机数生成
        
        Args:
            type: 生成类型
            min: 最小值
            max: 最大值
            length: 字符串长度
            charset: 字符集类型
            custom_chars: 自定义字符集
            choices: 选择列表
            count: 生成数量
            
        Returns:
            str: 生成的随机值或错误信息
        """
        try:
            type_lower = type.lower().strip()
            count = count or 1
            
            if count < 1:
                return "错误：count必须大于等于1"
            
            if count > 100:
                return "错误：count不能超过100（防止生成过多数据）"
            
            # 根据类型生成随机值
            if type_lower == "integer":
                result = self._generate_integer(min, max, count)
            elif type_lower == "float":
                result = self._generate_float(min, max, count)
            elif type_lower == "string":
                result = self._generate_string(length, charset, custom_chars, count)
            elif type_lower == "choice":
                result = self._generate_choice(choices, count)
            elif type_lower == "uuid":
                result = self._generate_uuid(count)
            else:
                return f"错误：不支持的生成类型 '{type}'，可选值：'integer'、'float'、'string'、'choice'、'uuid'"
            
            logger.info(
                f"Random generator executed: type={type}, count={count}",
                extra={"type": type, "count": count}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"错误：随机数生成失败 - {str(e)}"
            logger.error(f"Random generator error: {error_msg}", exc_info=True)
            return error_msg
    
    def _generate_integer(
        self,
        min_val: Optional[float],
        max_val: Optional[float],
        count: int
    ) -> str:
        """生成随机整数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            count: 生成数量
            
        Returns:
            str: 生成的随机整数（字符串）
        """
        min_val = int(min_val) if min_val is not None else 0
        max_val = int(max_val) if max_val is not None else 100
        
        if min_val >= max_val:
            return f"错误：min ({min_val}) 必须小于 max ({max_val})"
        
        if count == 1:
            result = random.randint(min_val, max_val)
            return str(result)
        else:
            results = [random.randint(min_val, max_val) for _ in range(count)]
            return ", ".join(map(str, results))
    
    def _generate_float(
        self,
        min_val: Optional[float],
        max_val: Optional[float],
        count: int
    ) -> str:
        """生成随机浮点数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            count: 生成数量
            
        Returns:
            str: 生成的随机浮点数（字符串）
        """
        min_val = float(min_val) if min_val is not None else 0.0
        max_val = float(max_val) if max_val is not None else 1.0
        
        if min_val >= max_val:
            return f"错误：min ({min_val}) 必须小于 max ({max_val})"
        
        if count == 1:
            result = random.uniform(min_val, max_val)
            return f"{result:.6f}".rstrip('0').rstrip('.')
        else:
            results = [random.uniform(min_val, max_val) for _ in range(count)]
            return ", ".join([f"{r:.6f}".rstrip('0').rstrip('.') for r in results])
    
    def _generate_string(
        self,
        length: Optional[int],
        charset: Optional[str],
        custom_chars: Optional[str],
        count: int
    ) -> str:
        """生成随机字符串
        
        Args:
            length: 字符串长度
            charset: 字符集类型
            custom_chars: 自定义字符集
            count: 生成数量
            
        Returns:
            str: 生成的随机字符串
        """
        length = length or 10
        
        if length < 1:
            return "错误：length必须大于等于1"
        
        if length > 1000:
            return "错误：length不能超过1000（防止生成过长字符串）"
        
        # 确定字符集
        charset = charset or "alphanumeric"
        charset_lower = charset.lower().strip()
        
        if charset_lower == "custom":
            if not custom_chars:
                return "错误：使用custom字符集时必须提供custom_chars参数"
            chars = custom_chars
        elif charset_lower == "alphanumeric":
            chars = string.ascii_letters + string.digits
        elif charset_lower == "letters":
            chars = string.ascii_letters
        elif charset_lower == "digits":
            chars = string.digits
        elif charset_lower == "hex":
            chars = string.hexdigits.lower()
        else:
            return f"错误：不支持的字符集类型 '{charset}'，可选值：'alphanumeric'、'letters'、'digits'、'hex'、'custom'"
        
        if not chars:
            return "错误：字符集不能为空"
        
        if count == 1:
            result = ''.join(random.choice(chars) for _ in range(length))
            return result
        else:
            results = [''.join(random.choice(chars) for _ in range(length)) for _ in range(count)]
            return ", ".join(results)
    
    def _generate_choice(
        self,
        choices: Optional[list],
        count: int
    ) -> str:
        """随机选择
        
        Args:
            choices: 选择列表
            count: 生成数量
            
        Returns:
            str: 随机选择的结果
        """
        if not choices:
            return "错误：使用choice类型时必须提供choices参数"
        
        if not isinstance(choices, list):
            return "错误：choices必须是一个列表"
        
        if len(choices) == 0:
            return "错误：choices列表不能为空"
        
        if count == 1:
            result = random.choice(choices)
            return str(result)
        else:
            # 允许重复选择
            results = [random.choice(choices) for _ in range(count)]
            return ", ".join(map(str, results))
    
    def _generate_uuid(self, count: int) -> str:
        """生成UUID
        
        Args:
            count: 生成数量
            
        Returns:
            str: 生成的UUID
        """
        if count == 1:
            result = str(uuid.uuid4())
            return result
        else:
            results = [str(uuid.uuid4()) for _ in range(count)]
            return ", ".join(results)

