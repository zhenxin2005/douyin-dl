#!/usr/bin/env python3
"""测试抖音视频页面格式"""
import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 测试短链接
print("=== 测试短链接 v.douyin.com ===")
url1 = "https://v.douyin.com/S6OkGBkgy2Q/"
resp1 = requests.get(url1, headers=headers, timeout=30, allow_redirects=True)
print(f"Status: {resp1.status_code}")
print(f"Final URL: {resp1.url}")
print(f"Length: {len(resp1.text)}")
has_router = "_ROUTER_DATA" in resp1.text
print(f"有 _ROUTER_DATA: {has_router}")

# 测试长链接
print("\n=== 测试长链接 www.douyin.com/video ===")
url2 = "https://www.douyin.com/video/7641614059170729268"
resp2 = requests.get(url2, headers=headers, timeout=30, allow_redirects=True)
print(f"Status: {resp2.status_code}")
print(f"Final URL: {resp2.url}")
print(f"Length: {len(resp2.text)}")
has_router2 = "_ROUTER_DATA" in resp2.text
print(f"有 _ROUTER_DATA: {has_router2}")

# 测试用短链接格式访问长视频ID
print("\n=== 尝试用短链接格式访问 ===")
# 原先的短链接 S6OkGBkgy2Q 对应视频 7641614059170729268
# 但我们没有其他视频的短链接
# 看看能不能找到短链接的重定向规律
print("短链会重定向到完整URL")
if resp1.status_code == 200 and resp1.url != url1:
    print(f"  短链 {url1} -> {resp1.url}")

# 尝试用Playwright获取视频页面
print("\n=== 用Playwright测试 ===")
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page()
    page.goto(url2, wait_until="load", timeout=30000)
    page.wait_for_timeout(5000)
    content = page.content()
    has_router3 = "_ROUTER_DATA" in content
    print(f"Playwright渲染后: 有 _ROUTER_DATA = {has_router3}")
    
    # 获取页面中的视频信息
    info = page.evaluate("""() => {
        var scripts = document.querySelectorAll('script');
        for (var s of scripts) {
            var t = s.textContent || '';
            var m = t.match(/window\\._ROUTER_DATA\\s*=\\s*(\\{.*?\\})\\s*<\\/script>/);
            if (m) {
                try {
                    var data = JSON.parse(m[1]);
                    var item = data.loaderData['video_(id)/page'].videoInfoRes.item_list[0];
                    return {
                        desc: item.desc,
                        create_time: item.create_time,
                        video: item.video.play_addr.url_list[0],
                        author: item.author.nickname
                    };
                } catch(e) { return {error: e.toString()}; }
            }
        }
        // 如果没有 _ROUTER_DATA，尝试从页面中找视频URL
        var videos = document.querySelectorAll('video source');
        if (videos.length > 0) return {source: 'video_tag', src: videos[0].src};
        
        return {error: 'no data found', content: document.body.innerHTML.substring(0, 500)};
    }""")
    print(f"页面数据: {json.dumps(info, ensure_ascii=False)[:300]}")
    
    browser.close()
