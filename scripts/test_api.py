#!/usr/bin/env python3
"""直接用requests测试cookies并获取视频列表"""
import requests
import json
import sys
from datetime import datetime, timezone

# 读取原始cookie字符串
with open("C:\\Users\\zhenx\\Documents\\cookies.txt", "r", encoding="utf-8") as f:
    content = f.read().strip()

lines = [l.strip() for l in content.split("\n") if l.strip()]
cookie_str = lines[-1]

# 解析为字典
cookie_dict = {}
for item in cookie_str.split(";"):
    item = item.strip()
    if "=" in item:
        k, v = item.split("=", 1)
        cookie_dict[k.strip()] = v.strip()

SEC_UID = "MS4wLjABAAAAxkqwjpqCtOKE2teMgB20p5gH2qPctLVgtqUCZOmpLZs"

# 直接用cookie字典请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.douyin.com/",
    "Origin": "https://www.douyin.com",
}

# 直接访问视频列表API - 将cookies作为dict传入
api_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
params = {
    "sec_user_id": SEC_UID,
    "count": 50,
    "max_cursor": 0,
    "aid": 1128,
}

resp = requests.get(api_url, headers=headers, cookies=cookie_dict, params=params, timeout=30)
print(f"Status: {resp.status_code}, Length: {len(resp.text)}", file=sys.stderr)

if resp.text.strip():
    data = resp.json()
    sc = data.get("status_code")
    print(f"status_code: {sc}", file=sys.stderr)
    
    if sc == 0:
        aweme_list = data.get("aweme_list", [])
        print(f"✅ 成功! 共 {len(aweme_list)} 个视频", file=sys.stderr)
        
        # 过滤5月8日之后
        since_ts = datetime(2026, 5, 8, tzinfo=timezone.utc).timestamp()
        filtered = []
        
        for item in aweme_list:
            ct = item.get("create_time", 0)
            if ct >= since_ts:
                video = item.get("video", {})
                author = item.get("author", {})
                filtered.append({
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
        
        print(f"5月8日后: {len(filtered)} 个", file=sys.stderr)
        print(f"还有更多: {data.get('has_more', False)}", file=sys.stderr)
        
        # 输出
        result = {"videos": filtered, "has_more": data.get("has_more"), "max_cursor": data.get("max_cursor")}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 保存
        with open("videos.json", "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print("\n已保存到 videos.json", file=sys.stderr)
    else:
        print(f"API错误: {json.dumps(data, ensure_ascii=False)[:300]}", file=sys.stderr)
else:
    print("❌ 空响应 - cookie可能已过期", file=sys.stderr)
    
    # 尝试先访问首页刷新cookie
    print("\n尝试先访问首页刷新session...", file=sys.stderr)
    s = requests.Session()
    s.headers.update({"User-Agent": headers["User-Agent"]})
    s.get("https://www.douyin.com/", timeout=15)
    
    # 再设置cookie
    resp2 = s.get(api_url, params=params, cookies=cookie_dict, timeout=30)
    print(f"第二次: Status={resp2.status_code}, Length={len(resp2.text)}", file=sys.stderr)
    if resp2.text.strip():
        data2 = resp2.json()
        sc2 = data2.get("status_code")
        print(f"第二次 status_code: {sc2}", file=sys.stderr)
