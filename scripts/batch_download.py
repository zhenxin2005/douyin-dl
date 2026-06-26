#!/usr/bin/env python3
"""用Playwright拦截网络请求批量下载羽川视频"""
import json
import os
import requests
import sys
import re
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

OUTPUT_DIR = "C:\\Users\\zhenx\\douyin-dl\\downloads\\羽川"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    with open("C:\\Users\\zhenx\\videos.json", "r", encoding="utf-8") as f:
        videos = json.load(f)
    
    existing = {f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp4")}
    
    print(f"📋 共 {len(videos)} 个视频待处理", file=sys.stderr)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()
        
        # 收集到的真实视频URL
        real_video_urls = {}
        pending = {v["aweme_id"]: v for v in videos}
        
        def on_response(response):
            url = response.url
            # 捕获视频文件请求（douyinvod 域名）
            if "douyinvod.com" in url or "douyincdn.com" in url:
                # 检查页面URL来关联
                try:
                    if response.status == 200 and response.headers.get("content-type", "").startswith("video"):
                        # 找到当前页面的视频ID
                        current_url = page.url
                        for aid, v in list(pending.items()):
                            if aid in current_url or v["share_url"] in current_url or current_url in v["share_url"]:
                                real_video_urls[aid] = url
                                print(f"  📡 捕获视频URL: {v['desc'][:30]}... → {url[:60]}...", file=sys.stderr)
                                break
                except:
                    pass
        
        page.on("response", on_response)
        
        success = 0
        failed = 0
        
        for idx, v in enumerate(videos, 1):
            desc_clean = v["desc"][:40].replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "_").replace("*", "_").replace('"', "_").replace("<", "_").replace(">", "_").replace("|", "_")
            filename = f"{v['date'][:10]}_{desc_clean}.mp4"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if filename in existing or os.path.exists(filepath):
                print(f"  ⏭ [{idx}/{len(videos)}] 已存在: {desc_clean}", file=sys.stderr)
                success += 1
                continue
            
            url = v["share_url"]
            print(f"\n📥 [{idx}/{len(videos)}] {v['date']} | {desc_clean}", file=sys.stderr)
            
            try:
                # 访问页面 - 用load或domcontentloaded
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # 等视频触发下载
                page.wait_for_timeout(5000)
                
                # 尝试从 _ROUTER_DATA 获取视频地址（短链接方式重定向后页面才有）
                video_url = None
                
                # 检查有没有捕获到视频URL
                if v["aweme_id"] in real_video_urls:
                    video_url = real_video_urls[v["aweme_id"]]
                else:
                    # 尝试通过JS获取页面信息
                    page_data = page.evaluate("""() => {
                        // 找 _ROUTER_DATA
                        var scripts = document.querySelectorAll('script');
                        for (var s of scripts) {
                            var t = s.textContent || '';
                            if (t.includes('_ROUTER_DATA')) {
                                var m = t.match(/window\\._ROUTER_DATA\\s*=\\s*(\\{.*?\\})\\s*<\\/script>/);
                                if (m) {
                                    try {
                                        var data = JSON.parse(m[1]);
                                        // 尝试多种路径
                                        for (var key in data.loaderData || {}) {
                                            var pageData = data.loaderData[key];
                                            if (pageData && pageData.videoInfoRes && pageData.videoInfoRes.item_list) {
                                                var item = pageData.videoInfoRes.item_list[0];
                                                var playUrls = item.video.play_addr.url_list;
                                                return {found: true, url: playUrls[0].replace('playwm', 'play')};
                                            }
                                        }
                                    } catch(e) {}
                                }
                            }
                        }
                        
                        // 尝试从video标签找真实源
                        var v = document.querySelector('video');
                        if (v) {
                            var src = v.currentSrc || v.src || '';
                            if (src && !src.startsWith('blob:')) return {found: true, url: src};
                        }
                        
                        // 查看所有网络资源
                        return {found: false};
                    }""")
                    
                    if page_data.get("found") and page_data.get("url"):
                        video_url = page_data["url"]
                        # 去水印
                        video_url = video_url.replace("playwm", "play")
                
                if not video_url:
                    print(f"  ⚠️ 未找到视频源URL，尝试备用方法...", file=sys.stderr)
                    
                    # 备用：用v.douyin.com短链方式
                    # 用requests访问视频页面，但使用iesdouyin格式
                    r = requests.get(
                        f"https://www.iesdouyin.com/share/video/{v['aweme_id']}/",
                        headers={
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                        },
                        allow_redirects=True,
                        timeout=30
                    )
                    if "_ROUTER_DATA" in r.text:
                        match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?})\s*</script>', r.text, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            for key in data.get("loaderData", {}):
                                ld = data["loaderData"][key]
                                if isinstance(ld, dict) and "videoInfoRes" in ld:
                                    item = ld["videoInfoRes"]["item_list"][0]
                                    play_url = item["video"]["play_addr"]["url_list"][0]
                                    video_url = play_url.replace("playwm", "play")
                                    break
                
                if not video_url:
                    print(f"  ❌ 无法获取视频源", file=sys.stderr)
                    failed += 1
                    continue
                
                # 下载
                print(f"  📥 正在下载...", file=sys.stderr)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.douyin.com/",
                }
                
                resp = requests.get(video_url, headers=headers, stream=True, timeout=300)
                if resp.status_code != 200:
                    print(f"  ❌ HTTP {resp.status_code}", file=sys.stderr)
                    failed += 1
                    continue
                
                total = 0
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192*1024):
                        if chunk:
                            f.write(chunk)
                            total += len(chunk)
                
                size_mb = total / (1024 * 1024)
                print(f"  ✅ {size_mb:.1f} MB", file=sys.stderr)
                success += 1
                
            except Exception as e:
                print(f"  ❌ 错误: {e}", file=sys.stderr)
                failed += 1
            
            if idx < len(videos):
                page.wait_for_timeout(500)
        
        browser.close()
    
    print(f"\n📊 汇总: 成功 {success} / 失败 {failed} / 总计 {len(videos)}", file=sys.stderr)

if __name__ == "__main__":
    main()
