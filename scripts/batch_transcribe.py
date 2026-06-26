#!/usr/bin/env python3
"""批量转写 - 直接导入模块方式，避免subprocess编码问题"""
import json
import os
import sys
import re
import importlib.util

KB_DIR = "C:\\Users\\zhenx\\knowledge-base\\羽川"
VIDEO_DIR = "C:\\Users\\zhenx\\douyin-dl\\downloads\\羽川"
os.makedirs(KB_DIR, exist_ok=True)

# 加载视频元数据
with open("C:\\Users\\zhenx\\videos.json", "r", encoding="utf-8") as f:
    videos_meta = json.load(f)

# 动态导入 douyin_transcribe 的转写函数
spec = importlib.util.spec_from_file_location(
    "dt", "C:\\Users\\zhenx\\douyin-transcriber\\douyin_transcribe.py"
)
dt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dt)
transcribe_local = dt.transcribe_local

video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")])
existing_kb = {f.replace(".md", "") for f in os.listdir(KB_DIR) if f.endswith(".md")}
existing_kb.add("_index.json")

# 建立文件名到元数据的映射
file_to_meta = {}
for v in videos_meta:
    dp = v["date"][:10]
    ds = v["desc"][:40]
    ds = ds.replace("/", "_").replace("\\", "_").replace(":", "_")
    ds = ds.replace("?", "_").replace("*", "_").replace('"', "_")
    ds = ds.replace("<", "_").replace(">", "_").replace("|", "_")
    file_to_meta[f"{dp}_{ds}"] = v

success = 0
for idx, fname in enumerate(video_files, 1):
    filepath = os.path.join(VIDEO_DIR, fname)
    kb_name = fname.replace(".mp4", "")
    kb_path = os.path.join(KB_DIR, kb_name + ".md")

    if kb_name in existing_kb:
        print(f"  ⏭ [{idx}/{len(video_files)}] 已有: {fname[:50]}", file=sys.stderr)
        success += 1
        continue

    print(f"\n🎙️ [{idx}/{len(video_files)}] {fname[:50]}", file=sys.stderr)
    print(f"  大小: {os.path.getsize(filepath)/(1024*1024):.1f}MB", file=sys.stderr)

    try:
        text = transcribe_local(filepath, dt.DEFAULT_MODELS["local"], "text")
        if not text:
            print(f"  ❌ 转写结果为空", file=sys.stderr)
            continue
    except Exception as e:
        print(f"  ❌ 转写失败: {e}", file=sys.stderr)
        continue

    # 找元数据
    meta = None
    for key, v in file_to_meta.items():
        if key[:20] in fname or fname[:30].startswith(key[:20]):
            meta = v
            break

    desc = meta["desc"] if meta else kb_name
    tags = " ".join(re.findall(r"#[^\s#]+", desc)) if meta else ""
    date_str = meta["date"] if meta else kb_name[:10]
    duration_str = f"{meta['duration']//1000//60}:{meta['duration']//1000%60:02d}" if meta else "?"
    author = meta["author"] if meta else "羽川"
    share_url = meta["share_url"] if meta else ""

    md = []
    md.append(f"# {desc}\n")
    md.append(f"> **日期**: {date_str}")
    md.append(f"> **时长**: {duration_str}")
    md.append(f"> **作者**: {author}")
    md.append(f"> **标签**: {tags}")
    if share_url:
        md.append(f"> **链接**: [{share_url}]({share_url})")
    md.append("")
    md.append("---\n")
    md.append("## 逐字稿\n")
    md.append(text)
    md.append("")
    md.append("---\n")
    md.append("## 核心观点\n")
    md.append("> (待补充)\n")

    with open(kb_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    text_len = len(text)
    print(f"  ✅ {text_len}字 → {kb_name}.md", file=sys.stderr)
    success += 1

print(f"\n📊 汇总: 成功 {success} / {len(video_files)}", file=sys.stderr)

# 生成索引
print("\n📚 生成索引...", file=sys.stderr)
index = []
for fname in sorted(os.listdir(KB_DIR)):
    if not fname.endswith(".md"):
        continue
    fpath = os.path.join(KB_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    title = re.search(r"^# (.+)", c)
    date_m = re.search(r"> \*\*日期\*\*: (.+)", c)
    tags_m = re.search(r"> \*\*标签\*\*: (.+)", c)
    text_m = re.search(r"## 逐字稿\n(.+?)(?:\n---|\Z)", c, re.DOTALL)
    index.append({
        "title": title.group(1) if title else fname,
        "date": date_m.group(1) if date_m else "",
        "tags": tags_m.group(1) if tags_m else "",
        "file": fname,
        "summary": (text_m.group(1).strip()[:150] + "..." if text_m else ""),
        "chars": len(c),
    })

with open(os.path.join(KB_DIR, "_index.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"\n✅ 知识库：{len(index)} 篇")
for i, item in enumerate(index, 1):
    print(f"  {i}. {item['date']} | {item['title'][:40]} | {item['chars']}字")
print(f"\n📁 {KB_DIR}")
