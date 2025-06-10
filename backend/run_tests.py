#!/usr/bin/env python3
"""
测试运行脚本
提供不同类型的测试运行选项
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} - 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - 失败 (退出码: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"\n❌ 命令未找到: {cmd[0]}")
        print("请确保已安装pytest: pip install pytest pytest-asyncio pytest-cov")
        return False


def main():
    parser = argparse.ArgumentParser(description="AI笔记项目测试运行器")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "cache", "database", "services", "models"],
        default="all",
        help="测试类型 (默认: all)"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="生成覆盖率报告"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="快速测试（跳过慢速测试）"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="并行运行测试的进程数"
    )
    
    args = parser.parse_args()
    
    # 基础命令
    base_cmd = ["python", "-m", "pytest"]
    
    # 添加详细输出
    if args.verbose:
        base_cmd.extend(["-v", "-s"])
    
    # 添加覆盖率
    if args.coverage:
        base_cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # 添加并行执行
    if args.parallel:
        base_cmd.extend(["-n", str(args.parallel)])
    
    # 跳过慢速测试
    if args.fast:
        base_cmd.extend(["-m", "not slow"])
    
    # 根据测试类型添加路径和标记
    test_configs = {
        "all": {
            "paths": ["tests/"],
            "description": "运行所有测试"
        },
        "unit": {
            "paths": ["tests/"],
            "markers": ["-m", "unit"],
            "description": "运行单元测试"
        },
        "integration": {
            "paths": ["tests/"],
            "markers": ["-m", "integration"],
            "description": "运行集成测试"
        },
        "cache": {
            "paths": ["tests/test_services/test_cache_service.py"],
            "description": "运行缓存服务测试"
        },
        "database": {
            "paths": ["tests/test_database.py"],
            "description": "运行数据库连接测试"
        },
        "services": {
            "paths": ["tests/test_services/"],
            "description": "运行服务层测试"
        },
        "models": {
            "paths": ["tests/test_models/"],
            "description": "运行模型测试"
        }
    }
    
    config = test_configs[args.type]
    cmd = base_cmd.copy()
    
    # 添加标记
    if "markers" in config:
        cmd.extend(config["markers"])
    
    # 添加测试路径
    cmd.extend(config["paths"])
    
    # 运行测试
    success = run_command(cmd, config["description"])
    
    if success:
        print(f"\n🎉 测试完成！")
        if args.coverage:
            print("📊 覆盖率报告已生成在 htmlcov/ 目录")
    else:
        print(f"\n💥 测试失败，请检查错误信息")
        sys.exit(1)


def check_dependencies():
    """检查测试依赖"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下测试依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)


def show_test_info():
    """显示测试信息"""
    print("🧪 AI笔记项目测试套件")
    print("=" * 50)
    print("测试类型:")
    print("  • all        - 运行所有测试")
    print("  • unit       - 单元测试")
    print("  • integration- 集成测试")
    print("  • cache      - 缓存服务测试")
    print("  • database   - 数据库测试")
    print("  • services   - 服务层测试")
    print("  • models     - 模型测试")
    print()
    print("使用示例:")
    print("  python run_tests.py --type cache --coverage")
    print("  python run_tests.py --type all --verbose")
    print("  python run_tests.py --fast --parallel 4")
    print()


if __name__ == "__main__":
    # 检查是否在正确的目录
    if not Path("tests").exists():
        print("❌ 请在backend目录下运行此脚本")
        sys.exit(1)
    
    # 显示测试信息
    show_test_info()
    
    # 检查依赖
    check_dependencies()
    
    # 运行测试
    main()
