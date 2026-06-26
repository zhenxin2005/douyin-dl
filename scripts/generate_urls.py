#!/usr/bin/env python3
"""读取videos.json生成urls.txt用于批量下载"""
import json

with open("C:\\Users\\zhenx\\videos.json", "r", encoding="utf-8") as f:
    videos = json.load(f)

with open("C:\\Users\\zhenx\\douyin-dl\\scripts\\urls.txt", "w", encoding="utf-8") as f:
    for v in videos:
        f.write(v["share_url"] + "\n")

print(f"✅ 已写入 {len(videos)} 个链接到 urls.txt")
for v in videos:
    print(f"  {v['date']} | {v['share_url']}")
