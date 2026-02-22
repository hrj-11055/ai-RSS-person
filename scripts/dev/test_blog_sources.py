#!/usr/bin/env python3
"""
测试 OPML 文件中的博客 RSS 源可用性

从 OPML 文件解析 RSS 源并测试每个源的可用性。
"""

import xml.etree.ElementTree as ET
import requests
import feedparser
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# OPML 文件内容
OPML_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Blog Feeds</title>
  </head>
  <body>
    <outline text="Blogs" title="Blogs">
      <outline type="rss" text="simonwillison.net" title="simonwillison.net" xmlUrl="https://simonwillison.net/atom/everything/" htmlUrl="https://simonwillison.net"/>
      <outline type="rss" text="jeffgeerling.com" title="jeffgeerling.com" xmlUrl="https://www.jeffgeerling.com/blog.xml" htmlUrl="https://jeffgeerling.com"/>
      <outline type="rss" text="seangoedecke.com" title="seangoedecke.com" xmlUrl="https://www.seangoedecke.com/rss.xml" htmlUrl="https://seangoedecke.com"/>
      <outline type="rss" text="krebsonsecurity.com" title="krebsonsecurity.com" xmlUrl="https://krebsonsecurity.com/feed/" htmlUrl="https://krebsonsecurity.com"/>
      <outline type="rss" text="daringfireball.net" title="daringfireball.net" xmlUrl="https://daringfireball.net/feeds/main" htmlUrl="https://daringfireball.net"/>
      <outline type="rss" text="ericmigi.com" title="ericmigi.com" xmlUrl="https://ericmigi.com/rss.xml" htmlUrl="https://ericmigi.com"/>
      <outline type="rss" text="antirez.com" title="antirez.com" xmlUrl="http://antirez.com/rss" htmlUrl="http://antirez.com"/>
      <outline type="rss" text="idiallo.com" title="idiallo.com" xmlUrl="https://idiallo.com/feed.rss" htmlUrl="https://idiallo.com"/>
      <outline type="rss" text="maurycyz.com" title="maurycyz.com" xmlUrl="https://maurycyz.com/index.xml" htmlUrl="https://maurycyz.com"/>
      <outline type="rss" text="pluralistic.net" title="pluralistic.net" xmlUrl="https://pluralistic.net/feed/" htmlUrl="https://pluralistic.net"/>
      <outline type="rss" text="shkspr.mobi" title="shkspr.mobi" xmlUrl="https://shkspr.mobi/blog/feed/" htmlUrl="https://shkspr.mobi"/>
      <outline type="rss" text="lcamtuf.substack.com" title="lcamtuf.substack.com" xmlUrl="https://lcamtuf.substack.com/feed" htmlUrl="https://lcamtuf.substack.com"/>
      <outline type="rss" text="mitchellh.com" title="mitchellh.com" xmlUrl="https://mitchellh.com/feed.xml" htmlUrl="https://mitchellh.com"/>
      <outline type="rss" text="dynomight.net" title="dynomight.net" xmlUrl="https://dynomight.net/feed.xml" htmlUrl="https://dynomight.net"/>
      <outline type="rss" text="utcc.utoronto.ca/~cks" title="utcc.utoronto.ca/~cks" xmlUrl="https://utcc.utoronto.ca/~cks/space/blog/?atom" htmlUrl="https://utcc.utoronto.ca/~cks"/>
      <outline type="rss" text="xeiaso.net" title="xeiaso.net" xmlUrl="https://xeiaso.net/blog.rss" htmlUrl="https://xeiaso.net"/>
      <outline type="rss" text="devblogs.microsoft.com/oldnewthing" title="devblogs.microsoft.com/oldnewthing" xmlUrl="https://devblogs.microsoft.com/oldnewthing/feed" htmlUrl="https://devblogs.microsoft.com/oldnewthing"/>
      <outline type="rss" text="righto.com" title="righto.com" xmlUrl="https://www.righto.com/feeds/posts/default" htmlUrl="https://righto.com"/>
      <outline type="rss" text="lucumr.pocoo.org" title="lucumr.pocoo.org" xmlUrl="https://lucumr.pocoo.org/feed.atom" htmlUrl="https://lucumr.pocoo.org"/>
      <outline type="rss" text="skyfall.dev" title="skyfall.dev" xmlUrl="https://skyfall.dev/rss.xml" htmlUrl="https://skyfall.dev"/>
      <outline type="rss" text="garymarcus.substack.com" title="garymarcus.substack.com" xmlUrl="https://garymarcus.substack.com/feed" htmlUrl="https://garymarcus.substack.com"/>
      <outline type="rss" text="rachelbythebay.com" title="rachelbythebay.com" xmlUrl="https://rachelbythebay.com/w/atom.xml" htmlUrl="https://rachelbythebay.com"/>
      <outline type="rss" text="overreacted.io" title="overreacted.io" xmlUrl="https://overreacted.io/rss.xml" htmlUrl="https://overreacted.io"/>
      <outline type="rss" text="timsh.org" title="timsh.org" xmlUrl="https://timsh.org/rss/" htmlUrl="https://timsh.org"/>
      <outline type="rss" text="johndcook.com" title="johndcook.com" xmlUrl="https://www.johndcook.com/blog/feed/" htmlUrl="https://johndcook.com"/>
      <outline type="rss" text="gilesthomas.com" title="gilesthomas.com" xmlUrl="https://gilesthomas.com/feed/rss.xml" htmlUrl="https://gilesthomas.com"/>
      <outline type="rss" text="matklad.github.io" title="matklad.github.io" xmlUrl="https://matklad.github.io/feed.xml" htmlUrl="https://matklad.github.io"/>
      <outline type="rss" text="derekthompson.org" title="derekthompson.org" xmlUrl="https://www.theatlantic.com/feed/author/derek-thompson/" htmlUrl="https://derekthompson.org"/>
      <outline type="rss" text="evanhahn.com" title="evanhahn.com" xmlUrl="https://evanhahn.com/feed.xml" htmlUrl="https://evanhahn.com"/>
      <outline type="rss" text="terriblesoftware.org" title="terriblesoftware.org" xmlUrl="https://terriblesoftware.org/feed/" htmlUrl="https://terriblesoftware.org"/>
      <outline type="rss" text="rakhim.exotext.com" title="rakhim.exotext.com" xmlUrl="https://rakhim.exotext.com/rss.xml" htmlUrl="https://rakhim.exotext.com"/>
      <outline type="rss" text="joanwestenberg.com" title="joanwestenberg.com" xmlUrl="https://joanwestenberg.com/rss" htmlUrl="https://joanwestenberg.com"/>
      <outline type="rss" text="xania.org" title="xania.org" xmlUrl="https://xania.org/feed" htmlUrl="https://xania.org"/>
      <outline type="rss" text="micahflee.com" title="micahflee.com" xmlUrl="https://micahflee.com/feed/" htmlUrl="https://micahflee.com"/>
      <outline type="rss" text="nesbitt.io" title="nesbitt.io" xmlUrl="https://nesbitt.io/feed.xml" htmlUrl="https://nesbitt.io"/>
      <outline type="rss" text="construction-physics.com" title="construction-physics.com" xmlUrl="https://www.construction-physics.com/feed" htmlUrl="https://www.construction-physics.com"/>
      <outline type="rss" text="tedium.co" title="tedium.co" xmlUrl="https://feed.tedium.co/" htmlUrl="https://tedium.co"/>
      <outline type="rss" text="susam.net" title="susam.net" xmlUrl="https://susam.net/feed.xml" htmlUrl="https://susam.net"/>
      <outline type="rss" text="entropicthoughts.com" title="entropicthoughts.com" xmlUrl="https://entropicthoughts.com/feed.xml" htmlUrl="https://entropicthoughts.com"/>
      <outline type="rss" text="buttondown.com/hillelwayne" title="buttondown.com/hillelwayne" xmlUrl="https://buttondown.com/hillelwayne/rss" htmlUrl="https://buttondown.com/hillelwayne"/>
      <outline type="rss" text="dwarkesh.com" title="dwarkesh.com" xmlUrl="https://www.dwarkeshpatel.com/feed" htmlUrl="https://dwarkesh.com"/>
      <outline type="rss" text="borretti.me" title="borretti.me" xmlUrl="https://borretti.me/feed.xml" htmlUrl="https://borretti.me"/>
      <outline type="rss" text="wheresyoured.at" title="wheresyoured.at" xmlUrl="https://www.wheresyoured.at/rss/" htmlUrl="https://wheresyoured.at"/>
      <outline type="rss" text="jayd.ml" title="jayd.ml" xmlUrl="https://jayd.ml/feed.xml" htmlUrl="https://jayd.ml"/>
      <outline type="rss" text="minimaxir.com" title="minimaxir.com" xmlUrl="https://minimaxir.com/index.xml" htmlUrl="https://minimaxir.com"/>
      <outline type="rss" text="geohot.github.io" title="geohot.github.io" xmlUrl="https://geohot.github.io/blog/feed.xml" htmlUrl="https://geohot.github.io"/>
      <outline type="rss" text="paulgraham.com" title="paulgraham.com" xmlUrl="http://www.aaronsw.com/2002/feeds/pgessays.rss" htmlUrl="https://paulgraham.com"/>
      <outline type="rss" text="filfre.net" title="filfre.net" xmlUrl="https://www.filfre.net/feed/" htmlUrl="https://filfre.net"/>
      <outline type="rss" text="blog.jim-nielsen.com" title="blog.jim-nielsen.com" xmlUrl="https://blog.jim-nielsen.com/feed.xml" htmlUrl="https://blog.jim-nielsen.com"/>
      <outline type="rss" text="dfarq.homeip.net" title="dfarq.homeip.net" xmlUrl="https://dfarq.homeip.net/feed/" htmlUrl="https://dfarq.homeip.net"/>
      <outline type="rss" text="jyn.dev" title="jyn.dev" xmlUrl="https://jyn.dev/atom.xml" htmlUrl="https://jyn.dev"/>
      <outline type="rss" text="geoffreylitt.com" title="geoffreylitt.com" xmlUrl="https://www.geoffreylitt.com/feed.xml" htmlUrl="https://geoffreylitt.com"/>
      <outline type="rss" text="downtowndougbrown.com" title="downtowndougbrown.com" xmlUrl="https://www.downtowndougbrown.com/feed/" htmlUrl="https://downtowndougbrown.com"/>
      <outline type="rss" text="brutecat.com" title="brutecat.com" xmlUrl="https://brutecat.com/rss.xml" htmlUrl="https://brutecat.com"/>
      <outline type="rss" text="eli.thegreenplace.net" title="eli.thegreenplace.net" xmlUrl="https://eli.thegreenplace.net/feeds/all.atom.xml" htmlUrl="https://eli.thegreenplace.net"/>
      <outline type="rss" text="abortretry.fail" title="abortretry.fail" xmlUrl="https://www.abortretry.fail/feed" htmlUrl="https://www.abortretry.fail"/>
      <outline type="rss" text="fabiensanglard.net" title="fabiensanglard.net" xmlUrl="https://fabiensanglard.net/rss.xml" htmlUrl="https://fabiensanglard.net"/>
      <outline type="rss" text="oldvcr.blogspot.com" title="oldvcr.blogspot.com" xmlUrl="https://oldvcr.blogspot.com/feeds/posts/default" htmlUrl="https://oldvcr.blogspot.com"/>
      <outline type="rss" text="bogdanthegeek.github.io" title="bogdanthegeek.github.io" xmlUrl="https://bogdanthegeek.github.io/blog/index.xml" htmlUrl="https://bogdanthegeek.github.io"/>
      <outline type="rss" text="hugotunius.se" title="hugotunius.se" xmlUrl="https://hugotunius.se/feed.xml" htmlUrl="https://hugotunius.se"/>
      <outline type="rss" text="gwern.net" title="gwern.net" xmlUrl="https://gwern.substack.com/feed" htmlUrl="https://gwern.net"/>
      <outline type="rss" text="berthub.eu" title="berthub.eu" xmlUrl="https://berthub.eu/articles/index.xml" htmlUrl="https://berthub.eu"/>
      <outline type="rss" text="chadnauseam.com" title="chadnauseam.com" xmlUrl="https://chadnauseam.com/rss.xml" htmlUrl="https://chadnauseam.com"/>
      <outline type="rss" text="simone.org" title="simone.org" xmlUrl="https://simone.org/feed/" htmlUrl="https://simone.org"/>
      <outline type="rss" text="it-notes.dragas.net" title="it-notes.dragas.net" xmlUrl="https://it-notes.dragas.net/feed/" htmlUrl="https://it-notes.dragas.net"/>
      <outline type="rss" text="beej.us" title="beej.us" xmlUrl="https://beej.us/blog/rss.xml" htmlUrl="https://beej.us"/>
      <outline type="rss" text="hey.paris" title="hey.paris" xmlUrl="https://hey.paris/index.xml" htmlUrl="https://hey.paris"/>
      <outline type="rss" text="danielwirtz.com" title="danielwirtz.com" xmlUrl="https://danielwirtz.com/rss.xml" htmlUrl="https://danielwirtz.com"/>
      <outline type="rss" text="matduggan.com" title="matduggan.com" xmlUrl="https://matduggan.com/rss/" htmlUrl="https://matduggan.com"/>
      <outline type="rss" text="refactoringenglish.com" title="refactoringenglish.com" xmlUrl="https://refactoringenglish.com/index.xml" htmlUrl="https://refactoringenglish.com"/>
      <outline type="rss" text="worksonmymachine.substack.com" title="worksonmymachine.substack.com" xmlUrl="https://worksonmymachine.substack.com/feed" htmlUrl="https://worksonmymachine.substack.com"/>
      <outline type="rss" text="philiplaine.com" title="philiplaine.com" xmlUrl="https://philiplaine.com/index.xml" htmlUrl="https://philiplaine.com"/>
      <outline type="rss" text="steveblank.com" title="steveblank.com" xmlUrl="https://steveblank.com/feed/" htmlUrl="https://steveblank.com"/>
      <outline type="rss" text="bernsteinbear.com" title="bernsteinbear.com" xmlUrl="https://bernsteinbear.com/feed.xml" htmlUrl="https://bernsteinbear.com"/>
      <outline type="rss" text="danieldelaney.net" title="danieldelaney.net" xmlUrl="https://danieldelaney.net/feed" htmlUrl="https://danieldelaney.net"/>
      <outline type="rss" text="troyhunt.com" title="troyhunt.com" xmlUrl="https://www.troyhunt.com/rss/" htmlUrl="https://troyhunt.com"/>
      <outline type="rss" text="herman.bearblog.dev" title="herman.bearblog.dev" xmlUrl="https://herman.bearblog.dev/feed/" htmlUrl="https://herman.bearblog.dev"/>
      <outline type="rss" text="tomrenner.com" title="tomrenner.com" xmlUrl="https://tomrenner.com/index.xml" htmlUrl="https://tomrenner.com"/>
      <outline type="rss" text="blog.pixelmelt.dev" title="blog.pixelmelt.dev" xmlUrl="https://blog.pixelmelt.dev/rss/" htmlUrl="https://blog.pixelmelt.dev"/>
      <outline type="rss" text="martinalderson.com" title="martinalderson.com" xmlUrl="https://martinalderson.com/feed.xml" htmlUrl="https://martinalderson.com"/>
      <outline type="rss" text="danielchasehooper.com" title="danielchasehooper.com" xmlUrl="https://danielchasehooper.com/feed.xml" htmlUrl="https://danielchasehooper.com"/>
      <outline type="rss" text="chiark.greenend.org.uk/~sgtatham" title="chiark.greenend.org.uk/~sgtatham" xmlUrl="https://www.chiark.greenend.org.uk/~sgtatham/quasiblog/feed.xml" htmlUrl="https://chiark.greenend.org.uk/~sgtatham"/>
      <outline type="rss" text="grantslatton.com" title="grantslatton.com" xmlUrl="https://grantslatton.com/rss.xml" htmlUrl="https://grantslatton.com"/>
      <outline type="rss" text="experimental-history.com" title="experimental-history.com" xmlUrl="https://www.experimental-history.com/feed" htmlUrl="https://www.experimental-history.com"/>
      <outline type="rss" text="anildash.com" title="anildash.com" xmlUrl="https://anildash.com/feed.xml" htmlUrl="https://anildash.com"/>
      <outline type="rss" text="aresluna.org" title="aresluna.org" xmlUrl="https://aresluna.org/main.rss" htmlUrl="https://aresluna.org"/>
      <outline type="rss" text="michael.stapelberg.ch" title="michael.stapelberg.ch" xmlUrl="https://michael.stapelberg.ch/feed.xml" htmlUrl="https://michael.stapelberg.ch"/>
      <outline type="rss" text="miguelgrinberg.com" title="miguelgrinberg.com" xmlUrl="https://blog.miguelgrinberg.com/feed" htmlUrl="https://miguelgrinberg.com"/>
      <outline type="rss" text="keygen.sh" title="keygen.sh" xmlUrl="https://keygen.sh/blog/feed.xml" htmlUrl="https://keygen.sh"/>
      <outline type="rss" text="mjg59.dreamwidth.org" title="mjg59.dreamwidth.org" xmlUrl="https://mjg59.dreamwidth.org/data/rss" htmlUrl="https://mjg59.dreamwidth.org"/>
      <outline type="rss" text="computer.rip" title="computer.rip" xmlUrl="https://computer.rip/rss.xml" htmlUrl="https://computer.rip"/>
      <outline type="rss" text="tedunangst.com" title="tedunangst.com" xmlUrl="https://www.tedunangst.com/flak/rss" htmlUrl="https://tedunangst.com"/>
    </outline>
  </body>
