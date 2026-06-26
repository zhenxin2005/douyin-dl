#!/usr/bin/env python3
"""提取抖音视频作者的 sec_uid 信息"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("douyin_dl", os.path.join(os.path.dirname(os.path.abspath(__file__)), "douyin-dl.py"))
douyin_dl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(douyin_dl)
fetch_page = douyin_dl.fetch_page

url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/S6OkGBkgy2Q/"

html = fetch_page(url)
match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
data = json.loads(match.group(1))
item = data['loaderData']['video_(id)/page']['videoInfoRes']['item_list'][0]
author = item.get('author', {})

# 提取关键作者信息
info = {
    "nickname": author.get("nickname"),
    "unique_id": author.get("unique_id"),
    "sec_uid": author.get("sec_uid"),
    "uid": author.get("uid"),
    "short_id": author.get("short_id"),
    "signature": author.get("signature"),
}
print(json.dumps(info, ensure_ascii=False, indent=2))
