#!/usr/bin/env python3
"""
文档一致性检查脚本

校验 README 中的关键默认值是否与代码/配置保持一致，避免文档漂移。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def extract_int_constant(content: str, name: str) -> int:
    m = re.search(rf"^{re.escape(name)}\s*=\s*(\d+)\b", content, flags=re.MULTILINE)
    if not m:
        raise ValueError(f"未找到常量: {name}")
    return int(m.group(1))


def count_sources(sources_yaml: str) -> int:
    return len(re.findall(r"^\s*-\s+name:\s+", sources_yaml, flags=re.MULTILINE))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    constants_path = repo_root / "core" / "utils" / "constants.py"
    sources_path = repo_root / "config" / "sources.yaml"
    readme_path = repo_root / "README.md"

    constants_text = read_text(constants_path)
    sources_text = read_text(sources_path)
    readme_text = read_text(readme_path)

    max_items = extract_int_constant(constants_text, "DEFAULT_MAX_ITEMS_PER_SOURCE")
    max_articles = extract_int_constant(constants_text, "DEFAULT_MAX_ARTICLES_IN_REPORT")
    source_total = count_sources(sources_text)

    checks = [
        (f"README 包含 '每源最多 {max_items} 条'", rf"每源最多\s*{max_items}\s*条"),
        (f"README 包含 'Top {max_articles} 筛选'", rf"Top\s*{max_articles}\s*筛选"),
        (f"README 包含 '输出: Top {max_articles} 条高质量文章'", rf"输出:\s*Top\s*{max_articles}\s*条高质量文章"),
        (f"README 包含 '(Top {max_articles})'", rf"\(Top\s*{max_articles}\)"),
        (f"README 包含 'MAX_ITEMS_PER_SOURCE={max_items}'", rf"MAX_ITEMS_PER_SOURCE={max_items}\b"),
        (f"README 包含 'MAX_ARTICLES_IN_REPORT={max_articles}'", rf"MAX_ARTICLES_IN_REPORT={max_articles}\b"),
        (f"README 包含 'config/sources.yaml ({source_total}个RSS源)'", rf"config/sources\.yaml\s*\({source_total}个RSS源\)"),
    ]

    failed: list[str] = []
    for label, pattern in checks:
        if re.search(pattern, readme_text, flags=re.MULTILINE) is None:
            failed.append(label)

    if failed:
        print("❌ 文档一致性检查失败：")
        for item in failed:
            print(f"  - {item}")
        print("\n建议：同步更新 README.md 或代码默认值。")
        return 1

    print("✅ 文档一致性检查通过")
    print(f"  DEFAULT_MAX_ITEMS_PER_SOURCE = {max_items}")
    print(f"  DEFAULT_MAX_ARTICLES_IN_REPORT = {max_articles}")
    print(f"  config/sources.yaml 总源数 = {source_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
