#!/usr/bin/env python3
"""
抖音视频下载脚本

用法:
  # 单个视频
  python3 douyin-dl.py <douyin_url>

  # 批量下载（多个链接）
  python3 douyin-dl.py <url1> <url2> <url3> ...

  # 从文件读取链接列表
  python3 douyin-dl.py urls.txt

  # 指定输出目录
  python3 douyin-dl.py <url> [output_dir]

支持链接格式:
  - https://v.douyin.com/xxx/             (短链)
  - https://www.douyin.com/video/xxx      (长链)
  - https://www.iesdouyin.com/share/video/xxx (分享链)

urls.txt 格式:
  一行一个链接，忽略空行和 # 注释行
"""

import sys
import os
import re
import json
import time
import urllib.parse
from pathlib import Path

import requests


# ============================================================
# 配置
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

TIMEOUT = 30


# ============================================================
# 核心逻辑
# ============================================================


def fetch_page(url: str) -> str:
    """请求抖音页面，跟随短链重定向，返回 HTML"""
    resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def parse_video_info(html: str) -> dict:
    """从页面 HTML 中提取视频信息"""
    match = re.search(
        r"window\._ROUTER_DATA\s*=\s*({.*?})\s*</script>", html, re.DOTALL
    )
    if not match:
        raise ValueError("无法在页面中找到视频数据 (_ROUTER_DATA)")

    data = json.loads(match.group(1))
    item = data["loaderData"]["video_(id)/page"]["videoInfoRes"]["item_list"][0]
    video = item["video"]
    author = item.get("author", {})

    play_addr = video.get("play_addr", {})
    url_list = play_addr.get("url_list", [])
    if not url_list:
        raise ValueError("未找到视频播放地址")

    # 去掉水印: playwm → play
    play_url = url_list[0].replace("playwm", "play")

    return {
        "desc": item.get("desc", "未命名"),
        "author": author.get("nickname", "未知"),
        "author_id": author.get("unique_id", ""),
        "duration_ms": video.get("duration", 0),
        "width": video.get("width", 0),
        "height": video.get("height", 0),
        "play_url": play_url,
        "video_id": play_addr.get("uri", ""),
        "create_time": item.get("create_time", 0),
    }


def download_video(play_url: str, output_path: str) -> int:
    """下载视频文件，返回文件大小（字节）"""
    video_headers = {
        **HEADERS,
        "Referer": "https://www.douyin.com/",
    }
    resp = requests.get(
        play_url, headers=video_headers, allow_redirects=True, timeout=120, stream=True
    )
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "video" not in content_type:
        print(f"  ⚠️  警告: Content-Type 不是视频类型 ({content_type})，仍尝试保存")

    total = 0
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192 * 1024):
            f.write(chunk)
            total += len(chunk)
    return total


def safe_filename(text: str, max_len: int = 80) -> str:
    """清理文件名中的非法字符"""
    # 替换不允许的字符
    text = re.sub(r'[\\/:*?"<>|]', "_", text)
    # 去除多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 截断
    if len(text) > max_len:
        text = text[:max_len]
    return text


def format_duration(ms: int) -> str:
    """毫秒 → MM:SS 格式"""
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"


def format_size(size_bytes: int) -> str:
    """字节 → 人类可读"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# ============================================================
# URL 提取
# ============================================================

DOUYIN_URL_PATTERN = re.compile(
    r"https?://(?:v\.douyin\.com|www\.douyin\.com|www\.iesdouyin\.com)/\S+"
)


def extract_url(text: str) -> str:
    """
    从复制文本中提取抖音链接。
    支持直接粘贴抖音口令文本，自动识别其中的链接。
    """
    text = text.strip()

    # 如果已经是纯 URL
    if text.startswith("http"):
        return text

    # 从混合文本中提取
    match = DOUYIN_URL_PATTERN.search(text)
    if match:
        return match.group(0).rstrip("/")

    # 没找到 URL，原样返回（让后续报错）
    return text


# ============================================================
# URL 收集
# ============================================================


def load_urls_from_file(filepath: str) -> list:
    """从文本文件中读取链接，一行一个，忽略空行和 # 注释"""
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def collect_urls(args: list) -> list:
    """
    从命令行参数中收集所有 URL。
    支持: URL 列表、.txt 文件、混合输入
    """
    urls = []
    for arg in args:
        if arg.endswith(".txt"):
            urls.extend(load_urls_from_file(arg))
        else:
            urls.append(arg)
    return urls


def is_text_file(path: str) -> bool:
    return path.endswith(".txt")