</opml>'''


def parse_opml(opml_content: str) -> List[Dict[str, str]]:
    """解析 OPML 内容，提取 RSS 源"""
    sources = []

    # 移除可能的 XML 声明和编码问题
    try:
        root = ET.fromstring(opml_content)
    except ET.ParseError:
        # 如果解析失败，尝试移除命名空间
        opml_content = opml_content.replace('xmlns="http://www.w3.org/1999/xhtml"', '')
        root = ET.fromstring(opml_content)

    # 查找所有 outline 元素（不区分命名空间）
    for elem in root.iter():
        if elem.tag.endswith('outline'):
            xml_url = elem.get('xmlUrl')
            if xml_url:
                sources.append({
                    'name': elem.get('title', elem.get('text', 'Unknown')),
                    'url': xml_url,
                    'html_url': elem.get('htmlUrl', ''),
                })

    return sources


def test_rss_source(source: Dict[str, str], timeout: int = 15) -> Dict:
    """测试单个 RSS 源是否可用"""
    name = source['name']
    url = source['url']

    result = {
        'name': name,
        'url': url,
        'status': 'FAILED',
        'error': None,
        'entry_count': 0
    }

    try:
        # 先尝试简单的 HTTP 请求检查
        response = requests.head(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code not in (200, 301, 302, 304):
            # 如果 HEAD 失败，尝试 GET
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, stream=True)

        if response.status_code in (200, 301, 302, 304):
            # 尝试解析 RSS
            feed = feedparser.parse(url)
            if feed.entries:
                result['status'] = 'SUCCESS'
                result['entry_count'] = len(feed.entries)
            else:
                result['status'] = 'EMPTY'
        else:
            result['error'] = f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
    except requests.exceptions.SSLError:
        result['error'] = 'SSL Error'
    except requests.exceptions.RequestException as e:
        result['error'] = str(e)[:50]
    except Exception as e:
        result['error'] = str(e)[:50]

    return result


def test_sources_parallel(sources: List[Dict], max_workers: int = 10) -> List[Dict]:
    """并行测试多个 RSS 源"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_source = {executor.submit(test_rss_source, source): source for source in sources}

        for future in as_completed(future_to_source):
            result = future.result()
            results.append(result)
            status_emoji = "✅" if result['status'] == 'SUCCESS' else "⚠️" if result['status'] == 'EMPTY' else "❌"
            print(f"{status_emoji} {result['name']}: {result['status']}", end='')
            if result['entry_count'] > 0:
                print(f" ({result['entry_count']} articles)", end='')
            if result['error']:
                print(f" - {result['error']}", end='')
            print()

    return results


def generate_config_code(results: List[Dict]) -> str:
    """生成可用的源配置代码"""
    successful = [r for r in results if r['status'] == 'SUCCESS']

    lines = [
        "    # --- 📝 博客 RSS (从 OPML 添加) ---",
    ]

    for r in sorted(successful, key=lambda x: x['name']):
        lines.append(f'    {{"name": "{r["name"]}", "url": "{r["url"]}", "strategy": "STRATEGY_DIRECT"}},')

    return '\n'.join(lines)


if __name__ == "__main__":
    print("🧪 测试博客 RSS 源")
    print("=" * 60)

    # 解析 OPML
    sources = parse_opml(OPML_CONTENT)
    print(f"📋 从 OPML 解析了 {len(sources)} 个 RSS 源\n")

    # 测试源
    print("🔍 开始测试...\n")
    results = test_sources_parallel(sources)

    # 统计
    success = len([r for r in results if r['status'] == 'SUCCESS'])
    empty = len([r for r in results if r['status'] == 'EMPTY'])
    failed = len([r for r in results if r['status'] == 'FAILED'])

    print("\n" + "=" * 60)
    print(f"📊 统计结果:")
    print(f"  总计: {len(results)}")
    print(f"  ✅ 成功: {success}")
    print(f"  ⚠️  为空: {empty}")
    print(f"  ❌ 失败: {failed}")

    # 生成配置代码
    print("\n" + "=" * 60)
    print("📝 生成配置代码:\n")
    print(generate_config_code(results))

    # 保存结果
    with open('blog_sources_test_results.txt', 'w', encoding='utf-8') as f:
        f.write("博客 RSS 源测试结果\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"总计: {len(results)}\n")
        f.write(f"成功: {success}\n")
        f.write(f"为空: {empty}\n")
        f.write(f"失败: {failed}\n\n")

        f.write("\n成功的源:\n")
        f.write("-" * 40 + "\n")
        for r in sorted([r for r in results if r['status'] == 'SUCCESS'], key=lambda x: x['name']):
            f.write(f"✅ {r['name']}: {r['url']} ({r['entry_count']} articles)\n")

        f.write("\n失败的源:\n")
        f.write("-" * 40 + "\n")
        for r in sorted([r for r in results if r['status'] != 'SUCCESS'], key=lambda x: x['name']):
            f.write(f"❌ {r['name']}: {r['url']}")
            if r['error']:
                f.write(f" - {r['error']}")
            f.write("\n")

        f.write("\n\n配置代码:\n")
        f.write("-" * 40 + "\n")
        f.write(generate_config_code(results))

    print(f"\n💾 结果已保存到: blog_sources_test_results.txt")