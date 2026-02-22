#!/usr/bin/env python3
"""
测试运行脚本

运行所有测试套件并生成报告。
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(verbosity=2):
    """
    运行所有测试

    Args:
        verbosity: 输出详细程度 (0-2)
    """
    # 发现并加载所有测试
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


def run_specific_test(test_module, verbosity=2):
    """
    运行特定测试模块

    Args:
        test_module: 测试模块名称（例如 'test_rss_collector'）
        verbosity: 输出详细程度
    """
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 运行特定测试
        test_module = sys.argv[1]
        success = run_specific_test(test_module)
    else:
        # 运行所有测试
        success = run_tests()

    sys.exit(0 if success else 1)
