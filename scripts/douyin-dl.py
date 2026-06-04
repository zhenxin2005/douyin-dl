#!/usr/bin/env python3
"""
抖音视频下载脚本
用法: python3 douyin-dl.py <douyin_url> [output_dir]

支持:
  - https://v.douyin.com/xxx/       (短链)
  - https://www.douyin.com/video/xxx (长链)
  - https://www.iesdouyin.com/share/video/xxx (分享链)

输出: 无水印 MP4 视频文件
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
# 主入口
# ============================================================


def main():
    if len(sys.argv) < 2:
        print("❌ 用法: python3 douyin-dl.py <douyin_url> [output_dir]")
        print("示例: python3 douyin-dl.py https://v.douyin.com/xxxx/")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads"
    )

    print(f"🔍 解析抖音链接: {url}")
    print(f"📁 输出目录: {output_dir}")
    print()

    try:
        # Step 1: 获取页面
        print("📡 获取页面数据...")
        html = fetch_page(url)

        # Step 2: 解析视频信息
        print("🔎 解析视频信息...")
        info = parse_video_info(html)

        print(f"  📹 标题: {info['desc']}")
        print(f"  👤 作者: {info['author']} (@{info['author_id']})")
        print(f"  ⏱️  时长: {format_duration(info['duration_ms'])}")
        print(f"  📐 分辨率: {info['width']}x{info['height']}")
        print()

        # Step 3: 下载
        filename = safe_filename(info['desc']) + ".mp4"
        output_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)

        print(f"⬇️  下载视频中...")
        file_size = download_video(info["play_url"], output_path)

        print()
        print("✅ 下载完成！")
        print(f"  📁 文件: {output_path}")
        print(f"  📦 大小: {format_size(file_size)}")
        print(f"  🎬 无水印 MP4")

    except requests.RequestException as e:
        print(f"❌ 网络错误: {e}")
        print("💡 请检查链接是否有效，或稍后重试")
        sys.exit(1)
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"❌ 解析错误: {e}")
        print("💡 抖音可能更新了页面结构，请反馈此问题")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
