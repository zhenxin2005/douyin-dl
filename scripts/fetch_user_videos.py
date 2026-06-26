#!/usr/bin/env python3
"""使用Playwright自动化拦截API请求获取羽川视频列表"""
import json
import sys
import os
import re
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

SEC_UID = "MS4wLjABAAAAxkqwjpqCtOKE2teMgB20p5gH2qPctLVgtqUCZOmpLZs"
USER_URL = f"https://www.douyin.com/user/{SEC_UID}"
SINCE_TS = datetime(2026, 5, 8, tzinfo=timezone.utc).timestamp()

def main():
    all_videos = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",
            ]
        )
        
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        
        page = context.new_page()
        
        # 拦截XHR请求 - 捕获视频列表API响应
        api_responses = []
        
        def on_response(response):
            url = response.url
            if "aweme/post" in url or "aweme/v1/web/post" in url:
                try:
                    body = response.text()
                    if body and len(body) > 10:
                        api_responses.append(body)
                        print(f"  📡 捕获到API响应: {url[:80]}... 长度={len(body)}", file=sys.stderr)
                except:
                    pass
        
        page.on("response", on_response)
        
        print(f"🌐 正在访问用户主页...", file=sys.stderr)
        # 使用load而不是networkidle，因为抖音有持续的网络请求
        page.goto(USER_URL, wait_until="load", timeout=30000)
        
        # 等待页面渲染
        page.wait_for_timeout(8000)
        
        # 获取页面内容
        content = page.content()
        print(f"  页面大小: {len(content)} 字节", file=sys.stderr)
        
        # 截图
        page.screenshot(path="douyin_page.png")
        print(f"  已截图: douyin_page.png", file=sys.stderr)
        
        # 在页面中执行JS来获取数据
        print("\n执行JS提取数据...", file=sys.stderr)
        page_data = page.evaluate("""() => {
            // 尝试从 window.__INITIAL_STATE__ 获取
            if (window.__INITIAL_STATE__) return {source: '__INITIAL_STATE__', data: window.__INITIAL_STATE__};
            
            // 尝试从 _ROUTER_DATA 获取
            var scripts = document.querySelectorAll('script');
            for (var s of scripts) {
                var text = s.textContent || '';
                if (text.includes('_ROUTER_DATA')) {
                    var match = text.match(/window\\._ROUTER_DATA\\s*=\\s*(\\{.*?\\})\\s*<\\/script>/);
                    if (match) {
                        try {
                            return {source: '_ROUTER_DATA', data: JSON.parse(match[1])};
                        } catch(e) {}
                    }
                }
            }
            
            // 尝试从页面中找视频链接
            var links = [];
            document.querySelectorAll('a[href*=\"/video/\"]').forEach(a => links.push(a.href));
            return {source: 'links', data: links};
        }""")
        
        print(f"  JS返回: {json.dumps(page_data, ensure_ascii=False)[:200]}", file=sys.stderr)
        
        # 滚动画廊以加载更多视频
        print("\n滚动页面加载更多视频...", file=sys.stderr)
        for i in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            print(f"  滚动 {i+1}/3", file=sys.stderr)
        
        # 再次获取页面并解析
        content2 = page.content()
        match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?})\s*</script>', content2, re.DOTALL)
        if match:
            print("  ✅ 滚动后找到 _ROUTER_DATA!", file=sys.stderr)
            data = json.loads(match.group(1))
            
            def find_video_items(obj, depth=0):
                items = []
                if depth > 6:
                    return items
                if isinstance(obj, dict):
                    if "item_list" in obj and isinstance(obj["item_list"], list) and len(obj["item_list"]) > 0:
                        if isinstance(obj["item_list"][0], dict) and "video" in obj["item_list"][0]:
                            for item in obj["item_list"]:
                                items.append(item)
                    for v in obj.values():
                        items.extend(find_video_items(v, depth+1))
                elif isinstance(obj, list):
                    for item in obj:
                        items.extend(find_video_items(item, depth+1))
                return items
            
            all_items = find_video_items(data)
            print(f"  找到 {len(all_items)} 个视频", file=sys.stderr)
            
            for item in all_items:
                ct = item.get("create_time", 0)
                if ct >= SINCE_TS:
                    video = item.get("video", {})
                    author = item.get("author", {})
                    all_videos.append({
                        "desc": item.get("desc", "").strip(),
                        "create_time": ct,
                        "date": datetime.fromtimestamp(ct, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "duration": video.get("duration", 0),
                        "width": video.get("width", 0),
                        "height": video.get("height", 0),
                        "author": author.get("nickname", ""),
                        "aweme_id": item.get("aweme_id", ""),
                        "share_url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
                    })
        else:
            print("  ❌ 仍没有 _ROUTER_DATA", file=sys.stderr)
        
        # 检查拦截到的API响应
        print(f"\n拦截到的API响应: {len(api_responses)} 个", file=sys.stderr)
        for i, body in enumerate(api_responses):
            try:
                data = json.loads(body)
                sc = data.get("status_code")
                print(f"  API[{i}] status_code={sc}", file=sys.stderr)
                if sc == 0:
                    aweme_list = data.get("aweme_list", [])
                    print(f"  视频数: {len(aweme_list)}", file=sys.stderr)
                    for item in aweme_list:
                        ct = item.get("create_time", 0)
                        if ct >= SINCE_TS:
                            video = item.get("video", {})
                            author = item.get("author", {})
                            all_videos.append({
                                "desc": item.get("desc", "").strip(),
                                "create_time": ct,
                                "date": datetime.fromtimestamp(ct, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                                "duration": video.get("duration", 0),
                                "width": video.get("width", 0),
                                "height": video.get("height", 0),
                                "author": author.get("nickname", ""),
                                "aweme_id": item.get("aweme_id", ""),
                                "share_url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
                            })
            except:
                pass
        
        browser.close()
    
    # 去重
    seen_ids = set()
    unique_videos = []
    for v in all_videos:
        if v["aweme_id"] and v["aweme_id"] not in seen_ids:
            seen_ids.add(v["aweme_id"])
            unique_videos.append(v)
    
    print(f"\n📊 5月8日后共 {len(unique_videos)} 个视频 (去重后)", file=sys.stderr)
    if unique_videos:
        for v in sorted(unique_videos, key=lambda x: x["create_time"]):
            dur = f"{v['duration']//1000//60}:{v['duration']//1000%60:02d}" if v['duration'] else "?"
            print(f"  📹 {v['date']} | {dur} | {v['desc'][:50]}", file=sys.stderr)
        
        print(f"\n{json.dumps(unique_videos, ensure_ascii=False, indent=2)}")
        
        with open("videos.json", "w", encoding="utf-8") as f:
            json.dump(unique_videos, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存 videos.json", file=sys.stderr)
    else:
        print("❌ 没有找到视频", file=sys.stderr)

if __name__ == "__main__":
    main()
