# AI-RSS-PERSON 测试套件

本目录包含项目的所有单元测试。

## 测试模块

### [test_rss_collector.py](test_rss_collector.py)
测试 RSS 采集功能：
- 采集器初始化
- 各种抓取策略（rsshub, cffi, direct, noproxy）
- 时间窗口过滤
- Feed 解析

### [test_article_ranker.py](test_article_ranker.py)
测试文章排序功能：
- 源权威性评分
- 内容相关性评分
- 综合评分计算
- 文章排序
- 边缘情况处理

### [test_ai_analyzer.py](test_ai_analyzer.py)
测试 AI 分析功能：
- 成本追踪器
- Prompt 构建
- JSON 响应解析
- API 调用（使用 mock）
- 结果验证

### [test_report_generator.py](test_report_generator.py)
测试报告生成功能：
- Markdown 生成
- HTML 生成
- JSON 生成
- 文件保存
- HTML 转义

## 运行测试

### 运行所有测试

```bash
# 方式 1: 使用测试运行脚本
cd tests
python3 run_tests.py

# 方式 2: 直接使用 unittest
cd tests
python3 -m unittest discover

# 方式 3: 运行特定测试文件
python3 -m unittest test_rss_collector
```

### 运行特定测试

```bash
# 运行特定模块
python3 run_tests.py test_rss_collector

# 运行特定测试类
python3 -m unittest test_rss_collector.TestRSSCollector

# 运行特定测试方法
python3 -m unittest test_rss_collector.TestRSSCollector.test_collector_initialization
```

### 详细输出

```bash
# 增加详细程度
python3 -m unittest discover -v
```

## 测试覆盖率

安装 coverage 工具：
```bash
pip3 install coverage
```

运行测试并生成覆盖率报告：
```bash
# 运行测试并收集覆盖率数据
cd ..
coverage run -m unittest discover tests

# 生成终端报告
coverage report

# 生成 HTML 报告
coverage html
open htmlcov/index.html
```

## 测试原则

1. **隔离性** - 每个测试独立运行，不依赖其他测试
2. **可重复性** - 测试结果应该可重复
3. **快速** - 使用 mock 避免实际网络请求
4. **清晰** - 测试名称和注释应该清楚说明测试内容

## 添加新测试

1. 在 `tests/` 目录创建 `test_<module>.py` 文件
2. 导入必要的模块和 unittest
3. 创建测试类，继承 `unittest.TestCase`
4. 编写测试方法，方法名以 `test_` 开头
5. 使用 `self.assert*` 方法验证结果

示例：
```python
import unittest
from lib.my_module import MyClass

class TestMyClass(unittest.TestCase):
    def setUp(self):
        """测试前设置"""
        self.instance = MyClass()

    def test_something(self):
        """测试某功能"""
        result = self.instance.do_something()
        self.assertEqual(result, expected_value)

if __name__ == '__main__':
    unittest.main()
```

## Mock 使用说明

测试中大量使用 mock 来避免实际的：
- 网络请求
- API 调用
- 文件系统操作

示例：
```python
from unittest.mock import patch, Mock

@patch('lib.rss_collector.requests.get')
def test_fetch_with_mock(self, mock_get):
    # 设置 mock 返回值
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"test content"
    mock_get.return_value = mock_response

    # 测试代码（不会发起真实网络请求）
    result = collector._fetch_direct("https://example.com/rss")
    self.assertIsNotNone(result)
```

## 故障排查

### 导入错误

如果遇到导入错误：
```bash
# 确保在项目根目录运行
cd /path/to/ai-RSS-person
python3 -m unittest discover tests
```

### 测试失败

如果某个测试失败：
```bash
# 只运行失败的测试
python3 -m unittest test_module.TestClass.test_method

# 增加详细输出
python3 -m unittest test_module.TestClass.test_method -v
```

## 持续集成

这些测试可以集成到 CI/CD 流程中：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python3 -m unittest discover tests
```
