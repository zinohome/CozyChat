"""
计算器工具

提供数学计算功能
"""

# 标准库
import math
import operator
from typing import Any, Dict

# 本地库
from app.engines.tools.base import Tool, ToolType
from app.utils.logger import logger


class CalculatorTool(Tool):
    """计算器工具
    
    支持基本数学运算、科学计算等
    """
    
    def __init__(self):
        """初始化计算器工具"""
        super().__init__(tool_type=ToolType.BUILTIN)
        # 安全的数学函数字典
        self.safe_functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "floor": math.floor,
            "ceil": math.ceil,
            "pi": math.pi,
            "e": math.e,
        }
        # 安全的运算符字典
        self.safe_operators = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "//": operator.floordiv,
            "%": operator.mod,
            "**": operator.pow,
        }
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "calculator"
    
    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "执行数学计算。支持基本运算（加减乘除）、科学计算（三角函数、对数等）、"
            "以及复杂表达式计算。适用于需要数值计算、数学运算的场景。"
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数schema"""
        return {
            "expression": {
                "type": "string",
                "description": "数学表达式，例如：'2 + 3 * 4'、'sqrt(16)'、'sin(pi/2)'",
                "required": True
            }
        }
    
    async def execute(self, expression: str) -> str:
        """执行数学计算
        
        Args:
            expression: 数学表达式
            
        Returns:
            str: 计算结果或错误信息
        """
        try:
            # 验证表达式安全性
            if not self._is_safe_expression(expression):
                return "错误：表达式包含不安全的字符或操作"
            
            # 构建安全的执行环境
            safe_dict = {
                "__builtins__": {},
                **self.safe_functions,
            }
            
            # 执行计算
            result = eval(expression, safe_dict)
            
            # 格式化结果
            if isinstance(result, float):
                # 如果是整数，显示为整数
                if result.is_integer():
                    result = int(result)
                else:
                    # 保留合理的小数位数
                    result = round(result, 10)
            
            logger.info(
                f"Calculator executed: {expression} = {result}",
                extra={"expression": expression, "result": result}
            )
            
            return str(result)
            
        except ZeroDivisionError:
            error_msg = "错误：除以零"
            logger.warning(f"Calculator error: {error_msg}")
            return error_msg
        except ValueError as e:
            error_msg = f"错误：无效的表达式 - {str(e)}"
            logger.warning(f"Calculator error: {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"错误：计算失败 - {str(e)}"
            logger.error(f"Calculator error: {error_msg}", exc_info=True)
            return error_msg
    
    def _is_safe_expression(self, expression: str) -> bool:
        """检查表达式是否安全
        
        Args:
            expression: 数学表达式
            
        Returns:
            bool: 是否安全
        """
        # 禁止的危险字符和关键字
        dangerous = [
            "import",
            "exec",
            "eval",
            "__",
            "open",
            "file",
            "input",
            "raw_input",
            "compile",
            "reload",
            "__import__",
            "exit",
            "quit",
            "help",
            "license",
            "credits",
            "copyright",
            "vars",
            "dir",
            "globals",
            "locals",
        ]
        
        expression_lower = expression.lower()
        for item in dangerous:
            if item in expression_lower:
                return False
        
        # 只允许字母、数字、运算符、括号、空格、点号
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "+-*/%()[]{}., "
        )
        
        if not all(c in allowed_chars for c in expression):
            return False
        
        return True

