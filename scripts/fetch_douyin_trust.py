#!/usr/bin/env python3
"""抓取抖音安全与信任中心文章并保存到知识库（修正版）"""
import os
import re
import sys
from playwright.sync_api import sync_playwright

KB_DIR = "C:\\Users\\zhenx\\knowledge-base\\抖音官方"
os.makedirs(KB_DIR, exist_ok=True)

articles = [
    ("从零开始了解推荐系统（完整版）", "https://95152.douyin.com/article/15358"),
    ("推荐算法升级：神经网络", "https://95152.douyin.com/article/15359"),
    ("深度学习与神经网络原理", "https://95152.douyin.com/article/15360"),
    ("抖音Wide&Deep模型", "https://95152.douyin.com/article/15361"),
    ("抖音双塔召回模型", "https://95152.douyin.com/article/15362"),
    ("总结推荐算法", "https://95152.douyin.com/article/15363"),
    ("算法和用户都想打破信息茧房", "https://95152.douyin.com/article/15366"),
]

def extract_article_body(text, title_hint=""):
    """从页面全文文本中提取文章正文"""
    lines = text.split("\n")
    
    # 找到正文开始: 标题后的内容
    # 查找"2025年03月30日"之类的时间标记，表示正文开始
    start_markers = ["2025年", "2026年", "今天，", "推荐算法"]
    
    # 方法1：找到文章标题行之后的内容
    # 从导航列表之后找
    body_start = 0
    for i, line in enumerate(lines):
        line_s = line.strip()
        # 跳过导航栏，找到第一个正文标题
        if line_s == "从零开始了解推荐系统":
            # 继续找下一段正文开始（跳过重复的标题）
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip() and lines[j].strip() != "从零开始了解推荐系统" and len(lines[j].strip()) > 5:
                    body_start = j
                    break
            break
    
    if body_start == 0:
        body_start = 4  # fallback
    
    # 找到尾部版权信息并截断
    body_end = len(lines)
    for i in range(body_start, len(lines)):
        if "2026 © 抖音" in lines[i] or "广告投放" == lines[i].strip():
            body_end = i
            break
    
    body_lines = lines[body_start:body_end]
    return "\n".join(body_lines).strip()

def fetch(page, url, label):
    print(f"📡 {label}...", file=sys.stderr)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000)
    
    text = page.evaluate("() => document.body.innerText")
    body = extract_article_body(text, label)
    
    if not body or len(body) < 50:
        # 如果提取失败，用全文
        body = text
    
    safe = re.sub(r'[\\/:*?"<>|]', '_', label[:50])
    fpath = os.path.join(KB_DIR, f"{safe}.md")
    
    md = [
        f"# {label}\n",
        f"> **来源**: [抖音安全与信任中心](https://95152.douyin.com/)",
        f"> **链接**: {url}",
        f"> **抓取日期**: 2026-06-18",
        "",
        "---\n",
        body
    ]
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    
    print(f"  ✅ {len(body)}字 ✅", file=sys.stderr)
    return len(body)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        total = 0
        for label, url in articles:
            size = fetch(page, url, label)
            total += size
        
        browser.close()
    
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"✅ 共 {len(articles)} 篇, {total} 字", file=sys.stderr)
    print(f"📁 {KB_DIR}", file=sys.stderr)
    for f in sorted(os.listdir(KB_DIR)):
        if f.endswith(".md"):
            fp = os.path.join(KB_DIR, f)
            sz = os.path.getsize(fp)
            print(f"  📄 {f} ({sz/1024:.1f}KB)", file=sys.stderr)

if __name__ == "__main__":
    main()
