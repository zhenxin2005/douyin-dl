#!/usr/bin/env python3
"""直接用ffmpeg录制抖音直播"""
import subprocess, sys, os
from datetime import datetime

sys.path.insert(0, "C:\\Users\\zhenx\\douyin-recorder")
from douyin_recorder.stream_extractor import StreamExtractor

ROOM_URL = "https://live.douyin.com/452466948652"
OUTPUT_DIR = "C:\\Users\\zhenx\\douyin-dl\\downloads\\直播间录制"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 获取流地址
print("📡 获取直播流地址...")
extractor = StreamExtractor()
info = extractor.extract(ROOM_URL)

if not info or not info.is_live:
    print("❌ 直播间未开播")
    sys.exit(1)

stream_url = info.stream_url
print(f"✅ 流地址获取成功")

# ffmpeg录制（tiny模式：540p H.265，30分钟）
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out = os.path.join(OUTPUT_DIR, f"DOUYIN_452466948652_{ts}_30min.ts")

cmd = [
    "ffmpeg", "-i", stream_url,
    "-t", "1800",
    "-vf", "scale=304:540",
    "-c:v", "libx265",
    "-preset", "ultrafast",
    "-crf", "32",
    "-c:a", "aac",
    "-b:a", "32k",
    "-y", out
]

print(f"🎬 录制30分钟 (540p H.265, tiny模式)")
print(f"   输出: {out}\n")

subprocess.run(cmd)
print(f"\n✅ 录制完成: {out}")