# ============================================================
# 单视频下载
# ============================================================


def download_one(url: str, output_dir: str, index: int = 0, total: int = 1) -> tuple:
    """
    下载单个视频。
    返回: (success: bool, info: dict)
    """
    tag = f"[{index}/{total}]" if total > 1 else ""
    prefix = f"\n{tag} " if tag else ""

    try:
        # Step 1: 获取页面
        print(f"{prefix}📡 获取: {url[:60]}...")
        html = fetch_page(url)

        # Step 2: 解析
        print(f"{prefix}🔎 解析...")
        info = parse_video_info(html)

        print(f"{prefix}📹 {info['desc']}")
        print(f"{prefix}👤 {info['author']} | ⏱️ {format_duration(info['duration_ms'])} | 📐 {info['width']}x{info['height']}")

        # Step 3: 下载
        desc = info["desc"].strip() or info.get("author", "未知") + "_" + info.get("video_id", "unknown")
        filename = safe_filename(desc) + ".mp4"
        output_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)

        print(f"{prefix}⬇️  下载中...")
        file_size = download_video(info["play_url"], output_path)

        print(f"{prefix}✅ 完成！{format_size(file_size)} → {output_path}")

        info["file_path"] = output_path
        info["file_size"] = file_size
        return (True, info)

    except requests.RequestException as e:
        print(f"{prefix}❌ 网络错误: {e}")
        return (False, {"url": url, "error": str(e)})
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"{prefix}❌ 解析错误: {e}")
        return (False, {"url": url, "error": str(e)})
    except Exception as e:
        print(f"{prefix}❌ 错误: {e}")
        return (False, {"url": url, "error": str(e)})


# ============================================================
# 主入口
# ============================================================


def print_usage():
    print("抖音视频下载工具 - douyin-dl")
    print()
    print("用法:")
    print("  python3 douyin-dl.py <URL>             下载单个视频")
    print("  python3 douyin-dl.py <URL1> <URL2> ... 批量下载")
    print("  python3 douyin-dl.py urls.txt          从文件读取链接")
    print("  python3 douyin-dl.py urls.txt <URL> ...混合输入")
    print()
    print("urls.txt 格式: 一行一个链接，# 开头为注释")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    args = sys.argv[1:]

    # 判断最后一个参数是否是输出目录
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads"
    )
    url_args = args

    # 如果最后一个参数是一个已存在的目录，把它当输出目录
    if os.path.isdir(args[-1]):
        output_dir = args[-1]
        url_args = args[:-1]
    elif len(args) >= 2 and not args[-1].startswith("http") and not args[-1].endswith(".txt"):
        # 可能是用户想指定的输出目录
        last_is_url = any(kw in args[-1] for kw in ["douyin", "iesdouyin"])
        if not last_is_url:
            output_dir = args[-1]
            url_args = args[:-1]

    # 如果没有任何有效的 URL 参数，报错
    if not url_args:
        print("❌ 未提供任何链接")
        print_usage()
        sys.exit(1)

    # 收集所有 URL
    urls = collect_urls(url_args)

    if not urls:
        print("❌ 未找到任何有效链接")
        sys.exit(1)

    # 去重（保持顺序），同时对每个参数提取纯 URL
    seen = set()
    clean_urls = []
    for u in urls:
        clean = extract_url(u)
        if clean and clean not in seen:
            seen.add(clean)
            clean_urls.append(clean)

    urls = clean_urls

    total = len(urls)
    print(f"📋 共 {total} 个视频待下载")
    print(f"📁 输出目录: {output_dir}")
    print("=" * 60)

    # 批量下载
    success_list = []
    fail_list = []

    for i, url in enumerate(urls, 1):
        success, info = download_one(url, output_dir, index=i, total=total)
        if success:
            success_list.append(info)
        else:
            fail_list.append(info)

        # 多视频时，间隔 1 秒防止被限流
        if i < total:
            time.sleep(1)

    # 汇总
    print()
    print("=" * 60)
    print(f"📊 下载汇总: 成功 {len(success_list)} / 失败 {len(fail_list)} / 总计 {total}")

    if success_list:
        print(f"\n✅ 成功:")
        for info in success_list:
            print(f"  📹 {info['desc']}")
            print(f"     📁 {info.get('file_path', 'N/A')}")
            print(f"     📦 {format_size(info.get('file_size', 0))}")

    if fail_list:
        print(f"\n❌ 失败:")
        for info in fail_list:
            print(f"  🔗 {info['url'][:80]}")
            print(f"     ⚠️ {info['error']}")

    print()


if __name__ == "__main__":
    main()
