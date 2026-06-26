#!/usr/bin/env python3
"""转换cookies.txt为Netscape格式并测试抖音API"""
import requests
import json
import sys
import time
from datetime import datetime, timezone
from http.cookiejar import MozillaCookieJar

# 读取cookie字符串
with open("C:\\Users\\zhenx\\Documents\\cookies.txt", "r", encoding="utf-8") as f:
    content = f.read().strip()

lines = [l.strip() for l in content.split("\n") if l.strip()]
cookie_str = lines[-1]

# 解析
pairs = []
for item in cookie_str.split(";"):
    item = item.strip()
    if "=" in item:
        k, v = item.split("=", 1)
        pairs.append((k.strip(), v.strip()))

print(f"✅ 解析到 {len(pairs)} 个cookie", file=sys.stderr)

# 保存为Netscape格式供yt-dlp使用
with open("dy_cookies_netscape.txt", "w", encoding="utf-8") as f:
    f.write("# Netscape HTTP Cookie File\n")
    f.write("# https://curl.se/rfc/cookie_spec.html\n")
    f.write("# This is a generated file\n\n")
    
    # douyin.com 域名
    for name, value in pairs:
        # 跳过带特殊字符的值
        if any(c in value for c in [" ", '"', "'"]) and not value.startswith("%"):
            continue
        # domain, includeSubdomains, path, secure, expires, name, value
        f.write(f".douyin.com\tTRUE\t/\tFALSE\t2147483647\t{name}\t{value}\n")
    
    # 同时也写 www.douyin.com
    for name, value in pairs:
        if any(c in value for c in [" ", '"', "'"]) and not value.startswith("%"):
            continue
        f.write(f"www.douyin.com\tTRUE\t/\tFALSE\t2147483647\t{name}\t{value}\n")

print("✅ 已保存 Netscape cookie 文件: dy_cookies_netscape.txt", file=sys.stderr)

# 用requests测试 - 先设置cookie jar
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

# 设置cookies
for name, value in pairs:
    session.cookies.set(name, value, domain=".douyin.com", path="/")

# 先访问首页，看能不能拿到新的session
print("\n=== 测试Cookie有效性 ===", file=sys.stderr)
r = session.get("https://www.douyin.com/", timeout=30)
# 看页面是否显示已登录
if "login" in r.text.lower()[:2000]:
    print("⚠️ 页面可能显示未登录状态", file=sys.stderr)

# 尝试获取推荐feed
print("\n=== 尝试推荐feed API ===", file=sys.stderr)
feed_url = "https://www.douyin.com/aweme/v1/web/feed/"
feed_params = {
    "aid": 1128,
    "count": 6,
    "type": 0,
    "max_cursor": 0,
    "min_cursor": 0,
    "pull_type": 2,
}
session.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.douyin.com/",
})
r2 = session.get(feed_url, params=feed_params, timeout=30)
print(f"  Feed Status: {r2.status_code}, 长度: {len(r2.text)}", file=sys.stderr)
if r2.text.strip():
    data = r2.json()
    print(f"  Feed status_code: {data.get('status_code')}", file=sys.stderr)
    if data.get("status_code") == 0:
        aweme_count = len(data.get("aweme_list", []))
        print(f"  ✅ Feed正常! 获取到 {aweme_count} 个推荐视频", file=sys.stderr)

# 尝试用户post API
print("\n=== 尝试用户post API ===", file=sys.stderr)
SEC_UID = "MS4wLjABAAAAxkqwjpqCtOKE2teMgB20p5gH2qPctLVgtqUCZOmpLZs"
post_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
post_params = {
    "sec_user_id": SEC_UID,
    "count": 20,
    "max_cursor": 0,
    "aid": 1128,
}
r3 = session.get(post_url, params=post_params, timeout=30)
print(f"  Post API Status: {r3.status_code}, 长度: {len(r3.text)}", file=sys.stderr)
if r3.text.strip():
    data = r3.json()
    print(f"  status_code: {data.get('status_code')}", file=sys.stderr)
else:
    print("  ❌ 仍为空响应 - cookie可能已过期", file=sys.stderr)
