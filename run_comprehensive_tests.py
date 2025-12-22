#!/usr/bin/env python3
"""
CozyChat v1.1.0 完整测试运行脚本

使用方法:
    python run_comprehensive_tests.py                  # 运行所有测试
    python run_comprehensive_tests.py --quick          # 快速测试（跳过慢速测试）
    python run_comprehensive_tests.py --engines        # 只测试三大引擎
    python run_comprehensive_tests.py --api            # 只测试API
    python run_comprehensive_tests.py --performance    # 只测试性能
    python run_comprehensive_tests.py --coverage       # 生成覆盖率报告
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print(f"{Colors.ENDC}")


def print_success(text):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text):
    """打印信息消息"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def run_command(cmd, cwd=None):
    """运行命令"""
    print_info(f"运行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result


def check_environment():
    """检查测试环境"""
    print_header("检查测试环境")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 11):
        print_success(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print_error(f"Python版本过低: {python_version.major}.{python_version.minor}")
        return False
    
    # 检查pytest
    result = run_command(["pytest", "--version"])
    if result.returncode == 0:
        print_success(f"pytest已安装: {result.stdout.strip()}")
    else:
        print_error("pytest未安装")
        return False
    
    # 检查数据库连接
    print_info("检查数据库连接...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://cozychat:passw0rd@192.168.66.10:5432/cozychat_test",
            connect_timeout=3
        )
        conn.close()
        print_success("数据库连接正常")
    except Exception as e:
        print_warning(f"数据库连接失败: {e}")
        print_warning("将跳过需要数据库的测试")
    
    # 检查三大引擎服务
    print_info("检查三大引擎服务...")
    engines_ok = True
    
    try:
        import httpx
        # Cognee
        try:
            response = httpx.get("http://192.168.66.11:8000/health", timeout=3)
            if response.status_code == 200:
                print_success("Cognee服务可用 (192.168.66.11:8000)")
            else:
                print_warning("Cognee服务响应异常")
                engines_ok = False
        except:
            print_warning("Cognee服务不可用")
            engines_ok = False
        
        # Memobase
        try:
            response = httpx.get("http://192.168.66.11:8019/health", timeout=3)
            if response.status_code == 200:
                print_success("Memobase服务可用 (192.168.66.11:8019)")
            else:
                print_warning("Memobase服务响应异常")
                engines_ok = False
        except:
            print_warning("Memobase服务不可用")
            engines_ok = False
        
        # Mem0
        try:
            response = httpx.get("http://192.168.66.11:8888/health", timeout=3)
            if response.status_code == 200:
                print_success("Mem0服务可用 (192.168.66.11:8888)")
            else:
                print_warning("Mem0服务响应异常")
                engines_ok = False
        except:
            print_warning("Mem0服务不可用")
            engines_ok = False
        
        if not engines_ok:
            print_warning("部分引擎服务不可用，相关测试将被跳过")
    
    except ImportError:
        print_warning("httpx未安装，无法检查引擎服务")
    
    return True


def run_all_tests(backend_dir, args):
    """运行所有测试"""
    print_header("运行完整测试套件")
    
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--durations=10",
        "-W", "ignore::DeprecationWarning"
    ]
    
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])
    
    if args.quick:
        cmd.extend(["-m", "not slow"])
        print_info("跳过慢速测试（--quick模式）")
    
    result = run_command(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print_success("所有测试通过！")
        if args.coverage:
            print_info(f"覆盖率报告: {backend_dir}/htmlcov/index.html")
        return True
    else:
        print_error("部分测试失败")
        print(result.stdout)
        print(result.stderr)
        return False


def run_engine_tests(backend_dir):
    """运行三大引擎测试"""
    print_header("运行三大引擎测试")
    
    cmd = [
        "pytest",
        "tests/test_v1_1_comprehensive.py",
        "-v",
        "-k", "Engine",
        "--tb=short"
    ]
    
    result = run_command(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print_success("引擎测试通过！")
        return True
    else:
        print_error("引擎测试失败")
        print(result.stdout)
        return False


def run_api_tests(backend_dir):
    """运行API测试"""
    print_header("运行API接口测试")
    
    cmd = [
        "pytest",
        "tests/test_v1_1_comprehensive.py::TestV11APIs",
        "-v",
        "--tb=short"
    ]
    
    result = run_command(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print_success("API测试通过！")
        return True
    else:
        print_error("API测试失败")
        print(result.stdout)
        return False


def run_performance_tests(backend_dir):
    """运行性能测试"""
    print_header("运行性能测试")
    
    cmd = [
        "pytest",
        "tests/test_v1_1_comprehensive.py::TestPerformance",
        "-v",
        "-m", "slow",
        "--tb=short",
        "--durations=0"
    ]
    
    result = run_command(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print_success("性能测试通过！")
        return True
    else:
        print_error("性能测试失败")
        print(result.stdout)
        return False


def run_regression_tests(backend_dir):
    """运行回归测试"""
    print_header("运行回归测试")
    
    cmd = [
        "pytest",
        "tests/test_v1_1_comprehensive.py::TestRegression",
        "-v",
        "--tb=short"
    ]
    
    result = run_command(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print_success("回归测试通过！")
        return True
    else:
        print_error("回归测试失败")
        print(result.stdout)
        return False


def generate_test_report(backend_dir, test_results):
    """生成测试报告"""
    print_header("生成测试报告")
    
    report_path = backend_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# CozyChat v1.1.0 测试报告\n\n")
        f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 测试结果\n\n")
        
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results.values() if r)
        
        f.write(f"- **总计**: {total_tests} 个测试套件\n")
        f.write(f"- **通过**: {passed_tests} 个\n")
        f.write(f"- **失败**: {total_tests - passed_tests} 个\n")
        f.write(f"- **通过率**: {passed_tests/total_tests*100:.1f}%\n\n")
        
        f.write("## 详细结果\n\n")
        for test_name, result in test_results.items():
            status = "✓ 通过" if result else "✗ 失败"
            f.write(f"- **{test_name}**: {status}\n")
        
        f.write("\n## 环境信息\n\n")
        f.write(f"- Python版本: {sys.version}\n")
        f.write(f"- 平台: {sys.platform}\n")
        f.write(f"- 工作目录: {os.getcwd()}\n")
    
    print_success(f"测试报告已生成: {report_path}")
    return report_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CozyChat v1.1.0 完整测试运行脚本"
    )
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="快速测试（跳过慢速测试）"
    )
    parser.add_argument(
        "--engines",
        action="store_true",
        help="只测试三大引擎"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="只测试API接口"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="只测试性能"
    )
    parser.add_argument(
        "--regression",
        action="store_true",
        help="只测试回归"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成覆盖率报告"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="跳过环境检查"
    )
    
    args = parser.parse_args()
    
    # 获取backend目录
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"
    
    if not backend_dir.exists():
        print_error(f"backend目录不存在: {backend_dir}")
        return 1
    
    print_header("CozyChat v1.1.0 完整覆盖性测试")
    print_info(f"Backend目录: {backend_dir}")
    
    # 检查环境
    if not args.no_check:
        if not check_environment():
            print_error("环境检查失败")
            return 1
    
    # 运行测试
    test_results = {}
    
    if args.engines:
        test_results["三大引擎测试"] = run_engine_tests(backend_dir)
    elif args.api:
        test_results["API测试"] = run_api_tests(backend_dir)
    elif args.performance:
        test_results["性能测试"] = run_performance_tests(backend_dir)
    elif args.regression:
        test_results["回归测试"] = run_regression_tests(backend_dir)
    else:
        # 运行所有测试
        test_results["完整测试套件"] = run_all_tests(backend_dir, args)
    
    # 生成报告
    if test_results:
        report_path = generate_test_report(backend_dir, test_results)
    
    # 总结
    print_header("测试完成")
    passed = sum(1 for r in test_results.values() if r)
    total = len(test_results)
    
    if passed == total:
        print_success(f"所有测试通过！({passed}/{total})")
        return 0
    else:
        print_error(f"部分测试失败：{passed}/{total} 通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())

