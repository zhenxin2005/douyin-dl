#!/usr/bin/env python3
"""调试：查看抖音API返回的内容"""
import requests
import json

SEC_UID = "MS4wLjABAAAAxkqwjpqCtOKE2teMgB20p5gH2qPctLVgtqUCZOmpLZs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.douyin.com/",
}

url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
params = {
    "sec_user_id": SEC_UID,
    "count": 5,
    "max_cursor": 0,
    "aid": 1128,
}

resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"Content (first 1000 chars):")
print(resp.text[:1000])
